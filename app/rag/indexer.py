import os, glob
from typing import List
from langchain_community.document_loaders import (TextLoader, PDFPlumberLoader, UnstructuredWordDocumentLoader, CSVLoader)
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient


# === 환경 변수 기본 설정 ===
DATA_DIR = "data"  # 색인할 문서들이 들어있는 폴더
QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")  # Qdrant 서버 주소
COLLECTION = os.getenv("QDRANT_COLLECTION", "kb")               # 컬렉션 이름 (knowledge base)
EMB_MODEL = os.getenv("EMB_MODEL", "intfloat/multilingual-e5-base")  # 임베딩 모델


# ----------------------------------------------------------
# 1. 문서 로드 함수
# ----------------------------------------------------------
def load_docs() -> List:
    docs = []
    for p in glob.glob(os.path.join(DATA_DIR, "**", "*.*"), recursive=True):
        lower = p.lower()
        try:
            if lower.endswith((".txt", ".md")):
                docs += TextLoader(p, encoding="utf-8").load()
            elif lower.endswith(".pdf"):
                docs += PDFPlumberLoader(p).load()
            elif lower.endswith((".docx", ".doc")):
                docs += UnstructuredWordDocumentLoader(p).load()
            elif lower.endswith(".csv"):
                docs += CSVLoader(p).load()
        except Exception as e:
            print(f"[RAG] Failed to load {p}: {e}")
    return docs

# ----------------------------------------------------------
# 2. 색인 실행 함수
# ----------------------------------------------------------
def run():
    """
    - 문서 로드
    - 청크 분할
    - 임베딩 생성
    - Qdrant 컬렉션에 업로드(색인)
    """
    docs = load_docs()

    # 1. 색인할 문서가 없을 경우 중단
    if not docs:
        print(f"[RAG] No documents found in '{DATA_DIR}'. 색인할 파일이 없습니다.")
        return

    # 2. 문서 분할 (긴 문서는 800자 단위로 자르고 120자 겹치게)
    splitter = RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=120)
    chunks = splitter.split_documents(docs)
    print(f"[RAG] {len(chunks)} chunks generated from {len(docs)} docs.")

    # 3.  임베딩 모델 로드 (HuggingFace)
    print(f"[RAG] Embedding model: {EMB_MODEL}")
    embeddings = HuggingFaceEmbeddings(model_name=EMB_MODEL)

    # 4. Qdrant 클라이언트 연결
    client = QdrantClient(url=QDRANT_URL)

    # 5. Qdrant에 색인 업로드
    print(f"[RAG] Indexing into collection '{COLLECTION}' at {QDRANT_URL} ...")
    QdrantVectorStore.from_documents(
        documents=chunks,
        embedding=embeddings,
        url=QDRANT_URL,
        collection_name=COLLECTION,
        prefer_grpc=False,  # gRPC보다 HTTP 방식 (로컬용)
    )

    print(f"[RAG] Successfully indexed {len(chunks)} chunks into '{COLLECTION}'.")


# ----------------------------------------------------------
# 3. 진입점
# ----------------------------------------------------------
if __name__ == "__main__":
    run()
