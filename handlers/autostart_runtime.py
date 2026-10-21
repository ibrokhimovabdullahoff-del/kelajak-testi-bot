"""Runtime glue: FSM storage for payment webhooks and localized wallet notices.

Earlier this module started a paid TEST right after payment. Tests are free
now (Phase 1): a payment unlocks the FULL REPORT, and `handlers/reports.py`
(`after_payment`) delivers it. `notify_paid` stays as the Click webhook entry
point so main.py keeps working.
"""
from __future__ import annotations

from aiogram.fsm.storage.base import BaseStorage

import database as db
import wallet

from . import payment

_bot_id: int | None = None
_storage: BaseStorage | None = None


def set_runtime(bot_id: int, storage: BaseStorage) -> None:
    global _bot_id, _storage
    _bot_id = bot_id
    _storage = storage


async def notify_paid(payment_id: int) -> None:
    """Click webhook callback: payment is verified — unlock and show the report."""
    await payment.notify_paid(payment_id)


async def notify_failed(payment_id: int) -> None:
    await payment.notify_failed(payment_id)


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


wallet.adjust = _localized_adjust
wallet.manual_review = _localized_manual_review
