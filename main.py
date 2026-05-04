import uvicorn
from fastapi import FastAPI
from routers import locks, admin, keys
from fastapi import Request
from fastapi.exceptions import RequestValidationError
import logging

# Настройки
PORT = 8082
CERT_FILE = 'ssl/cert.pem'
KEY_FILE = 'ssl/key.pem'

app = FastAPI(
    title="Smart Lock System",
    description="Система контроля и управления доступом",
    version="1.0.0"
)

# Подключаем модули (роутеры)
app.include_router(admin.router)
app.include_router(locks.router)
app.include_router(keys.router)

# @app.exception_handler(RequestValidationError)
# async def validation_exception_handler(request: Request, exc: RequestValidationError):
#     # Читаем тело запроса
#     body = await request.body()
#     logging.error(f"Ошибка валидации! Тело: {body.decode()}")
#     logging.error(f"Детали ошибки: {exc.errors()}")
    

if __name__ == "__main__":
    uvicorn.run(
        "main:app", 
        host="0.0.0.0", 
        port=PORT, 
        reload=True, 
        ssl_keyfile=KEY_FILE,
        ssl_certfile=CERT_FILE
    )