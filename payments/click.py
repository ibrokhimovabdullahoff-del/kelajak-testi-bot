"""Click bilan ishlash: imzo tekshiruvi, to'lov havolasi va invoice API.

Bu yerda Telegram ham, baza ham yo'q — faqat Click protokoli. Shu sababli
uni alohida sinab ko'rish oson (`clicktest.py` ga qarang).

PROTOKOL HAQIDA QISQACHA
------------------------
Click to'lovni ikki qadamda tasdiqlaydi va ikkalasida ham BIZNING serverga
so'rov yuboradi (docs.click.uz/shop-api/requests):

    1. Prepare  (action=0) — "shunday buyurtma bormi, summa to'g'rimi?"
    2. Complete (action=1) — "pul yechildi, endi xizmatni bering"

Har bir so'rov `sign_string` bilan keladi: bu maydonlarni ketma-ket ulab,
MD5 dan o'tkazish natijasi. Maxfiy kalit faqat bizda va Click'da bo'lgani
uchun, imzo to'g'ri chiqsa — so'rov haqiqatan Click'dan kelgan.
"""
from __future__ import annotations

import hashlib
import logging
import time
from urllib.parse import urlencode

from config import (
    CLICK_MERCHANT_ID,
    CLICK_MERCHANT_USER_ID,
    CLICK_SECRET_KEY,
    CLICK_SERVICE_ID,
    PUBLIC_URL,
)

log = logging.getLogger(__name__)

PAY_URL = "https://my.click.uz/services/pay"
API_URL = "https://api.click.uz/v2/merchant"

#: Click hujjatidagi xato kodlari. Javobda aynan shu raqamlarni kutadi.
SUCCESS = 0
SIGN_FAILED = -1
BAD_AMOUNT = -2
ACTION_NOT_FOUND = -3
ALREADY_PAID = -4
USER_NOT_FOUND = -5
TRANSACTION_NOT_FOUND = -6
BAD_REQUEST = -8
CANCELLED = -9

ERROR_NOTES = {
    SUCCESS: "Success",
    SIGN_FAILED: "SIGN CHECK FAILED!",
    BAD_AMOUNT: "Incorrect parameter amount",
    ACTION_NOT_FOUND: "Action not found",
    ALREADY_PAID: "Already paid",
    USER_NOT_FOUND: "User does not exist",
    TRANSACTION_NOT_FOUND: "Transaction does not exist",
    BAD_REQUEST: "Error in request from click",
    CANCELLED: "Transaction cancelled",
}

PREPARE = "0"
COMPLETE = "1"


# --- Imzo -------------------------------------------------------------------


def _md5(value: str) -> str:
    return hashlib.md5(value.encode("utf-8")).hexdigest()


def sign_string(data: dict[str, str], action: str) -> str:
    """Kutilayotgan imzoni hisoblaydi.

    DIQQAT: `amount` Click yuborgan STRING ko'rinishida ishlatiladi
    ("9900.00" bo'lishi mumkin). Uni songa aylantirib, keyin qayta matnga
    o'girsak ("9900") imzo mos kelmay qoladi.
    """
    parts = [
        data.get("click_trans_id", ""),
        data.get("service_id", ""),
        CLICK_SECRET_KEY,
        data.get("merchant_trans_id", ""),
    ]
    if action == COMPLETE:
        parts.append(data.get("merchant_prepare_id", ""))
    parts += [
        data.get("amount", ""),
        data.get("action", ""),
        data.get("sign_time", ""),
    ]
    return _md5("".join(parts))


def verify(data: dict[str, str], action: str) -> bool:
    """So'rov haqiqatan Click'danmi.

    `hmac.compare_digest` — imzoni belgima-belgi solishtirganda ketgan vaqt
    farqidan foydalanib kalitni topishga urinishning oldini oladi.
    """
    import hmac

    got = (data.get("sign_string") or "").strip().lower()
    return hmac.compare_digest(got, sign_string(data, action))


# --- To'lov havolasi --------------------------------------------------------


def payment_url(payment_id: int, amount: int, return_url: str | None = None) -> str:
    """my.click.uz sahifasiga olib boradigan to'lov havolasi.

    Foydalanuvchi u yerda telefon raqami yoki karta ma'lumotini kiritadi;
    Click Up o'rnatilgan bo'lsa, havola to'g'ridan-to'g'ri ilovada ochiladi.
    `transaction_param` — bizning to'lov raqamimiz; Click uni keyin
    `merchant_trans_id` sifatida qaytaradi.
    """
    params = {
        "service_id": CLICK_SERVICE_ID,
        "merchant_id": CLICK_MERCHANT_ID,
        "amount": amount,
        "transaction_param": payment_id,
    }
    if return_url or PUBLIC_URL:
        params["return_url"] = return_url or f"{PUBLIC_URL}/click/return"
    return f"{PAY_URL}?{urlencode(params)}"


# --- Merchant API: invoice --------------------------------------------------


def _auth_header() -> str:
    """Click Merchant API uchun `Auth` sarlavhasi.

    Format: merchant_user_id:sha1(timestamp + secret_key):timestamp
    """
    stamp = str(int(time.time()))
    digest = hashlib.sha1(f"{stamp}{CLICK_SECRET_KEY}".encode("utf-8")).hexdigest()
    return f"{CLICK_MERCHANT_USER_ID}:{digest}:{stamp}"


async def create_invoice(phone: str, amount: int, payment_id: int) -> dict:
    """Click Up ilovasiga hisob-faktura yuboradi.

    Foydalanuvchi ilovada bildirishnoma oladi va kartani tanlab to'laydi —
    hech qanday karta raqami kiritilmaydi. Buning uchun Click xizmatga shu
    metodni yoqib bergan bo'lishi kerak.

    Qaytaradi: {"ok": bool, "invoice_id": int | None, "note": str}
    """
    import aiohttp

    payload = {
        "service_id": int(CLICK_SERVICE_ID),
        "amount": float(amount),
        "phone_number": phone,
        "merchant_trans_id": str(payment_id),
    }
    headers = {"Auth": _auth_header(), "Content-Type": "application/json"}

    try:
        timeout = aiohttp.ClientTimeout(total=15)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(
                f"{API_URL}/invoice/create", json=payload, headers=headers
            ) as response:
                body = await response.json(content_type=None)
    except Exception as exc:  # tarmoq uzilishi foydalanuvchiga xato bo'lib chiqmasin
        log.warning("Click invoice so'rovi ketmadi: %s", exc)
        return {"ok": False, "invoice_id": None, "note": str(exc)}

    code = body.get("error_code")
    if code == 0:
        return {"ok": True, "invoice_id": body.get("invoice_id"), "note": "Success"}
    log.warning("Click invoice rad etdi: %s", body)
    return {"ok": False, "invoice_id": None, "note": body.get("error_note", "")}


def normalize_phone(raw: str) -> str | None:
    """Telefon raqamini 998XXXXXXXXX ko'rinishiga keltiradi.

    Odamlar raqamni har xil yozadi: +998 90 123-45-67, 90 123 45 67,
    998901234567. Hammasini bitta shaklga olib kelamiz; noto'g'ri bo'lsa
    None qaytadi va foydalanuvchidan qayta so'raymiz.
    """
    digits = "".join(c for c in (raw or "") if c.isdigit())
    if len(digits) == 9:            # 901234567
        digits = "998" + digits
    if len(digits) == 12 and digits.startswith("998"):
        return digits
    return None


# --- Merchant API: to'lov holatini so'rash ----------------------------------


async def check_status(payment_id: int, created_at: str | None = None) -> bool:
    """Click'da shu to'lov o'tganmi — to'g'ridan-to'g'ri so'rab ko'radi.

    Asosiy yo'l bu emas: huquq Complete so'rovi kelganda beriladi. Lekin
    Complete kechikishi yoki tarmoq uzilib qolishi mumkin, va odam pulini
    to'lab, "hech narsa bo'lmadi" degan holatda qolib ketmasligi kerak.
    Shuning uchun botdagi "To'ladim" tugmasi shu funksiyani chaqiradi.

    Xato bo'lsa False qaytadi — ya'ni "tasdiqlanmadi", "to'lanmagan" emas.
    """
    import aiohttp

    date = (created_at or "")[:10]
    paths = [f"{API_URL}/payment/status_by_mti/{CLICK_SERVICE_ID}/{payment_id}"]
    if date:
        # Hujjatning ba'zi versiyalarida sana ham talab qilinadi.
        paths.insert(0, f"{paths[0]}/{date}")

    headers = {"Auth": _auth_header()}
    try:
        timeout = aiohttp.ClientTimeout(total=6)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            for url in paths:
                async with session.get(url, headers=headers) as response:
                    if response.status != 200:
                        continue
                    body = await response.json(content_type=None)
                if body.get("error_code") == 0 and body.get("payment_status") == 2:
                    return True
                log.info("Click holat javobi: %s", body)
    except Exception as exc:  # noqa: BLE001
        log.warning("Click holatini so'rab bo'lmadi: %s", exc)
    return False
