"""Admin user lookup and quick wallet/access controls."""
from __future__ import annotations

import re

from aiogram import F, Router
from aiogram.filters import BaseFilter, Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder

import database as db
import wallet
from config import IQ_KEY, IQ_PRICE_DEFAULT, is_admin
from handlers.payment import price_for, product_title
from locales import money
from psytests import ORDER

router = Router()


class AdminFilter(BaseFilter):
    async def __call__(self, event: Message | CallbackQuery) -> bool:
        return bool(event.from_user) and is_admin(event.from_user.id)


router.message.filter(AdminFilter())
router.callback_query.filter(AdminFilter())


class FindUser(StatesGroup):
    waiting_id = State()
    waiting_adjust = State()


def menu(user_id: int):
    b = InlineKeyboardBuilder()
    b.button(text="➕ +5 000 so‘m", callback_data=f"admuser:+:{user_id}:5000")
    b.button(text="➕ +10 000 so‘m", callback_data=f"admuser:+:{user_id}:10000")
    b.button(text="➖ −5 000 so‘m", callback_data=f"admuser:-:{user_id}:5000")
    b.button(text="💰 Maxsus summa", callback_data=f"admuser:adjust:{user_id}")
    b.button(text="🧠 IQ ochish", callback_data=f"admuser:grant:{user_id}:{IQ_KEY}")
    b.button(text="🎁 Barchasini ochish", callback_data=f"admuser:grant:{user_id}:all")
    b.button(text="⛔ IQ kirishini bekor qilish", callback_data=f"admuser:revoke:{user_id}:{IQ_KEY}")
    b.button(text="⬅️ Admin panel", callback_data="adm:home")
    b.adjust(2, 1, 1, 2, 1, 1)
    return b.as_markup()


async def render(message: Message, user_id: int) -> None:
    bal = await wallet.balance(user_id)
    products = await db.paid_products(user_id)
    lang = await db.get_lang(user_id) or "uz"
    rows = await db.recent_payments(50)
    user_rows = [r for r in rows if r["user_id"] == user_id][:5]
    profile = next((r for r in await db.recent_users(100) if r["user_id"] == user_id), None)
    name = profile["full_name"] if profile else "Noma’lum"
    username = f"@{profile['username']}" if profile and profile.get("username") else "@—"
    owned_text = " · ".join(product_title(p, lang) for p in sorted(products)) or "—"
    text = (
        "👤 <b>Foydalanuvchi boshqaruvi</b>\n\n"
        f"<b>{name}</b> {username}\n"
        f"ID: <code>{user_id}</code>\n"
        f"Til: <b>{lang}</b>\n"
        f"Wallet: <b>{money(bal)} so‘m</b>\n"
        f"Ochilgan: <b>{owned_text}</b>\n\n"
        f"So‘nggi to‘lov yozuvlari: <b>{len(user_rows)}</b>"
    )
    await message.edit_text(text, reply_markup=menu(user_id))


@router.callback_query(F.data == "admuser:home")
async def ask_user(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await state.set_state(FindUser.waiting_id)
    await callback.message.edit_text(
        "👤 <b>Foydalanuvchini boshqarish</b>\n\n"
        "Telegram user ID yuboring, masalan: <code>123456789</code>\n"
        "Bekor qilish: /bekor"
    )
    await callback.answer()


@router.message(FindUser.waiting_id, Command("bekor"))
async def cancel_find(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer("❌ Bekor qilindi.")


@router.message(FindUser.waiting_id)
async def find_user(message: Message, state: FSMContext) -> None:
    raw = re.sub(r"\D", "", message.text or "")
    if not raw:
        await message.answer("ID faqat raqam bo‘lishi kerak.")
        return
    user_id = int(raw)
    await state.clear()
    await render(message, user_id)


@router.message(Command("user"))
async def user_command(message: Message) -> None:
    parts = (message.text or "").split()
    if len(parts) != 2 or not parts[1].isdigit():
        await message.answer("Format: <code>/user 123456789</code>")
        return
    # Command message cannot be edited cleanly into a panel, so send it.
    fake = message
    bal = await wallet.balance(int(parts[1]))
    await message.answer(f"👤 <b>User {parts[1]}</b>\nWallet: <b>{money(bal)} so‘m</b>", reply_markup=menu(int(parts[1])))


@router.callback_query(F.data.startswith("admuser:+:"))
async def quick_credit(callback: CallbackQuery) -> None:
    _, _, user_raw, amount_raw = callback.data.split(":")
    ok = await wallet.adjust(int(user_raw), int(amount_raw), callback.from_user.id, "Admin quick credit")
    await callback.answer("✅ Balans to‘ldirildi" if ok else "❌ Operatsiya bajarilmadi", show_alert=True)
    await render(callback.message, int(user_raw))


@router.callback_query(F.data.startswith("admuser:-:"))
async def quick_debit(callback: CallbackQuery) -> None:
    _, _, user_raw, amount_raw = callback.data.split(":")
    ok = await wallet.adjust(int(user_raw), -int(amount_raw), callback.from_user.id, "Admin quick debit")
    await callback.answer("✅ Balans kamaytirildi" if ok else "❌ Balans yetarli emas", show_alert=True)
    await render(callback.message, int(user_raw))


@router.callback_query(F.data.startswith("admuser:adjust:"))
async def ask_adjust(callback: CallbackQuery, state: FSMContext) -> None:
    user_id = int(callback.data.split(":")[-1])
    await state.set_state(FindUser.waiting_adjust)
    await state.update_data(user_id=user_id)
    await callback.message.edit_text(
        f"💰 <b>{user_id}</b> uchun o‘zgartirish summasini yuboring.\n\n"
        "+50000 — qo‘shish\n-5000 — ayirish\n\nBekor qilish: /bekor"
    )
    await callback.answer()


@router.message(FindUser.waiting_adjust, Command("bekor"))
async def cancel_adjust(message: Message, state: FSMContext) -> None:
    user_id = (await state.get_data()).get("user_id")
    await state.clear()
    if user_id:
        await message.answer("❌ Bekor qilindi.")
    else:
        await message.answer("❌ Bekor qilindi.")


@router.message(FindUser.waiting_adjust)
async def do_adjust(message: Message, state: FSMContext) -> None:
    raw = (message.text or "").strip().replace(" ", "")
    if not re.fullmatch(r"[+-]?\d+", raw) or int(raw) == 0:
        await message.answer("Masalan: <code>50000</code> yoki <code>-5000</code>")
        return
    data = await state.get_data()
    user_id = int(data.get("user_id", 0))
    amount = int(raw)
    ok = await wallet.adjust(user_id, amount, message.from_user.id, "Admin custom adjustment")
    if not ok:
        await message.answer("❌ Ayirish uchun balans yetarli emas.")
        return
    await state.clear()
    await message.answer(f"✅ {amount:+,} so‘m. Yangi balans: <b>{money(await wallet.balance(user_id))} so‘m</b>", reply_markup=menu(user_id))


@router.callback_query(F.data.startswith("admuser:grant:"))
async def grant(callback: CallbackQuery, bot) -> None:
    _, _, user_raw, product = callback.data.split(":")
    user_id = int(user_raw)
    await db.grant_access(user_id, product, callback.from_user.id)
    await callback.answer("✅ Kirish berildi", show_alert=True)
    try:
        lang = await db.get_lang(user_id) or "uz"
        await bot.send_message(user_id, f"✅ Admin sizga {product_title(product, lang)} ni ochdi.")
    except Exception:
        pass
    await render(callback.message, user_id)


@router.callback_query(F.data.startswith("admuser:revoke:"))
async def revoke(callback: CallbackQuery) -> None:
    _, _, user_raw, product = callback.data.split(":")
    changed = await db.revoke_access(int(user_raw), product)
    await callback.answer("✅ Kirish bekor qilindi" if changed else "ℹ️ O‘zgarish yo‘q", show_alert=True)
    await render(callback.message, int(user_raw))
