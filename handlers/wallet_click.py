"""Click checkout for wallet top-ups."""
from __future__ import annotations

from aiogram import F, Router
from aiogram.types import CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder

import database as db
import keyboards as kb
import wallet
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
            await message.answer(
                bi(lang, f"✅ Balans to‘ldirildi: <b>+{amount} so‘m</b>.\n\n💰 Yangi balans: <b>{money(await wallet.balance(int(payment['user_id'])))} so‘m</b>",
                   f"✅ Баланс пополнен на <b>+{amount} сум</b>.\n\n💰 Новый баланс: <b>{money(await wallet.balance(int(payment['user_id'])))} сум</b>"),
                reply_markup=wallet_menu(lang),
            )
        return
    await original_announce(message, payment, lang)


# payment.py is imported before this module by handlers/__init__.py. Wrap its
# notification functions so both webhook Complete and the manual "Paid" check
# credit wallet_topup payments atomically/idempotently.
from handlers import payment as _payment_module
_original_announce = _payment_module._announce

async def _announce(message, payment: dict, lang: str) -> None:
    await _announce_wallet_aware(message, payment, lang, _original_announce)

_payment_module._announce = _announce

_original_notify_paid = _payment_module.notify_paid

async def notify_paid(payment_id: int) -> None:
    payment = await db.get_payment(payment_id)
    if payment and payment.get("product") == PRODUCT and payment.get("status") == "paid":
        user_id = int(payment["user_id"])
        lang = await db.get_lang(user_id) or "uz"
        credited = await _credit_click_topup(payment)
        if _payment_module._bot is not None:
            try:
                await _payment_module._bot.send_message(
                    user_id,
                    bi(lang, f"✅ Balans to‘ldirildi: <b>+{money(int(payment['amount']))} so‘m</b>.\n💰 Yangi balans: <b>{money(await wallet.balance(user_id))} so‘m</b>",
                       f"✅ Баланс пополнен на <b>+{money(int(payment['amount']))} сум</b>.\n💰 Новый баланс: <b>{money(await wallet.balance(user_id))} сум</b>"),
                    reply_markup=wallet_menu(lang),
                )
            except Exception:
                pass
        return
    await _original_notify_paid(payment_id)

_payment_module.notify_paid = notify_paid


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
