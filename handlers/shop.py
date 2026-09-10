"""Premium shop: spend the internal wallet balance on individual products."""
from __future__ import annotations

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder

import database as db
import wallet
from config import IQ_EMOJI, IQ_KEY
from handlers.payment import price_for, product_title
from locales import money
from psytests import ORDER, REGISTRY

router = Router()


def bi(lang: str, uz: str, ru: str) -> str:
    return uz if lang == "uz" else ru


def product_rows(lang: str):
    rows = []
    for key in ORDER:
        rows.append((key, REGISTRY[key].emoji, REGISTRY[key].title.get(lang, REGISTRY[key].title["uz"])))
    rows.append((IQ_KEY, IQ_EMOJI, "Premium IQ testi" if lang == "uz" else "Премиум IQ-тест"))
    return rows


async def shop_markup(lang: str):
    b = InlineKeyboardBuilder()
    for key, emoji, title in product_rows(lang):
        price = await price_for(key)
        b.button(text=f"{emoji} {price:,} so‘m · {title}", callback_data=f"shop:buy:{key}")
    b.button(text=bi(lang, "⬅️ Balans", "⬅️ Баланс"), callback_data="wallet:open")
    b.adjust(1)
    return b.as_markup()


async def _buy(callback: CallbackQuery, product: str, lang: str) -> None:
    from handlers.payment import is_product

    if not is_product(product) or product == db.ALL_PRODUCTS:
        await callback.answer()
        return
    owned = await db.paid_products(callback.from_user.id)
    if product in owned or product in await db.free_tests():
        await callback.answer(bi(lang, "Bu mahsulot allaqachon ochiq.", "Этот продукт уже открыт."), show_alert=True)
        return
    amount = await price_for(product)
    if await wallet.purchase(callback.from_user.id, product, amount):
        await callback.message.answer(
            bi(lang, f"✅ Xarid muvaffaqiyatli. {product_title(product, lang)} ochildi.",
               f"✅ Покупка успешна. {product_title(product, lang)} открыто."),
        )
        await callback.answer()
    else:
        await callback.answer(bi(lang, "❌ Balans yetarli emas. Balansni to‘ldiring.", "❌ Недостаточно средств. Пополните баланс."), show_alert=True)


@router.message(Command("shop", "sotib_olish"))
async def shop(message: Message, lang: str) -> None:
    bal = await wallet.balance(message.from_user.id)
    await message.answer(
        f"🛒 <b>{bi(lang, 'Premium do‘kon', 'Премиум-магазин')}</b>\n\n"
        f"{bi(lang, 'Balansingiz', 'Ваш баланс')}: <b>{money(bal)} so‘m</b>\n\n"
        f"{bi(lang, 'Testlarni alohida balansdan oching.', 'Открывайте тесты по отдельности с внутреннего баланса.')}",
        reply_markup=await shop_markup(lang),
    )


@router.callback_query(F.data == "wallet:shop")
async def shop_callback(callback: CallbackQuery, lang: str) -> None:
    await callback.message.edit_text(
        f"🛒 <b>{bi(lang, 'Premium do‘kon', 'Премиум-магазин')}</b>\n\n"
        f"{bi(lang, 'Balansingiz', 'Ваш баланс')}: <b>{money(await wallet.balance(callback.from_user.id))} so‘m</b>",
        reply_markup=await shop_markup(lang),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("shop:buy:"))
async def buy(callback: CallbackQuery, lang: str) -> None:
    product = callback.data.split(":", 2)[2]
    await _buy(callback, product, lang)
