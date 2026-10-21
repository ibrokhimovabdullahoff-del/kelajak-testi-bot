"""Narxlar va Click to'lovi (to'liq tahlil uchun).

Asosiy oqim `handlers/reports.py` da: to'lov ekrani, karta cheki va
to'lovdan keyin tahlilni ochish. Bu yerda:
  * narxlar (admin panelda o'zgaradi) va mahsulot nomlari;
  * eski xabarlardagi "pay:<test>" tugmasi → yangi to'lov ekrani;
  * "✅ To'ladim, tekshirish" — Click'dan holatni so'raydi;
  * Click Up invoice (CLICK_INVOICE=1 bo'lsa).
"""
from __future__ import annotations

import logging

from aiogram import Bot, F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder

import database as db
import keyboards as kb
from config import BUNDLE_KEY, BUNDLE_PRICE_DEFAULT, CLICK_ENABLED, DEFAULT_PRICE, IQ_EMOJI, IQ_KEY, IQ_PRICE_DEFAULT
from locales import t, tr
from payments import click
from psytests import REGISTRY

log = logging.getLogger(__name__)
router = Router()
_bot: Bot | None = None


def set_bot(bot: Bot) -> None:
    global _bot
    _bot = bot


class Invoice(StatesGroup):
    waiting_phone = State()


async def price_for(product: str) -> int:
    """To'liq tahlil narxi (so'm). "bundle" — 5 ta testning to'plami."""
    if product == db.ALL_PRODUCTS:
        return 0  # eski "hamma test" paketi endi sotilmaydi
    if product == BUNDLE_KEY:
        return await db.price_of(BUNDLE_KEY, BUNDLE_PRICE_DEFAULT)
    default = IQ_PRICE_DEFAULT if product == IQ_KEY else DEFAULT_PRICE
    return await db.price_of(product, default)


def is_product(product: str) -> bool:
    return product in (IQ_KEY, BUNDLE_KEY) or product in REGISTRY


def product_title(product: str, lang: str) -> str:
    if product == IQ_KEY:
        return f"{IQ_EMOJI} {t('iq_title', lang)}"
    if product == BUNDLE_KEY:
        return "📦 " + ("5 ta testning to‘liq tahlili" if lang == "uz" else "Полный разбор всех 5 тестов")
    test = REGISTRY.get(product)
    return f"{test.emoji} {tr(test.title, lang)}" if test else product


@router.callback_query(F.data.startswith("pay:"))
async def start_payment(callback: CallbackQuery, state: FSMContext, lang: str) -> None:
    """Eski xabarlardagi "Click orqali to'lash" tugmasi → yangi to'lov ekrani."""
    from . import reports

    product = callback.data.split(":", 1)[1]
    if not is_product(product):
        return
    await state.clear()
    row = await db.latest_result(callback.from_user.id, product) if product != BUNDLE_KEY else None
    await reports.payment_screen(callback.message, callback.from_user.id, product,
                                 row["id"] if row else 0, lang, edit=not callback.message.photo)


@router.callback_query(F.data.startswith("paychk:"))
async def check_payment(callback: CallbackQuery, lang: str) -> None:
    from . import reports

    try:
        payment_id = int(callback.data.split(":", 1)[1])
    except (ValueError, IndexError):
        return
    payment = await db.get_payment(payment_id)
    if payment is None or payment["user_id"] != callback.from_user.id:
        return
    if payment["status"] != "paid":
        if not CLICK_ENABLED or not await click.check_status(payment_id, payment["created_at"]):
            b = InlineKeyboardBuilder()
            b.button(text=t("btn_check_again", lang), callback_data=f"paychk:{payment_id}")
            b.button(text=t("btn_menu", lang), callback_data="nav:menu")
            b.adjust(1)
            await callback.message.answer(t("pay_pending", lang), reply_markup=b.as_markup())
            return
        if await db.mark_paid(payment_id):
            log.info("To'lov Click API orqali tasdiqlandi: #%s", payment_id)
    await reports.after_payment(payment_id, source="click")


@router.callback_query(F.data.startswith("payinv:"))
async def ask_phone(callback: CallbackQuery, state: FSMContext, lang: str) -> None:
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


async def notify_paid(payment_id: int) -> None:
    """Click Complete webhook'i: to'lov tasdiqlandi."""
    from . import reports

    await reports.after_payment(payment_id, source="click")


async def notify_failed(payment_id: int) -> None:
    """Click to'lovni bekor qildi."""
    from . import reports

    await reports.payment_failed(payment_id)
