# app/rag/indexer.py
import os, glob, shutil
from pathlib import Path
from typing import List
from langchain_community.document_loaders import (
    TextLoader, PDFPlumberLoader, UnstructuredWordDocumentLoader, CSVLoader
)
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient

# === 환경 변수 기본 설정 ===
BASE_DATA_DIR = Path("data")
UPLOAD_DIR = BASE_DATA_DIR / "uploads"      # 임베딩 대기 파일
EMBEDDED_DIR = BASE_DATA_DIR / "embedded"   # 임베딩 완료 파일

QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
COLLECTION = os.getenv("QDRANT_COLLECTION", "kb")
EMB_MODEL = os.getenv("EMB_MODEL", "intfloat/multilingual-e5-base")

UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
EMBEDDED_DIR.mkdir(parents=True, exist_ok=True)


# ----------------------------------------------------------
# 1. 문서 로드 함수
# ----------------------------------------------------------
def load_docs() -> List:
    docs = []
    for p in glob.glob(str(UPLOAD_DIR / "**" / "*.*"), recursive=True):
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
    - data/uploads 안의 문서들만 로드
    - 청크 분할
    - 임베딩 생성
    - Qdrant 컬렉션에 업로드(색인)
    - 성공 시, 원본 파일을 data/embedded로 이동
    """
    docs = load_docs()

    if not docs:
        print(f"[RAG] No documents found in '{UPLOAD_DIR}'. 색인할 파일이 없습니다.")
        return

    splitter = RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=120)
    chunks = splitter.split_documents(docs)
    print(f"[RAG] {len(chunks)} chunks generated from {len(docs)} docs.")

    print(f"[RAG] Embedding model: {EMB_MODEL}")
    embeddings = HuggingFaceEmbeddings(model_name=EMB_MODEL)

    client = QdrantClient(url=QDRANT_URL)

    print(f"[RAG] Indexing into collection '{COLLECTION}' at {QDRANT_URL} ...")
    QdrantVectorStore.from_documents(
        documents=chunks,
        embedding=embeddings,
        url=QDRANT_URL,
        collection_name=COLLECTION,
        prefer_grpc=False,
    )

    print(f"[RAG] Successfully indexed {len(chunks)} chunks into '{COLLECTION}'.")

    # 임베딩 성공 후, uploads 안에 있던 파일들을 embedded로 이동
    move_uploaded_files()


def move_uploaded_files():
    for p in UPLOAD_DIR.glob("**/*.*"):
        src = Path(p)
        if not src.is_file():
            continue

        dst = EMBEDDED_DIR / src.name
        # 이름 충돌 처리
        if dst.exists():
            dst.unlink()  # 단순히 덮어쓰기
        shutil.move(str(src), str(dst))
        print(f"[RAG] Moved '{src}' -> '{dst}'")


if __name__ == "__main__":
    run()
