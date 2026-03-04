import json
import time
import threading
from datetime import datetime
from pathlib import Path

import requests

TOKEN = "8426233676:AAGPALZ6pA8hLQERcD5oUxkRjzp0GqE2ej8"
BOT_USERNAME = "@napominalshik_fai_bot"
API = f"https://api.telegram.org/bot{TOKEN}"
DATA_FILE = Path("bot_data.json")
CHECK_EVERY_SECONDS = 15

last_update_id = 0


def load_data():
    if DATA_FILE.exists():
        try:
            return json.loads(DATA_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {"users": {}}


def save_data(data):
    DATA_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def ensure_user(data, chat_id):
    chat_id = str(chat_id)
    if chat_id not in data["users"]:
        data["users"][chat_id] = {
            "state": None,
            "temp": {},
            "reminders": []
        }
    return data["users"][chat_id]


def keyboard(rows):
    return {
        "keyboard": [[{"text": item} for item in row] for row in rows],
        "resize_keyboard": True,
        "one_time_keyboard": False,
    }


def send_message(chat_id, text, reply_markup=None):
    payload = {"chat_id": chat_id, "text": text}
    if reply_markup is not None:
        payload["reply_markup"] = reply_markup
    requests.post(f"{API}/sendMessage", json=payload, timeout=30)


def main_menu(chat_id, text=None):
    if text is None:
        text = (
            "Привет ✨\n\n"
            f"Я бот-напоминалка {BOT_USERNAME}\n"
            "Могу сохранить напоминание и отправить его в нужное время."
        )
    send_message(chat_id, text, keyboard([
        ["➕ Добавить", "📋 Список"],
        ["🗑 Удалить", "ℹ️ Помощь"]
    ]))


def parse_dt(value):
    value = value.strip()
    for fmt in ("%d.%m.%Y %H:%M", "%Y-%m-%d %H:%M"):
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            pass
    return None


def next_id(reminders):
    return max((r["id"] for r in reminders), default=0) + 1


def get_updates(offset=None):
    params = {"timeout": 30}
    if offset is not None:
        params["offset"] = offset
    r = requests.get(f"{API}/getUpdates", params=params, timeout=35)
    return r.json()


def format_reminder(r):
    status = "✅ отправлено" if r.get("sent") else "⏳ ждёт"
    text = f"ID {r['id']}\n🕒 {r['time']}\n📝 {r['title']}"
    if r.get("description"):
        text += f"\n📄 {r['description']}"
    text += f"\n{status}"
    return text


def handle_add_flow(user, chat_id, text, data):
    state = user["state"]

    if state == "wait_title":
        user["temp"] = {"title": text.strip()[:120]}
        user["state"] = "wait_description"
        save_data(data)
        send_message(chat_id, "Отправь описание. Если не нужно — отправь минус: -")
        return True

    if state == "wait_description":
        user["temp"]["description"] = "" if text.strip() == "-" else text.strip()[:600]
        user["state"] = "wait_datetime"
        save_data(data)
        send_message(chat_id, "Отправь дату и время\nНапример: 05.03.2026 18:30")
        return True

    if state == "wait_datetime":
        dt = parse_dt(text)
        if not dt:
            send_message(chat_id, "Неверный формат. Пример: 05.03.2026 18:30")
            return True

        reminder = {
            "id": next_id(user["reminders"]),
            "title": user["temp"].get("title", "Напоминание"),
            "description": user["temp"].get("description", ""),
            "time": dt.strftime("%Y-%m-%d %H:%M"),
            "sent": False,
        }
        user["reminders"].append(reminder)
        user["state"] = None
        user["temp"] = {}
        save_data(data)
        main_menu(chat_id, f"✅ Напоминание сохранено\n\n{format_reminder(reminder)}")
        return True

    if state == "wait_delete_id":
        raw = text.strip()
        if not raw.isdigit():
            send_message(chat_id, "Пришли ID числом. Например: 2")
            return True
        reminder_id = int(raw)
        before = len(user["reminders"])
        user["reminders"] = [r for r in user["reminders"] if r["id"] != reminder_id]
        user["state"] = None
        user["temp"] = {}
        save_data(data)
        if len(user["reminders"]) < before:
            main_menu(chat_id, "🗑 Напоминание удалено")
        else:
            main_menu(chat_id, "Такого ID нет")
        return True

    return False


def handle_message(data, chat_id, text):
    user = ensure_user(data, chat_id)
    text = (text or "").strip()

    if text in ("/start", "/menu", "🏠 Меню"):
        user["state"] = None
        user["temp"] = {}
        save_data(data)
        main_menu(chat_id)
        return

    if handle_add_flow(user, chat_id, text, data):
        return

    if text == "➕ Добавить":
        user["state"] = "wait_title"
        user["temp"] = {}
        save_data(data)
        send_message(chat_id, "Пришли заголовок напоминания")
        return

    if text == "📋 Список":
        reminders = sorted(user["reminders"], key=lambda x: x["time"])
        if not reminders:
            main_menu(chat_id, "Список пуст")
            return
        msg = ["📋 Твои напоминания:\n"]
        for r in reminders:
            msg.append(format_reminder(r))
            msg.append("")
        send_message(chat_id, "\n".join(msg).strip(), keyboard([
            ["➕ Добавить", "🗑 Удалить"],
            ["🏠 Меню"]
        ]))
        return

    if text == "🗑 Удалить":
        if not user["reminders"]:
            main_menu(chat_id, "Удалять пока нечего")
            return
        user["state"] = "wait_delete_id"
        save_data(data)
        send_message(chat_id, "Пришли ID напоминания, которое удалить")
        return

    if text == "ℹ️ Помощь":
        main_menu(chat_id,
            "Как пользоваться:\n\n"
            "1. Нажми ➕ Добавить\n"
            "2. Отправь заголовок\n"
            "3. Отправь описание или -\n"
            "4. Отправь дату и время\n\n"
            "Формат даты: 05.03.2026 18:30"
        )
        return

    main_menu(chat_id, "Нажми кнопку в меню 👇")


def polling_loop():
    global last_update_id
    data = load_data()

    while True:
        try:
            result = get_updates(last_update_id + 1)
            if result.get("ok"):
                for update in result.get("result", []):
                    last_update_id = update["update_id"]
                    message = update.get("message")
                    if not message:
                        continue
                    chat_id = message["chat"]["id"]
                    text = message.get("text", "")
                    handle_message(data, chat_id, text)
        except Exception as e:
            print("Polling error:", e)
            time.sleep(3)


def reminder_loop():
    while True:
        try:
            data = load_data()
            now = datetime.now()
            changed = False

            for chat_id, user in data.get("users", {}).items():
                for r in user.get("reminders", []):
                    if r.get("sent"):
                        continue
                    try:
                        when = datetime.strptime(r["time"], "%Y-%m-%d %H:%M")
                    except Exception:
                        continue
                    if now >= when:
                        text = f"🔔 Напоминание\n\n📝 {r['title']}"
                        if r.get("description"):
                            text += f"\n📄 {r['description']}"
                        text += f"\n🕒 {r['time']}"
                        send_message(chat_id, text, keyboard([
                            ["➕ Добавить", "📋 Список"],
                            ["🏠 Меню"]
                        ]))
                        r["sent"] = True
                        changed = True

            if changed:
                save_data(data)
        except Exception as e:
            print("Reminder error:", e)

        time.sleep(CHECK_EVERY_SECONDS)


if __name__ == "__main__":
    print("Bot started")
    threading.Thread(target=reminder_loop, daemon=True).start()
    polling_loop()
