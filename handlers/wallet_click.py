"""Click checkout for wallet top-ups."""
from __future__ import annotations

from aiogram import F, Router
from aiogram.types import CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder

import database as db
import keyboards as kb
from config import CLICK_ENABLED
from locales import money
from payments import click
from .wallet import TopUp

router = Router()
AMOUNTS = (10_000, 25_000, 50_000, 100_000, 200_000)
PRODUCT = "wallet_topup_click"


def bi(lang: str, uz: str, ru: str) -> str:
    return uz if lang == "uz" else ru


def amount_menu(lang: str):
    b = InlineKeyboardBuilder()
    for amount in AMOUNTS:
        b.button(text=bi(lang, f"💳 {money(amount)} so‘m", f"💳 {money(amount)} сум"), callback_data=f"wallet:click:{amount}")
    b.button(text=bi(lang, "⬅️ Orqaga", "⬅️ Назад"), callback_data="wallet:open")
    b.adjust(2, 2, 1, 1)
    return b.as_markup()


def methods_menu(lang: str):
    b = InlineKeyboardBuilder()
    if CLICK_ENABLED:
        b.button(text=bi(lang, "💳 Click orqali", "💳 Через Click"), callback_data="wallet:click")
    b.button(text=bi(lang, "💳 UZCARD/HUMO karta orqali", "💳 Картой UZCARD/HUMO"), callback_data="wallet:manual")
    b.button(text=bi(lang, "⬅️ Orqaga", "⬅️ Назад"), callback_data="wallet:open")
    b.adjust(1)
    return b.as_markup()


@router.callback_query(F.data == "wallet:topup")
async def choose_topup_method(callback: CallbackQuery, state, lang: str) -> None:
    await callback.answer()
    await state.clear()
    await callback.message.edit_text(
        bi(lang, "➕ <b>Balansni to‘ldirish</b>\n\nTo‘lov usulini tanlang:",
           "➕ <b>Пополнение баланса</b>\n\nВыберите способ оплаты:"),
        reply_markup=methods_menu(lang),
    )


@router.callback_query(F.data == "wallet:manual")
async def manual_topup(callback: CallbackQuery, state, lang: str) -> None:
    await callback.answer()
    await state.set_state(TopUp.amount)
    from config import MANUAL_CARD_HOLDER, MANUAL_CARD_NUMBER
    await callback.message.edit_text(
        bi(lang,
           "➕ <b>Balansni karta orqali to‘ldirish</b>\n\n"
           "UZCARD/HUMO orqali quyidagi kartaga to‘lov qiling:\n"
           f"💳 <code>{MANUAL_CARD_NUMBER}</code>\n"
           f"👤 {MANUAL_CARD_HOLDER}\n\n"
           "To‘lagan summangizni faqat raqamda yuboring (masalan: 50000).\n"
           "Bekor qilish: /bekor",
           "➕ <b>Пополнение баланса картой</b>\n\n"
           "Оплатите через UZCARD/HUMO на карту:\n"
           f"💳 <code>{MANUAL_CARD_NUMBER}</code>\n"
           f"👤 {MANUAL_CARD_HOLDER}\n\n"
           "Отправьте сумму оплаты цифрами (например: 50000).\n"
           "Отмена: /bekor"),
    )


@router.callback_query(F.data == "wallet:click")
async def click_topup_menu(callback: CallbackQuery, lang: str) -> None:
    await callback.answer()
    if not CLICK_ENABLED:
        await callback.message.edit_text(bi(lang, "❌ Click hozircha sozlanmagan.", "❌ Click пока не настроен."), reply_markup=methods_menu(lang))
        return
    await callback.message.edit_text(
        bi(lang, "💳 <b>Click orqali balansni to‘ldirish</b>\n\nSummani tanlang:",
           "💳 <b>Пополнение баланса через Click</b>\n\nВыберите сумму:"),
        reply_markup=amount_menu(lang),
    )


@router.callback_query(F.data.startswith("wallet:click:"))
async def click_topup_create(callback: CallbackQuery, lang: str) -> None:
    await callback.answer()
    if not CLICK_ENABLED:
        return
    try:
        amount = int(callback.data.rsplit(":", 1)[1])
    except (ValueError, IndexError):
        return
    if amount not in AMOUNTS:
        return
    existing = await db.open_payment(callback.from_user.id, PRODUCT, amount)
    payment_id = existing["id"] if existing else await db.create_payment(callback.from_user.id, PRODUCT, amount, "click")
    url = click.payment_url(payment_id, amount)
    await callback.message.edit_text(
        bi(lang,
           f"💳 <b>Click orqali balansni to‘ldirish</b>\n\n💰 Summa: <b>{money(amount)} so‘m</b>\n🧾 To‘lov: <code>#{payment_id}</code>\n\n"
           "Click orqali to‘lang. To‘lov tasdiqlangach, pul balansingizga avtomatik qo‘shiladi.",
           f"💳 <b>Пополнение баланса через Click</b>\n\n💰 Сумма: <b>{money(amount)} сум</b>\n🧾 Платёж: <code>#{payment_id}</code>\n\n"
           "Оплатите через Click. После подтверждения деньги автоматически зачислятся на баланс."),
        reply_markup=kb.pay_links(payment_id, url, lang, invoice=False),
    )
