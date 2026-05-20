import os
import uuid
import shutil
import asyncio
import subprocess
from pathlib import Path

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

def get_file_size_mb(path: Path) -> float:
    return path.stat().st_size / 1024 / 1024

def compress_video(input_file: Path, output_file: Path):
    command = [
        "ffmpeg",
        "-y",
        "-i", str(input_file),
        "-vcodec", "libx264",
        "-crf", "32",
        "-preset", "veryfast",
        "-acodec", "aac",
        "-b:a", "96k",
        "-movflags", "+faststart",
        str(output_file)
    ]

    subprocess.run(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def extract_audio(video_file: Path, audio_file: Path):
    command = [
        "ffmpeg",
        "-y",
        "-i", str(video_file),
        "-vn",
        "-ab", "192k",
        str(audio_file)
    ]

    subprocess.run(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def download_video(url: str):
    unique_id = str(uuid.uuid4())
    folder = DOWNLOADS / unique_id
    folder.mkdir(exist_ok=True)

    video_template = str(folder / "%(title).80s.%(ext)s")

    ydl_opts = {
        "outtmpl": video_template,
        "format": "bestvideo+bestaudio/best",
        "merge_output_format": "mp4",
        "noplaylist": True,
        "quiet": True,
        "no_warnings": True,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.extract_info(url, download=True)

    video_file = None

    for file in folder.iterdir():
        if file.suffix.lower() in [".mp4", ".mkv", ".webm", ".mov"]:
            video_file = file
            break

    if not video_file:
        raise Exception("Видео не найдено после скачивания")

    final_video = video_file

    if video_file.suffix.lower() != ".mp4":
        converted = folder / "converted.mp4"

        command = [
            "ffmpeg",
            "-y",
            "-i", str(video_file),
            "-vcodec", "libx264",
            "-acodec", "aac",
            "-movflags", "+faststart",
            str(converted)
        ]

        subprocess.run(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        if converted.exists():
            final_video = converted

    if final_video.stat().st_size > MAX_TELEGRAM_SIZE:
        compressed_video = folder / "compressed.mp4"
        compress_video(final_video, compressed_video)

        if not compressed_video.exists():
            raise Exception("Не получилось сжать видео")

        if compressed_video.stat().st_size > MAX_TELEGRAM_SIZE:
            raise Exception(
                f"Видео слишком большое даже после сжатия: "
                f"{get_file_size_mb(compressed_video):.1f} МБ. "
                f"Лимит примерно {MAX_TELEGRAM_SIZE_MB} МБ."
            )

        final_video = compressed_video

    audio_file = folder / "audio.mp3"
    extract_audio(final_video, audio_file)

    if not audio_file.exists():
        audio_file = None
    elif audio_file.stat().st_size > MAX_TELEGRAM_SIZE:
        audio_file = None

    return folder, final_video, audio_file

@dp.message(F.text)
async def handle_link(message: Message):
    url = message.text.strip()

    if not is_supported_link(url):
        return await message.answer(
            "Пришли ссылку на YouTube / Shorts / TikTok / Instagram Reels."
        )

    status = await message.answer("⏳ Скачиваю видео...")

    folder = None

    try:
        folder, video_file, audio_file = await asyncio.to_thread(download_video, url)

        await status.edit_text("📤 Отправляю видео...")

        await message.answer_video(
            video=FSInputFile(video_file),
            supports_streaming=True
        )

        if audio_file:
            await status.edit_text("🎧 Отправляю аудио...")
            await message.answer_audio(
                audio=FSInputFile(audio_file)
            )
        else:
            await message.answer(
                "⚠️ Аудио получилось слишком большим или не извлеклось."
            )

        await status.edit_text("✅ Готово")

    except Exception as e:
        await status.edit_text(f"❌ Ошибка:\n<code>{e}</code>")

    finally:
        if folder and folder.exists():
            shutil.rmtree(folder, ignore_errors=True)

async def main():
    print("Bot started")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
