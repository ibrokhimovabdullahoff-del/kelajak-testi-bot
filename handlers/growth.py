"""Natija sertifikati va do'st taklifi — Telegram tomoni.

  * send_certificate() — test tugagach, matnli hisobotdan OLDIN rasm yuboradi;
    uning ostida "to'liq sifatda yuklab olish" tugmasi (PNG hujjat sifatida);
  * handle_start() — /start ref_<id> orqali kelgan yangi odamni yozadi.

Mazmun va chizish — `result_image.py`, qoidalar — `referrals.py`.
Hamma matn `locales.py` da.
"""
from __future__ import annotations

import asyncio
import logging
from datetime import date, datetime, timedelta, timezone
from urllib.parse import quote
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from aiogram import F, Router
from aiogram.types import (BufferedInputFile, CallbackQuery, InputMediaPhoto, LinkPreviewOptions,
                           Message, User)
from aiogram.utils.keyboard import InlineKeyboardBuilder

import access
import database as db
import events
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


async def _png(row: dict, name: str | None, *, full: bool = False, show_score: bool = True) -> bytes:
    card = result_image.build_card(row["test_key"], row["total"], row["scales"], row["lang"],
                                   full=full, show_score=show_score)
    # Chizish ~0.4 soniya — shu vaqtda bot boshqa foydalanuvchilarga ham javob bersin.
    return await asyncio.to_thread(result_image.render, card, row["lang"], bot_username(),
                                   name, _local_date(row["created_at"]))


def _card_markup(row: dict, show_score: bool):
    markup = InlineKeyboardBuilder()
    flag = int(show_score)
    markup.button(text=t("btn_card_download", row["lang"]), callback_data=f"card:{row['id']}:{flag}")
    if row["test_key"] == IQ_KEY:
        # Ball kamtarroq bo'lsa ham kuchli tomonini ulasha olsin — raqamsiz.
        key = "btn_card_hide" if show_score else "btn_card_show"
        markup.button(text=t(key, row["lang"]), callback_data=f"cardsc:{row['id']}:{1 - flag}")
    markup.adjust(1)
    return markup.as_markup()


async def send_certificate(message: Message, user: User, row: dict | None, full: bool = False) -> None:
    """Sertifikatni rasm sifatida yuboradi. Xato bo'lsa, natijaga to'sqinlik qilmaydi.

    full — to'liq tahlil ochiq (IQ da taxminiy IQ shunda yoziladi). Farzand
    testida bolaning natijasi rasmga tushmaydi (neytral ota-ona kartasi).
    """
    if row is None or not bot_username():
        return
    try:
        png = await _png(row, user.full_name, full=full)
        await message.answer_photo(
            BufferedInputFile(png, filename="kelajak-sertifikat.png"),
            caption=t("card_caption", row["lang"]),
            reply_markup=_card_markup(row, show_score=True),
        )
        events.track(user.id, "certificate_sent", row["test_key"])
    except Exception as exc:  # rasm chiqmasa ham matnli natija baribir kelishi shart
        log.warning("Sertifikat yuborilmadi (%s, %s): %s", user.id, row.get("test_key"), exc)


async def _own_row(callback: CallbackQuery, raw: str) -> dict | None:
    row = await db.get_result(int(raw)) if raw.isdigit() else None
    return row if row and row["user_id"] == callback.from_user.id else None


@router.callback_query(F.data.startswith("card:"))
async def download_certificate(callback: CallbackQuery, lang: str) -> None:
    """To'liq sifatdagi PNG — rasm sifatida yuborilganda Telegram uni siqadi."""
    parts = callback.data.split(":")
    row = await _own_row(callback, parts[1])
    if row is None:
        await callback.message.answer(t("review_missing", lang))
        return
    show_score = not (len(parts) == 3 and parts[2] == "0")
    full = await access.has(callback.from_user.id, row["test_key"])
    png = await _png(row, callback.from_user.full_name, full=full, show_score=show_score)
    await callback.message.answer_document(
        BufferedInputFile(png, filename=f"kelajak-sertifikat-{row['id']}.png"),
        caption=t("card_file_caption", row["lang"]),
    )


@router.callback_query(F.data.startswith("cardsc:"))
async def toggle_score(callback: CallbackQuery, lang: str) -> None:
    """IQ sertifikati: "Ballni yashirish" / "Ballni ko'rsatish" — rasm shu xabarda almashadi."""
    _, raw, flag = callback.data.split(":")
    row = await _own_row(callback, raw)
    if row is None:
        return
    show_score = flag == "1"
    full = await access.has(callback.from_user.id, row["test_key"])
    png = await _png(row, callback.from_user.full_name, full=full, show_score=show_score)
    await callback.message.edit_media(
        InputMediaPhoto(media=BufferedInputFile(png, filename="kelajak-sertifikat.png"),
                        caption=t("card_caption", row["lang"])),
        reply_markup=_card_markup(row, show_score),
    )


# --- Do'st taklifi -----------------------------------------------------------


@router.callback_query(F.data == "ref:menu")
async def invite_menu(callback: CallbackQuery, lang: str) -> None:
    """🎁 Do'stni taklif qilish — shaxsiy havola va ulashish tugmasi."""
    if not bot_username():
        return
    try:
        import referral_rewards
    except ImportError:
        referral_rewards = None
    if referral_rewards is not None and await referral_rewards.enabled():
        await referral_rewards.show_menu(callback, lang)
        return
    link = referrals.link(bot_username(), callback.from_user.id)
    markup = InlineKeyboardBuilder()
    share = f"https://t.me/share/url?url={quote(link, safe='')}&text={quote(t('invite_share_text', lang))}"
    markup.button(text=t("btn_ref_share", lang), url=share)
    markup.button(text=t("btn_menu", lang), callback_data="nav:menu")
    markup.adjust(1)
    await callback.message.edit_text(t("invite_plain", lang, link=link), reply_markup=markup.as_markup(),
                                     link_preview_options=LinkPreviewOptions(is_disabled=True))


async def handle_start(message: Message, payload: str | None, is_new_user: bool) -> str | None:
    """/start ref_<id> — yangi odamni taklif qilganga yozadi. Natija: referrals.record() qiymati."""
    referrer = referrals.parse(payload)
    if referrer is None:
        return None
    outcome = await referrals.record(referrer, message.from_user.id, is_new_user)
    log.info("Referral %s → %s: %s", referrer, message.from_user.id, outcome)
    if outcome == referrals.COUNTED:
        events.track(message.from_user.id, "referral_joined", referrer=referrer)
    return outcome
