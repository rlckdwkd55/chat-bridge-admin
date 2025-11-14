import os
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from ..service.chat_service import ask_upstream
from ..service.rag_service import build_context, augment_prompt

router = APIRouter(
    prefix="/api/chat",
    tags=["chat"]
)

# .env 설정값 중 STRICT_RAG: RAG 엄격 모드 (컨텍스트 없으면 바로 종료)
STRICT_RAG = os.getenv("STRICT_RAG", "false").lower() == "true"

@router.post("/ask")
async def ask(payload: dict):
    """
    클라이언트로부터 들어온 질의(`message`)를 받아
    1) RAG 컨텍스트를 생성하고
    2) 상황에 따라 LLM(vLLM 서버)에 전달하거나
    3) 색인 상태에 따라 안내 메시지를 반환하는 엔드포인트.

    - 색인 없음 → "색인 필요 안내"
    - 컨텍스트 없음 → "적절한 정보 없음 안내"
    - 컨텍스트 있음 → vLLM 호출 후 응답 반환
    """
    try:
        # 1. 입력 검증
        message = (payload.get("message") or "").strip()
        if not message:
            raise HTTPException(status_code=400, detail="message is required")

        # 2. .env 값 (없으면 기본값 사용)
        temperature = float(os.getenv("DEFAULT_TEMPERATURE", "0.7"))
        max_tokens  = int(os.getenv("DEFAULT_MAX_TOKENS", "4096"))
        system_prompt = os.getenv("DEFAULT_SYSTEM")

        # 3. RAG 컨텍스트 생성
        context, sources, ready = build_context(message)

        # 4. 색인된 데이터가 아예 없는 경우 (컬렉션 없음 or 비어 있음)
        if not ready:
            return JSONResponse({
                "ok": True,
                "answer": "현재 검색 가능한 데이터가 없습니다. 먼저 문서를 색인해 주세요.",
                "raw": {"reason": "no_collection_or_empty"}
            })

        # 5. 색인은 있지만 관련 문서가 없을 경우 (컨텍스트 없음)
        if STRICT_RAG and not context.strip():
            return JSONResponse({
                "ok": True,
                "answer": "관련된 정보를 찾을 수 없습니다. 다른 표현으로 다시 질문해 주세요.",
                "raw": {"reason": "no_context"}
            })

        # 6. LLM 프롬프트 생성
        system_prompt, augmented = augment_prompt(system_prompt, context, message)

        # 7. vLLM 서버로 질의 전송
        result = await ask_upstream(
            message=augmented,
            system=system_prompt,
            temperature=temperature,
            max_tokens=max_tokens,
        )

        # 8. 최종 응답 (일관된 포맷)
        return JSONResponse({
            "ok": True,
            "answer": result["answer"],
            "raw": {"llm_raw": result["raw"], "sources": sources}
        })

    # FastAPI 기본 예외
    except HTTPException as e:
        print("[/api/ask] HTTPException:", repr(e.detail))
        return JSONResponse(status_code=e.status_code, content={"ok": False, "error": e.detail})

    # 기타 모든 예외 (예: 네트워크, JSON 파싱, Qdrant 오류 등)
    except Exception as e:
        print("[/api/ask] Exception:", repr(e))
        return JSONResponse(status_code=500, content={"ok": False, "error": str(e)})
