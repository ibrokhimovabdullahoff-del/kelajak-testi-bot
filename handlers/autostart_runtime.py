"""Runtime glue that starts a paid test immediately after successful payment.

The payment/shop handlers historically announced that a product was unlocked and
left the user on a confirmation screen.  This module bridges payment completion
to the same FSM-backed quiz starters used by the normal test menu.
"""
from __future__ import annotations

from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.base import StorageKey, BaseStorage
from aiogram.types import CallbackQuery, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder

import database as db
import keyboards as kb
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
    return FSMContext(
        storage=_storage,
        key=StorageKey(bot_id=_bot_id, chat_id=user_id, user_id=user_id),
    )


async def start_paid_message(message: Message, user_id: int, product: str, lang: str) -> None:
    """Start the purchased product using the real dispatcher FSM storage."""
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
    if not await _purchase_and_start(callback, product, amount, lang):
        await callback.answer(
            "❌ Balans yetarli emas. Balansni to‘ldiring."
            if lang == "uz" else "❌ Недостаточно средств. Пополните баланс.",
            show_alert=True,
        )


async def _purchase_and_start(callback: CallbackQuery, product: str, amount: int, lang: str) -> bool:
    import wallet
    if not await wallet.purchase(callback.from_user.id, product, amount):
        return False
    await start_paid_message(callback.message, callback.from_user.id, product, lang)
    await callback.answer()
    return True


async def _click_announce(message: Message, payment_row: dict, lang: str, state: FSMContext | None = None) -> None:
    product = payment_row["product"]
    if product == db.ALL_PRODUCTS:
        await message.answer("✅ Xarid muvaffaqiyatli." if lang == "uz" else "✅ Покупка успешна.", reply_markup=kb.back_to_menu(lang))
        return
    await start_paid_message(message, payment_row["user_id"], product, lang)


async def notify_paid(payment_id: int) -> None:
    """Webhook callback: payment is already verified, so start the FSM immediately."""
    if payment._bot is None:
        payment.log.warning("notify_paid chaqirildi, lekin bot o'rnatilmagan")
        return
    row = await db.get_payment(payment_id)
    if row is None:
        return
    lang = await db.get_lang(row["user_id"]) or "uz"
    try:
        await start_paid_message(
            await payment._bot.send_message(row["user_id"], "⏳"),
            row["user_id"], row["product"], lang,
        )
    except Exception as exc:
        payment.log.warning("To‘lovdan keyingi testni boshlashda xato (%s): %s", row["user_id"], exc)


# Preserve the normal module API while redirecting successful wallet purchases
# and Click confirmations into the real FSM.
_original_wallet_buy = shop._buy
_original_announce = payment._announce

async def _patched_wallet_buy(callback: CallbackQuery, product: str, lang: str) -> None:
    await _wallet_buy(callback, product, lang)

async def _patched_announce(message: Message, payment_row: dict, lang: str) -> None:
    await _click_announce(message, payment_row, lang)

shop._buy = _patched_wallet_buy
payment._announce = _patched_announce
