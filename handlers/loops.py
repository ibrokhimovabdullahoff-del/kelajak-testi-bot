"""2-bosqich tugmalari: bepul tahlil, do'st bilan solishtirish, promo kod, eslatmani o'chirish.

Qoidalar va ma'lumot o'z modullarida: `credits.py`, `compare.py`,
`promo.py`, `reminders.py`. Bu yerda faqat Telegram tomoni.
"""
from __future__ import annotations

import logging

from aiogram import Bot, F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command, CommandObject
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, LinkPreviewOptions, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder

import access
import compare
import credits
import database as db
import keyboards as kb
import promo
import reminders
from config import IQ_KEY
from locales import t

from . import growth
from . import reports

log = logging.getLogger(__name__)
router = Router()


async def _show(message: Message, text: str, markup, edit: bool = True) -> None:
    """Tahrirlab bo'lmasa (rasm yoki eski xabar) — yangi xabar."""
    if edit and not message.photo:
        try:
            await message.edit_text(text, reply_markup=markup)
            return
        except TelegramBadRequest as exc:
            if "not modified" in str(exc):
                return
    await message.answer(text, reply_markup=markup)


# --- Bepul to'liq tahlil (do'st mukofoti) -------------------------------------


@router.callback_query(F.data == "cred:menu")
async def credit_menu(callback: CallbackQuery, lang: str) -> None:
    user_id = callback.from_user.id
    have = await credits.available(user_id)
    if not have:
        await callback.answer(t("credit_none", lang), show_alert=True)
        return
    missing = await access.missing(user_id)
    b = InlineKeyboardBuilder()
    for key in missing:
        b.button(text=reports.test_title(key, lang), callback_data=f"cred:use:{key}:0")
    b.button(text=t("btn_menu", lang), callback_data="nav:menu")
    b.adjust(1)
    text = t("credit_menu", lang, n=have) if missing else t("credit_all_open", lang)
    await _show(callback.message, text, b.as_markup())


@router.callback_query(F.data.startswith("cred:use:"))
async def credit_use(callback: CallbackQuery, lang: str) -> None:
    """Bepul tahlilni ishlatish. Natija (rid) berilgan bo'lsa — o'sha darhol ochiladi."""
    parts = callback.data.split(":")
    if len(parts) != 4 or parts[2] not in access.TESTS:
        return
    test_key, raw = parts[2], parts[3]
    user_id = callback.from_user.id
    if await access.has(user_id, test_key):
        await callback.answer(t("report_already", lang))
    elif not await credits.use(user_id, test_key):
        await callback.answer(t("credit_none", lang), show_alert=True)
        return
    row = await reports._user_row(user_id, int(raw) if raw.isdigit() else 0)
    row = row or await db.latest_result(user_id, test_key)
    title = reports.test_title(test_key, lang)
    if row is None:
        await callback.message.answer(t("credit_used_take", lang, title=title),
                                      reply_markup=kb.start_test(test_key, lang))
        return
    await callback.message.answer(t("credit_used", lang, title=title))
    await reports.deliver(callback.bot, user_id, row, lang)


# --- Do'st bilan solishtirish ---------------------------------------------------


@router.callback_query(F.data.startswith("cmp:share:"))
async def compare_share(callback: CallbackQuery, lang: str) -> None:
    test_key = callback.data.rsplit(":", 1)[1]
    user_id = callback.from_user.id
    if test_key not in compare.TESTS or not growth.bot_username():
        return
    if await db.latest_result(user_id, test_key) is None:
        await callback.answer(t("cmp_need_result", lang), show_alert=True)
        return
    b = InlineKeyboardBuilder()
    b.button(text=t("btn_compare_send", lang),
             url=compare.share_url(growth.bot_username(), test_key, user_id, lang))
    b.button(text=t("btn_menu", lang), callback_data="nav:menu")
    b.adjust(1)
    await callback.message.answer(t("cmp_share_screen", lang), reply_markup=b.as_markup(),
                                  link_preview_options=LinkPreviewOptions(is_disabled=True))


async def compare_start(message: Message, payload: str | None, lang: str) -> bool:
    """/start cmp_<test>_<id>: taklifni yozadi va do'stga nima qilishini aytadi.

    Do'st bu testni avval topshirgan bo'lsa — solishtirish darhol chiqadi.
    Qaytaradi: True — xabar yuborildi (bosh menyu kerak emas).
    """
    parsed = compare.parse(payload)
    if parsed is None:
        return False
    test_key, inviter = parsed
    friend = message.from_user.id
    if not await compare.register(friend, test_key, inviter):
        return False
    if await db.latest_result(friend, test_key):
        return await compare.show(message.bot, friend, test_key, inviter, lang)
    name = await compare.first_name(inviter, lang)
    title = "Big Five" if test_key == "bigfive" else t("iq_title", lang)
    b = InlineKeyboardBuilder()
    b.button(text=t("btn_start_test", lang), callback_data="iq:card" if test_key == IQ_KEY else f"test:{test_key}")
    b.button(text=t("btn_menu", lang), callback_data="nav:menu")
    b.adjust(1)
    await message.answer(t("cmp_intro", lang, name=name, test=title), reply_markup=b.as_markup())
    return True


# --- Promo kod -------------------------------------------------------------


class PromoInput(StatesGroup):
    waiting = State()


_PROMO_ERRORS = {
    promo.NOT_FOUND: "promo_not_found", promo.INACTIVE: "promo_inactive", promo.EXPIRED: "promo_expired",
    promo.USED_UP: "promo_used_up", promo.ALREADY: "promo_already",
}


async def redeem_and_reply(message: Message, user_id: int, raw: str | None, lang: str) -> str:
    status, row = await promo.redeem(user_id, raw)
    if status != promo.OK:
        await message.answer(t(_PROMO_ERRORS[status], lang), reply_markup=kb.back_to_menu(lang))
        return status
    if row["kind"] == promo.FREE:
        tests = promo.tests_of(row)
        names = ", ".join(reports.test_title(key, lang) for key in tests)
        markup = kb.start_test(tests[0], lang) if len(tests) == 1 else kb.back_to_menu(lang, other_tests=True)
        await message.answer(t("promo_ok_free", lang, tests=names), reply_markup=markup)
    else:
        await message.answer(t("promo_ok_discount", lang, pct=row["percent"]),
                             reply_markup=kb.back_to_menu(lang, other_tests=True))
    return status


@router.message(Command("promo"))
async def cmd_promo(message: Message, command: CommandObject, state: FSMContext, lang: str) -> None:
    if command.args:
        await state.clear()
        await redeem_and_reply(message, message.from_user.id, command.args, lang)
        return
    await state.set_state(PromoInput.waiting)
    await message.answer(t("promo_ask", lang))


@router.callback_query(F.data == "promo:ask")
async def ask_promo(callback: CallbackQuery, state: FSMContext, lang: str) -> None:
    await state.set_state(PromoInput.waiting)
    await callback.message.answer(t("promo_ask", lang))


@router.message(PromoInput.waiting, Command("bekor", "cancel"))
async def cancel_promo(message: Message, state: FSMContext, lang: str) -> None:
    await state.clear()
    await message.answer(t("cancelled", lang), reply_markup=kb.back_to_menu(lang))


@router.message(PromoInput.waiting, F.text)
async def got_promo(message: Message, state: FSMContext, lang: str) -> None:
    await state.clear()
    await redeem_and_reply(message, message.from_user.id, message.text, lang)


# --- Eslatmalar ---------------------------------------------------------------


@router.callback_query(F.data == "rem:off")
async def reminders_off(callback: CallbackQuery, lang: str, bot: Bot) -> None:
    await reminders.opt_out(callback.from_user.id)
    await callback.answer()
    await callback.message.answer(t("rem_off_ok", lang))
