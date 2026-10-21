"""Balansdan to'liq tahlil sotib olish (/shop).

Balans — majburiy qadam emas: u faqat avval pul to'ldirganlar uchun qoladi.
Sotib olish `handlers/reports.py` dagi "rep:wallet:<mahsulot>:0" yo'lidan
o'tadi — to'lovdan keyin oxirgi natijaning to'liq tahlili darhol ochiladi.
"""
from __future__ import annotations

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder

import wallet
from config import BUNDLE_KEY, MENU_ORDER
from handlers.payment import price_for, product_title
from locales import money, t

router = Router()


def bi(lang: str, uz: str, ru: str) -> str:
    return uz if lang == "uz" else ru


async def shop_markup(lang: str):
    b = InlineKeyboardBuilder()
    for key in [*MENU_ORDER, BUNDLE_KEY]:
        price = await price_for(key)
        b.button(text=f"{product_title(key, lang)} · {money(price)} " + bi(lang, "so‘m", "сум"),
                 callback_data=f"rep:wallet:{key}:0")
    b.button(text=t("btn_menu", lang), callback_data="nav:menu")
    b.adjust(1)
    return b.as_markup()


def _text(balance: int, lang: str) -> str:
    return (f"🛒 <b>{bi(lang, 'To‘liq tahlilni balansdan ochish', 'Полный разбор с баланса')}</b>\n\n"
            f"{bi(lang, 'Balansingiz', 'Ваш баланс')}: <b>{money(balance)} " + bi(lang, "so‘m", "сум") + "</b>")


@router.message(Command("shop", "sotib_olish"))
async def shop(message: Message, lang: str) -> None:
    await message.answer(_text(await wallet.balance(message.from_user.id), lang), reply_markup=await shop_markup(lang))


@router.callback_query(F.data == "wallet:shop")
async def shop_callback(callback: CallbackQuery, lang: str) -> None:
    await callback.message.edit_text(_text(await wallet.balance(callback.from_user.id), lang),
                                     reply_markup=await shop_markup(lang))


@router.callback_query(F.data.startswith("shop:buy:") | F.data.startswith("wallet:buy:"))
async def old_buy(callback: CallbackQuery, lang: str) -> None:
    """Eski xabarlardagi "Balansdan to'lash" tugmasi → to'liq tahlilni balansdan ochish."""
    from . import reports

    product = callback.data.split(":", 2)[2]
    await reports.wallet_buy(callback, product, "0", lang)
