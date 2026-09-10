"""Click checkout for wallet top-ups."""
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
AMOUNTS = (10_000, 25_000, 50_000, 100_000, 200_000)
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


async def _credit_click_topup(payment: dict) -> bool:
    """Credit a Click wallet top-up exactly once."""
    if payment.get("product") != PRODUCT or payment.get("status") != "paid":
        return False
    return await wallet.credit(
        int(payment["user_id"]),
        int(payment["amount"]),
        "click_topup",
        reference=f"click_topup:{payment['id']}",
        note=f"Click wallet top-up #{payment['id']}",
    )


async def _announce_wallet_aware(message, payment: dict, lang: str, original_announce) -> None:
    if payment.get("product") == PRODUCT:
        credited = await _credit_click_topup(payment)
        amount = money(int(payment["amount"]))
        if credited or payment.get("status") == "paid":
            user_id = int(payment["user_id"])
            await message.answer(
                bi(
                    lang,
                    f"✅ Balans to‘ldirildi: <b>+{amount} so‘m</b>.\n\n💰 Yangi balans: <b>{money(await wallet.balance(user_id))} so‘m</b>",
                    f"✅ Баланс пополнен на <b>+{amount} сум</b>.\n\n💰 Новый баланс: <b>{money(await wallet.balance(user_id))} сум</b>",
                ),
                reply_markup=wallet_menu(lang),
            )
        return
    await original_announce(message, payment, lang)


from handlers import payment as _payment_module

_original_announce = _payment_module._announce


async def _announce(message, payment, lang: str) -> None:
    await _announce_wallet_aware(message, payment, lang, _original_announce)


_payment_module._announce = _announce

_original_notify_paid = _payment_module.notify_paid


async def notify_paid(payment_id: int) -> None:
    payment = await db.get_payment(payment_id)
    if payment and payment.get("product") == PRODUCT and payment.get("status") == "paid":
        user_id = int(payment["user_id"])
        lang = await db.get_lang(user_id) or "uz"
        await _credit_click_topup(payment)
        if _payment_module._bot is not None:
            try:
                await _payment_module._bot.send_message(
                    user_id,
                    bi(
                        lang,
                        f"✅ Balans to‘ldirildi: <b>+{money(int(payment['amount']))} so‘m</b>.\n💰 Yangi balans: <b>{money(await wallet.balance(user_id))} so‘m</b>",
                        f"✅ Баланс пополнен на <b>+{money(int(payment['amount']))} сум</b>.\n💰 Новый баланс: <b>{money(await wallet.balance(user_id))} сум</b>",
                    ),
                    reply_markup=wallet_menu(lang),
                )
            except Exception:
                pass
        return
    await _original_notify_paid(payment_id)


_payment_module.notify_paid = notify_paid


async def _payment_text(amount: int, payment_id: int, lang: str) -> str:
    return bi(
        lang,
        f"💳 <b>Click orqali balansni to‘ldirish</b>\n\n💰 Summa: <b>{money(amount)} so‘m</b>\n🧾 To‘lov: <code>#{payment_id}</code>\n\nClick orqali to‘lang. To‘lov tasdiqlangach, pul balansingizga avtomatik qo‘shiladi.",
        f"💳 <b>Пополнение баланса через Click</b>\n\n💰 Сумма: <b>{money(amount)} сум</b>\n🧾 Платёж: <code>#{payment_id}</code>\n\nОплатите через Click. После подтверждения деньги автоматически зачислятся на баланс.",
    )


async def _send_click_payment(target, user_id: int, amount: int, lang: str) -> None:
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
            "✍️ <b>Введите сумму</b>\n\nНапример: <code>75000</code>\nМинимум: <b>1 000 сум</b>\nМаксимум: <b>50 000 000 сум</b>\n\nОтмена: /bekor",
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
