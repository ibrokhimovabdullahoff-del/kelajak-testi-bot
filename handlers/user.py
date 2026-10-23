"""Foydalanuvchi oqimi: menyu, test oldidan ekran, savollar, natija.

Yangi model (1-bosqich): hamma test BEPUL topshiriladi. Natijadan keyin
qisqa natija va sertifikat bepul; to'liq tahlil — pullik (`handlers/reports.py`).
Nima bepul, nima pullik — test BOSHLANISHIDAN OLDIN aytiladi.

Javoblar har bir bosishdan keyin bazaga yoziladi (`progress.py`): test
tashlab ketilsa yoki bot qayta ishga tushsa, /start menyusida "▶️ Testni
davom ettirish (23/50)" chiqadi va eski savol tugmasi ham ishlayveradi.
"""
from __future__ import annotations

import asyncio
import logging

from aiogram import F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command, CommandObject, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder

import access
import content
import credits
import database as db
import events
import keyboards as kb
import progress
import report
import wallet
from config import IQ_KEY, MENU_ORDER
from locales import LANGS, money, t, tr
from psytests import REGISTRY, score

from . import growth
from . import payment as pay
from . import reports

log = logging.getLogger(__name__)
router = Router()

TELEGRAM_LIMIT = 3800


class Quiz(StatesGroup):
    answering = State()


# --- Yordamchilar -----------------------------------------------------------


async def _awaited(awaitable):
    """asyncio.gather uchun o'ram (aiogram metodlari korutina emas)."""
    return await awaitable


async def parallel(*awaitables):
    """Bir nechta Telegram so'rovini bir vaqtda yuboradi."""
    return await asyncio.gather(*(_awaited(a) for a in awaitables))


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
    """Uzun matnni Telegram cheklovi doirasida bo'lib yuboradi."""
    parts = reports._chunks(text)
    for i, chunk in enumerate(parts):
        await message.answer(chunk, reply_markup=reply_markup if i == len(parts) - 1 else None)


def milestone_line(index: int, total: int, lang: str) -> str:
    """Progress chizig'i ostidagi qisqa ruhlantiruvchi qator (25/50/75 %)."""
    done = index / total * 100 if total else 0
    for pct in (75, 50, 25):
        if done >= pct:
            return "\n" + t(f"ms_{pct}", lang)
    return ""


def question_text(test_key: str, index: int, lang: str) -> str:
    test = REGISTRY[test_key]
    text = t(
        "question",
        lang,
        index=index + 1,
        total=test.size,
        bar=report.bar(index / test.size * 100),
        text=tr(test.items[index].text, lang),
    )
    if test.kind == "interests":
        # Har ekranda faqat mashg'ulot nomi turadi — savolning o'zi ham ko'rinsin.
        text += f"\n<i>{t('interest_prompt', lang)}</i>"
    line = milestone_line(index, test.size, lang)
    if line:
        head, _, rest = text.partition("</code>")
        text = f"{head}</code>{line}{rest}"
    return text


async def min_price() -> int:
    prices = [await pay.price_for(key) for key in MENU_ORDER]
    paid = [p for p in prices if p > 0]
    return min(paid) if paid else 0


async def card_text(test_key: str, lang: str, user_id: int, saved: dict | None) -> str:
    """Test oldidan ekran: nima bepul, to'liq tahlilda nima bor va narxi."""
    test = REGISTRY[test_key]
    paid = tr(content.text("tests", test_key, "paid"), lang)
    if await access.has(user_id, test_key):
        owned = test_key in await access.owned(user_id)
        paid_line = t("card_owned" if owned else "card_report_free", lang, paid=paid)
    else:
        paid_line = t("card_paid", lang, price=money(await pay.price_for(test_key)), paid=paid)
    instruction = {"career": "instr_career", "child": "instr_child"}.get(test_key, "instr_self")
    text = t(
        "card", lang,
        emoji=test.emoji, title=tr(test.title, lang), count=test.size,
        minutes=tr(test.minutes, lang),
        badge=t("badge_validated" if test.validated else "badge_composite", lang),
        instruction=t(instruction, lang),
        free=tr(content.text("tests", test_key, "free"), lang),
        paid_line=paid_line,
    )
    if saved and saved.get("answers"):
        text += t("card_progress", lang, done=len(saved["answers"]))
    return text


async def show_menu(message: Message, lang: str, user_id: int, edit: bool = True) -> None:
    """Bosh menyu. `user_id` alohida: callback ichida `message.from_user` — bot."""
    markup = kb.main_menu(lang, await db.disabled_tests(), await progress.latest(user_id))
    text = t("menu", lang, price=money(await min_price()))
    if edit:
        await safe_edit(message, text, reply_markup=markup)
    else:
        await message.answer(text, reply_markup=markup)


async def _show_question(message: Message, test_key: str, index: int, lang: str, edit: bool) -> None:
    text = question_text(test_key, index, lang)
    markup = kb.answer_menu(test_key, index, lang)
    if edit:
        await safe_edit(message, text, reply_markup=markup)
    else:
        await message.answer(text, reply_markup=markup)


async def start_quiz(message: Message, state: FSMContext, test_key: str, lang: str,
                     age_group: str | None, user_id: int | None = None) -> None:
    user_id = user_id or message.chat.id
    await state.set_state(Quiz.answering)
    await state.update_data(test_key=test_key, age_group=age_group, answers=[], ms=[])
    await progress.save(user_id, test_key, [], age_group, {"ms": []})
    await db.log_start(user_id, test_key)
    events.track(user_id, "test_started", test_key)
    await _show_question(message, test_key, 0, lang, edit=True)


async def _restore(state: FSMContext, user_id: int, test_key: str) -> dict | None:
    """FSM bo'sh bo'lsa (bot qayta ishga tushgan) — javoblarni bazadan tiklaydi."""
    saved = await progress.load(user_id, test_key)
    if saved is None:
        return None
    data = {"test_key": test_key, "age_group": saved["age_group"], "answers": saved["answers"],
            "ms": saved["extra"].get("ms", [])}
    await state.set_state(Quiz.answering)
    await state.update_data(**data)
    return data


# --- Buyruqlar --------------------------------------------------------------


@router.message(CommandStart())
async def cmd_start(
    message: Message, state: FSMContext, lang: str, command: CommandObject,
    is_new_user: bool = False,
) -> None:
    await state.clear()
    # Qayerdan keldi: /start src_instagram, ref_<id>, promo_<kod>. Faqat
    # birinchi manba saqlanadi; eski foydalanuvchining manbasi o'zgarmaydi.
    source, _ = events.parse_source(command.args)
    if is_new_user:
        await db.set_first_source(message.from_user.id, source or "direct")
    events.track(message.from_user.id, "start", new=is_new_user, **({"src": source} if source else {}))
    await growth.handle_start(message, command.args, is_new_user)
    from . import loops
    if source and source.startswith("promo_"):
        await loops.redeem_and_reply(message, message.from_user.id, command.args[6:], lang)
    elif source == "cmp" and await loops.compare_start(message, command.args, lang):
        return
    await show_menu(message, lang, message.from_user.id, edit=False)


@router.message(Command("til", "language", "lang"))
async def cmd_lang(message: Message, state: FSMContext, lang: str) -> None:
    await message.answer(t("choose_language", lang), reply_markup=kb.language_menu())


@router.message(Command("haqida", "about"))
async def cmd_about(message: Message, lang: str) -> None:
    await message.answer(t("about", lang), reply_markup=kb.back_to_menu(lang))


@router.message(Command("yordam", "help"))
async def cmd_help(message: Message, lang: str) -> None:
    await message.answer(t("help", lang), reply_markup=kb.back_to_menu(lang))


@router.message(Command("bekor", "cancel"))
async def cmd_cancel(message: Message, state: FSMContext, lang: str) -> None:
    paused = await state.get_state() == Quiz.answering.state
    await state.clear()
    if paused:
        await message.answer(t("test_paused", lang))
    await show_menu(message, lang, message.from_user.id, edit=False)


async def _recent_results(user_id: int) -> list[dict]:
    conn = await db.connect()
    cursor = await conn.execute(
        "SELECT id, test_key, created_at FROM results WHERE user_id = ? ORDER BY id DESC LIMIT 5", (user_id,))
    return [{"id": r[0], "test_key": r[1], "created_at": r[2]} for r in await cursor.fetchall()]


async def history_screen(user_id: int, lang: str) -> tuple[str, object]:
    rows = await db.user_history(user_id)
    opened = {key for key in access.TESTS if await access.has(user_id, key)}
    text = report.render_history(rows, lang, REGISTRY, opened)
    b = InlineKeyboardBuilder()
    if rows:
        text += "\n\n" + t("history_hint", lang)
        for row in await _recent_results(user_id):
            title = reports.test_title(row["test_key"], lang)
            b.button(text=f"{title} · {(row['created_at'] or '')[:10]}", callback_data=f"rep:open:{row['id']}")
    have = await credits.available(user_id)
    if have:
        text += "\n\n" + t("history_credits", lang, n=have)
        b.button(text=t("btn_credit_use", lang, n=have), callback_data="cred:menu")
    balance = await wallet.balance(user_id)
    if balance > 0:
        text += "\n\n" + t("history_balance", lang, balance=money(balance))
        b.button(text=t("btn_wallet", lang), callback_data="wallet:open")
    b.button(text=t("btn_promo", lang), callback_data="promo:ask")
    b.button(text=t("btn_menu", lang), callback_data="nav:menu")
    b.adjust(1)
    return text, b.as_markup()


@router.message(Command("natijalar", "results"))
async def cmd_history(message: Message, lang: str) -> None:
    text, markup = await history_screen(message.from_user.id, lang)
    await message.answer(text, reply_markup=markup)


# --- Til --------------------------------------------------------------------


@router.callback_query(F.data.startswith("lang:"))
async def pick_language(callback: CallbackQuery, state: FSMContext) -> None:
    code = callback.data.split(":", 1)[1]
    if code not in LANGS:
        return
    await db.set_lang(callback.from_user.id, code)
    events.track(callback.from_user.id, "lang_set", lang=code)
    await callback.answer(t("language_set", code))
    await show_menu(callback.message, code, callback.from_user.id)


@router.callback_query(F.data == "nav:lang")
async def ask_language(callback: CallbackQuery, lang: str) -> None:
    await safe_edit(callback.message, t("choose_language", lang), reply_markup=kb.language_menu())


# --- Navigatsiya ------------------------------------------------------------


@router.callback_query(F.data == "nav:menu")
async def nav_menu(callback: CallbackQuery, state: FSMContext, lang: str) -> None:
    if await state.get_state() == Quiz.answering.state:
        await state.clear()  # javoblar bazada qoladi — menyuda "davom ettirish" chiqadi
    await show_menu(callback.message, lang, callback.from_user.id, edit=not callback.message.photo)


@router.callback_query(F.data == "nav:about")
async def nav_about(callback: CallbackQuery, lang: str) -> None:
    await safe_edit(callback.message, t("about", lang), reply_markup=kb.back_to_menu(lang))


@router.callback_query(F.data == "nav:history")
async def nav_history(callback: CallbackQuery, lang: str) -> None:
    text, markup = await history_screen(callback.from_user.id, lang)
    await safe_edit(callback.message, text, reply_markup=markup)


@router.callback_query(F.data.startswith("nav:cancel"))
async def nav_cancel(callback: CallbackQuery, state: FSMContext, lang: str) -> None:
    """❌ Bekor qilish — avval so'raymiz va javoblar saqlanishini aytamiz."""
    parts = callback.data.split(":")
    test_key = parts[2] if len(parts) == 3 else (await state.get_data()).get("test_key")
    if test_key not in REGISTRY:
        await show_menu(callback.message, lang, callback.from_user.id)
        return
    await safe_edit(callback.message, t("cancel_confirm", lang), reply_markup=kb.quit_menu(test_key, lang))


@router.callback_query(F.data.startswith("quit:"))
async def quit_choice(callback: CallbackQuery, state: FSMContext, lang: str) -> None:
    _, choice, test_key = callback.data.split(":")
    if test_key not in REGISTRY:
        return
    user_id = callback.from_user.id
    if choice == "yes":
        await state.clear()
        await safe_edit(callback.message, t("test_paused", lang))
        await show_menu(callback.message, lang, user_id, edit=False)
        return
    data = await state.get_data()
    if data.get("test_key") != test_key:
        data = await _restore(state, user_id, test_key)
    if not data:
        await show_menu(callback.message, lang, user_id)
        return
    await _show_question(callback.message, test_key, len(data["answers"]), lang, edit=True)


# --- Test oldidan ekran -----------------------------------------------------


@router.callback_query(F.data.startswith("test:"))
async def show_card(callback: CallbackQuery, state: FSMContext, lang: str) -> None:
    test_key = callback.data.split(":", 1)[1]
    if test_key not in REGISTRY or test_key in await db.disabled_tests():
        await show_menu(callback.message, lang, callback.from_user.id)
        return
    if await state.get_state() == Quiz.answering.state:
        await state.clear()
    saved = await progress.load(callback.from_user.id, test_key)
    events.track(callback.from_user.id, "test_opened", test_key)
    await safe_edit(callback.message, await card_text(test_key, lang, callback.from_user.id, saved),
                    reply_markup=kb.test_card(test_key, lang, saved))


@router.callback_query(F.data.startswith("src:"))
async def show_source(callback: CallbackQuery, lang: str) -> None:
    test_key = callback.data.split(":", 1)[1]
    test = REGISTRY.get(test_key)
    if not test:
        return
    badge = t("badge_validated" if test.validated else "badge_composite", lang)
    text = (
        f"{t('source_title', lang)}\n\n"
        f"{test.emoji} <b>{tr(test.title, lang)}</b>\n{badge}\n\n"
        f"{tr(test.source, lang)}"
    )
    await safe_edit(callback.message, text, reply_markup=kb.source_card(test_key, lang))


@router.callback_query(F.data.startswith("go:"))
async def begin(callback: CallbackQuery, state: FSMContext, lang: str) -> None:
    """▶️ Boshlash — yangidan. Test bepul: hech qanday to'lov tekshiruvi yo'q."""
    test_key = callback.data.split(":", 1)[1]
    test = REGISTRY.get(test_key)
    if not test or test_key in await db.disabled_tests():
        await show_menu(callback.message, lang, callback.from_user.id)
        return
    await state.clear()
    await progress.clear(callback.from_user.id, test_key)
    if test.ask_age:
        await state.update_data(test_key=test_key)
        prompt = t("choose_age_child" if test.subject == "child" else "choose_age_self", lang)
        await safe_edit(callback.message, prompt, reply_markup=kb.age_menu(test.subject, lang))
        return
    await start_quiz(callback.message, state, test_key, lang, None, callback.from_user.id)


@router.callback_query(F.data.startswith("age:"))
async def picked_age(callback: CallbackQuery, state: FSMContext, lang: str) -> None:
    data = await state.get_data()
    test_key = data.get("test_key")
    if test_key not in REGISTRY:
        await show_menu(callback.message, lang, callback.from_user.id)
        return
    await start_quiz(callback.message, state, test_key, lang, callback.data.split(":", 1)[1],
                     callback.from_user.id)


@router.callback_query(F.data.startswith("resume:"))
async def resume(callback: CallbackQuery, state: FSMContext, lang: str) -> None:
    test_key = callback.data.split(":", 1)[1]
    if test_key == IQ_KEY:
        from . import iq
        await iq.resume(callback, state, lang)
        return
    data = await _restore(state, callback.from_user.id, test_key) if test_key in REGISTRY else None
    if not data:
        await show_menu(callback.message, lang, callback.from_user.id)
        return
    index = len(data["answers"])
    if index >= REGISTRY[test_key].size:  # oxirgi javob yozilgan, natija chiqmay qolgan
        await finish(callback, state, test_key, lang, data["age_group"], data["answers"])
        return
    await _show_question(callback.message, test_key, index, lang, edit=not callback.message.photo)


# --- Savollar ---------------------------------------------------------------


def _parse_answer(data: str) -> tuple[str | None, int, int] | None:
    """"ans:<test>:<i>:<v>" (yangi) yoki "ans:<i>:<v>" (eski xabarlar)."""
    parts = data.split(":")
    try:
        if len(parts) == 4:
            return parts[1], int(parts[2]), int(parts[3])
        if len(parts) == 3:
            return None, int(parts[1]), int(parts[2])
    except ValueError:
        pass
    return None


@router.callback_query(F.data.startswith("ans:"))
async def answer(callback: CallbackQuery, state: FSMContext, lang: str) -> None:
    parsed = _parse_answer(callback.data)
    if parsed is None:
        return
    test_key, index, value = parsed
    user_id = callback.from_user.id

    data = await state.get_data() if await state.get_state() == Quiz.answering.state else {}
    if test_key and data.get("test_key") != test_key:
        data = await _restore(state, user_id, test_key) or {}
    elif not test_key:
        test_key = data.get("test_key")
    if test_key not in REGISTRY or not data:
        await callback.answer(t("stale_test", lang), show_alert=True)
        await show_menu(callback.message, lang, user_id, edit=False)
        return

    answers: list[int] = list(data.get("answers", []))
    # Eski xabardagi tugma yoki ikki marta bosish — e'tiborsiz qoldiramiz.
    if index != len(answers) or not 0 <= value <= 4:
        await callback.answer(t("already_answered", lang))
        return

    answers.append(value)
    test = REGISTRY[test_key]
    reached = list(data.get("ms") or [])
    for pct in events.crossed_milestones(len(answers), test.size, reached):
        reached.append(pct)
        events.track(user_id, "q_answered", test_key, pct=pct)
    await state.update_data(answers=answers, ms=reached)
    await progress.save(user_id, test_key, answers, data.get("age_group"), {"ms": reached})

    if len(answers) < test.size:
        await _show_question(callback.message, test_key, len(answers), lang, edit=True)
        return
    await finish(callback, state, test_key, lang, data.get("age_group"), answers)


@router.callback_query(F.data.startswith("back"))
async def go_back(callback: CallbackQuery, state: FSMContext, lang: str) -> None:
    parts = callback.data.split(":")
    user_id = callback.from_user.id
    data = await state.get_data() if await state.get_state() == Quiz.answering.state else {}
    test_key = parts[1] if len(parts) == 2 else data.get("test_key")
    if test_key in REGISTRY and data.get("test_key") != test_key:
        data = await _restore(state, user_id, test_key) or {}
    answers: list[int] = list(data.get("answers", []))
    if not answers or test_key not in REGISTRY:
        return
    answers.pop()
    await state.update_data(answers=answers)
    await progress.save(user_id, test_key, answers, data.get("age_group"), {"ms": data.get("ms") or []})
    await _show_question(callback.message, test_key, len(answers), lang, edit=True)


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
    user_id = callback.from_user.id
    await db.save_result(user_id, test_key, lang, age_group, result.get("total"), result["scales"])
    await progress.clear(user_id, test_key)
    events.track(user_id, "test_completed", test_key)
    saved = await db.latest_result(user_id, test_key)

    await safe_edit(callback.message, t("finished", lang))
    full = await access.has(user_id, test_key)
    # Avval sertifikat (bepul, ulashish uchun), keyin natija: to'liq yoki bepul + to'lov.
    await growth.send_certificate(callback.message, callback.from_user, saved, full=full)
    if saved:
        await reports.deliver(callback.bot, user_id, saved, lang)
    await growth.after_test(callback.bot, user_id, test_key, lang)


# --- Oxirgi tayanch ---------------------------------------------------------


@router.message()
async def fallback(message: Message, state: FSMContext, lang: str) -> None:
    if await state.get_state() == Quiz.answering.state:
        await message.answer(t("press_buttons", lang))
        return
    await show_menu(message, lang, message.from_user.id, edit=False)
