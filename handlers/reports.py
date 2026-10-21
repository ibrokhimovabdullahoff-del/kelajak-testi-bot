"""Natija va to'liq tahlil: test bepul, to'liq tahlil pullik (1-bosqich).

Oqim:
    test tugadi → sertifikat (bepul) → huquq bo'lsa to'liq tahlil, bo'lmasa
    bepul natija + [🔓 To'liq tahlil — narx] [📦 5 ta test — narx] ...

To'lov ekrani: avval Click (to'g'ridan-to'g'ri aynan shu tahlil narxiga),
keyin karta (chek → admin bir bosishda tasdiqlaydi), balans yetarli bo'lsa
— balansdan. To'lovdan keyin tahlil shu chatning o'zida darhol ochiladi.

Hamma to'lov yo'li bitta joyga keladi: `after_payment()`.
"""
from __future__ import annotations

import html
import logging
import re

from aiogram import Bot, F, Router
from aiogram.dispatcher.event.bases import SkipHandler
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import BaseFilter
from aiogram.types import CallbackQuery, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder

import access
import compare
import credits
import database as db
import events
import keyboards as kb
import peers
import profiles
import promo
import report
import wallet
from config import (ADMINS, BUNDLE_KEY, CLICK_ENABLED, IQ_EMOJI, IQ_KEY, MANUAL_CARD_HOLDER,
                    MANUAL_CARD_NUMBER, MANUAL_RECEIPT_CHAT, OPTIMISTIC_MAX, is_admin)
from locales import money, t, tr
from payments import click
from psytests import REGISTRY, TestDef

from . import payment as pay

log = logging.getLogger(__name__)
router = Router()

TELEGRAM_LIMIT = 3800
_CTX = re.compile(r"ctx=(\d+)")
_PROMO = re.compile(r"promo=([a-z0-9_]+)")


# --- Matn ---------------------------------------------------------------------


def test_title(test_key: str, lang: str) -> str:
    if test_key == IQ_KEY:
        return f"{IQ_EMOJI} {t('iq_title', lang)}"
    test = REGISTRY.get(test_key)
    return f"{test.emoji} {tr(test.title, lang)}" if test else test_key


def result_dict(test: TestDef, row: dict) -> dict:
    """Saqlangan natijadan `report.render` kutgan lug'at."""
    scales = {key: float(row["scales"].get(key) or 0) for key in test.scales}
    order = profiles.ranked(test.key, scales)
    out = {"scales": scales, "ranked": order, "top": order[:2], "bottom": order[-2:][::-1]}
    if row.get("total") is not None:
        out["total"] = float(row["total"])
    return out


async def full_text(row: dict, lang: str) -> str:
    key = row["test_key"]
    if key == IQ_KEY:
        details = row["scales"]
        correct = int(details.get("correct") or row.get("total") or 0)
        estimate = {"iq": details.get("iq"), "low": details.get("iq_low"), "high": details.get("iq_high")}
        comparison = await peers.compare(IQ_KEY, row["user_id"], correct)
        return report.render_iq(correct, estimate, details.get("seconds"), lang, comparison, details)
    test = REGISTRY[key]
    result = result_dict(test, row)
    comparison = await peers.compare(key, row["user_id"], result.get("total"))
    return report.render(test, result, lang, row.get("age_group"), comparison)


def free_text(row: dict, lang: str) -> str:
    key = row["test_key"]
    if key == IQ_KEY:
        details = row["scales"]
        return report.render_iq_free(int(details.get("correct") or 0), details, lang)
    test = REGISTRY[key]
    return report.render_free(test, result_dict(test, row), lang)


def _chunks(text: str) -> list[str]:
    if len(text) <= TELEGRAM_LIMIT:
        return [text]
    chunks, current = [], ""
    for block in text.split("\n\n"):
        candidate = f"{current}\n\n{block}" if current else block
        if len(candidate) > TELEGRAM_LIMIT and current:
            chunks.append(current)
            current = block
        else:
            current = candidate
    if current:
        chunks.append(current)
    return chunks


async def send_long(bot: Bot, chat_id: int, text: str, reply_markup=None) -> None:
    parts = _chunks(text)
    for i, part in enumerate(parts):
        await bot.send_message(chat_id, part, reply_markup=reply_markup if i == len(parts) - 1 else None)


# --- To'lov tugmalari -----------------------------------------------------------


async def bundle_offer(user_id: int) -> tuple[int, int] | None:
    """(to'plam narxi, alohida olinsa) — to'plam foydali bo'lsa, aks holda None."""
    missing = await access.missing(user_id)
    if len(missing) < 2:
        return None
    separate = sum([await pay.price_for(key) for key in missing])
    price = await pay.price_for(BUNDLE_KEY)
    return (price, separate) if 0 < price < separate else None


async def referral_unlock_enabled() -> bool:
    """Do'st taklifi orqali bepul ochish (admin panelda o'chirsa bo'ladi)."""
    import referral_rewards
    return await referral_rewards.enabled()


async def price_for_user(user_id: int, product: str) -> tuple[int, int, dict | None]:
    """(to'lanadigan narx, asl narx, chegirma) — promo kod chegirmasi bo'lsa, hisobga olingan."""
    full = await pay.price_for(product)
    discount = await promo.active_discount(user_id) if full > 0 else None
    if discount is None:
        return full, full, None
    return promo.apply(full, discount["percent"]), full, discount


async def paywall_markup(user_id: int, row: dict, lang: str):
    key, rid = row["test_key"], row["id"]
    b = InlineKeyboardBuilder()
    price, _, _ = await price_for_user(user_id, key)
    b.button(text=t("btn_unlock", lang, price=money(price)), callback_data=f"rep:buy:{rid}")
    offer = await bundle_offer(user_id)
    if offer:
        b.button(text=t("btn_bundle", lang, price=money(offer[0])), callback_data=f"rep:bundle:{rid}")
    have = await credits.available(user_id)
    if have:
        b.button(text=t("btn_credit_paywall", lang, n=have), callback_data=f"cred:use:{key}:{rid}")
    elif await referral_unlock_enabled():
        b.button(text=t("btn_ref_unlock", lang), callback_data="ref:menu")
    compare.add_button(b, key, lang)
    b.button(text=t("btn_other_tests", lang), callback_data="nav:menu")
    b.adjust(1)
    return b.as_markup()


def full_markup(row: dict, user_id: int, lang: str):
    if row["test_key"] == IQ_KEY:
        from . import iq
        details = row["scales"]
        return iq.result_markup({"correct": int(details.get("correct") or 0)},
                                int(details.get("iq") or 0), user_id, lang)
    from . import growth
    share = growth.share_url(user_id, growth.share_text(row)) if growth.bot_username() else None
    return kb.result_menu(row["test_key"], lang, share_url=share)


# --- Natijani yetkazish --------------------------------------------------------


async def deliver(bot: Bot, user_id: int, row: dict, lang: str) -> None:
    """Natija: huquq bo'lsa — to'liq tahlil, bo'lmasa — bepul natija va to'lov tugmalari."""
    key = row["test_key"]
    if await access.has(user_id, key):
        await send_long(bot, user_id, await full_text(row, lang), reply_markup=full_markup(row, user_id, lang))
        return
    await bot.send_message(user_id, free_text(row, lang), reply_markup=await paywall_markup(user_id, row, lang))
    events.track(user_id, "free_result_shown", key)
    events.track(user_id, "paywall_shown", key, where="result")


async def _user_row(user_id: int, rid: int) -> dict | None:
    row = await db.get_result(rid) if rid else None
    return row if row and row["user_id"] == user_id else None


@router.callback_query(F.data.startswith("rep:open:"))
async def open_result(callback: CallbackQuery, lang: str) -> None:
    raw = callback.data.rsplit(":", 1)[1]
    row = await _user_row(callback.from_user.id, int(raw) if raw.isdigit() else 0)
    if row is None:
        await callback.answer(t("review_missing", lang), show_alert=True)
        return
    await deliver(callback.bot, callback.from_user.id, row, lang)


# --- To'lov ekrani -------------------------------------------------------------


def product_title(product: str, lang: str) -> str:
    if product == BUNDLE_KEY:
        return t("btn_bundle", lang, price="").split(" — ")[0]
    return test_title(product, lang)


def _note(rid: int | str, discount: dict | None) -> str:
    """To'lov izohi: qaysi natijadan boshlangani va (bo'lsa) promo kod."""
    return f"ctx={rid}" + (f";promo={discount['code']}" if discount else "")


async def _ctx_payment(user_id: int, product: str, price: int, rid: int, discount: dict | None = None) -> int:
    """Click uchun buyurtma: tegilmagan eskisi bo'lsa — o'sha, natija raqami yoziladi."""
    existing = await db.open_payment(user_id, product, price)
    payment_id = existing["id"] if existing else await db.create_payment(user_id, product, price, "click")
    await db.set_payment_note(payment_id, _note(rid, discount))
    return payment_id


async def payment_screen(message: Message, user_id: int, product: str, rid: int, lang: str,
                         edit: bool = True) -> None:
    price, list_price, discount = await price_for_user(user_id, product)
    if product == BUNDLE_KEY:
        offer = await bundle_offer(user_id)
        full = offer[1] if offer else list_price
        text = t("pay_screen_bundle", lang, price=money(price), full=money(full))
    else:
        text = t("pay_screen", lang, title=test_title(product, lang), price=money(price))
    if discount:
        # Narx qatoridan keyin (birinchi bo'sh qatordan oldin).
        head, gap, rest = text.partition("\n\n")
        text = head + t("pay_discount_line", lang, code=discount["code"].upper(), pct=discount["percent"],
                        full=money(list_price), price=money(price)) + gap + rest
    b = InlineKeyboardBuilder()
    payment_id = None
    if CLICK_ENABLED:
        payment_id = await _ctx_payment(user_id, product, price, rid, discount)
        b.button(text=t("btn_pay_click", lang, price=money(price)), url=click.payment_url(payment_id, price))
    b.button(text=t("btn_pay_card", lang), callback_data=f"rep:card:{product}:{rid}")
    balance = await wallet.balance(user_id)
    if balance >= price > 0:
        b.button(text=t("btn_pay_wallet", lang, balance=money(balance)),
                 callback_data=f"rep:wallet:{product}:{rid}")
    if payment_id:
        b.button(text=t("btn_pay_check", lang), callback_data=f"paychk:{payment_id}")
    b.button(text=t("btn_back", lang), callback_data=f"rep:open:{rid}" if rid else "nav:menu")
    b.adjust(1)
    events.track(user_id, "pay_clicked", product, where="paywall", amount=price)
    if edit:
        try:
            await message.edit_text(text, reply_markup=b.as_markup())
            return
        except TelegramBadRequest as exc:
            if "not modified" in str(exc):
                return
    await message.answer(text, reply_markup=b.as_markup())


@router.callback_query(F.data.startswith("rep:buy:") | F.data.startswith("rep:bundle:"))
async def buy(callback: CallbackQuery, lang: str) -> None:
    _, kind, raw = callback.data.split(":")
    row = await _user_row(callback.from_user.id, int(raw) if raw.isdigit() else 0)
    if row is None:
        await callback.answer(t("review_missing", lang), show_alert=True)
        return
    product = BUNDLE_KEY if kind == "bundle" else row["test_key"]
    if product != BUNDLE_KEY and await access.has(callback.from_user.id, product):
        await callback.answer(t("report_already", lang))
        await deliver(callback.bot, callback.from_user.id, row, lang)
        return
    await payment_screen(callback.message, callback.from_user.id, product, row["id"], lang,
                         edit=not callback.message.photo)


# --- Balansdan ---------------------------------------------------------------


@router.callback_query(F.data.startswith("rep:wallet:"))
async def pay_from_wallet(callback: CallbackQuery, lang: str) -> None:
    _, _, product, raw = callback.data.split(":")
    await wallet_buy(callback, product, raw, lang)


async def wallet_buy(callback: CallbackQuery, product: str, raw: str, lang: str) -> None:
    if product != BUNDLE_KEY and product not in access.TESTS:
        return
    if product != BUNDLE_KEY and await access.has(callback.from_user.id, product):
        await callback.answer(t("report_already", lang), show_alert=True)
        return
    price, _, discount = await price_for_user(callback.from_user.id, product)
    events.track(callback.from_user.id, "pay_clicked", product, method="wallet", amount=price)
    payment_id = await wallet.purchase(callback.from_user.id, product, price)
    if not payment_id:
        await callback.answer(t("wallet_low", lang), show_alert=True)
        return
    await callback.answer()
    await db.set_payment_note(payment_id, _note(raw, discount))
    await after_payment(payment_id, source="wallet")


# --- Karta orqali (chek) ------------------------------------------------------


@router.callback_query(F.data.startswith("rep:card:"))
async def pay_by_card(callback: CallbackQuery, lang: str) -> None:
    _, _, product, raw = callback.data.split(":")
    if product != BUNDLE_KEY and product not in access.TESTS:
        return
    price, _, discount = await price_for_user(callback.from_user.id, product)
    payment_id = await db.awaiting_card_payment(callback.from_user.id, product, price)
    await db.set_payment_note(payment_id, _note(raw, discount))
    events.track(callback.from_user.id, "pay_clicked", product, method="card", amount=price)
    back = f"rep:bundle:{raw}" if product == BUNDLE_KEY else f"rep:buy:{raw}"
    b = InlineKeyboardBuilder()
    b.button(text=t("btn_back", lang), callback_data=back)
    text = t("pay_card", lang, price=money(price), card=html.escape(MANUAL_CARD_NUMBER),
             holder=html.escape(MANUAL_CARD_HOLDER))
    try:
        await callback.message.edit_text(text, reply_markup=b.as_markup())
    except TelegramBadRequest:
        await callback.message.answer(text, reply_markup=b.as_markup())


class AwaitingReceipt(BaseFilter):
    """Foydalanuvchi karta ekranini yaqinda ochgan va hali chek yubormagan."""

    def __init__(self, minutes: int) -> None:
        self.minutes = minutes

    async def __call__(self, message: Message) -> bool | dict:
        if not message.from_user:
            return False
        row = await db.awaiting_receipt(message.from_user.id, self.minutes)
        return {"awaiting": row} if row else False


@router.message(F.photo, AwaitingReceipt(minutes=120))
async def receipt(message: Message, lang: str, awaiting: dict, bot: Bot) -> None:
    user = message.from_user
    payment_id = awaiting["id"]
    file_id = message.photo[-1].file_id
    await db.attach_receipt(payment_id, file_id, message.caption or "")
    product, amount = awaiting["product"], int(awaiting["amount"])

    optimistic = (await db.get_setting("optimistic_unlock", "0") == "1"
                  and amount <= OPTIMISTIC_MAX and await access.can_open_optimistically(user.id))
    if optimistic:
        await access.grant(user.id, access.products_for(product), "card_optimistic", payment_id)
        await message.answer(t("receipt_ok_open", lang))
        await _deliver_ctx(bot, user.id, awaiting, lang)
    else:
        await message.answer(t("receipt_ok", lang), reply_markup=kb.back_to_menu(lang, other_tests=True))
    await notify_admins_receipt(bot, payment_id, user, product, amount, file_id, optimistic)


@router.message(F.text, AwaitingReceipt(minutes=10))
async def receipt_not_photo(message: Message, lang: str) -> None:
    if (message.text or "").startswith("/"):
        raise SkipHandler
    await message.answer(t("receipt_photo_only", lang))


def _receipt_targets() -> list:
    targets: list = list(ADMINS)
    chat = (MANUAL_RECEIPT_CHAT or "").strip()
    if chat.lstrip("-").isdigit():
        chat_id = int(chat)
        if chat_id not in targets:
            targets.append(chat_id)
    return targets


async def notify_admins_receipt(bot: Bot, payment_id: int, user, product: str, amount: int,
                                file_id: str, optimistic: bool) -> None:
    who = html.escape(user.full_name or "?")
    uname = f" @{user.username}" if user.username else ""
    caption = (
        f"🧾 <b>Chek #{payment_id}</b>\n"
        f"👤 {who}{uname} · <code>{user.id}</code>\n"
        f"📦 {html.escape(product_title(product, 'uz'))}\n"
        f"💰 <b>{money(amount)} so‘m</b>"
        + ("\n⚡️ Chekdan oldin ochildi — rad etsangiz, yopiladi." if optimistic else "")
    )
    b = InlineKeyboardBuilder()
    b.button(text="✅ Tasdiqlash", callback_data=f"rcpt:ok:{payment_id}")
    b.button(text="❌ Rad etish", callback_data=f"rcpt:no:{payment_id}")
    b.adjust(2)
    for target in _receipt_targets():
        try:
            await bot.send_photo(target, file_id, caption=caption, reply_markup=b.as_markup())
        except Exception as exc:  # noqa: BLE001 — bitta admin yetmasa, boshqasiga baribir boradi
            log.warning("Chek adminga yuborilmadi (%s): %s", target, exc)


class IsAdmin(BaseFilter):
    async def __call__(self, event: CallbackQuery) -> bool:
        return bool(event.from_user) and is_admin(event.from_user.id)


@router.callback_query(IsAdmin(), F.data.startswith("rcpt:"))
async def review_receipt(callback: CallbackQuery, bot: Bot) -> None:
    _, action, raw = callback.data.split(":")
    payment_id = int(raw) if raw.isdigit() else 0
    row = await db.get_payment(payment_id)
    if row is None or row["status"] != "pending" or row["method"] != "manual_card":
        await callback.answer("Bu chek allaqachon ko‘rib chiqilgan.", show_alert=True)
        return
    approve = action == "ok"
    admin = callback.from_user.id
    user_id = int(row["user_id"])
    lang = await db.get_lang(user_id) or "uz"
    if row["product"] == "wallet_topup":
        ok = await wallet.manual_review(payment_id, admin, approve)
    elif approve:
        ok = await db.mark_paid(payment_id, reviewed_by=admin)
    else:
        await db.set_status(payment_id, "cancelled", reviewed_by=admin)
        ok = True
    if not ok:
        await callback.answer("Bu chek allaqachon ko‘rib chiqilgan.", show_alert=True)
        return
    mark = f"✅ Tasdiqlandi ({callback.from_user.full_name})" if approve else f"❌ Rad etildi ({callback.from_user.full_name})"
    try:
        await callback.message.edit_caption(caption=(callback.message.caption or "") + f"\n\n{html.escape(mark)}",
                                            reply_markup=None)
    except TelegramBadRequest:
        pass
    await callback.answer("Tasdiqlandi" if approve else "Rad etildi")
    if row["product"] == "wallet_topup":
        return  # balans xabarini wallet.manual_review o'zi yuboradi
    if approve:
        if not await access.confirm_optimistic(payment_id):
            await after_payment(payment_id, source="card", announce=t("receipt_approved", lang,
                                title=product_title(row["product"], lang)))
        else:
            used = _PROMO.search(row.get("note") or "")
            if used:
                await promo.consume(user_id, used.group(1), payment_id)
        return
    revoked = await access.revoke_optimistic(user_id, payment_id) if await _was_optimistic(payment_id) else 0
    ctx = _ctx_of(row)
    b = InlineKeyboardBuilder()
    retry = f"rep:bundle:{ctx}" if row["product"] == BUNDLE_KEY else f"rep:buy:{ctx}"
    if ctx:
        b.button(text=t("btn_retry_pay", lang), callback_data=retry)
    b.button(text=t("btn_menu", lang), callback_data="nav:menu")
    b.adjust(1)
    events.track(user_id, "payment_failed", row["product"], method="manual_card", amount=row["amount"])
    try:
        await bot.send_message(user_id, t("receipt_rejected_open" if revoked else "receipt_rejected", lang),
                               reply_markup=b.as_markup())
    except Exception as exc:  # noqa: BLE001
        log.warning("Rad etilgan chek haqida xabar yetmadi (%s): %s", user_id, exc)


async def _was_optimistic(payment_id: int) -> bool:
    conn = await db.connect()
    cursor = await conn.execute(
        "SELECT 1 FROM report_access WHERE payment_id = ? AND source = 'card_optimistic' LIMIT 1", (payment_id,))
    return await cursor.fetchone() is not None


# --- To'lovdan keyin (hamma yo'l shu yerga keladi) ----------------------------


def _ctx_of(payment: dict) -> int:
    match = _CTX.search(payment.get("note") or "")
    return int(match.group(1)) if match else 0


async def _deliver_ctx(bot: Bot, user_id: int, payment: dict, lang: str) -> None:
    """To'lov qaysi natijadan boshlangan bo'lsa — o'shani to'liq ko'rsatadi."""
    product = payment["product"]
    row = await _user_row(user_id, _ctx_of(payment))
    if row is None and product in access.TESTS:
        row = await db.latest_result(user_id, product)
    if row is None:
        if product in access.TESTS:
            await bot.send_message(user_id, t("pay_no_result", lang), reply_markup=kb.start_test(product, lang))
        return
    await deliver(bot, user_id, row, lang)


async def after_payment(payment_id: int, source: str = "click", announce: str | None = None) -> None:
    """To'lov tasdiqlandi: huquq beradi va natijani shu zahoti ko'rsatadi."""
    payment = await db.get_payment(payment_id)
    if payment is None or payment["status"] != "paid":
        return
    bot = pay._bot
    user_id = int(payment["user_id"])
    lang = await db.get_lang(user_id) or "uz"
    product = payment["product"]

    if product == "wallet_topup_click":
        credited = await wallet.credit(user_id, int(payment["amount"]), "click_topup",
                                       reference=f"click_topup:{payment_id}",
                                       note=f"Click wallet top-up #{payment_id}")
        if credited and bot is not None:
            try:
                await bot.send_message(user_id, t("topup_ok", lang, amount=money(int(payment["amount"])),
                                                  balance=money(await wallet.balance(user_id))),
                                       reply_markup=kb.back_to_menu(lang))
            except Exception as exc:  # noqa: BLE001
                log.warning("Balans xabari yetmadi (%s): %s", user_id, exc)
        return

    tests = access.products_for(product)
    if not tests:
        return
    grant_source = "bundle" if product in (BUNDLE_KEY, "all") else source
    await access.grant(user_id, tests, grant_source, payment_id)
    used = _PROMO.search(payment.get("note") or "")
    if used:
        await promo.consume(user_id, used.group(1), payment_id)
    if bot is None:
        return
    try:
        if announce is None:
            announce = (t("pay_bundle_ok", lang) if product in (BUNDLE_KEY, "all")
                        else t("pay_report_ok", lang, title=product_title(product, lang)))
        await bot.send_message(user_id, announce)
        await _deliver_ctx(bot, user_id, payment, lang)
    except Exception as exc:  # noqa: BLE001 — huquq baribir saqlangan, "Natijalarim" da ochiladi
        log.warning("To‘lovdan keyin natija yetmadi (%s): %s", user_id, exc)


async def payment_failed(payment_id: int) -> None:
    """Click to'lovni bekor qildi: bitta aniq "qayta urinish" tugmasi."""
    payment = await db.get_payment(payment_id)
    bot = pay._bot
    if payment is None or bot is None or payment["product"] not in (*access.TESTS, BUNDLE_KEY):
        return
    user_id = int(payment["user_id"])
    lang = await db.get_lang(user_id) or "uz"
    ctx = _ctx_of(payment)
    b = InlineKeyboardBuilder()
    if ctx:
        b.button(text=t("btn_retry_pay", lang),
                 callback_data=f"rep:bundle:{ctx}" if payment["product"] == BUNDLE_KEY else f"rep:buy:{ctx}")
    b.button(text=t("btn_menu", lang), callback_data="nav:menu")
    b.adjust(1)
    try:
        await bot.send_message(user_id, t("pay_failed", lang), reply_markup=b.as_markup())
    except Exception as exc:  # noqa: BLE001
        log.warning("Bekor qilingan to‘lov xabari yetmadi (%s): %s", user_id, exc)
