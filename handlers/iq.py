"""Premium IQ testi: savol — rasm, javob — rasm ostidagi A–D tugmalari.

Oqim: test oldidan ekran (/iq yoki menyu; nima bepul, nima pullik) → yosh
(IQ tengdoshlarga nisbatan hisoblanadi) → 20 ta rasm bitta xabarning o'zida
almashib turadi (chat to'lib ketmaydi) → sertifikat → bepul natija (to'g'ri
javoblar soni va eng kuchli fikrlash turi) yoki to'liq tahlil (taxminiy IQ,
4 ta tur bo'yicha natija va mashqlar). Test o'zi bepul.

Javoblar har bosishda bazaga yoziladi (`progress.py`) — bot qayta ishga
tushsa ham test shu joydan davom etadi.

To'g'ri javoblar va qaysi savolda xato qilingani hech qachon ko'rsatilmaydi —
kalit faqat serverdagi IQ_ANSWERS o'zgaruvchisida turadi.

Rasmlar Telegram'ga bir marta yuklanadi: qaytgan file_id bazada saqlanadi va
keyingi hamma foydalanuvchiga shu id yuboriladi — server rasmni qayta-qayta
yubormaydi, rasm esa darhol ochiladi.
"""
from __future__ import annotations

import asyncio
import logging
import time
from urllib.parse import quote

from aiogram import F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, FSInputFile, InputMediaPhoto, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder

import access
import compare
import content
import database as db
import events
import keyboards as kb
import progress
import referrals
from config import IQ_EMOJI, IQ_KEY, is_admin
from handlers import growth
from handlers import payment as pay
from handlers import reports
from locales import money, t
from psytests.iq import (
    AGE_CODES, AGE_GROUPS, DEFAULT_AGE, LETTERS, PUZZLES, TOTAL, Puzzle, answer_key,
    estimate_iq, grade,
)
from result_image import IQ_NUMBER_MIN

log = logging.getLogger(__name__)
router = Router()

#: Natija yozuvidagi format. Eski matnli IQ natijalari versiyasiz saqlangan.
RESULT_VERSION = 2


class IQState(StatesGroup):
    age = State()
    answering = State()


def bi(lang: str, uz: str, ru: str) -> str:
    return uz if lang == "uz" else ru


def tr(value: dict[str, str], lang: str) -> str:
    return value.get(lang) or value["uz"]


# --- Rasm yuborish ----------------------------------------------------------

_file_ids: dict[str, str] = {}
_digests: dict[str, str] = {}


def _cache_key(puzzle: Puzzle) -> str:
    if puzzle.file not in _digests:
        _digests[puzzle.file] = puzzle.digest
    return f"iq_photo:{puzzle.file}:{_digests[puzzle.file]}"


async def _photo(puzzle: Puzzle) -> str | FSInputFile:
    key = _cache_key(puzzle)
    file_id = _file_ids.get(key) or await db.get_setting(key)
    if file_id:
        _file_ids[key] = file_id
        return file_id
    return FSInputFile(puzzle.path)


async def _remember(puzzle: Puzzle, sent) -> None:
    if not isinstance(sent, Message) or not sent.photo:
        return
    key, file_id = _cache_key(puzzle), sent.photo[-1].file_id
    if _file_ids.get(key) != file_id:
        _file_ids[key] = file_id
        await db.set_setting(key, file_id)


async def _forget(puzzle: Puzzle) -> None:
    key = _cache_key(puzzle)
    _file_ids.pop(key, None)
    await db.set_setting(key, "")


def _bad_file(exc: Exception) -> bool:
    text = str(exc).lower()
    return "file identifier" in text or "file_id" in text or "wrong type of the web page" in text


async def _send_puzzle(message: Message, puzzle: Puzzle, caption: str, markup, edit: bool) -> None:
    """Rasmni shu xabarning o'zida almashtiradi; bo'lmasa yangi xabar yuboradi."""
    if edit and message.photo:
        for _ in range(2):
            try:
                sent = await message.edit_media(
                    media=InputMediaPhoto(media=await _photo(puzzle), caption=caption),
                    reply_markup=markup,
                )
                await _remember(puzzle, sent)
                return
            except TelegramBadRequest as exc:
                if "not modified" in str(exc).lower():
                    return
                if _bad_file(exc):
                    await _forget(puzzle)
                    continue
                log.debug("IQ rasmini tahrirlab bo'lmadi, yangisi yuboriladi: %s", exc)
                break
    try:
        sent = await message.answer_photo(await _photo(puzzle), caption=caption, reply_markup=markup)
    except TelegramBadRequest as exc:
        if not _bad_file(exc):
            raise
        await _forget(puzzle)
        sent = await message.answer_photo(FSInputFile(puzzle.path), caption=caption, reply_markup=markup)
    await _remember(puzzle, sent)


async def _retire(message: Message, text: str | None = None) -> None:
    """Eski xabardagi tugmalarni olib tashlaydi — ular qayta bosilmasin."""
    try:
        if text and not message.photo:
            await message.edit_text(text, reply_markup=None)
        else:
            await message.edit_reply_markup(reply_markup=None)
    except TelegramBadRequest:
        pass


# --- Kartochka ----------------------------------------------------------------


def _unavailable_text(lang: str) -> str:
    return bi(lang, "⏳ IQ testi vaqtincha yopiq. Birozdan keyin qayta urinib ko‘ring.",
              "⏳ IQ-тест временно недоступен. Попробуйте чуть позже.")


async def card_text(user_id: int, lang: str, saved: dict | None) -> str:
    """Test oldidan ekran: nima bepul, to'liq tahlilda nima bor va narxi."""
    paid = tr(content.text("tests", IQ_KEY, "paid"), lang)
    if await access.has(user_id, IQ_KEY):
        owned = IQ_KEY in await access.owned(user_id)
        paid_line = t("card_owned" if owned else "card_report_free", lang, paid=paid)
    else:
        paid_line = t("card_paid", lang, price=money(await pay.price_for(IQ_KEY)), paid=paid)
    text = t("card_iq", lang, emoji=IQ_EMOJI, title=t("iq_title", lang), count=TOTAL,
             minutes=t("iq_minutes", lang), instruction=t("instr_iq", lang),
             free=tr(content.text("tests", IQ_KEY, "free"), lang), paid_line=paid_line)
    if saved and saved.get("answers"):
        text += t("card_progress", lang, done=len(saved["answers"]))
    return text


async def card(message: Message, user_id: int, lang: str, edit: bool) -> None:
    events.track(user_id, "test_opened", IQ_KEY)
    if answer_key() is None:
        # Kalitsiz natijani hisoblab bo'lmaydi — noto'g'ri baho berishdan ko'ra yopamiz.
        log.error("IQ_ANSWERS o'rnatilmagan yoki noto'g'ri — IQ testi yopiq")
        text = f"{IQ_EMOJI} <b>{t('iq_title', lang)}</b>\n\n" + _unavailable_text(lang)
        markup = kb.back_to_menu(lang)
    else:
        saved = await progress.load(user_id, IQ_KEY)
        text = await card_text(user_id, lang, saved)
        markup = kb.test_card(IQ_KEY, lang, saved)
    if edit and not message.photo:
        try:
            await message.edit_text(text, reply_markup=markup)
            return
        except TelegramBadRequest as exc:
            if "not modified" in str(exc).lower():
                return
    await message.answer(text, reply_markup=markup)


@router.message(Command("iq"))
async def iq_command(message: Message, state: FSMContext, lang: str) -> None:
    await state.clear()
    await card(message, message.from_user.id, lang, edit=False)


@router.callback_query(F.data == "iq:card")
async def iq_card(callback: CallbackQuery, state: FSMContext, lang: str) -> None:
    await callback.answer()
    await state.clear()
    await card(callback.message, callback.from_user.id, lang, edit=True)


# --- Savollar -----------------------------------------------------------------


def caption(index: int, lang: str) -> str:
    filled = round(index / TOTAL * 10)
    bar = "🟩" * filled + "⬜" * (10 - filled)
    return (
        f"{IQ_EMOJI} <b>{bi(lang, 'IQ testi', 'IQ-тест')}</b> · <b>{index + 1} / {TOTAL}</b>\n"
        f"{bar}\n\n"
        + bi(lang, "Qonuniyatni toping va «?» o‘rniga mos variantni tanlang.",
             "Найдите закономерность и выберите вариант вместо «?».")
    )


def question_markup(index: int, lang: str):
    b = InlineKeyboardBuilder()
    for letter in LETTERS:
        b.button(text=letter, callback_data=f"iq:a:{index}:{letter}")
    if index > 0:
        b.button(text=bi(lang, "⬅️ Oldingi", "⬅️ Назад"), callback_data="iq:back")
    b.button(text=bi(lang, "⛔ To‘xtatish", "⛔ Остановить"), callback_data="iq:stop")
    b.adjust(len(LETTERS), 2 if index > 0 else 1)
    return b.as_markup()


async def _show(message: Message, index: int, lang: str, edit: bool) -> None:
    await _send_puzzle(message, PUZZLES[index], caption(index, lang), question_markup(index, lang), edit)


async def _start_test(target, state: FSMContext, lang: str, user_id: int) -> None:
    """Testni boshlaydi. Kartochka, to'lovdan keyingi avtostart va eski tugmalar shu yerga keladi."""
    message = target.message if isinstance(target, CallbackQuery) else target
    if isinstance(target, CallbackQuery):
        await target.answer()
    if answer_key() is None:
        log.error("IQ_ANSWERS o'rnatilmagan yoki noto'g'ri — IQ testi boshlanmadi")
        await message.answer(_unavailable_text(lang))
        return
    # Test bepul: to'lov tekshiruvi yo'q. "Boshlash" — yangidan (eski javoblar o'chadi).
    await state.clear()
    await progress.clear(user_id, IQ_KEY)
    await state.set_state(IQState.age)
    b = InlineKeyboardBuilder()
    for code, label in AGE_GROUPS:
        b.button(text=tr(label, lang), callback_data=f"iqage:{code}")
    b.button(text=bi(lang, "⬅️ Orqaga", "⬅️ Назад"), callback_data="nav:menu")
    b.adjust(2, 2, 1)
    prompt = bi(
        lang,
        "🎂 <b>Yoshingizni tanlang</b>\n\nIQ tengdoshlaringizga nisbatan hisoblanadi: "
        "bir xil natija 12 yoshli bola va katta odam uchun turlicha baholanadi.",
        "🎂 <b>Выберите свой возраст</b>\n\nIQ считается относительно сверстников: "
        "одинаковый результат по-разному оценивается у ребёнка 12 лет и у взрослого.",
    )
    if not message.photo:  # rasmli xabarni matnga aylantirib bo'lmaydi
        try:
            await message.edit_text(prompt, reply_markup=b.as_markup())
            return
        except TelegramBadRequest:
            pass
    await message.answer(prompt, reply_markup=b.as_markup())


@router.callback_query(F.data.startswith("iqage:"))
async def picked_age(callback: CallbackQuery, state: FSMContext, lang: str) -> None:
    age = callback.data.split(":", 1)[1]
    if age not in AGE_CODES:
        await callback.answer()
        return
    await callback.answer()
    user_id = callback.from_user.id
    if answer_key() is None:
        log.error("IQ_ANSWERS o'rnatilmagan yoki noto'g'ri — IQ testi boshlanmadi")
        await callback.message.answer(_unavailable_text(lang))
        return
    await state.clear()
    await state.set_state(IQState.answering)
    started = time.time()
    await state.update_data(iq_answers=[], iq_started=started, iq_age=age, iq_ms=[])
    await progress.save(user_id, IQ_KEY, [], age, {"started": started, "ms": []})
    await db.log_start(user_id, IQ_KEY)
    events.track(user_id, "test_started", IQ_KEY)
    await _retire(callback.message, bi(lang, f"{IQ_EMOJI} IQ testi boshlandi. Omad!", f"{IQ_EMOJI} IQ-тест начался. Удачи!"))
    await _show(callback.message, 0, lang, edit=False)


@router.callback_query(F.data == "iq:start")
async def iq_start(callback: CallbackQuery, state: FSMContext, lang: str) -> None:
    await _start_test(callback, state, lang, callback.from_user.id)


#: Bitta foydalanuvchining tez-tez bosishlari ketma-ket ishlansin: aks holda
#: oxirgi savolda ikki marta bosilsa, natija ikki marta saqlanardi.
_locks: dict[int, asyncio.Lock] = {}


def _lock(user_id: int) -> asyncio.Lock:
    return _locks.setdefault(user_id, asyncio.Lock())


@router.callback_query(IQState.answering, F.data.startswith("iq:a:"))
async def answer(callback: CallbackQuery, state: FSMContext, lang: str) -> None:
    parts = callback.data.split(":")
    if len(parts) != 4 or not parts[2].isdigit() or parts[3] not in LETTERS:
        await callback.answer()
        return
    index, letter = int(parts[2]), parts[3]
    async with _lock(callback.from_user.id):
        if await state.get_state() != IQState.answering.state:
            # Bot qayta ishga tushgan bo'lishi mumkin — javoblarni bazadan tiklaymiz.
            if not await _restore(state, callback.from_user.id):
                await callback.answer(bi(lang, "Bu test tugagan yoki to‘xtatilgan. Qayta boshlash: /iq",
                                         "Этот тест завершён или остановлен. Начать заново: /iq"), show_alert=True)
                return
        data = await state.get_data()
        answers = list(data.get("iq_answers", []))
        if index != len(answers):
            await callback.answer(bi(lang, "Javob qabul qilingan ✅", "Ответ уже принят ✅"))
            return
        answers.append(letter)
        reached = list(data.get("iq_ms") or [])
        for pct in events.crossed_milestones(len(answers), TOTAL, reached):
            reached.append(pct)
            events.track(callback.from_user.id, "q_answered", IQ_KEY, pct=pct)
        await state.update_data(iq_answers=answers, iq_ms=reached)
        await progress.save(callback.from_user.id, IQ_KEY, answers, data.get("iq_age"),
                            {"started": data.get("iq_started"), "ms": reached})
        await callback.answer()
        if len(answers) < TOTAL:
            await _show(callback.message, len(answers), lang, edit=True)
            return
        await _finish(callback, state, lang, answers, data.get("iq_started"), data.get("iq_age"))


@router.callback_query(F.data == "iq:back")
async def back(callback: CallbackQuery, state: FSMContext, lang: str) -> None:
    async with _lock(callback.from_user.id):
        if await state.get_state() != IQState.answering.state and not await _restore(state, callback.from_user.id):
            await callback.answer()
            return
        data = await state.get_data()
        answers = list(data.get("iq_answers", []))
        await callback.answer()
        if not answers:
            return
        answers.pop()
        await state.update_data(iq_answers=answers)
        await progress.save(callback.from_user.id, IQ_KEY, answers, data.get("iq_age"),
                            {"started": data.get("iq_started"), "ms": data.get("iq_ms") or []})
        await _show(callback.message, len(answers), lang, edit=True)


async def _restore(state: FSMContext, user_id: int) -> dict | None:
    """FSM bo'sh — bazadagi javoblardan IQ testini tiklaydi."""
    saved = await progress.load(user_id, IQ_KEY)
    if saved is None:
        return None
    data = {"iq_answers": saved["answers"], "iq_age": saved["age_group"] or DEFAULT_AGE,
            "iq_started": saved["extra"].get("started"), "iq_ms": saved["extra"].get("ms", [])}
    await state.set_state(IQState.answering)
    await state.update_data(**data)
    return data


async def resume(callback: CallbackQuery, state: FSMContext, lang: str) -> None:
    """Menyudagi "▶️ Testni davom ettirish": joriy rasm yangi xabarda chiqadi."""
    if answer_key() is None:
        await callback.message.answer(_unavailable_text(lang))
        return
    async with _lock(callback.from_user.id):
        data = await _restore(state, callback.from_user.id)
    if not data:
        await card(callback.message, callback.from_user.id, lang, edit=True)
        return
    answers = data["iq_answers"]
    if len(answers) >= TOTAL:
        await _finish(callback, state, lang, answers, data["iq_started"], data["iq_age"])
        return
    await _show(callback.message, len(answers), lang, edit=False)


@router.callback_query(F.data == "iq:stop")
async def stop(callback: CallbackQuery, state: FSMContext, lang: str) -> None:
    """⛔ To'xtatish — avval so'raymiz: javoblar saqlanadi."""
    b = InlineKeyboardBuilder()
    b.button(text=t("btn_quit_yes", lang), callback_data=f"iqquit:yes:{callback.message.message_id}")
    b.button(text=t("btn_quit_no", lang), callback_data="iqquit:no")
    b.adjust(1)
    await callback.message.answer(t("cancel_confirm", lang), reply_markup=b.as_markup())


@router.callback_query(F.data.startswith("iqquit:"))
async def stop_choice(callback: CallbackQuery, state: FSMContext, lang: str) -> None:
    parts = callback.data.split(":")
    if parts[1] == "yes":
        if await state.get_state() == IQState.answering.state:
            await state.clear()
        if len(parts) == 3 and parts[2].isdigit():
            try:
                await callback.bot.delete_message(callback.message.chat.id, int(parts[2]))
            except TelegramBadRequest:
                pass
        from handlers import user  # aylanma importdan qochish uchun shu yerda

        await user.safe_edit(callback.message, t("test_paused", lang))
        await user.show_menu(callback.message, lang, callback.from_user.id, edit=False)
        return
    try:
        await callback.message.delete()
    except TelegramBadRequest:
        await _retire(callback.message)


@router.callback_query(F.data.startswith("iq:a:") | F.data.startswith("iq:ans:"))
async def stale(callback: CallbackQuery, lang: str) -> None:
    await callback.answer(
        bi(lang, "Bu test tugagan yoki to‘xtatilgan. Qayta boshlash: /iq",
           "Этот тест завершён или остановлен. Начать заново: /iq"),
        show_alert=True,
    )


@router.message(IQState.answering, ~F.text.startswith("/"))
async def typed_during_test(message: Message, lang: str) -> None:
    await message.answer(bi(
        lang,
        "Javob berish uchun rasm ostidagi A, B, C yoki D tugmasini bosing. To‘xtatish — ⛔ tugmasi.",
        "Чтобы ответить, нажмите A, B, C или D под картинкой. Остановить — кнопка ⛔.",
    ))


# --- Natija -------------------------------------------------------------------


async def _peer_scores(user_id: int, age_group: str) -> list[float]:
    """Shu yoshdagi boshqa ishtirokchilarning BIRINCHI urinishdagi natijalari.

    Qayta topshirishda javoblar eslab qolinadi — ular solishtirishni buzmasin.
    Adminning sinov natijalari ham hisobga olinmaydi.
    """
    conn = await db.connect()
    cursor = await conn.execute(
        """
        SELECT r.user_id, r.total FROM results r
        JOIN (
            SELECT MIN(id) AS first_id FROM results
            WHERE test_key = ? AND json_extract(scales, '$.version') = ?
            GROUP BY user_id
        ) f ON f.first_id = r.id
        WHERE r.user_id != ? AND r.age_group = ?
        """,
        (IQ_KEY, RESULT_VERSION, user_id, age_group),
    )
    return [total for uid, total in await cursor.fetchall() if not is_admin(uid)]


def _share_url(url: str, text: str) -> str:
    return f"https://t.me/share/url?url={quote(url, safe='')}&text={quote(text)}"


def result_markup(result: dict, iq: int, user_id: int, lang: str):
    b = InlineKeyboardBuilder()
    if growth.bot_username():
        # Ulashish havolasi — foydalanuvchining shaxsiy taklif havolasi:
        # do'sti shu orqali kelsa, xatolar tahlili ochiladi.
        link = referrals.link(growth.bot_username(), user_id)
        text = (t("iq_share_text", lang, iq=iq, correct=result["correct"], total=TOTAL)
                if iq >= IQ_NUMBER_MIN else t("ref_share_text", lang))
        b.button(text=t("btn_share", lang), url=_share_url(link, text))
    compare.add_button(b, IQ_KEY, lang)
    kb.next_test_button(b, IQ_KEY, lang)
    b.button(text=t("btn_retake", lang), callback_data="iq:card")
    b.button(text=t("btn_other_tests", lang), callback_data="nav:menu")
    b.adjust(1)
    return b.as_markup()


async def _finish(callback: CallbackQuery, state: FSMContext, lang: str,
                  answers: list[str], started: float | None, age: str | None) -> None:
    key = answer_key()
    if key is None:
        # Test davomida kalit yo'qolgan bo'lsa: natijani saqlamaymiz, urinish kuymaydi.
        log.error("IQ_ANSWERS test oxirida topilmadi — natija saqlanmadi")
        await callback.message.answer(_unavailable_text(lang))
        return
    await state.clear()
    user_id = callback.from_user.id
    await progress.clear(user_id, IQ_KEY)
    age = age if age in AGE_CODES else DEFAULT_AGE
    result = grade(answers, key)
    seconds = int(time.time() - started) if started else None
    estimate = estimate_iq(result["correct"], age, await _peer_scores(user_id, age))
    await db.save_result(user_id, IQ_KEY, lang, age, float(result["correct"]), {
        "version": RESULT_VERSION,
        "correct": result["correct"],
        "total": TOTAL,
        "iq": estimate["iq"],
        "iq_low": estimate["low"],
        "iq_high": estimate["high"],
        "iq_source": estimate["source"],
        "answers": answers,
        "kinds": result["kinds"],
        "seconds": seconds,
    })
    events.track(user_id, "test_completed", IQ_KEY)
    saved = await db.latest_result(user_id, IQ_KEY)
    if callback.message.photo:
        try:
            await callback.message.delete()
        except TelegramBadRequest:
            await _retire(callback.message)
    # Tartib: sertifikat (bepul) → natija: to'liq tahlil yoki bepul natija + to'lov.
    full = await access.has(user_id, IQ_KEY)
    await growth.send_certificate(callback.message, callback.from_user, saved, full=full)
    if saved:
        await reports.deliver(callback.bot, user_id, saved, lang)
    await growth.after_test(callback.bot, user_id, IQ_KEY, lang)


# --- Eski tugmalar -------------------------------------------------------------


@router.callback_query(F.data.startswith("iqrev:"))
async def review_gone(callback: CallbackQuery, lang: str) -> None:
    """Xatolar tahlili olib tashlangan. Eski xabarlardagi tugma bosilsa — qisqa izoh."""
    await callback.answer(t("review_gone", lang), show_alert=True)
