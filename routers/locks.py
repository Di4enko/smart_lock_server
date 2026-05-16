import requests
import logging
from fastapi import APIRouter, Depends, Form, HTTPException, status
from fastapi.responses import JSONResponse, PlainTextResponse
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

def validation(key, door):
    key_info = db.getKey(key)
    if key_info is not None:
        int_door = int(door)
        visitor, key, labs, valid = key_info
        if int_door in labs and valid:
            return True
    return False

# --- Модели данных ---
class AccessRequest(BaseModel):
    token: str
    door: str


# --- API для замков (POST) ---
@router.post("/check_access", response_class=PlainTextResponse)
async def check_access(request: AccessRequest):
    print(request)
    """
    Обработка запросов от нового замка на ESP8266 (JSON + HTTPS)
    """
    token: str= request.token.lower()
    door: str = request.door
    
    logging.info(f"Access attempt: Door={door}, Token={token}")
    
    # Валидация
    valid = validation(token, door)
    
    if valid:
        db.saveVisit(token, request.door, 'allowed')
        return "ALLOWED"
    else:
        db.saveVisit(token, request.door, 'denied')
        return "DENIED"

@router.post("/update_lock", response_class=JSONResponse)
async def update_lock(
    lab: Optional[str] = Form(None, alias='lab'), 
    server_ip: Optional[str] = Form(None, alias='server_ip'),
    lock_ip: Optional[str] = Form(None, alias='lock_ip'),
    old_ip: Optional[str] = Form(),
    username: str = Depends(get_current_username)
):
    """
    Получает данные из HTML формы и отправляет их на ESP8266
    """
    headers = {'X-Auth-Token': LOCK_API_KEY}
    payload = {}
    if lab:
        payload["lab"] = lab
    if lab:
        payload["lock_ip"] = lock_ip
    if lab:
        payload["server_ip"] = server_ip

    try:
        # Сервер отправляет команду замку
        response = requests.post(f"http://{lock_ip}/update", params=payload, headers=headers, timeout=5)
        
        if response.status_code == 200:
            db.updateLock(lab, old_ip, lock_ip=lock_ip, lab=lab, server_ip=server_ip)
            return {"status": "success", "message": f"Замок {lab} успешно обновлен."}
        else:
            return {"status": "error", "message": f"Замок вернул код {response.status_code}"}
    except Exception as e:
        logging.error(f"Ошибка связи: {e}")
        return {"status": "error", "message": f"Ошибка связи: {str(e)}"}
    
@router.post("/add_lock", response_class=JSONResponse)
async def add_lock(
    lab: str = Form(), 
    lock_ip: str = Form(),
    username: str = Depends(get_current_username)
):
    """
    Добавление нового замка
    """
    
    try:
        if db.addLock(lab, lock_ip):
            return {"status": "success", "message": "Замок успешно добавлен."}
        else:
            return {"status": "error", "message": "Не удалось добавить замок"}
    
    except Exception as e:
        logging.error(f"Ошибка БД: {e}")
        return {"status": "error", "message": "Не удалось добавить замок"}
    
@router.post("/dell_lock", response_class=JSONResponse)
async def dell_lock(
    lock_ip: str = Form(),
    username: str = Depends(get_current_username)
):
    """
    Удаление замка
    """
    
    try:
        if db.dellLock(lock_ip):
            return {"status": "success", "message": "Замок успешно удален."}
        else:
            return {"status": "error", "message": "Не удалось удалить замок"}
    
    except Exception as e:
        logging.error(f"Ошибка БД: {e}")
        return {"status": "error", "message": "Не удалось удалить замок"}
    

@router.get("/find_lock")
async def find_lock(lock_ip: str, username: str = Depends(get_current_username)):
    """Отправляет команду на ESP8266, чтобы она мигнула светодиодом или пискнула"""
    headers = {'X-Auth-Token': LOCK_API_KEY}
    try:
        # Допустим, на замке есть эндпоинт /identify
        requests.get(f"http://{lock_ip}/identify", headers=headers, timeout=3)
        return {"status": "ok"}
    except:
        raise HTTPException(status_code=502, detail="Lock unreachable")

    
