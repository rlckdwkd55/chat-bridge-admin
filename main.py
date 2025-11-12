from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

# .env 로드
load_dotenv()

app = FastAPI(title="GPT Bridge (Lean)")

# CORS (개발 편의: 모두 허용)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_methods=["*"], allow_headers=["*"]
)

# 정적/템플릿
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# 기본 페이지
@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

# API 라우터 등록 (POST /api/ask)
from app.api.routes import router as api_router
app.include_router(api_router, prefix="/api")
