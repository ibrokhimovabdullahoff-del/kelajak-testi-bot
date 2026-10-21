"""Natija sertifikati va do'st taklifi — Telegram tomoni.

  * send_certificate() — test tugagach, matnli hisobotdan OLDIN rasm yuboradi;
    uning ostida "to'liq sifatda yuklab olish" tugmasi (PNG hujjat sifatida);
  * handle_start() — /start ref_<id> orqali kelgan yangi odamni yozadi va
    taklif qilgan odamga tahlil ochilganini darhol xabar qiladi.

Mazmun va chizish — `result_image.py`, qoidalar — `referrals.py`.
Hamma matn `locales.py` da.
"""
from __future__ import annotations

import asyncio
import logging
from datetime import date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from aiogram import Bot, F, Router
from aiogram.types import BufferedInputFile, CallbackQuery, Message, User
from aiogram.utils.keyboard import InlineKeyboardBuilder

import database as db
import referrals
import result_image
from config import BOT_USERNAME, IQ_KEY, TIMEZONE
from locales import t

log = logging.getLogger(__name__)
router = Router()

_bot_username = BOT_USERNAME


def set_bot_username(username: str | None) -> None:
    """main.py ishga tushganda getMe() dan olingan haqiqiy nomni beradi."""
    global _bot_username
    if username:
        _bot_username = username.lstrip("@")


def bot_username() -> str:
    return _bot_username


def _local_date(created_at: str | None) -> date:
    """Natija sanasi foydalanuvchi vaqt mintaqasida (bazada UTC)."""
    try:
        tz = ZoneInfo(TIMEZONE)
    except (ZoneInfoNotFoundError, ValueError):
        tz = timezone(timedelta(hours=5))  # Toshkent: yozgi vaqt yo'q
    try:
        moment = datetime.fromisoformat(created_at) if created_at else datetime.now(timezone.utc)
    except ValueError:
        moment = datetime.now(timezone.utc)
    if moment.tzinfo is None:
        moment = moment.replace(tzinfo=timezone.utc)
    return moment.astimezone(tz).date()


async def _png(row: dict, name: str | None) -> bytes:
    card = result_image.build_card(row["test_key"], row["total"], row["scales"], row["lang"])
    # Chizish ~0.4 soniya — shu vaqtda bot boshqa foydalanuvchilarga ham javob bersin.
    return await asyncio.to_thread(result_image.render, card, row["lang"], bot_username(),
                                   name, _local_date(row["created_at"]))


async def send_certificate(message: Message, user: User, row: dict | None) -> None:
    """Sertifikatni rasm sifatida yuboradi. Xato bo'lsa, hisobotga to'sqinlik qilmaydi."""
    if row is None or not bot_username():
        return
    try:
        png = await _png(row, user.full_name)
        markup = InlineKeyboardBuilder()
        markup.button(text=t("btn_card_download", row["lang"]), callback_data=f"card:{row['id']}")
        await message.answer_photo(
            BufferedInputFile(png, filename="kelajak-sertifikat.png"),
            caption=t("card_caption", row["lang"]),
            reply_markup=markup.as_markup(),
        )
    except Exception as exc:  # rasm chiqmasa ham matnli natija baribir kelishi shart
        log.warning("Sertifikat yuborilmadi (%s, %s): %s", user.id, row.get("test_key"), exc)


@router.callback_query(F.data.startswith("card:"))
async def download_certificate(callback: CallbackQuery, lang: str) -> None:
    """To'liq sifatdagi PNG — rasm sifatida yuborilganda Telegram uni siqadi."""
    raw = callback.data.split(":", 1)[1]
    row = await db.get_result(int(raw)) if raw.isdigit() else None
    if row is None or row["user_id"] != callback.from_user.id:
        await callback.message.answer(t("review_missing", lang))
        return
    png = await _png(row, callback.from_user.full_name)
    await callback.message.answer_document(
        BufferedInputFile(png, filename=f"kelajak-sertifikat-{row['id']}.png"),
        caption=t("card_file_caption", row["lang"]),
    )


# --- Do'st taklifi -----------------------------------------------------------


async def review_button(user_id: int, lang: str):
    """Oxirgi IQ natijasida xato bo'lsa — tahlilni ochadigan tugma, aks holda None."""
    row = await db.latest_result(user_id, IQ_KEY)
    if row is None or row["scales"].get("version") != 2:
        return None
    markup = InlineKeyboardBuilder()
    markup.button(text=t("btn_review", lang), callback_data=f"iqrev:{row['id']}:0")
    return markup.as_markup()


async def handle_start(message: Message, payload: str | None, is_new_user: bool) -> None:
    """/start ref_<id> — yangi odamni yozadi, kerak bo'lsa taklif qilganga xabar beradi."""
    referrer = referrals.parse(payload)
    if referrer is None:
        return
    outcome = await referrals.record(referrer, message.from_user.id, is_new_user)
    log.info("Referral %s → %s: %s", referrer, message.from_user.id, outcome)
    if outcome == referrals.UNLOCKED:
        await notify_unlocked(message.bot, referrer)


async def notify_unlocked(bot: Bot, referrer: int) -> None:
    lang = await db.get_lang(referrer) or "uz"
    try:
        await bot.send_message(referrer, t("ref_unlocked_notify", lang),
                               reply_markup=await review_button(referrer, lang))
    except Exception as exc:  # botni bloklagan bo'lishi mumkin — ochilish baribir saqlangan
        log.warning("Taklif qilgan odamga xabar yetmadi (%s): %s", referrer, exc)
