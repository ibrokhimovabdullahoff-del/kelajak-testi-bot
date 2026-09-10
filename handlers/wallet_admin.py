"""Admin wallet balance adjustments with an atomic no-negative floor."""
from __future__ import annotations

from aiogram import Router
from aiogram.filters import BaseFilter, Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message

import wallet
from config import is_admin
from locales import money

router = Router()


class AdminFilter(BaseFilter):
    async def __call__(self, event: Message) -> bool:
        return bool(event.from_user) and is_admin(event.from_user.id)


class WalletAdjustState(StatesGroup):
    user_id = State()
    amount = State()
    note = State()


router.message.filter(AdminFilter())


async def _apply_adjustment(message: Message, user_id: int, amount: int, note: str) -> None:
    ok = await wallet.adjust(user_id, amount, message.from_user.id, note or "Admin adjustment")
    if not ok:
        await message.answer("❌ Balans yetarli emas yoki summa 0.")
        return
    await message.answer(
        f"✅ User <code>{user_id}</code>: {amount:+,} so‘m\n"
        f"Yangi balans: <b>{money(await wallet.balance(user_id))} so‘m</b>"
    )


@router.message(Command("walletadjust"))
async def wallet_adjust_command(message: Message, state: FSMContext) -> None:
    parts = (message.text or "").split(maxsplit=2)

    # Preserve the original one-line command:
    # /walletadjust USER_ID AMOUNT [note]
    if len(parts) >= 3 and parts[1].isdigit() and parts[2].split(maxsplit=1)[0].lstrip("-").isdigit():
        user_id = int(parts[1])
        value_parts = parts[2].split(maxsplit=1)
        amount = int(value_parts[0])
        note = value_parts[1] if len(value_parts) > 1 else "Admin adjustment"
        await state.clear()
        await _apply_adjustment(message, user_id, amount, note)
        return

    await state.clear()
    await state.set_state(WalletAdjustState.user_id)
    await message.answer(
        "👤 User ID ni yuboring.\n\n"
        "Masalan: <code>123456789</code>\n"
        "Bekor qilish: /bekor"
    )


@router.message(WalletAdjustState.user_id, Command("bekor", "cancel"))
async def wallet_adjust_cancel(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer("❌ Bekor qilindi.")


@router.message(WalletAdjustState.user_id)
async def wallet_adjust_user_id(message: Message, state: FSMContext) -> None:
    raw = (message.text or "").strip()
    if not raw.isdigit():
        await message.answer("❌ User ID noto‘g‘ri. Faqat raqam yuboring.")
        return
    await state.update_data(user_id=int(raw))
    await state.set_state(WalletAdjustState.amount)
    await message.answer(
        "💰 Summani yuboring.\n\n"
        "Qo‘shish: <code>50000</code>\n"
        "Ayirish: <code>-5000</code>\n\n"
        "Bekor qilish: /bekor"
    )


@router.message(WalletAdjustState.amount, Command("bekor", "cancel"))
async def wallet_adjust_cancel_amount(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer("❌ Bekor qilindi.")


@router.message(WalletAdjustState.amount)
async def wallet_adjust_amount(message: Message, state: FSMContext) -> None:
    raw = (message.text or "").strip().replace(" ", "")
    if not raw.lstrip("-").isdigit():
        await message.answer("❌ Summa noto‘g‘ri. Masalan: <code>50000</code> yoki <code>-5000</code>")
        return
    amount = int(raw)
    if amount == 0:
        await message.answer("❌ Summa 0 bo‘lishi mumkin emas.")
        return
    await state.update_data(amount=amount)
    await state.set_state(WalletAdjustState.note)
    await message.answer(
        "📝 Izoh yuboring yoki <code>/skip</code> deb yozing.\n\n"
        "Masalan: <i>Admin bonus</i>"
    )


@router.message(WalletAdjustState.note, Command("bekor", "cancel"))
async def wallet_adjust_cancel_note(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer("❌ Bekor qilindi.")


@router.message(WalletAdjustState.note, Command("skip"))
async def wallet_adjust_skip_note(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    await state.clear()
    await _apply_adjustment(
        message,
        int(data["user_id"]),
        int(data["amount"]),
        "Admin adjustment",
    )


@router.message(WalletAdjustState.note)
async def wallet_adjust_note(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    note = (message.text or "").strip()[:500]
    if not note:
        await message.answer("❌ Izoh bo‘sh bo‘lmasin yoki /skip yuboring.")
        return
    await state.clear()
    await _apply_adjustment(
        message,
        int(data["user_id"]),
        int(data["amount"]),
        note,
    )
