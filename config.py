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
BOT_USERNAME = os.getenv("BOT_USERNAME", "").lstrip("@").strip()


def is_admin(user_id: int) -> bool:
    return user_id in ADMINS

DEFAULT_PRICE = int(os.getenv("PRICE_UZS", "9900"))
DEFAULT_PRICE_ALL = int(os.getenv("PRICE_ALL_UZS", "24900"))
CURRENCY = "so'm"

CLICK_SERVICE_ID = os.getenv("CLICK_SERVICE_ID", "").strip()
CLICK_MERCHANT_ID = os.getenv("CLICK_MERCHANT_ID", "").strip()
CLICK_SECRET_KEY = os.getenv("CLICK_SECRET_KEY", "").strip()
CLICK_MERCHANT_USER_ID = os.getenv("CLICK_MERCHANT_USER_ID", "").strip()
PUBLIC_URL = os.getenv("PUBLIC_URL", "").strip().rstrip("/")
PORT = int(os.getenv("PORT", "8080"))
CLICK_INVOICE = os.getenv("CLICK_INVOICE", "0").strip().lower() in ("1", "true", "yes")
CLICK_ENABLED = bool(
    CLICK_SERVICE_ID and CLICK_MERCHANT_ID and CLICK_SECRET_KEY and PUBLIC_URL
)
PAYMENTS_ENABLED = CLICK_ENABLED

# Manual UZCARD/HUMO top-up. Keep these configurable for deployment changes.
MANUAL_CARD_NUMBER = os.getenv("MANUAL_CARD_NUMBER", "9860 0401 0808 1262").strip()
MANUAL_CARD_HOLDER = os.getenv("MANUAL_CARD_HOLDER", "ABDULLOX I").strip()
# Telegram username or numeric chat ID that receives receipt review requests.
MANUAL_RECEIPT_CHAT = os.getenv("MANUAL_RECEIPT_CHAT", "@yordamchi_savdo").strip()
