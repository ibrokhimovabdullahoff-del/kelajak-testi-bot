"""User wallet, manual card top-ups and admin review.

Manual card payments are never credited automatically. An admin must approve
an individual pending payment, and the approval is atomic/idempotent.
"""
from __future__ import annotations

import re

from aiogram import Bot, F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import BaseFilter, Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder

import database as db
import wallet
from config import MANUAL_CARD_HOLDER, MANUAL_CARD_NUMBER, MANUAL_RECEIPT_CHAT, is_admin
from locales import money

router = Router()


def bi(lang: str, uz: str, ru: str) -> str:
    return uz if lang == "uz" else ru


class TopUp(StatesGroup):
    amount = State()
    receipt = State()


class Adjust(StatesGroup):
    value = State()


class AdminFilter(BaseFilter):
    async def __call__(self, event: Message | CallbackQuery) -> bool:
        return bool(event.from_user) and is_admin(event.from_user.id)


admin_router = Router()
admin_router.message.filter(AdminFilter())
admin_router.callback_query.filter(AdminFilter())


def wallet_menu(lang: str):
    b = InlineKeyboardBuilder()
    b.button(text=bi(lang, "➕ Balansni to‘ldirish", "➕ Пополнить баланс"), callback_data="wallet:topup")
    b.button(text=bi(lang, "🧾 Tranzaksiyalar", "🧾 История операций"), callback_data="wallet:history")
    b.button(text=bi(lang, "⬅️ Orqaga", "⬅️ Назад"), callback_data="nav:menu")
    b.adjust(1)
    return b.as_markup()


def review_menu(payment_id: int):
    b = InlineKeyboardBuilder()
    b.button(text="✅ Tasdiqlash", callback_data=f"admwallet:approve:{payment_id}")
    b.button(text="❌ Rad etish", callback_data=f"admwallet:reject:{payment_id}")
    b.adjust(2)
    return b.as_markup()


@router.message(Command("balans", "balance", "wallet"))
async def wallet_command(message: Message, lang: str) -> None:
    bal = await wallet.balance(message.from_user.id)
    await message.answer(
        f"💰 <b>{bi(lang, 'Mening balansim', 'Мой баланс')}</b>\n\n"
        f"<b>{money(bal)} so‘m</b>\n\n"
        f"{bi(lang, 'Bu bot ichidagi xaridlar uchun ishlatiladigan balans.', 'Это внутренний баланс для покупок внутри бота.')}",
        reply_markup=wallet_menu(lang),
    )


@router.callback_query(F.data == "wallet:open")
async def wallet_open(callback: CallbackQuery, lang: str) -> None:
    bal = await wallet.balance(callback.from_user.id)
    await callback.message.edit_text(
        f"💰 <b>{bi(lang, 'Mening balansim', 'Мой баланс')}</b>\n\n<b>{money(bal)} so‘m</b>",
        reply_markup=wallet_menu(lang),
    )
    await callback.answer()


@router.callback_query(F.data == "wallet:history")
async def wallet_history(callback: CallbackQuery, lang: str) -> None:
    rows = await wallet.history(callback.from_user.id)
    lines = [f"🧾 <b>{bi(lang, 'Tranzaksiyalar', 'История операций')}</b>", ""]
    if not rows:
        lines.append(bi(lang, "Hali tranzaksiya yo‘q.", "Операций пока нет."))
    for row in rows:
        sign = "+" if row["amount"] > 0 else ""
        lines.append(f"{sign}{money(row['amount'])} so‘m · {row['kind']} · {(row['created_at'] or '')[:16]}")
    await callback.message.edit_text("\n".join(lines), reply_markup=wallet_menu(lang))
    await callback.answer()


@router.callback_query(F.data == "wallet:topup")
async def topup_start(callback: CallbackQuery, state: FSMContext, lang: str) -> None:
    await state.set_state(TopUp.amount)
    await callback.message.edit_text(
        bi(lang,
           "➕ <b>Balansni to‘ldirish</b>\n\n"
           "UZCARD/HUMO orqali quyidagi kartaga to‘lov qiling:\n"
           f"💳 <code>{MANUAL_CARD_NUMBER}</code>\n"
           f"👤 {MANUAL_CARD_HOLDER}\n\n"
           "To‘lagan summangizni faqat raqamda yuboring (masalan: 50000).\n"
           "Bekor qilish: /bekor",
           "➕ <b>Пополнение баланса</b>\n\n"
           "Оплатите через UZCARD/HUMO на карту:\n"
           f"💳 <code>{MANUAL_CARD_NUMBER}</code>\n"
           f"👤 {MANUAL_CARD_HOLDER}\n\n"
           "Отправьте сумму оплаты цифрами (например: 50000).\n"
           "Отмена: /bekor"),
    )
    await callback.answer()


@router.message(TopUp.amount, Command("bekor"))
async def cancel_topup(message: Message, state: FSMContext, lang: str) -> None:
    await state.clear()
    await message.answer(bi(lang, "❌ Bekor qilindi.", "❌ Отменено."), reply_markup=wallet_menu(lang))


@router.message(TopUp.amount)
async def topup_amount(message: Message, state: FSMContext, lang: str) -> None:
    raw = re.sub(r"\D", "", message.text or "")
    amount = int(raw) if raw else 0
    if amount < 1000:
        await message.answer(bi(lang, "❌ Kamida 1 000 so‘m kiriting.", "❌ Минимальная сумма — 1 000 сум."))
        return
    await state.update_data(amount=amount)
    await state.set_state(TopUp.receipt)
    await message.answer(
        bi(lang,
           f"📸 Endi <b>{money(amount)} so‘m</b> to‘lov chekini rasm sifatida yuboring.\n\n"
           "Chek <b>@yordamchi_savdo</b> ga tekshiruv uchun yuboriladi. Admin tasdiqlamaguncha balans oshmaydi.",
           f"📸 Теперь отправьте фото чека на <b>{money(amount)} сум</b>.\n\n"
           "Чек будет отправлен на проверку в <b>@yordamchi_savdo</b>. Баланс увеличится только после одобрения админом."),
    )


@router.message(TopUp.receipt, Command("bekor"))
async def cancel_receipt(message: Message, state: FSMContext, lang: str) -> None:
    await state.clear()
    await message.answer(bi(lang, "❌ Bekor qilindi.", "❌ Отменено."), reply_markup=wallet_menu(lang))


@router.message(TopUp.receipt, F.photo)
async def topup_receipt(message: Message, state: FSMContext, lang: str, bot: Bot) -> None:
    data = await state.get_data()
    amount = int(data.get("amount", 0))
    if amount <= 0:
        await state.clear()
        await message.answer(bi(lang, "❌ To‘lov oynasi eskirgan. Qaytadan boshlang.", "❌ Сессия оплаты устарела. Начните заново."))
        return
    receipt_id = message.photo[-1].file_id
    payment_id = await wallet.manual_create(message.from_user.id, amount, receipt_id, message.caption or "")
    await state.clear()
    text = (
        f"🧾 <b>Manual to‘lov #{payment_id}</b>\n"
        f"👤 <code>{message.from_user.id}</code>\n"
        f"💰 <b>{money(amount)} so‘m</b>\n"
        f"📅 {(message.date.isoformat())[:19]}\n\n"
        "⚠️ Admin tasdig‘idan keyin balansga tushadi."
    )
    # Notify the configured Telegram review chat when it is a numeric chat ID.
    if MANUAL_RECEIPT_CHAT:
        try:
            await bot.send_photo(MANUAL_RECEIPT_CHAT, receipt_id, caption=text, reply_markup=review_menu(payment_id))
        except Exception:
            pass
    await message.answer(
        bi(lang,
           f"✅ Chek qabul qilindi. Buyurtma: <code>#{payment_id}</code>\nBalans admin tasdig‘idan keyin <b>{money(amount)} so‘m</b> ga oshadi.",
           f"✅ Чек принят. Заказ: <code>#{payment_id}</code>\nБаланс увеличится на <b>{money(amount)} сум</b> после проверки админом."),
        reply_markup=wallet_menu(lang),
    )


@router.message(TopUp.receipt)
async def receipt_required(message: Message, lang: str) -> None:
    await message.answer(bi(lang, "Iltimos, chekni rasm sifatida yuboring.", "Пожалуйста, отправьте чек именно фотографией."))


@router.callback_query(F.data.startswith("wallet:buy:"))
async def buy_from_wallet(callback: CallbackQuery, lang: str) -> None:
    product = callback.data.split(":", 2)[2]
    from psytests import REGISTRY
    from handlers.payment import price_for, product_title
    if product != db.ALL_PRODUCTS and product not in REGISTRY:
        await callback.answer()
        return
    amount = await price_for(product)
    if await wallet.purchase(callback.from_user.id, product, amount):
        await callback.message.answer(
            bi(lang, f"✅ Xarid muvaffaqiyatli. {product_title(product, lang)} ochildi.",
               f"✅ Покупка успешна. {product_title(product, lang)} открыто."),
        )
        await callback.answer()
    else:
        await callback.answer(bi(lang, "❌ Balans yetarli emas.", "❌ Недостаточно средств."), show_alert=True)


@admin_router.callback_query(F.data == "adm:wallet")
async def admin_wallet(callback: CallbackQuery) -> None:
    rows = await wallet.pending_manual(30)
    lines = ["💰 <b>Wallet / manual payments</b>", ""]
    if not rows:
        lines.append("Hali manual to‘lov yo‘q.")
    for r in rows:
        mark = {"pending": "⏳", "paid": "✅", "cancelled": "❌"}.get(r["status"], "•")
        who = f"@{r['username']}" if r["username"] else f"id{r['user_id']}"
        lines.append(f"{mark} <code>#{r['id']}</code> {who} · <b>{money(r['amount'])}</b> · {r['status']}")
    b = InlineKeyboardBuilder()
    b.button(text="🔄 Yangilash", callback_data="adm:wallet")
    b.button(text="⬅️ Admin panel", callback_data="adm:home")
    b.adjust(1)
    await callback.message.edit_text("\n".join(lines), reply_markup=b.as_markup())
    await callback.answer()


@admin_router.callback_query(F.data.startswith("admwallet:"))
async def admin_review(callback: CallbackQuery, bot: Bot) -> None:
    _, action, raw_id = callback.data.split(":")
    payment_id = int(raw_id)
    ok = await wallet.manual_review(payment_id, callback.from_user.id, action == "approve")
    if not ok:
        await callback.answer("Bu to‘lov allaqachon ko‘rib chiqilgan.", show_alert=True)
        return
    await callback.answer("Tasdiqlandi" if action == "approve" else "Rad etildi", show_alert=True)
    payment = await db.get_payment(payment_id)
    if payment:
        try:
            lang = await db.get_lang(payment["user_id"]) or "uz"
            if action == "approve":
                await bot.send_message(payment["user_id"], bi(lang,
                    f"✅ Manual to‘lov #{payment_id} tasdiqlandi. Balansingiz +{money(payment['amount'])} so‘m.",
                    f"✅ Ручной платёж #{payment_id} подтверждён. Баланс пополнен на {money(payment['amount'])} сум."))
            else:
                await bot.send_message(payment["user_id"], bi(lang,
                    f"❌ Manual to‘lov #{payment_id} rad etildi.",
                    f"❌ Ручной платёж #{payment_id} отклонён."))
        except Exception:
            pass
    await admin_wallet(callback)


@admin_router.message(Command("walletadmin"))
async def wallet_admin_command(message: Message) -> None:
    rows = await wallet.pending_manual(30)
    await message.answer(f"💰 Manual payments: {len(rows)}")
