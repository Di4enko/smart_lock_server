import requests
import logging
import serial.tools.list_ports 
from fastapi import APIRouter, Depends, Form, HTTPException, status
from fastapi.responses import HTMLResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from DB import DB


router = APIRouter(prefix="/admin")
security = HTTPBasic()

db = DB()

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
async def render_main_menu(username: str = Depends(get_current_username)):
    return """
    <html><head><title>СКУД Админ</title>
    <style>
        body { font-family: sans-serif; display: flex; justify-content: center; align-items: center; height: 100vh; background: #f0f2f5; }
        .menu { background: white; padding: 40px; border-radius: 12px; box-shadow: 0 4px 10px rgba(0,0,0,0.1); text-align: center; }
        .btn { display: block; width: 250px; padding: 15px; margin: 10px; background: #007bff; color: white; text-decoration: none; border-radius: 5px; font-weight: bold; }
        .btn:hover { background: #0056b3; }
    </style></head>
    <body>
        <div class="menu">
            <h2>Панель управления СКУД</h2>
            <a href="/admin/keys" class="btn">🔑 Администрирование ключей</a>
            <a href="/admin/locks" class="btn">🔒 Администрирование замков</a>
        </div>
    </body></html>
    """

@router.get("/locks", response_class=HTMLResponse)
async def render_locks_admin(username: str = Depends(get_current_username)):
    locks = db.getLocks()
    print(locks)
    rows_html = ""
    if locks.__sizeof__ != 0:
        for lock in locks:
            lab, address = lock
            rows_html += f"""
                <tr style="border: 2px solid black;">
                    <td style="padding: 15px; vertical-align: middle; background: #aaa; width: 30%;">
                        <strong style="font-size: 1.1em;">{lab}</strong><br>
                        <span style="color: #666;">IP: {address}</span>
                    </td>
                    <td style="padding: 15px;">
                        <form action="/admin/update_lock" method="post" style="margin: 0;">            
                            <div style="margin-bottom: 10px;">
                                <label style="display: block; font-weight: bold; margin-bottom: 5px;">Номер лаборатории:</label>
                                <input type="number" name="lab" placeholder="{lab}" style="width: 100%; max-width: 300px; padding: 8px; border: 1px solid #ccc; border-radius: 4px;">
                            </div>

                            <div style="margin-bottom: 15px;">
                                <label style="display: block; font-weight: bold; margin-bottom: 5px;">Адрес сервера:</label>
                                <input type="text" name="server_ip" placeholder="адрес сервера" style="width: 100%; max-width: 300px; padding: 8px; border: 1px solid #ccc; border-radius: 4px;">
                            </div>
                            
                            <div style="margin-bottom: 15px;">
                                <label style="display: block; font-weight: bold; margin-bottom: 5px;">Адрес замка:</label>
                                <input type="text" name="lock_ip" placeholder="{address}" style="width: 100%; max-width: 300px; padding: 8px; border: 1px solid #ccc; border-radius: 4px;">
                            </div>

                            <div>
                                <input type="hidden" name="old_ip" value="{address}">
                                <input type="submit" value="Применить настройки для {lab}" 
                                    style="background: #007bff; color: white; border: none; padding: 10px 20px; border-radius: 4px; cursor: pointer; font-weight: bold;">
                            </div>
                        </form>
                        <br>
                        <form action="/admin/find_lock" method="get" style="margin: 0;">            
                            <div>
                                <input type="hidden" name="lock_ip" value="{address}">
                                <input type="submit" value="Найти замок"
                                    style="background: #007bff; color: white; border: none; padding: 10px 20px; border-radius: 4px; cursor: pointer; font-weight: bold;">
                            </div>
                        </form>
                        <br>
                        <form action="/admin/dell_lock" method="post" style="margin: 0;">            
                            <div>
                                <input type="hidden" name="lock_ip" value="{address}">
                                <input type="submit" value="Удалить"
                                    style="background: red; color: white; border: none; padding: 10px 20px; border-radius: 4px; cursor: pointer; font-weight: bold;">
                            </div>
                        </form>
                    </td>
                </tr>
                """
        
    return f"""
        <html>
        <head>
            <title>Управление замками</title>
            <style>
                body {{ font-family: sans-serif; padding: 20px; background: #f4f7f6; }}
                .container {{ max-width: 900px; margin: auto; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }}
                table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
                th {{ text-align: left; background: #eee; padding: 10px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h2>Список активных замков</h2>
                <table>
                    <thead>
                        <tr>
                            <th>Замок / IP</th>
                            <th>Параметры конфигурации</th>
                        </tr>
                    </thead>
                    <tbody>
                        {rows_html}
                        <tr style="border: 2px solid black;">
                            <td style="padding: 15px; vertical-align: middle; background: #aaa; width: 30%;">
                                <strong style="font-size: 1.1em;">Новый замок</strong><br>
                            </td>
                            <td style="padding: 15px;">
                                <form action="/admin/add_lock" method="post" style="margin: 0;">            
                                    <div style="margin-bottom: 10px;">
                                        <label style="display: block; font-weight: bold; margin-bottom: 5px;">Номер лаборатории:</label>
                                        <input type="number" name="lab" required placeholder="{lab}" style="width: 100%; max-width: 300px; padding: 8px; border: 1px solid #ccc; border-radius: 4px;">
                                    </div>

                                    <div style="margin-bottom: 15px;">
                                        <label style="display: block; font-weight: bold; margin-bottom: 5px;">Адрес замка:</label>
                                        <input type="text" name="lock_ip" required placeholder="{address}" style="width: 100%; max-width: 300px; padding: 8px; border: 1px solid #ccc; border-radius: 4px;">
                                    </div>

                                    <div>
                                        <input type="submit" value="Добавить замок" 
                                            style="background: #007bff; color: white; border: none; padding: 10px 20px; border-radius: 4px; cursor: pointer; font-weight: bold;">
                                    </div>
                                </form>
                            </td>
                        </tr>
                    </tbody>
                </table>
                <br>
                <a href="/admin" style="text-decoration: none; color: #007bff;">← Вернуться в меню</a>
            </div>
        </body>
        </html>
        """

@router.get("/keys", response_class=HTMLResponse)
async def render_keys_admin(username: str = Depends(get_current_username)):
    keys = db.getKeys()
    print(keys)
    rows_html = ""
    ports_html = ""
    ports = serial.tools.list_ports.comports()
    for port in ports:
        ports_html += f"""<option value="{port.device}">{port.device}</option>""" 
    if keys.__sizeof__ != 0:
        for key in keys:
            visitor, key, labs, valid = key
            rows_html += f"""
                <tr style="border: 2px solid black;">
                    <td style="padding: 15px; vertical-align: middle; background: #aaa; width: 30%;">
                        <strong style="font-size: 1.1em;">{visitor}</strong><br>
                    </td>
                    <td style="padding: 15px;">
                        <form action="/admin/update_key" method="post" style="margin: 0;">            
                            <div style="margin-bottom: 15px;">
                                <label style="display: block; font-weight: bold; margin-bottom: 5px;">Доступные помещения:</label>
                                <input type="text" name="labs" placeholder="{labs}" style="width: 100%; max-width: 300px; padding: 8px; border: 1px solid #ccc; border-radius: 4px;">
                            </div>
                            <div style="margin-bottom: 15px;">
                                <label style="display: block; font-weight: bold; margin-bottom: 5px;">Ключ активен:</label>
                                <input type="text" name="valid" placeholder="{"Да" if valid else "Нет"}" style="width: 100%; max-width: 300px; padding: 8px; border: 1px solid #ccc; border-radius: 4px;">
                            </div>

                            
                            <div>
                                <input type="hidden" name="visitor" value="{visitor}">
                                <input type="submit" value="Применить настройки" 
                                    style="background: #007bff; color: white; border: none; padding: 10px 20px; border-radius: 4px; cursor: pointer; font-weight: bold;">
                            </div>
                            <br>
                            <form action="/admin/dell_key" method="post" style="margin: 0;">            
                                <div>
                                    <input type="hidden" name="key" value="{key}">
                                    <input type="submit" value="Удалить"
                                        style="background: red; color: white; border: none; padding: 10px 20px; border-radius: 4px; cursor: pointer; font-weight: bold;">
                                </div>
                            </form>
                        </form>
                    </td>
                </tr>
                """
        
    return f"""
        <html>
        <head>
            <title>Управление ключами</title>
            <style>
                body {{ font-family: sans-serif; padding: 20px; background: #f4f7f6; }}
                .container {{ max-width: 900px; margin: auto; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }}
                table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
                th {{ text-align: left; background: #eee; padding: 10px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h2>Управление ключами</h2>
                <table>
                    <thead>
                        <tr>
                            <th>Владелец ключа</th>
                            <th>Параметры</th>
                        </tr>
                    </thead>
                    <tbody>
                        {rows_html}
                        <tr style="border: 2px solid black;">
                            <td style="padding: 15px; vertical-align: middle; background: #aaa; width: 30%;">
                                <strong style="font-size: 1.1em;">Новый ключ</strong><br>
                            </td>
                            <td style="padding: 15px;">
                                <form action="/admin/add_key" method="post" style="margin: 0;">            
                                    <div style="margin-bottom: 10px;">
                                        <label style="display: block; font-weight: bold; margin-bottom: 5px;">Владелец ключа:</label>
                                        <input type="text" name="visitor" required placeholder="ФИО" style="width: 100%; max-width: 300px; padding: 8px; border: 1px solid #ccc; border-radius: 4px;">
                                    </div>
                                    <div style="margin-bottom: 15px;">
                                        <label style="display: block; font-weight: bold; margin-bottom: 5px;">Выберите порт Nano:</label>
                                        <select name="port" style="width: 100%; max-width: 300px; padding: 8px; border-radius: 4px;">
                                        {ports_html}
                                        </select>
                                    </div>
                                    
                                    <div style="margin-bottom: 15px;">
                                        <label style="display: block; font-weight: bold; margin-bottom: 5px;">Доступные помещения:</label>
                                        <input type="text" name="labs" required placeholder="504, 505" style="width: 100%; max-width: 300px; padding: 8px; border: 1px solid #ccc; border-radius: 4px;">
                                    </div>

                                    <div>
                                        <input type="hidden" name="valid" value="True"> 
                                        <input type="submit" value="Добавить ключ" 
                                            style="background: #007bff; color: white; border: none; padding: 10px 20px; border-radius: 4px; cursor: pointer; font-weight: bold;">
                                    </div>
                                </form>
                            </td>
                        </tr>
                    </tbody>
                </table>
                <br>
                <a href="/admin" style="text-decoration: none; color: #007bff;">← Вернуться в меню</a>
            </div>
        </body>
        </html>
        """

# --- ОБРАБОТКА ФОРМЫ (POST) ---

@router.post("/update_lock", response_class=HTMLResponse)
async def update_lock(
    lab: str = Form(), 
    server_ip: str = Form(),
    lock_ip: str = Form(),
    username: str = Depends(get_current_username)
):
    """
    Получает данные из HTML формы и отправляет их на ESP8266
    """
    headers = {'X-Auth-Token': LOCK_API_KEY}

    payload = {'lab': lab}
    
    try:
        # Сервер отправляет команду замку
        response = requests.post(f"http://{LOCK_IP}/update", params=payload, headers=headers, timeout=5)
        
        if response.status_code == 200:
            return "<h1>Успех!</h1><p>Замок успешно обновлен.</p><a href='/admin/locks'>Назад</a>"
        else:
            return f"<h1>Ошибка</h1><p>Замок вернул код {response.status_code}</p><a href='/admin/locks'>Назад</a>"
    
    except Exception as e:
        logging.error(f"Ошибка связи с замком: {e}")
        return f"<h1>Ошибка связи</h1><p>{str(e)}</p><a href='/admin/locks'>Назад</a>"