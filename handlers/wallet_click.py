"""Click checkout for wallet top-ups (credit happens in reports.after_payment)."""
from __future__ import annotations

import re

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder

import database as db
import keyboards as kb
import wallet
from config import CLICK_ENABLED
from locales import money
from payments import click
from .wallet import TopUp, wallet_menu

router = Router()
AMOUNTS = (5_000, 10_000, 15_000, 30_000)
PRODUCT = "wallet_topup_click"
MIN_CUSTOM_AMOUNT = 1_000
MAX_CUSTOM_AMOUNT = 50_000_000


class CustomClickTopUp(StatesGroup):
    amount = State()


def bi(lang: str, uz: str, ru: str) -> str:
    return uz if lang == "uz" else ru


def amount_menu(lang: str):
    b = InlineKeyboardBuilder()
    for amount in AMOUNTS:
        b.button(
            text=bi(lang, f"💳 {money(amount)} so‘m", f"💳 {money(amount)} сум"),
            callback_data=f"wallet:click:{amount}",
        )
    b.button(
        text=bi(lang, "✍️ Boshqa summani kiritish", "✍️ Ввести другую сумму"),
        callback_data="wallet:click:custom",
    )
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


# Click orqali to'ldirilgan pul balansga `handlers/reports.after_payment()` da
# tushadi (reference "click_topup:<id>" — ikki marta tushmaydi). Avval bu yerda
# payment._announce va notify_paid almashtirilardi; ular boshqa modul bilan
# bir-birini bosib, webhook yo'lida balans umuman to'ldirilmas edi.


async def _payment_text(amount: int, payment_id: int, lang: str) -> str:
    return bi(
        lang,
        f"💳 <b>Click orqali balansni to‘ldirish</b>\n\n💰 Summa: <b>{money(amount)} so‘m</b>\n🧾 To‘lov: <code>#{payment_id}</code>\n\nClick orqali to‘lang. To‘lov tasdiqlangach, pul balansingizga avtomatik qo‘shiladi.",
        f"💳 <b>Пополнение баланса через Click</b>\n\n💰 Сумма: <b>{money(amount)} сум</b>\n🧾 Платёж: <code>#{payment_id}</code>\n\nОплатите через Click. После подтверждения деньги автоматически зачислятся на баланс.",
    )


async def _send_click_payment(target, user_id: int, amount: int, lang: str) -> None:
    import events
    events.track(user_id, "pay_clicked", PRODUCT, method="click", amount=amount)
    existing = await db.open_payment(user_id, PRODUCT, amount)
    payment_id = existing["id"] if existing else await db.create_payment(user_id, PRODUCT, amount, "click")
    url = click.payment_url(payment_id, amount)
    text = await _payment_text(amount, payment_id, lang)
    markup = kb.pay_links(payment_id, url, lang, invoice=False)
    if isinstance(target, CallbackQuery):
        await target.message.edit_text(text, reply_markup=markup)
    else:
        await target.answer(text, reply_markup=markup)


@router.callback_query(F.data == "wallet:topup")
async def choose_topup_method(callback: CallbackQuery, state: FSMContext, lang: str) -> None:
    await callback.answer()
    await state.clear()
    await callback.message.edit_text(
        bi(lang, "➕ <b>Balansni to‘ldirish</b>\n\nTo‘lov usulini tanlang:",
           "➕ <b>Пополнение баланса</b>\n\nВыберите способ оплаты:"),
        reply_markup=methods_menu(lang),
    )


@router.callback_query(F.data == "wallet:manual")
async def manual_topup(callback: CallbackQuery, state: FSMContext, lang: str) -> None:
    await callback.answer()
    import events
    events.track(callback.from_user.id, "pay_clicked", "wallet_topup", method="manual_card")
    await state.set_state(TopUp.amount)
    from config import MANUAL_CARD_HOLDER, MANUAL_CARD_NUMBER
    await callback.message.edit_text(
        bi(lang,
           "➕ <b>Balansni karta orqali to‘ldirish</b>\n\nUZCARD/HUMO orqali quyidagi kartaga to‘lov qiling:\n"
           f"💳 <code>{MANUAL_CARD_NUMBER}</code>\n"
           f"👤 {MANUAL_CARD_HOLDER}\n\n"
           "To‘lagan summangizni faqat raqamda yuboring (masalan: 50000).\nBekor qilish: /bekor",
           "➕ <b>Пополнение баланса картой</b>\n\nОплатите через UZCARD/HUMO на карту:\n"
           f"💳 <code>{MANUAL_CARD_NUMBER}</code>\n"
           f"👤 {MANUAL_CARD_HOLDER}\n\n"
           "Отправьте сумму оплаты цифрами (например: 50000).\nОтмена: /bekor"),
    )


@router.callback_query(F.data == "wallet:click")
async def click_topup_menu(callback: CallbackQuery, lang: str) -> None:
    await callback.answer()
    if not CLICK_ENABLED:
        await callback.message.edit_text(
            bi(lang, "❌ Click hozircha sozlanmagan.", "❌ Click пока не настроен."),
            reply_markup=methods_menu(lang),
        )
        return
    await callback.message.edit_text(
        bi(lang,
           "💳 <b>Click orqali balansni to‘ldirish</b>\n\nSummani tanlang yoki o‘zingiz kiriting:",
           "💳 <b>Пополнение баланса через Click</b>\n\nВыберите сумму или введите свою:"),
        reply_markup=amount_menu(lang),
    )


@router.callback_query(F.data == "wallet:click:custom")
async def click_custom_start(callback: CallbackQuery, state: FSMContext, lang: str) -> None:
    await callback.answer()
    await state.set_state(CustomClickTopUp.amount)
    await callback.message.edit_text(
        bi(
            lang,
            "✍️ <b>Summani kiriting</b>\n\nMasalan: <code>75000</code>\nMinimal: <b>1 000 so‘m</b>\nMaksimal: <b>50 000 000 so‘m</b>\n\nBekor qilish: /bekor",
            "✍️ <b>Введите сумму</b>\n\nНапример: <code>75000</code>\nМинимум: <b>1 000 сум</b>\nМаксимум: <b>50 000 000 сум</b>\n\nОтмена: /cancel",
        )
    )


@router.message(CustomClickTopUp.amount, Command("bekor", "cancel"))
async def cancel_custom_click(message: Message, state: FSMContext, lang: str) -> None:
    await state.clear()
    await message.answer(bi(lang, "❌ Bekor qilindi.", "❌ Отменено."), reply_markup=wallet_menu(lang))


@router.message(CustomClickTopUp.amount)
async def custom_click_amount(message: Message, state: FSMContext, lang: str) -> None:
    raw = re.sub(r"\D", "", message.text or "")
    amount = int(raw) if raw else 0
    if amount < MIN_CUSTOM_AMOUNT or amount > MAX_CUSTOM_AMOUNT:
        await message.answer(
            bi(
                lang,
                "❌ Summa noto‘g‘ri. 1 000 dan 50 000 000 so‘mgacha kiriting.",
                "❌ Неверная сумма. Введите от 1 000 до 50 000 000 сум.",
            )
        )
        return
    await state.clear()
    await _send_click_payment(message, message.from_user.id, amount, lang)


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
    await _send_click_payment(callback, callback.from_user.id, amount, lang)
