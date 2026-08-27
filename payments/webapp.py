"""Click uchun HTTP server.

Bot uzun so'rov (long polling) bilan ishlaydi, lekin Click to'lov haqida
BIZGA murojaat qiladi — demak tashqaridan ochiq manzil kerak. Shu sababli
bot yonida kichik aiohttp serveri ko'tariladi:

    POST /click/prepare    — Click: "buyurtma bormi, summa to'g'rimi?"
    POST /click/complete   — Click: "pul yechildi, xizmatni bering"
    GET  /click/return     — to'lovdan keyin odam tushadigan sahifa
    GET  /health           — platforma tekshiruvi uchun

Prepare va Complete manzillari merchant.click.uz kabinetida "Servislar →
Действие (qalam belgisi)" bo'limiga yoziladi.
"""
from __future__ import annotations

import logging

from aiohttp import web

import database as db
from config import CLICK_SERVICE_ID, PORT

from . import click

log = logging.getLogger(__name__)

#: To'lov tasdiqlanganda chaqiriladigan funksiya. main.py uni o'rnatadi —
#: shu tufayli bu modul Telegram haqida hech narsa bilmaydi va aksincha.
_on_paid = None


def _reply(data: dict, error: int, extra: dict | None = None) -> web.Response:
    """Click kutgan ko'rinishdagi JSON javob."""
    body = {
        "click_trans_id": _as_int(data.get("click_trans_id")),
        "merchant_trans_id": data.get("merchant_trans_id"),
        "error": error,
        "error_note": click.ERROR_NOTES.get(error, ""),
    }
    body.update(extra or {})
    return web.json_response(body)


def _as_int(value):
    try:
        return int(value)
    except (TypeError, ValueError):
        return value


async def _params(request: web.Request) -> dict[str, str]:
    """So'rov maydonlari.

    Click odatda `application/x-www-form-urlencoded` POST yuboradi, lekin
    testlash vositasi ba'zan GET bilan ham uradi — ikkalasini ham olamiz.
    """
    data = dict(request.query)
    if request.method == "POST":
        try:
            data.update({k: v for k, v in (await request.post()).items()})
        except Exception:  # noqa: BLE001 — buzuq tana so'rovni yiqitmasin
            log.warning("Click so'rovi tanasini o'qib bo'lmadi")
    return {k: str(v) for k, v in data.items()}


def _amount_matches(sent: str, expected: int) -> bool:
    """Click yuborgan summa biz kutganiga tengmi.

    Click summani "9900.00" ko'rinishida yuboradi, shuning uchun matnni
    to'g'ridan-to'g'ri solishtirib bo'lmaydi. Tiyin darajasidagi yaxlitlash
    farqi bo'lishi mumkin — 1 so'mgacha yo'l qo'yamiz.
    """
    try:
        return abs(float(sent) - float(expected)) < 1
    except (TypeError, ValueError):
        return False


# --- Prepare ----------------------------------------------------------------


async def prepare(request: web.Request) -> web.Response:
    data = await _params(request)
    log.info("Click prepare: %s", {k: v for k, v in data.items() if k != "sign_string"})

    if data.get("service_id") != CLICK_SERVICE_ID:
        return _reply(data, click.BAD_REQUEST)
    if not click.verify(data, click.PREPARE):
        log.warning("Click prepare imzosi mos kelmadi: %s", data.get("merchant_trans_id"))
        return _reply(data, click.SIGN_FAILED)

    payment_id = _as_int(data.get("merchant_trans_id"))
    if not isinstance(payment_id, int):
        return _reply(data, click.USER_NOT_FOUND)

    payment = await db.get_payment(payment_id)
    if payment is None:
        return _reply(data, click.USER_NOT_FOUND)
    if payment["status"] == "paid":
        return _reply(data, click.ALREADY_PAID)
    if payment["status"] == "cancelled":
        return _reply(data, click.CANCELLED)
    if not _amount_matches(data.get("amount", ""), payment["amount"]):
        log.warning(
            "Click prepare summasi mos emas: keldi=%s kutilgan=%s",
            data.get("amount"), payment["amount"],
        )
        return _reply(data, click.BAD_AMOUNT)

    await db.set_click_prepare(payment_id, data.get("click_trans_id", ""))
    return _reply(data, click.SUCCESS, {"merchant_prepare_id": payment_id})


# --- Complete ---------------------------------------------------------------


async def complete(request: web.Request) -> web.Response:
    data = await _params(request)
    log.info("Click complete: %s", {k: v for k, v in data.items() if k != "sign_string"})

    if data.get("service_id") != CLICK_SERVICE_ID:
        return _reply(data, click.BAD_REQUEST)
    if not click.verify(data, click.COMPLETE):
        log.warning("Click complete imzosi mos kelmadi: %s", data.get("merchant_trans_id"))
        return _reply(data, click.SIGN_FAILED)

    payment_id = _as_int(data.get("merchant_trans_id"))
    if not isinstance(payment_id, int):
        return _reply(data, click.TRANSACTION_NOT_FOUND)

    payment = await db.get_payment(payment_id)
    if payment is None:
        return _reply(data, click.TRANSACTION_NOT_FOUND)

    # Prepare bosqichi o'tmagan bo'lsa, bu bizning tranzaksiyamiz emas.
    if _as_int(data.get("merchant_prepare_id")) != payment["click_prepare_id"]:
        return _reply(data, click.TRANSACTION_NOT_FOUND)
    if not _amount_matches(data.get("amount", ""), payment["amount"]):
        return _reply(data, click.BAD_AMOUNT)

    # Click o'z tomonida to'lovni bekor qilgan bo'lsa, `error` manfiy keladi.
    reported = _as_int(data.get("error", 0))
    if isinstance(reported, int) and reported < 0:
        await db.set_status(payment_id, "cancelled")
        return _reply(data, click.CANCELLED)

    if payment["status"] == "paid":
        # Click javobimizni olmay qolsa, so'rovni takror yuboradi. Bu xato
        # emas — huquq allaqachon berilgan, shunchaki muvaffaqiyat qaytaramiz.
        return _reply(data, click.SUCCESS, {"merchant_confirm_id": payment_id})

    changed = await db.mark_paid(payment_id, click_confirm_id=data.get("click_trans_id"))
    if changed and _on_paid is not None:
        try:
            await _on_paid(payment_id)
        except Exception:  # noqa: BLE001 — xabar ketmasa ham to'lov to'lovligicha qoladi
            log.exception("To'lov haqida xabar yuborilmadi: %s", payment_id)

    return _reply(data, click.SUCCESS, {"merchant_confirm_id": payment_id})


# --- Yordamchi sahifalar ----------------------------------------------------

_RETURN_PAGE = """<!doctype html>
<html lang="uz"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>To'lov qabul qilindi</title>
<style>
 body{margin:0;min-height:100vh;display:flex;align-items:center;
      justify-content:center;background:#0f172a;color:#e2e8f0;
      font-family:system-ui,-apple-system,Segoe UI,Roboto,sans-serif;padding:24px}
 .card{max-width:420px;text-align:center;background:#1e293b;padding:40px 28px;
       border-radius:20px;box-shadow:0 12px 40px rgba(0,0,0,.35)}
 h1{font-size:22px;margin:0 0 12px}
 p{margin:0 0 24px;line-height:1.6;color:#94a3b8}
 a{display:inline-block;background:#22c55e;color:#052e16;text-decoration:none;
   font-weight:600;padding:14px 28px;border-radius:12px}
 .tick{font-size:52px;margin-bottom:8px}
</style></head><body><div class="card">
<div class="tick">✅</div>
<h1>To'lov qabul qilindi</h1>
<p>Endi botga qayting — test siz uchun ochildi.<br>
Открыто: вернитесь в бот, тест доступен.</p>
{button}
</div></body></html>"""


async def return_page(request: web.Request) -> web.Response:
    """To'lovdan keyin Click odamni shu sahifaga qaytaradi.

    Sahifa hech narsani tasdiqlamaydi — huquq faqat Complete so'rovi bilan
    beriladi. Bu yerda faqat "botga qayting" degan tugma bor.
    """
    from config import BOT_USERNAME

    button = (
        f'<a href="https://t.me/{BOT_USERNAME}">Botga qaytish</a>'
        if BOT_USERNAME else ""
    )
    return web.Response(
        text=_RETURN_PAGE.replace("{button}", button), content_type="text/html"
    )


async def health(request: web.Request) -> web.Response:
    return web.json_response({"status": "ok"})


# --- Ishga tushirish --------------------------------------------------------


def build_app() -> web.Application:
    app = web.Application()
    app.router.add_route("*", "/click/prepare", prepare)
    app.router.add_route("*", "/click/complete", complete)
    app.router.add_get("/click/return", return_page)
    app.router.add_get("/health", health)
    app.router.add_get("/", health)
    return app


async def run_server(on_paid=None) -> web.AppRunner:
    """Serverni ko'taradi va uni qaytaradi (to'xtatish uchun kerak)."""
    global _on_paid
    _on_paid = on_paid

    runner = web.AppRunner(build_app())
    await runner.setup()
    # 0.0.0.0 — konteyner tashqarisidan ham ko'rinishi uchun.
    await web.TCPSite(runner, "0.0.0.0", PORT).start()
    log.info("Click serveri tinglayapti: 0.0.0.0:%s", PORT)
    return runner
