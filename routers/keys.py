import secrets
import serial
import time
import logging
from fastapi import APIRouter, Depends, Form, HTTPException, status, Request
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from typing import Optional
from DB import DB
from pydantic import BaseModel
from DB import DB

router = APIRouter()

# --- Настройка логгера и базы данных ---
logging.basicConfig(level=logging.INFO)
security = HTTPBasic()


db = DB()

LOCK_API_KEY = "SUPER_SECRET_TOKEN_505"
ADMIN_USER = "admin"
ADMIN_PASS = "admin"

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

# --- Модели данных ---
class AccessRequest(BaseModel):
    token: str
    door: str

# --- API для ключей (POST) ---

@router.post("/dell_key", response_class=JSONResponse)
async def dell_key(
    key: str = Form(None, alias='key'),
    username: str = Depends(get_current_username)
):
    """
    Получает данные из HTML формы и отправляет их на ESP8266
    """
    try:
       
        if db.dellKey(key):
            return {"status": "success", "message": "Ключ успешно удален."}
        else:
            return {"status": "error", "message": "Не удалось удалить ключ"}
    
    except Exception as e:
        logging.error(f"Ошибка БД: {e}")
        return {"status": "error", "message": "Не удалось удалить ключ"}
    
@router.get("/add_key", response_class=JSONResponse)
async def add_key():
    try:
        # 1. Генерируем 16 байт для блока 6
        # Используем структуру: 4 нуля + 8 байт ключа + 4 нуля
        random_key = secrets.token_bytes(8)
        data_packet = bytes([0x00]*4) + random_key + bytes([0x00]*4)
        key = data_packet.hex()
        logging.info("Ключ успешно сгенерирован")
        return {"status": "success", "message": str(key)}
    except Exception as e:
        logging.info("Ключ успешно сгенерирован")
        return {f'status": "error", "message": "Не удалось добавить ключ: {e}'}
    

@router.post("/save_key", response_class=JSONResponse)
async def add_key(request: Request):
    payload = await request.json()
    try:
        res_labs = [int(r.strip()) for r in payload['labs'].split(",")]
        if db.addKey(payload['visitor'], payload['key'], res_labs, payload['valid']):
            logging.info("Ключ успешно сохранен в БД.")
            return {"status": "success", "message": "Ключ успешно добавлен"}
        else:
            logging.info("Не удалось сохранить ключ в БД")  
            return {"status": "error", "message": "Не удалось добавить ключ"}
    except Exception as e:
           logging.error(f"Ошибка записи в БД: {e}")
    return {"status": "error", "message": "Не удалось добавить ключ"}
