import secrets
import serial
import time
import logging
from fastapi import APIRouter, Depends, Form, HTTPException, status, Request
from fastapi.responses import HTMLResponse, PlainTextResponse
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

@router.post("/admin/update_key", response_class=HTMLResponse)
async def update_lock(
    visitor: Optional[str] = Form(None, alias='visitor'),
    key: Optional[str] = Form(None, alias='key'),
    labs: Optional[str] = Form(None, alias='labs'),
    valid: Optional[str] = Form(None, alias='valid'),
    username: str = Depends(get_current_username)
):
    """
    Получает данные из HTML формы и отправляет их на ESP8266
    """
    if labs is not None:
        labs = [int(r.strip()) for r in labs.split(",")]
    try:
       
        if db.updateKey(visitor, key=key, labs=labs, valid=valid):
            return "<h1>Успех!</h1><p>Замок успешно обновлен.</p><a href='/admin/keys'>Назад</a>"
        else:
            return f"<h1>Ошибка</h1><p>Не удалось обновить ключ</p><a href='/admin/keys'>Назад</a>"
    
    except Exception as e:
        logging.error(f"Ошибка связи с замком: {e}")
        return f"<h1>Ошибка связи</h1><p>{str(e)}</p><a href='/admin/keys'>Назад</a>"
      
@router.post("/admin/dell_key", response_class=HTMLResponse)
async def dell_key(
    key: str = Form(None, alias='key'),
    username: str = Depends(get_current_username)
):
    """
    Получает данные из HTML формы и отправляет их на ESP8266
    """
    try:
       
        if db.addKey(key):
            return "<h1>Успех!</h1><p>Ключ успешно удален.</p><a href='/admin/keys'>Назад</a>"
        else:
            return f"<h1>Ошибка</h1><p>Не удалось удалить ключ</p><a href='/admin/keys'>Назад</a>"
    
    except Exception as e:
        logging.error(f"Ошибка связи с замком: {e}")
        return f"<h1>Ошибка связи</h1><p>{str(e)}</p><a href='/admin/keys'>Назад</a>"
    
@router.post("/admin/add_key")
async def add_key(
    port: str = Form(...), 
    visitor: str = Form(None, alias='visitor'),
    labs: str = Form(None, alias='labs'),
    valid: str = Form(None, alias='valid'),
    username: str = Depends(get_current_username)
):
    try:
        # 1. Генерируем 16 байт для блока 6
        # Используем структуру: 4 нуля + 8 байт ключа + 4 нуля
        random_key = secrets.token_bytes(8)
        data_packet = bytes([0x00]*4) + random_key + bytes([0x00]*4)
        

        # 2. Открываем выбранный пользователем порт
        with serial.Serial(port, 9600, timeout=2) as ser:
            time.sleep(2) # Даем Nano перезагрузиться
            
            # Отправляем команду записи 'W' и пакет данных
            ser.write(b'W')
            ser.write(data_packet)
            
            # Читаем ответ от Nano
            response = ""
            while response == "":
                response = ser.readline().decode().strip()
            logging.info(response)
            if response == "Write complite":
                res_labs = [int(r.strip()) for r in labs.split(",")]
                key = data_packet.hex()
                try:
            
                    if db.addKey(visitor, key, res_labs, valid):
                        logging.info("Ключ успешно сохранен в БД.")
                    else:
                        logging.info("Не удалось сохранить ключ в БД")
        
                except Exception as e:
                    logging.error(f"Ошибка связи с замком: {e}")
                    return f"<h1>Ошибка связи</h1><p>{str(e)}</p><a href='/admin/keys'>Назад</a>"
                return f"<h1>Статус прошивки</h1><p>Использован порт: {port}</p><p>Ответ Nano: {response}</p><a href='/admin/locks'>Назад</a>"
            else:
                return f"<h1>Ошибка записи ключа</h1><a href='/admin/locks'>Назад</a>"        
    except Exception as e:
        return f"<h1>Ошибка порта</h1><p>{str(e)}</p><a href='/admin/locks'>Назад</a>"