"""Admin wallet balance adjustments with an atomic no-negative floor."""
from __future__ import annotations

from aiogram import Router
from aiogram.filters import BaseFilter, Command
from aiogram.types import Message

import wallet
from config import is_admin
from locales import money

router = Router()


class AdminFilter(BaseFilter):
    async def __call__(self, event: Message) -> bool:
        return bool(event.from_user) and is_admin(event.from_user.id)


router.message.filter(AdminFilter())


@router.message(Command("walletadjust"))
async def wallet_adjust(message: Message) -> None:
    parts = (message.text or "").split(maxsplit=2)
    if len(parts) < 2 or not parts[0].startswith("/") or not parts[1].isdigit():
        await message.answer(
            "Format: <code>/walletadjust 123456789 50000</code>\n"
            "Minus bilan ayirish: <code>/walletadjust 123456789 -5000</code>"
        )
        return
    value_raw = parts[2].split(maxsplit=1) if len(parts) == 3 else []
    if not value_raw or not value_raw[0].lstrip("-").isdigit():
        await message.answer("Summa noto‘g‘ri. Masalan: <code>/walletadjust 123456789 50000</code>")
        return
    user_id = int(parts[1])
    amount = int(value_raw[0])
    note = value_raw[1] if len(value_raw) > 1 else "Admin adjustment"
    ok = await wallet.adjust(user_id, amount, message.from_user.id, note)
    if not ok:
        await message.answer("❌ Balans yetarli emas yoki summa 0.")
        return
    await message.answer(
        f"✅ User <code>{user_id}</code>: {amount:+,} so‘m\n"
        f"Yangi balans: <b>{money(await wallet.balance(user_id))} so‘m</b>"
    )
