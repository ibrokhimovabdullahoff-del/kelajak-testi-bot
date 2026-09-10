"""Original IQ-style reasoning assessment.

This is an original reasoning benchmark, not a clinical or normed IQ test.
It uses multiple-choice items and a transparent 0-100 reasoning score.
"""
from __future__ import annotations

import html
import random

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message

import database as db
from locales import money
from psytests.base import L

router = Router()

QUESTIONS = [
    ("🔢", L("Ketma-ketlikni davom ettiring: 2, 6, 12, 20, 30, ?", "Продолжите ряд: 2, 6, 12, 20, 30, ?"), ["36", "40", "42", "44", "48"], 2),
    ("🔷", L("Qaysi son boshqalardan farq qiladi: 16, 25, 36, 49, 63?", "Какое число отличается: 16, 25, 36, 49, 63?"), ["16", "25", "36", "49", "63"], 4),
    ("🧩", L("Agar barcha NARlar ZEL bo‘lsa va ayrim ZELlar TOR bo‘lsa, qaysi xulosa aniq?", "Если все NAR являются ZEL, а некоторые ZEL являются TOR, какой вывод точен?"), ["Barcha NARlar TOR", "Hech bir NAR TOR emas", "Ba'zi NARlar TOR bo‘lishi mumkin", "Barcha TORlar NAR", "NAR va TOR bir xil"], 2),
    ("⚖️", L("3 ta bir xil quti 18 kg. 5 ta shunday quti necha kg?", "3 одинаковые коробки весят 18 кг. Сколько весят 5 таких коробок?"), ["24", "27", "30", "33", "36"], 2),
    ("🔤", L("A, C, F, J, O, ? harflarida keyingi harf qaysi?", "Какой следующей буквой будет ряд A, C, F, J, O, ?"), ["S", "T", "U", "V", "W"], 2),
    ("🕒", L("Soat 3:15 da minut strelkasi 3 ni ko‘rsatadi. Soat strelkasi qayerda bo‘ladi?", "В 3:15 минутная стрелка на 3. Где будет часовая стрелка?"), ["3 da", "3 va 4 oralig‘ida", "4 da", "2 va 3 oralig‘ida", "12 da"], 1),
    ("🧠", L("Bir sonning yarmi 18 ga teng. Shu sonning 25% i nechaga teng?", "Половина числа равна 18. Чему равны 25% этого числа?"), ["6", "8", "9", "12", "18"], 2),
    ("📐", L("Kvadratning tomoni 6. Perimetri 24 bo‘lsa, yuzi nechaga teng?", "Сторона квадрата 6. Если периметр 24, чему равна площадь?"), ["18", "24", "30", "36", "48"], 3),
    ("🔁", L("5 → 11, 7 → 15, 10 → 21 bo‘lsa, 13 → ?", "Если 5 → 11, 7 → 15, 10 → 21, то 13 → ?"), ["24", "25", "26", "27", "28"], 3),
    ("🧭", L("Shimolga qarab turib 90° o‘ngga, keyin 180° chapga burildingiz. Qaysi tomonga qaraysiz?", "Вы смотрите на север, поворачиваете на 90° направо, затем на 180° налево. Куда смотрите?"), ["Shimol", "Janub", "Sharq", "G‘arb", "Janubi-sharq"], 3),
    ("🧮", L("Bir xil qoida: 4, 9, 19, 39, ?", "По одному правилу: 4, 9, 19, 39, ?"), ["59", "69", "79", "89", "99"], 2),
    ("🧱", L("5 ishchi ishni 12 kunda tugatsa, bir xil tezlikda 10 ishchi necha kunda tugatadi?", "Если 5 работников выполняют работу за 12 дней, сколько дней нужно 10 работникам при той же скорости?"), ["3", "5", "6", "8", "10"], 2),
    ("🔍", L("Qaysi juftlik munosabati bir xil: Qush : uya = Ari : ?", "Какая связь такая же: Птица : гнездо = Пчела : ?"), ["Asal", "Gul", "Uya", "Katak", "Qanot"], 3),
    ("📊", L("Ketma-ketlik: 81, 27, 9, 3, ?", "Ряд: 81, 27, 9, 3, ?"), ["0", "1", "2", "1.5", "-1"], 1),
    ("🧩", L("Agar kecha dushanba bo‘lgan bo‘lsa, ertadan ikki kun keyin qaysi kun?", "Если вчера был понедельник, какой день будет послезавтра?"), ["Seshanba", "Chorshanba", "Payshanba", "Juma", "Shanba"], 2),
    ("🔢", L("2, 3, 5, 8, 12, ? ketma-ketlikda keyingi son?", "Следующее число: 2, 3, 5, 8, 12, ?"), ["15", "16", "17", "18", "20"], 2),
    ("🧠", L("Barcha K lar L. Hech bir L M emas. Demak K lar M bo‘lishi mumkinmi?", "Все K являются L. Ни один L не является M. Могут ли K быть M?"), ["Ha, albatta", "Yo‘q, mumkin emas", "Faqat ayrimlari", "Ma'lumot yetarli emas", "Faqat M bo‘lsa"], 1),
    ("⚡", L("Bir mashina 60 km/soat tezlikda 30 daqiqada qancha yo‘l bosadi?", "Сколько проедет машина со скоростью 60 км/ч за 30 минут?"), ["20 km", "25 km", "30 km", "40 km", "60 km"], 2),
    ("🧮", L("Agar 7 + 3 = 410 va 5 + 2 = 37 ko‘rinishida yozilsa, 8 + 4 = ?", "Если 7 + 3 записано как 410, а 5 + 2 как 37, то 8 + 4 = ?"), ["412", "212", "432", "4120", "84"], 0),
    ("🎯", L("Bir xil naqsh: 1, 4, 10, 22, 46, ?", "Один шаблон: 1, 4, 10, 22, 46, ?"), ["70", "82", "90", "94", "96"], 3),
]

class IQState(StatesGroup):
    answering = State()


def _text(lang: str, uz: str, ru: str) -> str:
    return uz if lang == "uz" else ru


def menu(lang: str):
    from aiogram.utils.keyboard import InlineKeyboardBuilder
    b = InlineKeyboardBuilder()
    b.button(text=_text(lang, "🧠 IQ-style testni boshlash", "🧠 Начать IQ-style тест"), callback_data="iq:start")
    b.button(text=_text(lang, "⬅️ Orqaga", "⬅️ Назад"), callback_data="nav:menu")
    b.adjust(1)
    return b.as_markup()


def question_markup(index: int, lang: str):
    from aiogram.utils.keyboard import InlineKeyboardBuilder
    b = InlineKeyboardBuilder()
    for i, option in enumerate(QUESTIONS[index][2]):
        b.button(text=f"{i+1}️⃣ {option}", callback_data=f"iq:ans:{index}:{i}")
    b.adjust(1)
    return b.as_markup()


def question_text(index: int, lang: str) -> str:
    q = QUESTIONS[index]
    return (
        f"🧠 <b>{_text(lang, 'IQ-style reasoning testi', 'IQ-style тест рассуждений')}</b>\n\n"
        f"{index+1} / {len(QUESTIONS)}\n\n"
        f"<b>{html.escape(q[1].get(lang, q[1]['uz']))}</b>"
    )


@router.message(Command("iq"))
async def iq_command(message: Message, state: FSMContext, lang: str) -> None:
    await state.clear()
    await message.answer(
        _text(lang,
              "Bu original mantiqiy fikrlash baholashi. U klinik yoki standartlashtirilgan IQ testi emas.\n\nBoshlaymizmi?",
              "Это оригинальная оценка логического мышления. Это не клинический и не нормированный IQ-тест.\n\nНачнём?"),
        reply_markup=menu(lang),
    )


@router.callback_query(F.data == "iq:start")
async def iq_start(callback: CallbackQuery, state: FSMContext, lang: str) -> None:
    await state.clear()
    await state.update_data(iq_answers=[], iq_started=True)
    await state.set_state(IQState.answering)
    await callback.message.edit_text(question_text(0, lang), reply_markup=question_markup(0, lang))
    await callback.answer()


@router.callback_query(IQState.answering, F.data.startswith("iq:ans:"))
async def iq_answer(callback: CallbackQuery, state: FSMContext, lang: str) -> None:
    _, _, raw_index, raw_value = callback.data.split(":")
    index, value = int(raw_index), int(raw_value)
    data = await state.get_data()
    answers = list(data.get("iq_answers", []))
    if index != len(answers) or value not in range(5):
        await callback.answer(_text(lang, "Bu savol allaqachon javoblangan.", "На этот вопрос уже отвечено."), show_alert=True)
        return
    answers.append(value)
    await state.update_data(iq_answers=answers)
    await callback.answer()
    if len(answers) < len(QUESTIONS):
        await callback.message.edit_text(question_text(len(answers), lang), reply_markup=question_markup(len(answers), lang))
        return

    correct = sum(1 for i, answer in enumerate(answers) if answer == QUESTIONS[i][3])
    score = round(correct / len(QUESTIONS) * 100)
    await db.save_result(callback.from_user.id, "iq", lang, None, float(score),
                         {"reasoning": float(score), "accuracy": float(score)})
    await state.clear()
    if score >= 85:
        band = _text(lang, "🏆 Juda kuchli mantiqiy natija", "🏆 Очень сильный результат рассуждений")
    elif score >= 70:
        band = _text(lang, "🌟 Kuchli mantiqiy natija", "🌟 Сильный результат рассуждений")
    elif score >= 50:
        band = _text(lang, "💪 Yaxshi natija", "💪 Хороший результат")
    else:
        band = _text(lang, "🌱 Rivojlantirish uchun yaxshi nuqta", "🌱 Хорошая точка для развития")
    text = (
        f"🧠 <b>{_text(lang, 'IQ-style test natijasi', 'Результат IQ-style теста')}</b>\n\n"
        f"<b>{score}/100</b> — {band}\n\n"
        f"{_text(lang, f'To‘g‘ri javoblar: {correct}/{len(QUESTIONS)}', f'Правильных ответов: {correct}/{len(QUESTIONS)}')}\n\n"
        f"⚠️ {_text(lang, 'Bu natija standart IQ koeffitsienti emas. U ushbu original topshiriqlardagi mantiqiy aniqlikni ko‘rsatadi.', 'Это не стандартизированный коэффициент IQ. Результат отражает точность рассуждений в этих оригинальных заданиях.')}"
    )
    from aiogram.utils.keyboard import InlineKeyboardBuilder
    b = InlineKeyboardBuilder()
    b.button(text=_text(lang, "🔄 Qayta topshirish", "🔄 Пройти снова"), callback_data="iq:start")
    b.button(text=_text(lang, "🧠 Boshqa testlar", "🧠 Другие тесты"), callback_data="nav:menu")
    b.adjust(1)
    await callback.message.edit_text(text, reply_markup=b.as_markup())
