import os
import json
import time
import threading
import base64
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import requests
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
DATA_FILE = Path("napomni_data.json")

API = f"https://api.telegram.org/bot{BOT_TOKEN}"

app = FastAPI(title="Napomni API")

# CORS: разрешаем запросы с любого сайта (webhost1, домены и т.д.)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


def ensure_ready():
    if not BOT_TOKEN:
        raise RuntimeError("BOT_TOKEN пустой")


def load_data():
    if DATA_FILE.exists():
        try:
            return json.loads(DATA_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {"users": {}, "reminders": []}  # users: client_id -> chat_id


def save_data(data):
    DATA_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def tg(method: str, payload: dict, files: Optional[dict] = None):
    url = f"{API}/{method}"
    if files:
        r = requests.post(url, data=payload, files=files, timeout=45)
        return r.json()
    r = requests.post(url, json=payload, timeout=30)
    return r.json()


def parse_iso(iso_str: str):
    try:
        s = iso_str.replace("Z", "+00:00")
        return datetime.fromisoformat(s)
    except Exception:
        return None


@app.get("/ping")
def ping():
    return {"ok": True}


@app.get("/status")
def status(client_id: str):
    data = load_data()
    return {"connected": client_id in data.get("users", {})}


@app.get("/list")
def list_items(client_id: str):
    data = load_data()
    users = data.get("users", {})
    if client_id not in users:
        return {"items": []}

    items = []
    for r in data.get("reminders", []):
        if r.get("client_id") != client_id:
            continue
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
    ensure_ready()
    body = await req.json()

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

    rems = [r for r in data.get("reminders", []) if str(r.get("id")) != rid]
    rems.append({
        "id": rid,
        "client_id": client_id,
        "chat_id": chat_id,
        "title": title,
        "desc": desc,
        "when": when,
        "photo": photo,
        "sent": False
    })
    data["reminders"] = rems
    save_data(data)

    return JSONResponse({"ok": True})


@app.post("/delete")
async def delete(req: Request):
    ensure_ready()
    body = await req.json()
    client_id = str(body.get("client_id", "")).strip()
    rid = str(body.get("id", "")).strip()
    if not client_id or not rid:
        raise HTTPException(status_code=400, detail="missing_fields")

    data = load_data()
    # удаляем только если принадлежит этому client_id
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
    ensure_ready()
    body = await req.json()
    client_id = str(body.get("client_id", "")).strip()
    if not client_id:
        raise HTTPException(status_code=400, detail="missing_fields")

    data = load_data()
    data["reminders"] = [r for r in data.get("reminders", []) if r.get("client_id") != client_id]
    save_data(data)
    return {"ok": True}


def poll_updates_loop():
    """
    Слушаем /start <client_id> и сохраняем client_id -> chat_id.
    """
    ensure_ready()
    offset = 0

    while True:
        try:
            r = requests.get(
                f"{API}/getUpdates",
                params={"timeout": 30, "offset": offset},
                timeout=35
            ).json()

            if r.get("ok"):
                for upd in r.get("result", []):
                    offset = upd["update_id"] + 1
                    msg = upd.get("message") or upd.get("edited_message")
                    if not msg:
                        continue

                    text = (msg.get("text") or "").strip()
                    chat_id = msg["chat"]["id"]

                    if text.startswith("/start"):
                        parts = text.split(maxsplit=1)
                        payload = parts[1].strip() if len(parts) > 1 else ""

                        if payload:
                            data = load_data()
                            data.setdefault("users", {})[payload] = chat_id
                            save_data(data)
                            tg("sendMessage", {
                                "chat_id": chat_id,
                                "text": "✅ Telegram подключён!\nТеперь вы будете получать напоминания с сайта."
                            })
                        else:
                            tg("sendMessage", {
                                "chat_id": chat_id,
                                "text": "Откройте сайт и нажмите “Подключить Telegram”."
                            })
        except Exception:
            time.sleep(2)


def send_due_loop():
    ensure_ready()
    while True:
        try:
            data = load_data()
            rems = data.get("reminders", [])
            if not rems:
                time.sleep(3)
                continue

            now = datetime.now(timezone.utc)
            changed = False
            new_rems = []

            for r in rems:
                dt = parse_iso(str(r.get("when", "")))
                if not dt:
                    new_rems.append(r)
                    continue

                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)

                if now >= dt:
                    chat_id = r.get("chat_id")
                    title = (r.get("title") or "").strip()
                    desc = (r.get("desc") or "").strip()

                    text = "🔔 Напоминание\n\n" + title
                    if desc:
                        text += "\n\n" + desc

                    photo = r.get("photo")
                    sent_ok = False

                    if isinstance(photo, str) and photo.startswith("data:image/"):
                        try:
                            _, b64 = photo.split(",", 1)
                            img_bytes = base64.b64decode(b64)
                            files = {"photo": ("photo.jpg", img_bytes)}
                            tg("sendPhoto", {"chat_id": chat_id, "caption": text}, files=files)
                            sent_ok = True
                        except Exception:
                            pass

                    if not sent_ok:
                        try:
                            tg("sendMessage", {"chat_id": chat_id, "text": text})
                        except Exception:
                            pass

                    # НЕ добавляем обратно -> удаляется после отправки
                    changed = True
                else:
                    new_rems.append(r)

            if changed:
                data["reminders"] = new_rems
                save_data(data)

        except Exception:
            pass

        time.sleep(3)


@app.on_event("startup")
def startup():
    threading.Thread(target=poll_updates_loop, daemon=True).start()
    threading.Thread(target=send_due_loop, daemon=True).start()
