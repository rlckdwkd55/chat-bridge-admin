# server.py
from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from app.api.system import router as system_router
from app.api.routes import router as chat_router


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


@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "title": "대시보드"},
    )


@app.get("/chat", response_class=HTMLResponse)
async def chat(request: Request):
    return templates.TemplateResponse(
        "chat.html",
        {"request": request, "title": "채팅"},
    )


@app.get("/upload", response_class=HTMLResponse)
async def upload(request: Request):
    return templates.TemplateResponse(
        "upload.html",
        {"request": request, "title": "임베딩 파일 업로드"},
    )


# API 라우터 등록
app.include_router(system_router)
app.include_router(chat_router)
