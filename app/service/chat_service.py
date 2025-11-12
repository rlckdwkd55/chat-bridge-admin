import os
import httpx
from fastapi import HTTPException

# === 환경 변수 설정 ===
BASE_URL = os.getenv("OPENAI_COMPAT_BASE_URL") or ""  # 예: http://192.168.0.164:8999/v1
API_KEY = os.getenv("OPENAI_API_KEY") or ""            # 필요 시 Bearer 인증
TIMEOUT = httpx.Timeout(60.0, connect=10.0)            # 요청 타임아웃 (초)

# === vLLM(OpenAI 호환 API) 호출 ===
async def ask_upstream(message: str, *, system, temperature, max_tokens) -> dict:
    """
    사용자의 입력(message)을 vLLM(OpenAI 호환 서버)에 전달하고,
    모델의 응답을 받아 반환합니다.
    """

    # 환경 변수 누락 시 예외
    if not BASE_URL:
        raise RuntimeError("OPENAI_COMPAT_BASE_URL is not set")

    # 호출할 API 엔드포인트
    url = f"{BASE_URL}/chat/completions"

    # 기본 헤더
    headers = {"Content-Type": "application/json"}
    if API_KEY:
        headers["Authorization"] = f"Bearer {API_KEY}"

    # 요청 본문
    body = {
        "model": "openai/gpt-oss-20b",  # 사용할 모델 이름 (vLLM에서 지정된 alias)
        "messages": [
            {"role": "system", "content": system or "You are a helpful assistant."},
            {"role": "user", "content": message},
        ],
        "temperature": temperature,  # 창의성 정도 (0.0~1.0)
        "max_tokens": max_tokens,    # 응답 최대 길이
    }

    # === 실제 HTTP 요청 수행 ===
    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        r = await client.post(url, headers=headers, json=body)

        # vLLM에서 오류 코드 반환 시 예외 발생
        if r.status_code >= 400:
            raise HTTPException(status_code=r.status_code, detail=r.text)

        data = r.json()

    # === 응답 파싱 ===
    # OpenAI 포맷 기준으로 choices[0].message.content 추출
    answer = (data.get("choices") or [{}])[0].get("message", {}).get("content", "")

    # 최종 반환
    return {
        "answer": answer,  # 실제 모델의 응답 텍스트
        "raw": data,       # 전체 응답(JSON)을 함께 전달 (디버깅용)
    }
