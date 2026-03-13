import os
import sys
import json
import time
import threading
import base64
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Dict, Any

# Импорты для ASGI-сервера
try:
    from fastapi import FastAPI, HTTPException, Request
    from fastapi.responses import JSONResponse
    from fastapi.middleware.cors import CORSMiddleware
except ImportError as e:
    print(f"! Ошибка импорта FastAPI: {e}")
    print("! Убедитесь, что fastapi установлен: pip install fastapi uvicorn")
    sys.exit(1)

import requests

# ========== НАСТРОЙКИ ==========
BOT_TOKEN = os.getenv("BOT_TOKEN", "8426233676:AAGPALZ6pA8hLQERcD5oUxkRjzp0GqE2ej8")  # Токен из переменных окружения
DATA_FILE = Path("napomni_data.json")
API = f"https://api.telegram.org/bot{BOT_TOKEN}"

print("=" * 50)
print("Napomni Telegram Bot (ASGI-версия)")
print("=" * 50)
print(f"Токен: {BOT_TOKEN[:10]}...")
print(f"Файл данных: {DATA_FILE.absolute()}")
print("=" * 50)

# ========== ОСНОВНЫЕ ФУНКЦИИ ==========
def load_data() -> Dict[str, Any]:
    """Загрузка данных из JSON-файла"""
    if DATA_FILE.exists():
        try:
            return json.loads(DATA_FILE.read_text(encoding="utf-8"))
        except Exception as e:
            print(f"Ошибка загрузки: {e}")
    return {"users": {}, "reminders": []}

def save_data(data: Dict[str, Any]):
    """Сохранение данных в JSON-файл"""
    DATA_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

def tg_send_message(chat_id: int, text: str) -> dict:
    """Отправка текстового сообщения через Telegram API"""
    try:
        r = requests.post(f"{API}/sendMessage", json={
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "HTML"
        }, timeout=10)
        return r.json()
    except Exception as e:
        print(f"Ошибка отправки сообщения: {e}")
        return {"ok": False}

def tg_send_photo(chat_id: int, photo_bytes: bytes, caption: str) -> dict:
    """Отправка фото через Telegram API"""
    try:
        files = {"photo": ("photo.jpg", photo_bytes)}
        r = requests.post(f"{API}/sendPhoto", data={
            "chat_id": chat_id,
            "caption": caption
        }, files=files, timeout=10)
        return r.json()
    except Exception as e:
        print(f"Ошибка отправки фото: {e}")
        return {"ok": False}

def parse_iso(iso_str: str):
    """Парсинг ISO даты"""
    try:
        s = iso_str.replace("Z", "+00:00")
        return datetime.fromisoformat(s)
    except Exception:
        return None

# ========== СОЗДАНИЕ FASTAPI APP ==========
app = FastAPI(title="Napomni API")

# Добавляем CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ========== ЭНДПОИНТЫ FASTAPI ==========
@app.get("/")
async def root():
    return {
        "status": "ok",
        "service": "Napomni Bot",
        "time": datetime.now().isoformat()
    }

@app.get("/ping")
async def ping():
    return {"ok": True, "time": datetime.now().isoformat()}

@app.get("/status")
async def status(client_id: str):
    """Проверка подключения пользователя"""
    data = load_data()
    return {"connected": client_id in data.get("users", {})}

@app.get("/list")
async def list_items(client_id: str):
    """Получение списка напоминаний пользователя"""
    data = load_data()
    users = data.get("users", {})
    if client_id not in users:
        return {"items": []}

    items = []
    for r in data.get("reminders", []):
        if r.get("client_id") != client_id:
            continue
        if not r.get("completed", False):
            items.append({
                "id": r.get("id"),
                "title": r.get("title"),
                "desc": r.get("desc"),
                "when": r.get("when"),
                "has_photo": bool(r.get("photo")),
            })
    return {"items": items}

@app.post("/upsert")
async def upsert(req: Request):
    """Создание или обновление напоминания"""
    try:
        body = await req.json()
    except Exception:
        raise HTTPException(status_code=400, detail="invalid_json")

    client_id = str(body.get("client_id", "")).strip()
    rid = str(body.get("id", "")).strip()
    title = str(body.get("title", "")).strip()
    desc = str(body.get("desc", "")).strip()
    when = str(body.get("when", "")).strip()
    photo = body.get("photo")

    if not client_id or not rid or not title or not when:
        raise HTTPException(status_code=400, detail="missing_fields")

    data = load_data()
    users = data.get("users", {})
    if client_id not in users:
        raise HTTPException(status_code=409, detail="not_connected")

    chat_id = users[client_id]

    # Удаляем старое напоминание
    rems = [r for r in data.get("reminders", []) if str(r.get("id")) != rid]
    
    # Добавляем новое
    rems.append({
        "id": rid,
        "client_id": client_id,
        "chat_id": chat_id,
        "title": title,
        "desc": desc,
        "when": when,
        "photo": photo,
        "completed": False,
        "created_at": datetime.now().isoformat()
    })
    
    data["reminders"] = rems
    save_data(data)

    return JSONResponse({"ok": True})

@app.post("/delete")
async def delete(req: Request):
    """Удаление напоминания"""
    try:
        body = await req.json()
    except Exception:
        raise HTTPException(status_code=400, detail="invalid_json")
        
    client_id = str(body.get("client_id", "")).strip()
    rid = str(body.get("id", "")).strip()
    
    if not client_id or not rid:
        raise HTTPException(status_code=400, detail="missing_fields")

    data = load_data()
    new_rems = []
    for r in data.get("reminders", []):
        if str(r.get("id")) == rid and r.get("client_id") == client_id:
            continue
        new_rems.append(r)
    
    data["reminders"] = new_rems
    save_data(data)
    return {"ok": True}

@app.post("/wipe")
async def wipe(req: Request):
    """Удаление всех напоминаний пользователя"""
    try:
        body = await req.json()
    except Exception:
        raise HTTPException(status_code=400, detail="invalid_json")
        
    client_id = str(body.get("client_id", "")).strip()
    if not client_id:
        raise HTTPException(status_code=400, detail="missing_fields")

    data = load_data()
    data["reminders"] = [r for r in data.get("reminders", []) if r.get("client_id") != client_id]
    save_data(data)
    return {"ok": True}

# ========== ФОНОВЫЕ ЗАДАЧИ ==========
def check_reminders_loop():
    """Поток для проверки и отправки напоминаний"""
    print("✅ Запущен поток проверки напоминаний")
    while True:
        try:
            data = load_data()
            reminders = data.get("reminders", [])
            now = datetime.now(timezone.utc)
            changed = False

            for r in reminders:
                if r.get("completed", False):
                    continue

                dt = parse_iso(r.get("when", ""))
                if not dt:
                    continue

                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)

                if now >= dt:
                    chat_id = r.get("chat_id")
                    if not chat_id:
                        continue

                    title = r.get("title", "")
                    desc = r.get("desc", "")
                    text = f"🔔 Напоминание\n\n<b>{title}</b>"
                    if desc:
                        text += f"\n\n{desc}"

                    photo = r.get("photo")
                    sent = False

                    if photo and isinstance(photo, str) and photo.startswith("data:image/"):
                        try:
                            _, b64 = photo.split(",", 1)
                            img_bytes = base64.b64decode(b64)
                            result = tg_send_photo(chat_id, img_bytes, text)
                            if result.get("ok"):
                                sent = True
                                print(f"📸 Фото отправлено {chat_id}")
                        except Exception as e:
                            print(f"Ошибка фото: {e}")

                    if not sent:
                        result = tg_send_message(chat_id, text)
                        if result.get("ok"):
                            sent = True
                            print(f"📨 Сообщение отправлено {chat_id}")

                    if sent:
                        print(f"✅ Отправлено напоминание '{title}' для {chat_id}")
                        r["completed"] = True
                        r["sent_at"] = now.isoformat()
                        changed = True

            if changed:
                save_data(data)
                print("💾 Данные сохранены")

        except Exception as e:
            print(f"❌ Ошибка в check_reminders_loop: {e}")

        time.sleep(3)

def handle_updates_loop():
    """Поток для обработки входящих сообщений Telegram"""
    offset = 0
    print("✅ Запущен поток обработки сообщений")
    
    while True:
        try:
            response = requests.get(f"{API}/getUpdates", params={
                "timeout": 30,
                "offset": offset
            }, timeout=35)
            
            r = response.json()

            if not r.get("ok"):
                time.sleep(3)
                continue

            for update in r.get("result", []):
                offset = update["update_id"] + 1
                msg = update.get("message")
                if not msg:
                    continue

                chat_id = msg["chat"]["id"]
                text = msg.get("text", "").strip()
                first_name = msg.get("from", {}).get("first_name", "пользователь")

                print(f"📨 Сообщение от {first_name} (id:{chat_id}): {text}")

                # /start - подключение
                if text.startswith("/start"):
                    parts = text.split(maxsplit=1)
                    payload = parts[1].strip() if len(parts) > 1 else ""

                    if payload:
                        data = load_data()
                        data.setdefault("users", {})[payload] = chat_id
                        save_data(data)
                        
                        welcome_text = (
                            f"✅ <b>Telegram подключён!</b>\n\n"
                            f"Привет, {first_name}!\n"
                            f"Теперь ты будешь получать напоминания с сайта.\n\n"
                            f"📌 Твой client_id: <code>{payload}</code>"
                        )
                        tg_send_message(chat_id, welcome_text)
                        print(f"🔗 Подключен client_id {payload} -> chat_id {chat_id}")
                    else:
                        tg_send_message(chat_id, 
                            "❌ Ошибка: не указан код подключения.\n"
                            "Открой сайт и нажми «Подключить Telegram»."
                        )

                # /help - справка
                elif text == "/help":
                    help_text = (
                        "🔍 <b>Доступные команды:</b>\n\n"
                        "/start [код] - подключить аккаунт\n"
                        "/myid - показать мой chat_id\n"
                        "/stats - статистика моих напоминаний\n"
                        "/clear_my - очистить мои напоминания\n"
                        "/help - это сообщение"
                    )
                    tg_send_message(chat_id, help_text)

                # /myid - показать свой chat_id
                elif text == "/myid":
                    tg_send_message(chat_id, 
                        f"🆔 <b>Твой chat_id:</b> <code>{chat_id}</code>\n"
                        f"👤 Имя: {first_name}"
                    )

                # /stats - статистика
                elif text == "/stats":
                    data = load_data()
                    
                    user_reminders = []
                    for r in data.get("reminders", []):
                        if r.get("chat_id") == chat_id:
                            user_reminders.append(r)
                    
                    total = len(user_reminders)
                    completed = sum(1 for r in user_reminders if r.get("completed", False))
                    active = total - completed
                    
                    stats_text = (
                        f"📊 <b>Статистика</b>\n\n"
                        f"Всего напоминаний: {total}\n"
                        f"✅ Выполнено: {completed}\n"
                        f"⏳ Активных: {active}"
                    )
                    tg_send_message(chat_id, stats_text)

                # /clear_my - очистить свои напоминания
                elif text == "/clear_my":
                    data = load_data()
                    
                    old_count = len([r for r in data.get("reminders", []) if r.get("chat_id") == chat_id])
                    data["reminders"] = [r for r in data.get("reminders", []) if r.get("chat_id") != chat_id]
                    
                    save_data(data)
                    tg_send_message(chat_id, 
                        f"🧹 <b>Очищено!</b>\n"
                        f"Удалено {old_count} напоминаний."
                    )

        except Exception as e:
            print(f"❌ Ошибка в handle_updates_loop: {e}")
            time.sleep(3)

# ========== ЗАПУСК ПРИ СТАРТЕ ==========
@app.on_event("startup")
async def startup_event():
    """Действия при запуске приложения"""
    print("🚀 Запуск Napomni API...")
    
    # Создаем файл данных если нет
    if not DATA_FILE.exists():
        save_data({"users": {}, "reminders": []})
        print("📁 Создан новый файл данных")
    
    # Запускаем фоновые потоки
    thread1 = threading.Thread(target=check_reminders_loop, daemon=True)
    thread1.start()
    
    thread2 = threading.Thread(target=handle_updates_loop, daemon=True)
    thread2.start()
    
    print("✅ Фоновые задачи запущены")
    print("=" * 50)

# Для локального запуска
if __name__ == "__main__":
    import uvicorn
    print("🚀 Локальный запуск сервера...")
    uvicorn.run(app, host="0.0.0.0", port=8000)
