# app/api/upload.py
from pathlib import Path

from fastapi import APIRouter, UploadFile, File, HTTPException

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
