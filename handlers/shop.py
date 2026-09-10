"""Wallet purchases: spend internal balance on existing paid products."""
from __future__ import annotations

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder

import database as db
import wallet
from handlers.payment import price_for, product_title
from locales import money
from psytests import ORDER, REGISTRY

router = Router()


def bi(lang: str, uz: str, ru: str) -> str:
    return uz if lang == "uz" else ru


async def shop_markup(lang: str):
    b = InlineKeyboardBuilder()
    for key in ORDER:
        price = await price_for(key)
        b.button(text=f"{REGISTRY[key].emoji} {price:,} so‘m · {REGISTRY[key].title.get(lang, REGISTRY[key].title['uz'])}", callback_data=f"wallet:buy:{key}")
    price_all = await price_for(db.ALL_PRODUCTS)
    if price_all:
        b.button(text=f"🎁 {price_all:,} so‘m · {bi(lang, 'Barcha testlar', 'Все тесты')}", callback_data="wallet:buy:all")
    b.button(text=bi(lang, "⬅️ Balans", "⬅️ Баланс"), callback_data="wallet:open")
    b.adjust(1)
    return b.as_markup()


@router.message(Command("shop", "sotib_olish"))
async def shop(message: Message, lang: str) -> None:
    bal = await wallet.balance(message.from_user.id)
    await message.answer(
        f"🛒 <b>{bi(lang, 'Balansdan xarid', 'Покупка с баланса')}</b>\n\n"
        f"{bi(lang, 'Balansingiz', 'Ваш баланс')}: <b>{money(bal)} so‘m</b>",
        reply_markup=await shop_markup(lang),
    )


@router.callback_query(F.data == "wallet:shop")
async def shop_callback(callback: CallbackQuery, lang: str) -> None:
    await callback.message.edit_text(
        f"🛒 <b>{bi(lang, 'Balansdan xarid', 'Покупка с баланса')}</b>\n\n"
        f"{bi(lang, 'Balansingiz', 'Ваш баланс')}: <b>{money(await wallet.balance(callback.from_user.id))} so‘m</b>",
        reply_markup=await shop_markup(lang),
    )
    await callback.answer()
