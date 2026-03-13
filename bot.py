import os
import sys
import json
import time
import threading
import base64
from datetime import datetime, timezone
from pathlib import Path
import requests

# Токен бота (вставлен ваш токен)
BOT_TOKEN = "8426233676:AAGPALZ6pA8hLQERcD5oUxkRjzp0GqE2ej8"
DATA_FILE = Path("napomni_data.json")
API = f"https://api.telegram.org/bot{BOT_TOKEN}"

print("=" * 50)
print("Napomni Telegram Bot")
print("=" * 50)
print(f"Токен: {BOT_TOKEN[:10]}...")
print(f"Файл данных: {DATA_FILE.absolute()}")
print("=" * 50)

def load_data():
    if DATA_FILE.exists():
        try:
            return json.loads(DATA_FILE.read_text(encoding="utf-8"))
        except Exception as e:
            print(f"Ошибка загрузки: {e}")
    return {"users": {}, "reminders": []}

def save_data(data):
    DATA_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

def tg_send_message(chat_id, text):
    try:
        r = requests.post(f"{API}/sendMessage", json={
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "HTML"
        }, timeout=10)
        return r.json()
    except Exception as e:
        print(f"Ошибка отправки: {e}")
        return {"ok": False}

def tg_send_photo(chat_id, photo_bytes, caption):
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

def parse_iso(iso_str):
    try:
        s = iso_str.replace("Z", "+00:00")
        return datetime.fromisoformat(s)
    except Exception:
        return None

def check_reminders():
    """Проверяет и отправляет просроченные напоминания"""
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
            print(f"❌ Ошибка в check_reminders: {e}")

        time.sleep(3)

def handle_updates():
    """Обрабатывает входящие сообщения от Telegram"""
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
                username = msg.get("from", {}).get("username", "нет username")
                first_name = msg.get("from", {}).get("first_name", "пользователь")

                print(f"📨 Сообщение от {first_name} (@{username}, id:{chat_id}): {text}")

                # ===== ВСЕ КОМАНДЫ РАБОТАЮТ ДЛЯ ВСЕХ =====
                
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
                        f"👤 Имя: {first_name}\n"
                        f"📱 Username: @{username if username != 'нет username' else 'не указан'}"
                    )

                # /stats - статистика
                elif text == "/stats":
                    data = load_data()
                    
                    # Находим все напоминания пользователя
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
                    
                    # Удаляем только напоминания этого пользователя
                    old_count = len([r for r in data.get("reminders", []) if r.get("chat_id") == chat_id])
                    data["reminders"] = [r for r in data.get("reminders", []) if r.get("chat_id") != chat_id]
                    
                    save_data(data)
                    tg_send_message(chat_id, 
                        f"🧹 <b>Очищено!</b>\n"
                        f"Удалено {old_count} напоминаний."
                    )
                    print(f"🧹 Пользователь {chat_id} очистил свои напоминания")

                # /clear_all - очистить ВСЕ напоминания (тоже для всех, но с подтверждением)
                elif text == "/clear_all":
                    # Запрашиваем подтверждение
                    tg_send_message(chat_id, 
                        "⚠️ <b>ВНИМАНИЕ!</b>\n"
                        "Ты собираешься удалить ВСЕ напоминания ВСЕХ пользователей!\n\n"
                        "Если уверен, отправь:\n"
                        "<code>/confirm_clear_all</code>"
                    )

                # /confirm_clear_all - подтверждение очистки всего
                elif text == "/confirm_clear_all":
                    data = load_data()
                    total = len(data.get("reminders", []))
                    data["reminders"] = []
                    save_data(data)
                    
                    tg_send_message(chat_id, 
                        f"💥 <b>Все напоминания удалены!</b>\n"
                        f"Удалено записей: {total}"
                    )
                    print(f"💥 Пользователь {chat_id} очистил ВСЕ напоминания")

                # Любое другое сообщение
                elif not text.startswith("/"):
                    tg_send_message(chat_id, 
                        f"👋 Привет, {first_name}!\n"
                        f"Используй /help чтобы увидеть список команд."
                    )

        except Exception as e:
            print(f"❌ Ошибка в handle_updates: {e}")
            time.sleep(3)

def main():
    print("✅ Бот запускается...")
    
    # Создаем файл если нет
    if not DATA_FILE.exists():
        save_data({"users": {}, "reminders": []})
        print("📁 Создан новый файл данных")
    
    # Запускаем потоки
    reminders_thread = threading.Thread(target=check_reminders, daemon=True)
    reminders_thread.start()
    
    updates_thread = threading.Thread(target=handle_updates, daemon=True)
    updates_thread.start()
    
    print("✅ Бот успешно запущен!")
    print("📢 Все команды доступны всем пользователям")
    print("=" * 50)
    print("Команды:")
    print("  /start [код] - подключить аккаунт")
    print("  /myid - показать мой chat_id")
    print("  /stats - статистика моих напоминаний")
    print("  /clear_my - очистить мои напоминания")
    print("  /clear_all - очистить ВСЕ напоминания")
    print("  /help - помощь")
    print("=" * 50)
    
    # Держим главный поток живым
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n👋 Бот остановлен")

if __name__ == "__main__":
    main()
