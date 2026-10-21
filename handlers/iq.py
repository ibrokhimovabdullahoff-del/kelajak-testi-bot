"""Premium IQ testi: savol — rasm, javob — rasm ostidagi A–D tugmalari.

Oqim: kartochka (/iq yoki menyu) → to'lov tekshiruvi → yosh (IQ tengdoshlarga
nisbatan hisoblanadi) → 20 ta rasm bitta xabarning o'zida almashib turadi
(chat to'lib ketmaydi) → natija: sertifikat rasmi → xatolar tahlili taklifi →
taxminiy IQ bilan matnli natija.

To'g'ri javoblar faqat xatolar tahlilida ko'rinadi, u ham faqat do'stini
taklif qilgan odamga (referrals.py) va faqat o'zi xato qilgan 3–4 savol uchun.

Rasmlar Telegram'ga bir marta yuklanadi: qaytgan file_id bazada saqlanadi va
keyingi hamma foydalanuvchiga shu id yuboriladi — server rasmni qayta-qayta
yubormaydi, rasm esa darhol ochiladi.
"""
from __future__ import annotations

import asyncio
import html
import logging
import time
from urllib.parse import quote

from aiogram import F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (
    CallbackQuery, FSInputFile, InputMediaPhoto, LinkPreviewOptions, Message,
)
from aiogram.utils.keyboard import InlineKeyboardBuilder

import database as db
import keyboards as kb
import peers
import referrals
import report
from config import IQ_EMOJI, IQ_KEY, is_admin
from handlers import growth
from handlers import payment as pay
from locales import money, t
from psytests.iq import (
    AGE_CODES, AGE_GROUPS, DEFAULT_AGE, LETTERS, PUZZLES, TOTAL, Puzzle, answer_key,
    estimate_iq, explanations, grade, pick_mistakes,
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


def intro(lang: str) -> str:
    return bi(
        lang,
        f"{IQ_EMOJI} <b>Premium IQ testi — rasmli mantiq</b>\n\n"
        f"{TOTAL} ta rasmli topshiriq. Har birida rasmlar ma’lum qoida bo‘yicha "
        "o‘zgaradi: qoidani toping va «?» o‘rniga to‘g‘ri variantni tanlang.\n\n"
        "📊 <b>Natijada:</b> taxminiy IQ (yoshingizga qarab), darajangiz va "
        "to‘g‘ri javoblar soni.\n\n"
        "⏱ Taxminan 15–20 daqiqa. Shoshmang, lekin bitta savolda qotib qolmang.\n"
        "💡 Test yarmida to‘xtatilsa, to‘lov kuymaydi — u faqat test oxirigacha "
        "yechilganda hisoblanadi.",
        f"{IQ_EMOJI} <b>Премиум IQ-тест — логика в картинках</b>\n\n"
        f"{TOTAL} заданий с картинками. В каждом картинки меняются по определённому "
        "правилу: найдите правило и выберите вариант вместо «?».\n\n"
        "📊 <b>В результате:</b> примерный IQ (с учётом возраста), ваш уровень и "
        "число правильных ответов.\n\n"
        "⏱ Примерно 15–20 минут. Не спешите, но и не застревайте на одном вопросе.\n"
        "💡 Если остановить тест на полпути, оплата не сгорает — она засчитывается "
        "только когда тест пройден до конца.",
    )


def _unavailable_text(lang: str) -> str:
    return bi(lang, "⏳ IQ testi vaqtincha yopiq. Birozdan keyin qayta urinib ko‘ring.",
              "⏳ IQ-тест временно недоступен. Попробуйте чуть позже.")


async def card(message: Message, user_id: int, lang: str, edit: bool) -> None:
    locked = await pay.is_locked(user_id, IQ_KEY)
    text = intro(lang)
    b = InlineKeyboardBuilder()
    if answer_key() is None:
        # Kalitsiz natijani hisoblab bo'lmaydi — pul olib, noto'g'ri baho berishdan ko'ra yopamiz.
        log.error("IQ_ANSWERS o'rnatilmagan yoki noto'g'ri — IQ testi yopiq")
        text += "\n\n" + _unavailable_text(lang)
    elif locked:
        price = money(await pay.price_for(IQ_KEY))
        text += "\n\n" + bi(lang, f"🔒 Narxi: <b>{price} so‘m</b>", f"🔒 Цена: <b>{price} сум</b>")
        b.button(text=bi(lang, "💳 Click orqali to‘lash", "💳 Оплатить через Click"), callback_data=f"pay:{IQ_KEY}")
        b.button(text=bi(lang, "💰 Balansdan to‘lash", "💰 Оплатить с баланса"), callback_data=f"shop:buy:{IQ_KEY}")
        b.button(text=bi(lang, "➕ Balansni to‘ldirish", "➕ Пополнить баланс"), callback_data="wallet:topup")
    else:
        b.button(text=bi(lang, "▶️ Testni boshlash", "▶️ Начать тест"), callback_data="iq:start")
    b.button(text=bi(lang, "⬅️ Orqaga", "⬅️ Назад"), callback_data="nav:menu")
    b.adjust(1)
    if edit and not message.photo:
        try:
            await message.edit_text(text, reply_markup=b.as_markup())
            return
        except TelegramBadRequest as exc:
            if "not modified" in str(exc).lower():
                return
    await message.answer(text, reply_markup=b.as_markup())


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
    if await pay.is_locked(user_id, IQ_KEY):
        await pay.show_paywall(message, user_id, IQ_KEY, lang)
        return
    await state.clear()
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
    # Eski xabardagi yosh tugmasi ham shu yerga keladi — huquqni qayta tekshiramiz.
    if await pay.is_locked(user_id, IQ_KEY):
        await pay.show_paywall(callback.message, user_id, IQ_KEY, lang)
        return
    await state.clear()
    await state.set_state(IQState.answering)
    await state.update_data(iq_answers=[], iq_started=time.time(), iq_age=age)
    await db.log_start(user_id, IQ_KEY)
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
            await callback.answer()
            return
        data = await state.get_data()
        answers = list(data.get("iq_answers", []))
        if index != len(answers):
            await callback.answer(bi(lang, "Javob qabul qilingan ✅", "Ответ уже принят ✅"))
            return
        answers.append(letter)
        await state.update_data(iq_answers=answers)
        await callback.answer()
        if len(answers) < TOTAL:
            await _show(callback.message, len(answers), lang, edit=True)
            return
        await _finish(callback, state, lang, answers, data.get("iq_started"), data.get("iq_age"))


@router.callback_query(IQState.answering, F.data == "iq:back")
async def back(callback: CallbackQuery, state: FSMContext, lang: str) -> None:
    async with _lock(callback.from_user.id):
        data = await state.get_data()
        answers = list(data.get("iq_answers", []))
        await callback.answer()
        if not answers:
            return
        answers.pop()
        await state.update_data(iq_answers=answers)
        await _show(callback.message, len(answers), lang, edit=True)


@router.callback_query(F.data == "iq:stop")
async def stop(callback: CallbackQuery, state: FSMContext, lang: str) -> None:
    if await state.get_state() == IQState.answering.state:
        await state.clear()
    await callback.answer(bi(lang, "Test to‘xtatildi", "Тест остановлен"))
    try:
        await callback.message.delete()
    except TelegramBadRequest:
        await _retire(callback.message)
    from handlers import user  # aylanma importdan qochish uchun shu yerda

    await user.show_menu(callback.message, lang, callback.from_user.id, edit=False)


@router.callback_query(F.data.startswith("iq:a:") | F.data.startswith("iq:ans:") | (F.data == "iq:back"))
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
    kb.next_test_button(b, IQ_KEY, lang)
    b.button(text=t("btn_retake", lang), callback_data="iq:card")
    b.button(text=t("btn_other_tests", lang), callback_data="nav:menu")
    b.adjust(1)
    return b.as_markup()


async def _offer_review(message: Message, user_id: int, row: dict | None,
                        mistakes: int, lang: str) -> None:
    """Sertifikatdan keyin: xatolar tahlili — ochiq bo'lsa tugma, bo'lmasa taklif havolasi."""
    if row is None or mistakes == 0:
        return
    if explanations() is None:
        log.error("IQ_EXPLANATIONS o'rnatilmagan yoki to'liq emas — xatolar tahlili taklif qilinmadi")
        return
    b = InlineKeyboardBuilder()
    if await referrals.is_unlocked(user_id):
        b.button(text=t("btn_review", lang), callback_data=f"iqrev:{row['id']}:0")
        await message.answer(t("ref_offer_unlocked", lang), reply_markup=b.as_markup())
        return
    await _send_invite(message, user_id, lang)


async def _send_invite(message: Message, user_id: int, lang: str) -> None:
    link = referrals.link(growth.bot_username(), user_id)
    b = InlineKeyboardBuilder()
    b.button(text=t("btn_ref_share", lang), url=_share_url(link, t("ref_share_text", lang)))
    await message.answer(t("ref_offer", lang, link=link), reply_markup=b.as_markup(),
                         link_preview_options=LinkPreviewOptions(is_disabled=True))


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
    saved = await db.latest_result(user_id, IQ_KEY)
    comparison = await peers.compare(IQ_KEY, user_id, result["correct"])
    try:
        await callback.message.delete()
    except TelegramBadRequest:
        await _retire(callback.message)
    # Tartib: sertifikat → xatolar tahlili taklifi → batafsil natija.
    await growth.send_certificate(callback.message, callback.from_user, saved)
    await _offer_review(callback.message, user_id, saved, len(result["mistakes"]), lang)
    await callback.message.answer(
        report.render_iq(result["correct"], estimate, seconds, lang, comparison),
        reply_markup=result_markup(result, estimate["iq"], user_id, lang),
    )


# --- Xatolar tahlili ------------------------------------------------------------


@router.callback_query(F.data == "iqrev:close")
async def review_close(callback: CallbackQuery) -> None:
    try:
        await callback.message.delete()
    except TelegramBadRequest:
        await _retire(callback.message)


@router.callback_query(F.data.startswith("iqrev:"))
async def review(callback: CallbackQuery, lang: str) -> None:
    """Xato qilingan 3–4 savol: rasm, sizning javobingiz, to'g'ri javob, sababi."""
    parts = callback.data.split(":")
    if len(parts) != 3 or not parts[1].isdigit() or not parts[2].isdigit():
        return
    user_id = callback.from_user.id
    row = await db.get_result(int(parts[1]))
    if (row is None or row["user_id"] != user_id or row["test_key"] != IQ_KEY
            or row["scales"].get("version") != RESULT_VERSION
            or len(row["scales"].get("answers") or []) != TOTAL):
        await callback.message.answer(t("review_missing", lang))
        return
    if not await referrals.is_unlocked(user_id):
        await _send_invite(callback.message, user_id, lang)
        return
    key, texts = answer_key(), explanations()
    if key is None or texts is None:
        await callback.message.answer(t("review_unavailable", lang))
        return
    answers = row["scales"]["answers"]
    mistakes = pick_mistakes(answers, key)
    if not mistakes:
        await callback.message.answer(t("review_none", lang))
        return
    position = min(int(parts[2]), len(mistakes) - 1)
    index = mistakes[position]
    puzzle = PUZZLES[index]
    why = texts[puzzle.file].get(lang) or texts[puzzle.file]["uz"]
    caption = report.review_caption(position + 1, len(mistakes), index + 1, answers[index],
                                    key[index], html.escape(why), lang)
    b = InlineKeyboardBuilder()
    nav = 0
    if position > 0:
        b.button(text="⬅️", callback_data=f"iqrev:{row['id']}:{position - 1}")
        nav += 1
    if position < len(mistakes) - 1:
        b.button(text="➡️", callback_data=f"iqrev:{row['id']}:{position + 1}")
        nav += 1
    b.button(text=t("btn_close", lang), callback_data="iqrev:close")
    b.adjust(*([nav] if nav else []), 1)
    await _send_puzzle(callback.message, puzzle, caption, b.as_markup(),
                       edit=bool(callback.message.photo))
