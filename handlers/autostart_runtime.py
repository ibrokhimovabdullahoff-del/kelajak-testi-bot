"""Runtime glue for paid-test autostart, navigation and localized wallet notifications."""
from __future__ import annotations

from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.base import StorageKey, BaseStorage
from aiogram.types import CallbackQuery, Message

import database as db
import keyboards as kb
import wallet
from config import IQ_KEY
from locales import t
from psytests import REGISTRY

from . import iq, payment, shop, user

_bot_id: int | None = None
_storage: BaseStorage | None = None


def set_runtime(bot_id: int, storage: BaseStorage) -> None:
    global _bot_id, _storage
    _bot_id = bot_id
    _storage = storage


def _context(user_id: int) -> FSMContext:
    if _storage is None or _bot_id is None:
        raise RuntimeError("FSM runtime has not been initialized")
    return FSMContext(storage=_storage, key=StorageKey(bot_id=_bot_id, chat_id=user_id, user_id=user_id))


async def start_paid_message(message: Message, user_id: int, product: str, lang: str) -> None:
    """Start the purchased product using the exact Dispatcher FSM storage."""
    state = _context(user_id)
    if product == IQ_KEY:
        await iq._start_test(message, state, lang, user_id)
        return

    test = REGISTRY.get(product)
    if test is None:
        await message.answer(t("pay_success", lang, product=product))
        return

    await state.clear()
    if test.ask_age:
        await state.update_data(test_key=product)
        prompt = t("choose_age_child" if test.subject == "child" else "choose_age_self", lang)
        await user.safe_edit(message, prompt, reply_markup=kb.age_menu(test.subject, lang))
        return

    await user.start_quiz(message, state, product, lang, None)


async def _wallet_buy(callback: CallbackQuery, product: str, lang: str) -> None:
    from handlers.payment import is_product
    if not is_product(product) or product == db.ALL_PRODUCTS:
        await callback.answer()
        return
    owned = await db.paid_products(callback.from_user.id)
    if product in owned or product in await db.free_tests():
        await callback.answer(
            "Bu mahsulot allaqachon ochiq." if lang == "uz" else "Этот продукт уже открыт.",
            show_alert=True,
        )
        return
    amount = await payment.price_for(product)
    if not await wallet.purchase(callback.from_user.id, product, amount):
        await callback.answer(
            "❌ Balans yetarli emas. Balansni to‘ldiring."
            if lang == "uz" else "❌ Недостаточно средств. Пополните баланс.",
            show_alert=True,
        )
        return
    await start_paid_message(callback.message, callback.from_user.id, product, lang)
    await callback.answer()


async def _click_announce(message: Message, payment_row: dict, lang: str) -> None:
    product = payment_row["product"]
    if product == db.ALL_PRODUCTS:
        await message.answer(
            "✅ Xarid muvaffaqiyatli." if lang == "uz" else "✅ Покупка успешна.",
            reply_markup=kb.back_to_menu(lang),
        )
        return
    await start_paid_message(message, payment_row["user_id"], product, lang)


async def notify_paid(payment_id: int) -> None:
    """Click webhook callback: payment is verified, so start the FSM immediately."""
    if payment._bot is None:
        payment.log.warning("notify_paid chaqirildi, lekin bot o'rnatilmagan")
        return
    row = await db.get_payment(payment_id)
    if row is None:
        return
    lang = await db.get_lang(row["user_id"]) or "uz"
    try:
        temporary = await payment._bot.send_message(row["user_id"], "⏳")
        await start_paid_message(temporary, row["user_id"], row["product"], lang)
    except Exception as exc:
        payment.log.warning("To‘lovdan keyingi testni boshlashda xato (%s): %s", row["user_id"], exc)


async def _send_wallet_notice(user_id: int, amount: int, lang: str) -> None:
    if payment._bot is None:
        return
    current = await wallet.balance(user_id)
    if amount > 0:
        text = (
            f"💰 <b>Balansingiz to‘ldirildi!</b>\n\n➕ Qo‘shildi: <b>+{amount:,} so‘m</b>\n💳 Joriy balans: <b>{current:,} so‘m</b>"
            if lang == "uz" else
            f"💰 <b>Ваш баланс пополнен!</b>\n\n➕ Зачислено: <b>+{amount:,} сум</b>\n💳 Текущий баланс: <b>{current:,} сум</b>"
        )
    else:
        spent = abs(amount)
        text = (
            f"💳 <b>Balansingiz o‘zgartirildi.</b>\n\n➖ Yechildi: <b>-{spent:,} so‘m</b>\n💳 Joriy balans: <b>{current:,} so‘m</b>"
            if lang == "uz" else
            f"💳 <b>Ваш баланс изменён.</b>\n\n➖ Списано: <b>-{spent:,} сум</b>\n💳 Текущий баланс: <b>{current:,} сум</b>"
        )
    try:
        await payment._bot.send_message(user_id, text)
    except Exception as exc:
        payment.log.warning("Wallet xabari yuborilmadi (%s): %s", user_id, exc)


_original_wallet_adjust = wallet.adjust
_original_manual_review = wallet.manual_review

async def _localized_adjust(user_id: int, amount: int, admin_id: int, note: str = "") -> bool:
    ok = await _original_wallet_adjust(user_id, amount, admin_id, note)
    if ok:
        await _send_wallet_notice(user_id, amount, await db.get_lang(user_id) or "uz")
    return ok

async def _localized_manual_review(payment_id: int, admin_id: int, approve: bool) -> bool:
    row = await db.get_payment(payment_id)
    ok = await _original_manual_review(payment_id, admin_id, approve)
    if ok and approve and row:
        await _send_wallet_notice(int(row["user_id"]), int(row["amount"]), await db.get_lang(row["user_id"]) or "uz")
    return ok


# Redirect successful wallet purchases and Click confirmations into the real FSM.
async def _patched_wallet_buy(callback: CallbackQuery, product: str, lang: str) -> None:
    await _wallet_buy(callback, product, lang)

async def _patched_announce(message: Message, payment_row: dict, lang: str) -> None:
    await _click_announce(message, payment_row, lang)

shop._buy = _patched_wallet_buy
payment._announce = _patched_announce
wallet.adjust = _localized_adjust
wallet.manual_review = _localized_manual_review
