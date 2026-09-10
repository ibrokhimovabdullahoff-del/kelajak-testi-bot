"""Admin controls for the premium IQ product."""
from __future__ import annotations

from aiogram import F, Router
from aiogram.filters import BaseFilter, Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder

import database as db
import wallet
from config import IQ_KEY, IQ_PRICE_DEFAULT, is_admin

router = Router()


class AdminFilter(BaseFilter):
    async def __call__(self, event: Message | CallbackQuery) -> bool:
        return bool(event.from_user) and is_admin(event.from_user.id)


router.message.filter(AdminFilter())
router.callback_query.filter(AdminFilter())


class PriceState(StatesGroup):
    waiting = State()


async def _price() -> int:
    return await db.price_of(IQ_KEY, IQ_PRICE_DEFAULT)


def _menu(is_free: bool, price: int):
    b = InlineKeyboardBuilder()
    b.button(text=("🎁 Hozir Bepul — Pullikka o‘tkazish" if is_free else "💳 Hozir Pullik — Bepul qilish"), callback_data="admiq:toggle_free")
    b.button(text=f"💰 Narx: {price:,} so‘m — O‘zgartirish", callback_data="admiq:price")
    b.button(text="⬅️ Admin panel", callback_data="adm:home")
    b.adjust(1)
    return b.as_markup()


@router.callback_query(F.data == "admiq:home")
async def home(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    free = IQ_KEY in await db.free_tests()
    price = await _price()
    status = "🎁 Bepul" if free else "💳 Pullik"
    text = (
        "🧠 <b>Premium IQ sozlamalari</b>\n\n"
        f"Holat: <b>{status}</b>\n"
        f"Narx: <b>{price:,} so‘m</b>\n\n"
        "Bu yerda IQ testini istalgan payt bepul yoki pullik qilishingiz va narxini o‘zgartirishingiz mumkin."
    )
    await callback.message.edit_text(text, reply_markup=_menu(free, price))
    await callback.answer()


@router.callback_query(F.data == "admiq:toggle_free")
async def toggle_free(callback: CallbackQuery) -> None:
    now_free = await db.toggle_free_test(IQ_KEY)
    await callback.answer("🎁 IQ endi bepul" if now_free else "💳 IQ endi pullik", show_alert=True)
    free = IQ_KEY in await db.free_tests()
    await callback.message.edit_reply_markup(reply_markup=_menu(free, await _price()))


@router.callback_query(F.data == "admiq:price")
async def ask_price(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(PriceState.waiting)
    await callback.message.edit_text(
        "💰 <b>IQ narxini o‘zgartirish</b>\n\n"
        "Yangi narxni faqat raqamda yuboring, masalan: <code>5000</code>\n"
        "0 = bepul narx sifatida saqlanadi, lekin pullik/bepul holatini yuqoridagi tugma boshqaradi.\n\n"
        "Bekor qilish: /bekor"
    )
    await callback.answer()


@router.message(PriceState.waiting, Command("bekor"))
async def cancel(message: Message, state: FSMContext) -> None:
    await state.clear()
    free = IQ_KEY in await db.free_tests()
    await message.answer("❌ Bekor qilindi.", reply_markup=_menu(free, await _price()))


@router.message(PriceState.waiting)
async def set_price(message: Message, state: FSMContext) -> None:
    raw = "".join(c for c in (message.text or "") if c.isdigit())
    if not raw:
        await message.answer("Faqat raqam yuboring, masalan <code>5000</code>.")
        return
    amount = min(int(raw), 100000000)
    await db.set_price(IQ_KEY, amount)
    await state.clear()
    free = IQ_KEY in await db.free_tests()
    await message.answer(f"✅ IQ narxi <b>{amount:,} so‘m</b> bo‘ldi.", reply_markup=_menu(free, amount))


@router.message(Command("iqprice"))
async def iqprice(message: Message) -> None:
    await message.answer(f"🧠 IQ narxi: <b>{await _price():,} so‘m</b> · {'bepul' if IQ_KEY in await db.free_tests() else 'pullik'}")
