"""Sozlamalar. Hamma sir qiymatlar .env faylidan olinadi."""
import os

from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
if not BOT_TOKEN:
    raise RuntimeError(
        "BOT_TOKEN ko'rsatilmagan. .env.example ni .env ga nusxalab, tokenni yozing."
    )

ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))

_extra = os.getenv("EXTRA_ADMINS", "").strip()
ADMINS = {int(x) for x in _extra.split(",") if x.strip()}
if ADMIN_ID:
    ADMINS.add(ADMIN_ID)

DB_PATH = os.getenv("DB_PATH", "kelajak.db")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
TIMEZONE = os.getenv("TIMEZONE", "Asia/Tashkent")

# Botni do'stlarga ulashish uchun havola (natija ostida chiqadi).
BOT_USERNAME = os.getenv("BOT_USERNAME", "").lstrip("@").strip()


def is_admin(user_id: int) -> bool:
    return user_id in ADMINS
