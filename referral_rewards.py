"""Do'st taklifi mukofoti (2-bosqich).

Qoida (brief, 7.1): havola orqali kelgan YANGI odam birorta testni oxirigacha
topshirsa, taklif qilgan odamga 1 ta bepul to'liq tahlil (o'zi tanlaydi).

  * har bir yangi odam uchun mukofot bir marta (referral_rewards.referred_id PK);
  * oyiga ko'pi bilan `cap()` ta (Toshkent oyi bo'yicha), qolganlari "capped";
  * o'zini taklif qilish va eski foydalanuvchilar `referrals.record()` da
    allaqachon hisobga olinmaydi;
  * taklif qilgan odamga bir marta xabar boradi.

Sozlamalar admin panelda (🚀 O'sish): yoqish/o'chirish va oylik chegara.
"""
from __future__ import annotations

import asyncio
import logging
from urllib.parse import quote

from aiogram import Bot
from aiogram.exceptions import TelegramForbiddenError
from aiogram.types import CallbackQuery, LinkPreviewOptions
from aiogram.utils.keyboard import InlineKeyboardBuilder

import clock
import credits
import database as db
import events
import referrals
from locales import t

log = logging.getLogger(__name__)

DEFAULT_CAP = 10

REWARDED = "rewarded"
CAPPED = "capped"

_lock = asyncio.Lock()


async def enabled() -> bool:
    return await db.get_setting("ref_reward_on", "1") == "1"


async def cap() -> int:
    raw = await db.get_setting("ref_reward_cap", str(DEFAULT_CAP)) or ""
    return int(raw) if raw.isdigit() else DEFAULT_CAP


async def _referrer_of(user_id: int) -> int | None:
    conn = await db.connect()
    cursor = await conn.execute("SELECT referrer_id FROM referrals WHERE referred_id = ?", (user_id,))
    row = await cursor.fetchone()
    return int(row[0]) if row else None


async def rewarded_this_month(referrer_id: int) -> int:
    conn = await db.connect()
    cursor = await conn.execute(
        "SELECT COUNT(*) FROM referral_rewards WHERE referrer_id = ? AND month = ? AND status = ?",
        (referrer_id, clock.month_key(), REWARDED))
    return int((await cursor.fetchone())[0])


async def on_test_completed(bot: Bot | None, user_id: int, test_key: str) -> str | None:
    """Test tugadi: bu odamni kimdir taklif qilgan bo'lsa — mukofot. Natija: holat yoki None."""
    referrer = await _referrer_of(user_id)
    if referrer is None or not await enabled():
        return None
    async with _lock:
        conn = await db.connect()
        cursor = await conn.execute("SELECT 1 FROM referral_rewards WHERE referred_id = ?", (user_id,))
        if await cursor.fetchone():
            return None
        status = REWARDED if await rewarded_this_month(referrer) < await cap() else CAPPED
        await conn.execute(
            "INSERT INTO referral_rewards (referred_id, referrer_id, test_key, month, status, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (user_id, referrer, test_key, clock.month_key(), status, db._now()))
        await conn.commit()
        if status == REWARDED:
            await credits.add(referrer, "referral", f"ref:{user_id}")
    log.info("Referral mukofoti %s → %s: %s", user_id, referrer, status)
    if status != REWARDED:
        return status
    events.track(referrer, "referral_rewarded", test_key, referred=user_id)
    if bot is not None:
        lang = await db.get_lang(referrer) or "uz"
        b = InlineKeyboardBuilder()
        b.button(text=t("btn_credit_pick", lang), callback_data="cred:menu")
        try:
            await bot.send_message(referrer, t("ref_rewarded", lang), reply_markup=b.as_markup())
        except TelegramForbiddenError:
            from handlers.lifecycle import record_blocked
            await record_blocked(referrer)
        except Exception as exc:  # noqa: BLE001 — mukofot baribir saqlangan
            log.warning("Mukofot xabari yetmadi (%s): %s", referrer, exc)
    return status


async def _counts(referrer_id: int) -> tuple[int, int]:
    """(taklif qilinganlar, testni tugatganlar)."""
    conn = await db.connect()
    cursor = await conn.execute(
        "SELECT COUNT(*), COUNT(DISTINCT res.user_id) FROM referrals r "
        "LEFT JOIN results res ON res.user_id = r.referred_id WHERE r.referrer_id = ?", (referrer_id,))
    invited, done = await cursor.fetchone()
    return int(invited or 0), int(done or 0)


async def show_menu(callback: CallbackQuery, lang: str) -> None:
    """🎁 Do'stni taklif qilish: qoida, shaxsiy havola, hisob va bepul tahlillar."""
    from handlers.growth import bot_username

    user_id = callback.from_user.id
    link = referrals.link(bot_username(), user_id)
    invited, done = await _counts(user_id)
    have = await credits.available(user_id)
    text = t("ref_menu", lang, link=link, cap=await cap(), invited=invited, done=done, credits=have)
    b = InlineKeyboardBuilder()
    share = f"https://t.me/share/url?url={quote(link, safe='')}&text={quote(t('invite_share_text', lang))}"
    b.button(text=t("btn_ref_share", lang), url=share)
    if have:
        b.button(text=t("btn_credit_use", lang, n=have), callback_data="cred:menu")
    b.button(text=t("btn_menu", lang), callback_data="nav:menu")
    b.adjust(1)
    preview = LinkPreviewOptions(is_disabled=True)
    if callback.message.photo:
        await callback.message.answer(text, reply_markup=b.as_markup(), link_preview_options=preview)
        return
    await callback.message.edit_text(text, reply_markup=b.as_markup(), link_preview_options=preview)
