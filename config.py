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


# --- To'lov: umumiy ---------------------------------------------------------

#: Narxlar so'mda. Adminlar bularni panel orqali ham o'zgartira oladi —
#: bu yerdagi qiymat faqat boshlang'ich (baza bo'sh bo'lgandagi) narx.
DEFAULT_PRICE = int(os.getenv("PRICE_UZS", "9900"))
DEFAULT_PRICE_ALL = int(os.getenv("PRICE_ALL_UZS", "24900"))

#: Ma'lumot uchun — narx yonida ko'rsatiladigan valyuta belgisi.
CURRENCY = "so'm"


# --- To'lov: Click ----------------------------------------------------------

CLICK_SERVICE_ID = os.getenv("CLICK_SERVICE_ID", "").strip()
CLICK_MERCHANT_ID = os.getenv("CLICK_MERCHANT_ID", "").strip()
CLICK_SECRET_KEY = os.getenv("CLICK_SECRET_KEY", "").strip()
CLICK_MERCHANT_USER_ID = os.getenv("CLICK_MERCHANT_USER_ID", "").strip()

#: Click serveri bizga murojaat qiladigan ochiq manzil, masalan
#: https://kelajak-bot.up.railway.app — oxiridagi "/" olib tashlanadi.
PUBLIC_URL = os.getenv("PUBLIC_URL", "").strip().rstrip("/")

#: Prepare/Complete so'rovlarini qabul qiladigan HTTP server porti.
#: Railway va shunga o'xshash platformalar PORT ni o'zi beradi.
PORT = int(os.getenv("PORT", "8080"))

#: Click Up ilovasiga hisob-faktura (invoice) yuborish. Buning uchun Click
#: xizmatingizga shu metodni yoqib berishi kerak, shuning uchun alohida
#: kalit bilan boshqariladi: yoqilmagan bo'lsa faqat to'lov havolasi ishlaydi.
CLICK_INVOICE = os.getenv("CLICK_INVOICE", "0").strip().lower() in ("1", "true", "yes")

#: Click usuli faqat hamma kalit to'liq bo'lsa ko'rinadi. PUBLIC_URL shart,
#: chunki usiz Click to'lov haqida bizga xabar bera olmaydi va odam pulini
#: to'lab, testni ocholmay qoladi.
CLICK_ENABLED = bool(
    CLICK_SERVICE_ID and CLICK_MERCHANT_ID and CLICK_SECRET_KEY and PUBLIC_URL
)

#: Testlar pullik. Click sozlanmagan bo'lsa hech kim test ocha olmaydi —
#: bu ataylab shunday: pulsiz kirish yo'li qolmasin. Adminlar istisno,
#: aks holda sozlashni tekshirib ko'rishning iloji bo'lmasdi.
PAYMENTS_ENABLED = CLICK_ENABLED
