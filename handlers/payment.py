"""Payment flow for individual paid tests."""
from __future__ import annotations

import logging

from aiogram import Bot, F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message

import database as db
import keyboards as kb
from config import CLICK_ENABLED, CLICK_INVOICE, DEFAULT_PRICE, IQ_PRICE_DEFAULT, IQ_EMOJI, IQ_KEY, is_admin
from locales import money, t, tr
from payments import click
from psytests import ORDER, REGISTRY

log = logging.getLogger(__name__)
router = Router()
_bot: Bot | None = None


def set_bot(bot: Bot) -> None:
    global _bot
    _bot = bot


class Invoice(StatesGroup):
    waiting_phone = State()


async def _edit(message: Message, text: str, markup) -> None:
    try:
        await message.edit_text(text, reply_markup=markup)
    except TelegramBadRequest as exc:
        if "message is not modified" in str(exc):
            return
        await message.answer(text, reply_markup=markup)


async def price_for(product: str) -> int:
    if product == db.ALL_PRODUCTS:
        # Legacy compatibility: the package is no longer offered in the UI.
        return 0
    default = IQ_PRICE_DEFAULT if product == IQ_KEY else DEFAULT_PRICE
    return await db.price_of(product, default)


def is_product(product: str) -> bool:
    # "all" is retained only for old database records; it cannot be bought anymore.
    return product == IQ_KEY or product in REGISTRY


async def is_locked(user_id: int, test_key: str) -> bool:
    if is_admin(user_id) and not await db.admin_pays():
        return False
    if test_key in await db.free_tests():
        return False
    return not await db.has_access(user_id, test_key)


async def locked_tests(user_id: int) -> set[str]:
    if is_admin(user_id) and not await db.admin_pays():
        return set()
    free = await db.free_tests()
    owned = await db.paid_products(user_id)
    locked = {k for k in ORDER if k not in free and k not in owned}
    if IQ_KEY not in free and IQ_KEY not in owned:
        locked.add(IQ_KEY)
    return locked


def product_title(product: str, lang: str) -> str:
    if product == IQ_KEY:
        return "🧠 Premium IQ testi" if lang == "uz" else "🧠 Премиум IQ-тест"
    test = REGISTRY.get(product)
    return f"{test.emoji} {tr(test.title, lang)}" if test else product


async def show_paywall(message: Message, user_id: int, test_key: str, lang: str) -> None:
    price = await price_for(test_key)
    text = t("paywall", lang, title=product_title(test_key, lang), price=money(price))
    await _edit(message, text, kb.paywall(test_key, lang, price=price))


@router.callback_query(F.data.startswith("pay:"))
async def start_payment(callback: CallbackQuery, state: FSMContext, lang: str) -> None:
    # Acknowledge immediately so Telegram never leaves the button spinning
    # while the database/Click request is being prepared.
    await callback.answer()
    product = callback.data.split(":", 1)[1]
    if not is_product(product):
        return
    if not CLICK_ENABLED:
        await callback.message.answer(t("pay_unavailable", lang), reply_markup=kb.back_to_menu(lang))
        log.error("To'lov so'raldi, lekin Click sozlanmagan (PUBLIC_URL/CREDENTIALS)")
        return

    owned = await db.paid_products(callback.from_user.id)
    if product in owned or not await is_locked(callback.from_user.id, product):
        await callback.message.answer(t("pay_already", lang), reply_markup=kb.back_to_menu(lang))
        return

    await state.clear()
    price = await price_for(product)
    existing = await db.open_payment(callback.from_user.id, product, price)
    payment_id = existing["id"] if existing else await db.create_payment(
        callback.from_user.id, product, price, "click"
    )
    url = click.payment_url(payment_id, price)
    await _edit(
        callback.message,
        t("pay_created", lang, product=product_title(product, lang), price=money(price), payment_id=payment_id),
        kb.pay_links(payment_id, url, lang, invoice=CLICK_INVOICE),
    )


@router.callback_query(F.data.startswith("paychk:"))
async def check_payment(callback: CallbackQuery, lang: str) -> None:
    await callback.answer()
    try:
        payment_id = int(callback.data.split(":", 1)[1])
    except (ValueError, IndexError):
        return
    payment = await db.get_payment(payment_id)
    if payment is None or payment["user_id"] != callback.from_user.id:
        return
    if payment["status"] == "paid":
        await _announce(callback.message, payment, lang)
        return
    if not await click.check_status(payment_id, payment["created_at"]):
        await callback.message.answer(t("pay_pending", lang), reply_markup=kb.back_to_menu(lang))
        return
    if await db.mark_paid(payment_id):
        log.info("To'lov Click API orqali tasdiqlandi: #%s", payment_id)
    updated = await db.get_payment(payment_id)
    if updated:
        await _announce(callback.message, updated, lang)


@router.callback_query(F.data.startswith("payinv:"))
async def ask_phone(callback: CallbackQuery, state: FSMContext, lang: str) -> None:
    await callback.answer()
    try:
        payment_id = int(callback.data.split(":", 1)[1])
    except (ValueError, IndexError):
        return
    payment = await db.get_payment(payment_id)
    if payment is None or payment["user_id"] != callback.from_user.id:
        return
    await state.set_state(Invoice.waiting_phone)
    await state.update_data(payment_id=payment_id)
    await callback.message.answer(t("pay_ask_phone", lang))


@router.message(Invoice.waiting_phone, Command("bekor", "cancel"))
async def cancel_invoice(message: Message, state: FSMContext, lang: str) -> None:
    await state.clear()
    await message.answer(t("cancelled", lang), reply_markup=kb.back_to_menu(lang))


@router.message(Invoice.waiting_phone)
async def send_invoice(message: Message, state: FSMContext, lang: str) -> None:
    phone = click.normalize_phone(message.text or "")
    if not phone:
        await message.answer(t("pay_phone_bad", lang))
        return
    data = await state.get_data()
    await state.clear()
    payment_id = data.get("payment_id")
    payment = await db.get_payment(payment_id) if payment_id else None
    if payment is None or payment["user_id"] != message.from_user.id:
        await message.answer(t("pay_unavailable", lang), reply_markup=kb.back_to_menu(lang))
        return
    result = await click.create_invoice(phone, payment["amount"], payment_id)
    if result["ok"]:
        await message.answer(t("pay_invoice_sent", lang, phone=phone), reply_markup=kb.back_to_menu(lang))
    else:
        await message.answer(t("pay_invoice_failed", lang), reply_markup=kb.back_to_menu(lang))


async def _announce(message: Message, payment: dict, lang: str) -> None:
    product = payment["product"]
    test_key = "" if product == db.ALL_PRODUCTS else product
    await message.answer(t("pay_success", lang, product=product_title(product, lang)), reply_markup=kb.unlocked(test_key, lang))


async def notify_paid(payment_id: int) -> None:
    if _bot is None:
        log.warning("notify_paid chaqirildi, lekin bot o'rnatilmagan")
        return
    payment = await db.get_payment(payment_id)
    if payment is None:
        return
    lang = await db.get_lang(payment["user_id"]) or "uz"
    product = payment["product"]
    test_key = "" if product == db.ALL_PRODUCTS else product
    try:
        await _bot.send_message(payment["user_id"], t("pay_success", lang, product=product_title(product, lang)), reply_markup=kb.unlocked(test_key, lang))
    except Exception as exc:
        log.warning("To'lov xabari yetkazilmadi (%s): %s", payment["user_id"], exc)
