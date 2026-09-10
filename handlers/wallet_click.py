"""Click checkout for wallet top-ups."""
from __future__ import annotations

from aiogram import F, Router
from aiogram.types import CallbackQuery

import database as db
import keyboards as kb
import wallet
from config import CLICK_ENABLED
from locales import money
from payments import click

router = Router()

AMOUNTS = (10_000, 25_000, 50_000, 100_000, 200_000)
PRODUCT = "wallet_topup_click"


def bi(lang: str, uz: str, ru: str) -> str:
    return uz if lang == "uz" else ru


def amount_menu(lang: str):
    from aiogram.utils.keyboard import InlineKeyboardBuilder

    b = InlineKeyboardBuilder()
    for amount in AMOUNTS:
        b.button(
            text=f"💳 {money(amount)} so‘m" if lang == "uz" else f"💳 {money(amount)} сум",
            callback_data=f"wallet:click:{amount}",
        )
    b.button(text="⬅️ Orqaga" if lang == "uz" else "⬅️ Назад", callback_data="wallet:open")
    b.adjust(2, 2, 1, 1)
    return b.as_markup()


@router.callback_query(F.data == "wallet:click")
async def click_topup_menu(callback: CallbackQuery, lang: str) -> None:
    await callback.answer()
    if not CLICK_ENABLED:
        await callback.message.edit_text(
            bi(lang, "❌ Click hozircha sozlanmagan.", "❌ Click пока не настроен."),
            reply_markup=kb.back_to_menu(lang),
        )
        return
    await callback.message.edit_text(
        bi(lang, "💳 <b>Click orqali balansni to‘ldirish</b>\n\nSummani tanlang:",
           "💳 <b>Пополнение баланса через Click</b>\n\nВыберите сумму:"),
        reply_markup=amount_menu(lang),
    )


@router.callback_query(F.data.startswith("wallet:click:"))
async def create_click_topup(callback: CallbackQuery, lang: str) -> None:
    await callback.answer()
    if not CLICK_ENABLED:
        await callback.message.answer(bi(lang, "❌ Click hozircha sozlanmagan.", "❌ Click пока не настроен."))
        return
    try:
        amount = int(callback.data.rsplit(":", 1)[1])
    except (ValueError, IndexError):
        return
    if amount not in AMOUNTS:
        return

    existing = await db.open_payment(callback.from_user.id, PRODUCT, amount)
    payment_id = existing["id"] if existing else await db.create_payment(
        callback.from_user.id, PRODUCT, amount, "click"
    )
    url = click.payment_url(payment_id, amount)
    await callback.message.edit_text(
        bi(
            lang,
            f"💳 <b>Balansni Click orqali to‘ldirish</b>\n\n"
            f"💰 Summa: <b>{money(amount)} so‘m</b>\n"
            f"🧾 To‘lov: <code>#{payment_id}</code>\n\n"
            "Quyidagi tugma orqali Click sahifasini ochib to‘lang. To‘lov tasdiqlangach, summa balansingizga avtomatik qo‘shiladi.",
            f"💳 <b>Пополнение баланса через Click</b>\n\n"
            f"💰 Сумма: <b>{money(amount)} сум</b>\n"
            f"🧾 Платёж: <code>#{payment_id}</code>\n\n"
            "Откройте страницу Click и оплатите. После подтверждения сумма автоматически зачислится на ваш баланс.",
        ),
        reply_markup=kb.pay_links(payment_id, url, lang, invoice=False),
    )
