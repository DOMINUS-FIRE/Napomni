import os
import uuid
import shutil
import asyncio
from pathlib import Path

from aiohttp import web

from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, FSInputFile
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties

import yt_dlp


TOKEN = "8727309987:AAEnvF7wiGZ6wH1KW1a_tBUlQ5NJgfLJU_I"

DOWNLOADS = Path("downloads")
DOWNLOADS.mkdir(exist_ok=True)

MAX_TELEGRAM_SIZE_MB = 48
MAX_TELEGRAM_SIZE = MAX_TELEGRAM_SIZE_MB * 1024 * 1024


bot = Bot(
    token=TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)

dp = Dispatcher()


def is_supported_link(text: str) -> bool:
    domains = [
        "youtube.com",
        "youtu.be",
        "youtube.com/shorts",
        "tiktok.com",
        "instagram.com",
        "instagram.com/reel",
        "instagram.com/reels",
    ]

    return any(domain in text.lower() for domain in domains)


def download_content(url: str):
    unique_id = str(uuid.uuid4())

    folder = DOWNLOADS / unique_id
    folder.mkdir(exist_ok=True)

    video_template = str(folder / "%(title).80s.%(ext)s")

    ydl_opts = {
        "outtmpl": video_template,
        "format": "best",
        "noplaylist": True,
        "quiet": True,
        "no_warnings": True,
        "extractor_args": {
            "youtube": {
                "player_client": ["android"]
            }
        },
        "http_headers": {
            "User-Agent": "com.google.android.youtube/19.09.37 (Linux; U; Android 11)"
        }
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.extract_info(url, download=True)

    video_file = None

    for file in folder.iterdir():
        if file.suffix.lower() in [
            ".mp4",
            ".webm",
            ".mkv",
            ".mov"
        ]:
            video_file = file
            break

    if not video_file:
        raise Exception("Видео не найдено")

    if video_file.stat().st_size > MAX_TELEGRAM_SIZE:
        raise Exception(
            f"Видео слишком большое "
            f"({round(video_file.stat().st_size / 1024 / 1024, 1)} MB)"
        )

    return folder, video_file


@dp.message(F.text)
async def handle_link(message: Message):
    url = message.text.strip()

    if not is_supported_link(url):
        return await message.answer(
            "📎 Пришли ссылку на:\n"
            "• YouTube\n"
            "• Shorts\n"
            "• TikTok\n"
            "• Instagram Reels"
        )

    status = await message.answer("⏳ Скачиваю...")

    folder = None

    try:
        folder, video_file = await asyncio.to_thread(
            download_content,
            url
        )

        await status.edit_text("📤 Отправляю видео...")

        await message.answer_video(
            video=FSInputFile(video_file),
            supports_streaming=True
        )

        await status.edit_text("✅ Готово")

    except Exception as e:
        await status.edit_text(
            f"❌ Ошибка:\n<code>{e}</code>"
        )

    finally:
        if folder and folder.exists():
            shutil.rmtree(folder, ignore_errors=True)


# Render web server
async def healthcheck(request):
    return web.Response(text="Bot is running")


async def start_webserver():
    app = web.Application()

    app.router.add_get("/", healthcheck)

    port = int(os.environ.get("PORT", 10000))

    runner = web.AppRunner(app)
    await runner.setup()

    site = web.TCPSite(
        runner,
        "0.0.0.0",
        port
    )

    await site.start()


async def main():
    print("Bot started")

    await start_webserver()

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())