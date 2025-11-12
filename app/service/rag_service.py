import os
from typing import Tuple, List
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient


# === 환경 변수 설정 ===
QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")     # Qdrant 서버 주소
COLLECTION = os.getenv("QDRANT_COLLECTION", "kb")                  # 기본 컬렉션 이름
EMB_MODEL = os.getenv("EMB_MODEL", "intfloat/multilingual-e5-base")  # 임베딩 모델 이름
TOP_K = int(os.getenv("RAG_TOP_K", "5"))                           # 검색할 문서 개수 (상위 K개)
MAX_CTX = int(os.getenv("RAG_MAX_CONTEXT_CHARS", "6000"))          # LLM에 전달할 컨텍스트 최대 길이 제한


# === 전역 객체 (lazy load: 한 번만 로딩 후 재사용) ===
_embeddings = None
_vectorstore = None


# ---------------------------------------------------------
# Qdrant 컬렉션이 준비되어 있는지 확인
#    - 컬렉션이 없거나, 벡터 데이터가 0개면 False 반환
#    - RAG 동작 전에 색인 여부를 점검하는 역할
# ---------------------------------------------------------
def _collection_ready() -> bool:
    client = QdrantClient(url=QDRANT_URL)
    try:
        # 컬렉션 존재/접속 여부를 먼저 확인
        client.get_collection(COLLECTION)
        # 정확한 포인트(벡터) 개수로 체크
        cnt = client.count(COLLECTION, exact=True)
        return (getattr(cnt, "count", 0) or 0) > 0
    except Exception as e:
        # 디버깅에 도움되도록 로그 남기기
        print(f"[RAG] _collection_ready error: {e}")
        return False


# ---------------------------------------------------------
# Qdrant 벡터스토어 및 임베딩 초기화
#    - 최초 1회 HuggingFace 임베딩 모델을 로드하고
#      QdrantVectorStore 인스턴스를 생성하여 재사용
# ---------------------------------------------------------
def _get_vs() -> QdrantVectorStore:
    global _embeddings, _vectorstore
    if _embeddings is None:
        _embeddings = HuggingFaceEmbeddings(model_name=EMB_MODEL)
    if _vectorstore is None:
        _vectorstore = QdrantVectorStore(
            client=QdrantClient(url=QDRANT_URL),
            collection_name=COLLECTION,
            embedding=_embeddings,
        )
    return _vectorstore


# ---------------------------------------------------------
# 질문(query)에 맞는 문맥(context) 생성
#    - Qdrant에서 질문과 유사한 문서를 TOP_K개 검색
#    - 문서 내용을 연결해 LLM에 전달할 컨텍스트 구성
#    - 색인 없음 → ("", [], False) 반환
#      색인 있음 → (context, sources, True) 반환
# ---------------------------------------------------------
def build_context(query: str) -> Tuple[str, List[str], bool]:
    if not _collection_ready():
        return "", [], False  # 색인 데이터 없음 → LLM 호출 생략

    vs = _get_vs()
    retriever = vs.as_retriever(search_kwargs={"k": TOP_K})

    # LangChain 0.2+ 호환 (우선 사용)
    if hasattr(retriever, "invoke"):
        docs = retriever.invoke(query)
    else:
        # 구버전 호환
        docs = retriever.get_relevant_documents(query)

    buff, used = [], 0
    sources = []

    for i, d in enumerate(docs, 1):
        # 문서 원본 경로나 파일명 표시
        path = (d.metadata or {}).get("source") or (d.metadata or {}).get("path") or "unknown"
        piece = f"[Doc {i}] {path}\n{d.page_content}\n\n"

        # 컨텍스트 길이 제한 초과 시 중단
        if used + len(piece) > MAX_CTX:
            break

        buff.append(piece)
        sources.append(path)
        used += len(piece)

    # context(문맥), sources(문서 출처 목록), ready(색인 여부)
    return "".join(buff), sources, True


# ---------------------------------------------------------
# LLM에게 전달할 최종 프롬프트 구성
#    - context를 LLM 입력에 포함시켜 “검색+생성 결합형” 프롬프트 구성
#    - context가 비어 있으면 LLM이 자연스럽게 “관련 정보 없음” 응답 유도
# ---------------------------------------------------------
def augment_prompt(system_prompt: str | None, context: str, user_message: str):
    prefix = (
        "You are a retrieval-augmented assistant.\n"
        "Use ONLY the provided context. If no relevant context is available, "
        "respond naturally by saying you have no related information.\n\n"
        f"=== Context ===\n{context}=== End Context ===\n\n"
    )
    return system_prompt, prefix + user_message
