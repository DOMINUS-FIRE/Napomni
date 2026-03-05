import os
import json
import time
import threading
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime, timezone
from pathlib import Path

import requests
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse

BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
SECRET_KEY = os.getenv("SECRET_KEY", "").strip()
DATA_FILE = Path("reminders.json")

API = f"https://api.telegram.org/bot{BOT_TOKEN}"

app = FastAPI(title="Reminder Bot API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://tardis-worlds.ru"],
    allow_methods=["*"],
    allow_headers=["*"],
)

def load_data():
    if DATA_FILE.exists():
        try:
            return json.loads(DATA_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {"chat_id": None, "reminders": []}


def save_data(data):
    DATA_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def tg_send_message(chat_id: int, text: str):
    requests.post(f"{API}/sendMessage", json={"chat_id": chat_id, "text": text}, timeout=30)


def ensure_ready():
    if not BOT_TOKEN:
        raise RuntimeError("BOT_TOKEN пустой")
    if not SECRET_KEY:
        raise RuntimeError("SECRET_KEY пустой")


@app.get("/ping")
def ping():
    return {"ok": True}


@app.post("/add")
async def add(req: Request):
    ensure_ready()
    body = await req.json()

    key = str(body.get("key", "")).strip()
    if key != SECRET_KEY:
        raise HTTPException(status_code=401, detail="bad_key")

    rid = str(body.get("id", "")).strip()
    title = str(body.get("title", "")).strip()
    desc = str(body.get("desc", "")).strip()
    when = str(body.get("when", "")).strip()
    photo = body.get("photo")

    if not rid or not title or not when:
        raise HTTPException(status_code=400, detail="missing_fields")

    data = load_data()
    if not data.get("chat_id"):
        raise HTTPException(status_code=409, detail="chat_id_not_set")

    # upsert
    rems = [r for r in data.get("reminders", []) if str(r.get("id")) != rid]
    rems.append({"id": rid, "title": title, "desc": desc, "when": when, "photo": photo, "sent": False})
    data["reminders"] = rems
    save_data(data)
    return JSONResponse({"ok": True})


def parse_iso(iso_str: str):
    try:
        s = iso_str.replace("Z", "+00:00")
        return datetime.fromisoformat(s)
    except Exception:
        return None


def poll_for_chat_id():
    ensure_ready()
    offset = 0
    while True:
        try:
            r = requests.get(f"{API}/getUpdates", params={"timeout": 30, "offset": offset}, timeout=35).json()
            if r.get("ok"):
                for upd in r.get("result", []):
                    offset = upd["update_id"] + 1
                    msg = upd.get("message")
                    if not msg:
                        continue
                    chat_id = msg["chat"]["id"]
                    data = load_data()
                    if data.get("chat_id") != chat_id:
                        data["chat_id"] = chat_id
                        save_data(data)
                        tg_send_message(chat_id, "✅ Готово! Теперь напоминания будут приходить с сайта.")
        except Exception:
            time.sleep(2)


def send_reminders_loop():
    ensure_ready()
    while True:
        try:
            data = load_data()
            chat_id = data.get("chat_id")
            if not chat_id:
                time.sleep(5)
                continue

            now = datetime.now(timezone.utc)
            changed = False

            for r in data.get("reminders", []):
                if r.get("sent"):
                    continue
                dt = parse_iso(str(r.get("when", "")))
                if not dt:
                    continue
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)

                if now >= dt:
                    text = "🔔 Напоминание\n\n" + r.get("title", "")
                    if r.get("desc"):
                        text += "\n\n" + r["desc"]

                    photo = r.get("photo")
                    if isinstance(photo, str) and photo.startswith("data:image/"):
                        try:
                            header, b64 = photo.split(",", 1)
                            import base64
                            img_bytes = base64.b64decode(b64)
                            files = {"photo": ("photo.jpg", img_bytes)}
                            requests.post(
                                f"{API}/sendPhoto",
                                data={"chat_id": chat_id, "caption": text},
                                files=files,
                                timeout=40
                            )
                        except Exception:
                            tg_send_message(chat_id, text)
                    else:
                        tg_send_message(chat_id, text)

                    r["sent"] = True
                    changed = True

            if changed:
                save_data(data)

        except Exception:
            pass

        time.sleep(10)


@app.on_event("startup")
def startup():
    threading.Thread(target=poll_for_chat_id, daemon=True).start()
    threading.Thread(target=send_reminders_loop, daemon=True).start()
