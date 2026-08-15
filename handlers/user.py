"""Foydalanuvchi oqimi: til, testlar menyusi, savollar, natija."""
from __future__ import annotations

import logging

from aiogram import F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message

import database as db
import keyboards as kb
import report
from locales import LANGS, t, tr
from psytests import REGISTRY, score

log = logging.getLogger(__name__)
router = Router()

TELEGRAM_LIMIT = 3800


class Quiz(StatesGroup):
    answering = State()


# --- Yordamchilar -----------------------------------------------------------


async def safe_edit(message: Message, text: str, reply_markup=None) -> None:
    """Tahrirlab bo'lmasa yangi xabar yuboradi — tugma osilib qolmasligi uchun."""
    try:
        await message.edit_text(text, reply_markup=reply_markup)
    except TelegramBadRequest as exc:
        if "message is not modified" in str(exc):
            return
        log.debug("edit_text ishlamadi, yangi xabar: %s", exc)
        await message.answer(text, reply_markup=reply_markup)


async def send_chunked(message: Message, text: str, reply_markup=None) -> None:
    """Uzun natijani Telegram cheklovi doirasida bo'lib yuboradi.

    Bo'linish faqat bo'sh qator bo'yicha amalga oshadi, shuning uchun HTML
    teg hech qachon ikkiga bo'linib qolmaydi.
    """
    if len(text) <= TELEGRAM_LIMIT:
        await message.answer(text, reply_markup=reply_markup)
        return

    chunks: list[str] = []
    current = ""
    for block in text.split("\n\n"):
        candidate = f"{current}\n\n{block}" if current else block
        if len(candidate) > TELEGRAM_LIMIT and current:
            chunks.append(current)
            current = block
        else:
            current = candidate
    if current:
        chunks.append(current)

    for i, chunk in enumerate(chunks):
        await message.answer(
            chunk, reply_markup=reply_markup if i == len(chunks) - 1 else None
        )


def question_text(test_key: str, index: int, lang: str) -> str:
    test = REGISTRY[test_key]
    return t(
        "question",
        lang,
        index=index + 1,
        total=test.size,
        bar=report.bar(index / test.size * 100),
        text=tr(test.items[index].text, lang),
    )


def card_text(test_key: str, lang: str) -> str:
    test = REGISTRY[test_key]
    badge = t("badge_validated" if test.validated else "badge_composite", lang)
    return t(
        "card",
        lang,
        emoji=test.emoji,
        title=tr(test.title, lang),
        intro=tr(test.intro, lang),
        badge=badge,
        count=test.size,
        minutes=tr(test.minutes, lang),
    )


async def show_menu(message: Message, lang: str, edit: bool = True) -> None:
    text, markup = t("menu", lang), kb.main_menu(lang)
    if edit:
        await safe_edit(message, text, reply_markup=markup)
    else:
        await message.answer(text, reply_markup=markup)


async def start_quiz(
    message: Message, state: FSMContext, test_key: str, lang: str,
    age_group: str | None,
) -> None:
    await state.update_data(test_key=test_key, age_group=age_group, answers=[])
    await state.set_state(Quiz.answering)
    await safe_edit(message, card_text(test_key, lang))
    await message.answer(
        question_text(test_key, 0, lang),
        reply_markup=kb.answer_menu(test_key, 0, lang),
    )


# --- Buyruqlar --------------------------------------------------------------


@router.message(CommandStart())
async def cmd_start(
    message: Message, state: FSMContext, lang: str, lang_known: bool
) -> None:
    await state.clear()
    if not lang_known:
        await message.answer(t("choose_language", lang), reply_markup=kb.language_menu())
        return
    await show_menu(message, lang, edit=False)


@router.message(Command("til", "language", "lang"))
async def cmd_lang(message: Message, state: FSMContext, lang: str) -> None:
    await state.clear()
    await message.answer(t("choose_language", lang), reply_markup=kb.language_menu())


@router.message(Command("haqida", "about"))
async def cmd_about(message: Message, lang: str) -> None:
    await message.answer(t("about", lang), reply_markup=kb.back_to_menu(lang))


@router.message(Command("yordam", "help"))
async def cmd_help(message: Message, lang: str) -> None:
    await message.answer(t("help", lang), reply_markup=kb.back_to_menu(lang))


@router.message(Command("bekor", "cancel"))
async def cmd_cancel(message: Message, state: FSMContext, lang: str) -> None:
    await state.clear()
    await message.answer(t("cancelled", lang), reply_markup=kb.main_menu(lang))


@router.message(Command("natijalar", "results"))
async def cmd_history(message: Message, lang: str) -> None:
    rows = await db.user_history(message.from_user.id)
    await message.answer(
        report.render_history(rows, lang, REGISTRY),
        reply_markup=kb.back_to_menu(lang),
    )


# --- Til --------------------------------------------------------------------


@router.callback_query(F.data.startswith("lang:"))
async def pick_language(callback: CallbackQuery, state: FSMContext) -> None:
    code = callback.data.split(":", 1)[1]
    if code not in LANGS:
        await callback.answer()
        return
    await state.clear()
    await db.set_lang(callback.from_user.id, code)
    await callback.answer(t("language_set", code))
    await show_menu(callback.message, code)


@router.callback_query(F.data == "nav:lang")
async def ask_language(callback: CallbackQuery, lang: str) -> None:
    await safe_edit(
        callback.message, t("choose_language", lang), reply_markup=kb.language_menu()
    )
    await callback.answer()


# --- Navigatsiya ------------------------------------------------------------


@router.callback_query(F.data == "nav:menu")
async def nav_menu(callback: CallbackQuery, state: FSMContext, lang: str) -> None:
    await state.clear()
    await show_menu(callback.message, lang)
    await callback.answer()


@router.callback_query(F.data == "nav:about")
async def nav_about(callback: CallbackQuery, lang: str) -> None:
    await safe_edit(callback.message, t("about", lang), reply_markup=kb.back_to_menu(lang))
    await callback.answer()


@router.callback_query(F.data == "nav:history")
async def nav_history(callback: CallbackQuery, lang: str) -> None:
    rows = await db.user_history(callback.from_user.id)
    await safe_edit(
        callback.message,
        report.render_history(rows, lang, REGISTRY),
        reply_markup=kb.back_to_menu(lang),
    )
    await callback.answer()


@router.callback_query(F.data == "nav:cancel")
async def nav_cancel(callback: CallbackQuery, state: FSMContext, lang: str) -> None:
    await state.clear()
    await safe_edit(callback.message, t("cancelled", lang), reply_markup=kb.main_menu(lang))
    await callback.answer()


# --- Test tanlash -----------------------------------------------------------


@router.callback_query(F.data.startswith("test:"))
async def show_card(callback: CallbackQuery, state: FSMContext, lang: str) -> None:
    test_key = callback.data.split(":", 1)[1]
    if test_key not in REGISTRY:
        await callback.answer()
        return
    await state.clear()
    await safe_edit(
        callback.message, card_text(test_key, lang),
        reply_markup=kb.test_card(test_key, lang),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("src:"))
async def show_source(callback: CallbackQuery, lang: str) -> None:
    test_key = callback.data.split(":", 1)[1]
    test = REGISTRY.get(test_key)
    if not test:
        await callback.answer()
        return
    badge = t("badge_validated" if test.validated else "badge_composite", lang)
    text = (
        f"{t('source_title', lang)}\n\n"
        f"{test.emoji} <b>{tr(test.title, lang)}</b>\n{badge}\n\n"
        f"{tr(test.source, lang)}"
    )
    await safe_edit(callback.message, text, reply_markup=kb.source_card(test_key, lang))
    await callback.answer()


@router.callback_query(F.data.startswith("go:"))
async def begin(callback: CallbackQuery, state: FSMContext, lang: str) -> None:
    test_key = callback.data.split(":", 1)[1]
    test = REGISTRY.get(test_key)
    if not test:
        await callback.answer()
        return

    await state.clear()
    if test.ask_age:
        await state.update_data(test_key=test_key)
        prompt = t(
            "choose_age_child" if test.subject == "child" else "choose_age_self", lang
        )
        await safe_edit(
            callback.message, prompt, reply_markup=kb.age_menu(test.subject, lang)
        )
        await callback.answer()
        return

    await start_quiz(callback.message, state, test_key, lang, None)
    await callback.answer()


@router.callback_query(F.data.startswith("age:"))
async def picked_age(callback: CallbackQuery, state: FSMContext, lang: str) -> None:
    data = await state.get_data()
    test_key = data.get("test_key")
    if test_key not in REGISTRY:
        await show_menu(callback.message, lang)
        await callback.answer()
        return
    await start_quiz(
        callback.message, state, test_key, lang, callback.data.split(":", 1)[1]
    )
    await callback.answer()


# --- Savollar ---------------------------------------------------------------


@router.callback_query(Quiz.answering, F.data.startswith("ans:"))
async def answer(callback: CallbackQuery, state: FSMContext, lang: str) -> None:
    _, raw_index, raw_value = callback.data.split(":")
    index, value = int(raw_index), int(raw_value)

    data = await state.get_data()
    test_key = data.get("test_key")
    answers: list[int] = list(data.get("answers", []))

    if test_key not in REGISTRY:
        await state.clear()
        await show_menu(callback.message, lang)
        await callback.answer()
        return

    # Eski xabardagi tugma yoki ikki marta bosish — javoblar soni bilan
    # mos kelmaydi, e'tiborsiz qoldiramiz.
    if index != len(answers):
        await callback.answer(t("already_answered", lang))
        return

    answers.append(value)
    await state.update_data(answers=answers)

    test = REGISTRY[test_key]
    if len(answers) < test.size:
        await safe_edit(
            callback.message,
            question_text(test_key, len(answers), lang),
            reply_markup=kb.answer_menu(test_key, len(answers), lang),
        )
        await callback.answer()
        return

    await finish(callback, state, test_key, lang, data.get("age_group"), answers)


@router.callback_query(Quiz.answering, F.data == "back")
async def go_back(callback: CallbackQuery, state: FSMContext, lang: str) -> None:
    data = await state.get_data()
    test_key = data.get("test_key")
    answers: list[int] = list(data.get("answers", []))

    if not answers or test_key not in REGISTRY:
        await callback.answer()
        return

    answers.pop()
    await state.update_data(answers=answers)
    await safe_edit(
        callback.message,
        question_text(test_key, len(answers), lang),
        reply_markup=kb.answer_menu(test_key, len(answers), lang),
    )
    await callback.answer()


async def finish(
    callback: CallbackQuery,
    state: FSMContext,
    test_key: str,
    lang: str,
    age_group: str | None,
    answers: list[int],
) -> None:
    await state.clear()
    await callback.answer(t("analyzing", lang))

    test = REGISTRY[test_key]
    result = score(test, answers)
    await db.save_result(
        callback.from_user.id, test_key, lang, age_group,
        result.get("total"), result["scales"],
    )

    await safe_edit(callback.message, t("finished", lang))
    await send_chunked(
        callback.message,
        report.render(test, result, lang, age_group),
        reply_markup=kb.result_menu(test_key, lang),
    )


# --- Oxirgi tayanch ---------------------------------------------------------


@router.callback_query(F.data.startswith("ans:") | (F.data == "back"))
async def stale_callback(callback: CallbackQuery, lang: str) -> None:
    await callback.answer(t("stale_test", lang), show_alert=True)
    await show_menu(callback.message, lang, edit=False)


@router.message()
async def fallback(
    message: Message, state: FSMContext, lang: str, lang_known: bool
) -> None:
    if await state.get_state() == Quiz.answering.state:
        await message.answer(t("press_buttons", lang))
        return
    if not lang_known:
        await message.answer(t("choose_language", lang), reply_markup=kb.language_menu())
        return
    await show_menu(message, lang, edit=False)
