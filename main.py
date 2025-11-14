from dotenv import load_dotenv
load_dotenv()

from pathlib import Path
from datetime import datetime

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.api.system import router as system_router
from app.api.routes import router as chat_router
from app.api.upload import router as upload_router


app = FastAPI(title="Chat Bridge Admin")

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# 정적 리소스 및 템플릿 경로
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# 업로드 디렉토리 설정
UPLOAD_DIR = Path("data/uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "title": "대시보드"},
    )


@app.get("/chat", response_class=HTMLResponse)
async def chat_page(request: Request):
    return templates.TemplateResponse(
        "chat.html",
        {"request": request, "title": "채팅"},
    )


@app.get("/upload", response_class=HTMLResponse)
async def upload_page(request: Request):
    # 파일 목록 읽기
    files = []
    for file_path in UPLOAD_DIR.glob("*"):
        if file_path.is_file():
            files.append(
                {
                    "name": file_path.name,
                    "uploaded_at": datetime.fromtimestamp(
                        file_path.stat().st_mtime
                    ).strftime("%Y-%m-%d %H:%M:%S"),
                    "status": "업로드됨",
                }
            )

    return templates.TemplateResponse(
        "upload.html",
        {
            "request": request,
            "title": "임베딩 파일 업로드",
            "files": files,
            "count": len(files),
        },
    )


# API 라우터 등록
app.include_router(system_router)
app.include_router(chat_router)
app.include_router(upload_router)