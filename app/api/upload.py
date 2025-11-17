# app/api/upload.py
from pathlib import Path

from fastapi import APIRouter, UploadFile, File, HTTPException

from app.rag.indexer import run as run_indexer

router = APIRouter(prefix="/api/rag", tags=["rag"])

UPLOAD_DIR = Path("data/uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


@router.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    """
    업로드된 파일을 data/uploads 디렉토리에 저장합니다.
    """
    out_path = UPLOAD_DIR / file.filename

    try:
        contents = await file.read()
        out_path.write_bytes(contents)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"파일 저장 중 오류: {e}",
        )

    return {"ok": True, "filename": file.filename}

@router.post("/embed-all")
async def embed_all():
    try:
        run_indexer()
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"임베딩 중 오류: {e}",
        )

    return {"ok": True}

@router.delete("/file/{filename}")
async def delete_file(filename: str):
    file_path = UPLOAD_DIR / filename

    if not file_path.exists():
        raise HTTPException(status_code=404, detail="파일이 존재하지 않습니다.")

    try:
        file_path.unlink()
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"파일 삭제 중 오류: {e}",
        )

    return {"ok": True, "filename": filename}