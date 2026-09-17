"""Premium IQ testi: savol — rasm, javob — rasm ostidagi A–D tugmalari.

Oqim: kartochka (/iq yoki menyu) → to'lov tekshiruvi → yosh (IQ tengdoshlarga
nisbatan hisoblanadi) → 20 ta rasm bitta xabarning o'zida almashib turadi
(chat to'lib ketmaydi) → taxminiy IQ bilan natija.

To'g'ri javoblar foydalanuvchiga hech qayerda ko'rsatilmaydi: test pullik va
javoblar tarqalib ketsa, natijalar ma'nosini yo'qotadi.

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

import database as db
from config import BOT_USERNAME, IQ_EMOJI, IQ_KEY, is_admin
from handlers import payment as pay
from locales import money
from psytests.iq import (
    AGE_CODES, AGE_GROUPS, DEFAULT_AGE, IQ_MAX, IQ_MIN, LETTERS, PUZZLES,
    RUSHED_SECONDS_PER_PUZZLE, TOTAL, Puzzle, answer_key, estimate_iq, grade, level_for,
    percentile,
)

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


def _duration(seconds: int, lang: str) -> str:
    minutes, sec = divmod(max(0, seconds), 60)
    if lang == "uz":
        return f"{minutes} daqiqa {sec} soniya" if minutes else f"{sec} soniya"
    return f"{minutes} мин {sec} сек" if minutes else f"{sec} сек"


def iq_scale(iq: int) -> str:
    """70 dan 145 gacha shkalada natija qayerda turgani."""
    cells = 12
    pos = round((iq - IQ_MIN) / (IQ_MAX - IQ_MIN) * (cells - 1))
    return "".join("🔵" if i == pos else "▫️" for i in range(cells))


def render(result: dict, lang: str, seconds: int | None, estimate: dict,
           peers: list[float]) -> str:
    correct = result["correct"]
    iq = estimate["iq"]
    level = level_for(iq)
    lines = [
        f"{IQ_EMOJI} <b>{bi(lang, 'PREMIUM IQ TESTI — NATIJA', 'ПРЕМИУМ IQ-ТЕСТ — РЕЗУЛЬТАТ')}</b>",
        "",
        f"🧠 {bi(lang, 'Taxminiy IQ', 'Примерный IQ')}: <b>≈ {iq}</b>",
        bi(lang, f"<i>ehtimoliy oraliq: {estimate['low']}–{estimate['high']}</i>",
           f"<i>вероятный диапазон: {estimate['low']}–{estimate['high']}</i>"),
        f"{IQ_MIN} {iq_scale(iq)} {IQ_MAX}",
        "",
        f"{level.emoji} {bi(lang, 'Daraja', 'Уровень')}: <b>{tr(level.name, lang)}</b>",
        tr(level.note, lang),
        "",
        f"🎯 {bi(lang, 'To‘g‘ri javoblar', 'Правильных ответов')}: <b>{correct} / {TOTAL}</b>",
    ]
    pct = percentile(correct, peers)
    if pct is not None:
        lines.append(bi(
            lang,
            f"📊 Tengdoshlaringizning <b>{pct} foizi</b>dan yuqori (ishtirokchilar: {len(peers)}).",
            f"📊 Выше, чем у <b>{pct}%</b> ваших сверстников (участников: {len(peers)}).",
        ))
    if seconds is not None:
        lines.append(f"⏱ {bi(lang, 'Sarflangan vaqt', 'Затраченное время')}: {_duration(seconds, lang)}")
        if seconds < TOTAL * RUSHED_SECONDS_PER_PUZZLE:
            lines.append(bi(
                lang,
                "⚠️ Juda tez yechdingiz — ba’zi javoblar tavakkal belgilangan bo‘lishi mumkin.",
                "⚠️ Вы ответили очень быстро — часть ответов могла быть наугад.",
            ))

    return "\n".join(lines)


def result_markup(result: dict, iq: int, lang: str):
    b = InlineKeyboardBuilder()
    if BOT_USERNAME:
        share = quote(bi(
            lang,
            f"Mening taxminiy IQ im — {iq} ({result['correct']}/{TOTAL}). Sen ham sinab ko‘r:",
            f"Мой примерный IQ — {iq} ({result['correct']}/{TOTAL}). Попробуй и ты:",
        ))
        b.button(text=bi(lang, "📤 Natijani ulashish", "📤 Поделиться результатом"),
                 url=f"https://t.me/share/url?url=https://t.me/{BOT_USERNAME}&text={share}")
    b.button(text=bi(lang, "🔄 Qayta topshirish", "🔄 Пройти снова"), callback_data="iq:card")
    b.button(text=bi(lang, "🧠 Boshqa testlar", "🧠 Другие тесты"), callback_data="nav:menu")
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
    age = age if age in AGE_CODES else DEFAULT_AGE
    result = grade(answers, key)
    seconds = int(time.time() - started) if started else None
    peers = await _peer_scores(user_id, age)
    estimate = estimate_iq(result["correct"], age, peers)
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
    try:
        await callback.message.delete()
    except TelegramBadRequest:
        await _retire(callback.message)
    await callback.message.answer(render(result, lang, seconds, estimate, peers),
                                  reply_markup=result_markup(result, estimate["iq"], lang))
