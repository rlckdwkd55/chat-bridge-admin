from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="Chat Bridge Admin")

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)

# 정적 리소스 및 템플릿 경로
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=HTMLResponse)
async def admin(request: Request):
    return templates.TemplateResponse("base.html", {"request": request, "title": "Dashboard"})

# === AdminLTE 페이지 라우트 ===
@app.get("/admin", response_class=HTMLResponse)
async def admin_dashboard(request: Request):
    return templates.TemplateResponse("admin/dashboard.html", {"request": request, "title": "Dashboard"})

@app.get("/admin/chat", response_class=HTMLResponse)
async def admin_chat(request: Request):
    return templates.TemplateResponse("admin/chat.html", {"request": request, "title": "Chat"})

@app.get("/admin/upload", response_class=HTMLResponse)
async def admin_upload(request: Request):
    return templates.TemplateResponse("admin/upload.html", {"request": request, "title": "Upload"})
