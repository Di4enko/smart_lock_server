import serial.tools.list_ports 
from fastapi import APIRouter, Depends, Form, HTTPException, Request, status
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from DB import DB

security = HTTPBasic()
router = APIRouter()
db = DB()

# Подключаем папку с шаблонами
templates = Jinja2Templates(directory="templates")

# --- КОНФИГУРАЦИЯ ---
ADMIN_USER = "admin"
ADMIN_PASS = "admin"
LOCK_API_KEY = "SUPER_SECRET_TOKEN_505"
LOCK_IP = "192.168.0.50"

# --- ЗАЩИТА (Basic Auth) ---
def get_current_username(credentials: HTTPBasicCredentials = Depends(security)):
    """Проверка логина и пароля"""
    correct_username = credentials.username == ADMIN_USER
    correct_password = credentials.password == ADMIN_PASS
    
    if not (correct_username and correct_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный логин или пароль",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username

# --- СТРАНИЦЫ АДМИНКИ ---

@router.get("/", response_class=HTMLResponse)
async def render_main_menu(request: Request, username: str = Depends(get_current_username)):
    return templates.TemplateResponse(request, "index.html", )

@router.get("/locks", response_class=HTMLResponse)
async def render_locks_admin(request: Request, username: str = Depends(get_current_username)):
    locks = db.getLocks() or []
    return templates.TemplateResponse(request, "locks.html", {"locks": locks})

@router.get("/keys", response_class=HTMLResponse)
async def render_keys_admin(request: Request, username: str = Depends(get_current_username)):
    keys = db.getKeys() or []
    ports = [port.device for port in serial.tools.list_ports.comports()]
    return templates.TemplateResponse(request, "keys.html", {"keys": keys, "ports": ports})
