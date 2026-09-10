"""Premium IQ assessment with paid/free access control."""
from __future__ import annotations

import html

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder

import database as db
from config import IQ_EMOJI, IQ_KEY
from handlers import payment as pay
from locales import money
from psytests.base import L

router = Router()

QUESTIONS = [
    ("sequence", L("Ketma-ketlikni davom ettiring: 2, 6, 12, 20, 30, ?", "Продолжите ряд: 2, 6, 12, 20, 30, ?"), ["36", "40", "42", "44", "48"], ["36", "40", "42", "44", "48"], 2, 1),
    ("logic", L("Qaysi son boshqalardan farq qiladi: 16, 25, 36, 49, 63?", "Какое число отличается: 16, 25, 36, 49, 63?"), ["16", "25", "36", "49", "63"], ["16", "25", "36", "49", "63"], 4, 1),
    ("sequence", L("A, C, F, J, O, ? qatorida keyingi harf qaysi?", "Какая следующая буква в ряду A, C, F, J, O, ?"), ["S", "T", "U", "V", "W"], ["S", "T", "U", "V", "W"], 2, 2),
    ("numeric", L("3 ta bir xil quti 18 kg. 5 ta shunday quti necha kg?", "3 одинаковые коробки весят 18 кг. Сколько весят 5 таких коробок?"), ["24", "27", "30", "33", "36"], ["24", "27", "30", "33", "36"], 2, 1),
    ("sequence", L("Bir xil qoida: 4, 9, 19, 39, ?", "По одному правилу: 4, 9, 19, 39, ?"), ["59", "69", "79", "89", "99"], ["59", "69", "79", "89", "99"], 2, 1),
    ("sequence", L("Ketma-ketlik: 81, 27, 9, 3, ?", "Ряд: 81, 27, 9, 3, ?"), ["0", "1", "2", "1.5", "-1"], ["0", "1", "2", "1.5", "-1"], 1, 1),
    ("sequence", L("2, 3, 5, 8, 12, ? ketma-ketlikda keyingi son?", "Следующее число: 2, 3, 5, 8, 12, ?"), ["15", "16", "17", "18", "20"], ["15", "16", "17", "18", "20"], 2, 1),
    ("logic", L("Barcha NARlar ZEL. Ayrim ZELlar TOR. Qaysi xulosa aniq?", "Все NAR являются ZEL. Некоторые ZEL являются TOR. Какой вывод точен?"), ["Barcha NARlar TOR", "Hech bir NAR TOR emas", "Ba'zi NARlar TOR bo‘lishi mumkin", "Barcha TORlar NAR", "NAR va TOR bir xil"], ["Все NAR — TOR", "Ни один NAR не TOR", "Некоторые NAR могут быть TOR", "Все TOR — NAR", "NAR и TOR — одно и то же"], 2, 2),
    ("logic", L("Barcha K lar L. Hech bir L M emas. Demak K lar M bo‘lishi mumkinmi?", "Все K являются L. Ни один L не является M. Могут ли K быть M?"), ["Ha, albatta", "Yo‘q, mumkin emas", "Faqat ayrimlari", "Ma'lumot yetarli emas", "Faqat M bo‘lsa"], ["Да, обязательно", "Нет, невозможно", "Только некоторые", "Данных недостаточно", "Только если есть M"], 1, 2),
    ("applied", L("Mashina 60 km/soat tezlikda 45 daqiqada qancha yo‘l bosadi?", "Сколько проедет машина со скоростью 60 км/ч за 45 минут?"), ["30 km", "40 km", "45 km", "50 km", "60 km"], ["30 км", "40 км", "45 км", "50 км", "60 км"], 2, 1),
    ("spatial", L("Soat 3:15 da soat strelkasi qayerda bo‘ladi?", "Где будет часовая стрелка в 3:15?"), ["3 da", "3 va 4 oralig‘ida", "4 da", "2 va 3 oralig‘ida", "12 da"], ["На 3", "Между 3 и 4", "На 4", "Между 2 и 3", "На 12"], 1, 2),
    ("spatial", L("Shimolga qarab turib 90° o‘ngga, keyin 180° chapga burildingiz. Qaysi tomonga qaraysiz?", "Вы смотрите на север, поворачиваете на 90° направо, затем на 180° налево. Куда смотрите?"), ["Shimol", "Janub", "Sharq", "G‘arb", "Janubi-sharq"], ["Север", "Юг", "Восток", "Запад", "Юго-восток"], 3, 2),
    ("verbal", L("Qush : uya = Ari : ?", "Птица : гнездо = Пчела : ?"), ["Asal", "Gul", "Uya", "Katak", "Qanot"], ["Мёд", "Цветок", "Гнездо", "Соты", "Крыло"], 3, 1),
    ("applied", L("5 ishchi ishni 12 kunda tugatsa, bir xil tezlikda 10 ishchi necha kunda tugatadi?", "Если 5 работников выполняют работу за 12 дней, сколько нужно 10 работникам при той же скорости?"), ["3", "5", "6", "8", "10"], ["3", "5", "6", "8", "10"], 2, 1),
    ("numeric", L("Bir sonning yarmi 18 ga teng. Shu sonning 25% i nechaga teng?", "Половина числа равна 18. Чему равны 25% этого числа?"), ["6", "8", "9", "12", "18"], ["6", "8", "9", "12", "18"], 2, 1),
    ("numeric", L("2 : 3 = 8 : x bo‘lsa, x nechaga teng?", "Если 2 : 3 = 8 : x, чему равен x?"), ["10", "12", "14", "16", "18"], ["10", "12", "14", "16", "18"], 1, 1),
    ("probability", L("Oddiy 6 qirrali kubik tashlanganda juft son tushish ehtimoli qancha?", "Какова вероятность получить чётное число на обычном кубике с 6 гранями?"), ["1/6", "1/3", "1/2", "2/3", "5/6"], ["1/6", "1/3", "1/2", "2/3", "5/6"], 2, 1),
    ("verbal", L("CAT har bir harfni keyingi harfga almashtirib DBU bo‘lsa, DOG qanday yoziladi?", "Если каждую букву CAT заменить следующей, получится DBU. Как будет записано DOG?"), ["EPH", "EOG", "DPH", "FQI", "EOH"], ["EPH", "EOG", "DPH", "FQI", "EOH"], 0, 2),
    ("logic", L("Qaysi biri boshqalardan farq qiladi: uchburchak, kvadrat, beshburchak, doira, oltiburchak?", "Что отличается: треугольник, квадрат, пятиугольник, круг, шестиугольник?"), ["Uchburchak", "Kvadrat", "Beshburchak", "Doira", "Oltiburchak"], ["Треугольник", "Квадрат", "Пятиугольник", "Круг", "Шестиугольник"], 3, 1),
    ("sequence", L("1, 1, 2, 3, 5, 8, ? qatorida keyingi son?", "Какое число следующее: 1, 1, 2, 3, 5, 8, ?"), ["11", "12", "13", "14", "15"], ["11", "12", "13", "14", "15"], 2, 1),
    ("logic", L("Barcha atirgullar gullardir. Ayrim gullar qizil. Qaysi xulosa aniq?", "Все розы — цветы. Некоторые цветы красные. Какой вывод гарантирован?"), ["Barcha atirgullar qizil", "Ayrim atirgullar qizil", "Hech bir atirgul qizil emas", "Aniq xulosa chiqarib bo‘lmaydi", "Barcha qizillar atirgul"], ["Все розы красные", "Некоторые розы красные", "Ни одна роза не красная", "Нельзя сделать точный вывод", "Все красные — розы"], 3, 2),
    ("applied", L("3 ta mashina 6 soatda jami 90 dona detal ishlab chiqarsa, shu tezlikda 5 ta mashina 6 soatda nechta detal qiladi?", "Если 3 станка за 6 часов делают 90 деталей, сколько сделают 5 станков за 6 часов при той же скорости?"), ["120", "135", "150", "165", "180"], ["120", "135", "150", "165", "180"], 2, 2),
    ("sequence", L("100, 90, 81, 73, ? ketma-ketlikda keyingi son qaysi?", "Какое число следующее: 100, 90, 81, 73, ?"), ["64", "65", "66", "67", "68"], ["64", "65", "66", "67", "68"], 2, 2),
    ("numeric", L("2 → 4, 3 → 9, 4 → 16 bo‘lsa, 7 → ?", "Если 2 → 4, 3 → 9, 4 → 16, то 7 → ?"), ["28", "35", "42", "49", "56"], ["28", "35", "42", "49", "56"], 3, 1),
    ("sequence", L("AZ, BY, CX, DW, ? qatorida keyingi juftlik?", "Какая следующая пара в ряду AZ, BY, CX, DW, ?"), ["EV", "FU", "EX", "EW", "DV"], ["EV", "FU", "EX", "EW", "DV"], 0, 2),
    ("applied", L("Bugun payshanba bo‘lsa, 100 kundan keyin qaysi kun bo‘ladi?", "Если сегодня четверг, какой день будет через 100 дней?"), ["Juma", "Shanba", "Yakshanba", "Dushanba", "Seshanba"], ["Пятница", "Суббота", "Воскресенье", "Понедельник", "Вторник"], 1, 2),
    ("logic", L("Ikki sonning yig‘indisi 30, farqi 6. Katta son nechaga teng?", "Сумма двух чисел 30, разность 6. Чему равно большее число?"), ["12", "15", "16", "18", "21"], ["12", "15", "16", "18", "21"], 3, 1),
    ("numeric", L("121, 144, 169, 196, 225, 250 sonlaridan qaysi biri naqshga mos emas?", "Какое число лишнее: 121, 144, 169, 196, 225, 250?"), ["121", "144", "169", "196", "250"], ["121", "144", "169", "196", "250"], 4, 2),
    ("logic", L("Barcha GLIPlar GLOP. Hech bir GLOP yashil emas. GLIP yashil bo‘lishi mumkinmi?", "Все GLIP являются GLOP. Ни один GLOP не зелёный. Может ли GLIP быть зелёным?"), ["Ha", "Yo‘q", "Faqat ba'zilari", "Ma'lumot yetarli emas", "Faqat kechasi"], ["Да", "Нет", "Только некоторые", "Данных недостаточно", "Только ночью"], 1, 2),
]

class IQState(StatesGroup):
    answering = State()

CATEGORY_NAMES = {
    "uz": {"sequence": "Ketma-ketlik", "logic": "Mantiq", "numeric": "Sonli fikrlash", "verbal": "Verbal fikrlash", "spatial": "Fazoviy fikrlash", "applied": "Amaliy fikrlash", "probability": "Ehtimollik"},
    "ru": {"sequence": "Последовательности", "logic": "Логика", "numeric": "Числовое мышление", "verbal": "Вербальное мышление", "spatial": "Пространственное мышление", "applied": "Прикладное мышление", "probability": "Вероятность"},
}

def bi(lang: str, uz: str, ru: str) -> str:
    return uz if lang == "uz" else ru

def progress(index: int) -> str:
    total = len(QUESTIONS)
    filled = int(round((index / total) * 10))
    return "🟩" * filled + "⬜" * (10 - filled)

def intro(lang: str) -> str:
    if lang == "uz":
        return "🧠 <b>Premium IQ testi</b>\n\n30 ta mantiqiy topshiriq. Ketma-ketlik, mantiq, sonlar, fazoviy va amaliy fikrlash bo‘yicha natija olasiz.\n\n⏱ Taxminan 7–10 daqiqa\n📊 Yakunda IQ natijangiz va kuchli yo‘nalishlaringiz ko‘rsatiladi."
    return "🧠 <b>Премиум IQ-тест</b>\n\n30 заданий на последовательности, логику, числа, пространственное и прикладное мышление.\n\n⏱ Примерно 7–10 минут\n📊 В конце вы увидите свой IQ-результат и сильные направления."

def menu(lang: str):
    b = InlineKeyboardBuilder()
    b.button(text=bi(lang, "🧠 Boshlash", "🧠 Начать тест"), callback_data="iq:start")
    b.button(text=bi(lang, "⬅️ Orqaga", "⬅️ Назад"), callback_data="nav:menu")
    b.adjust(1)
    return b.as_markup()

def question_markup(index: int, lang: str):
    b = InlineKeyboardBuilder()
    for i, option in enumerate(QUESTIONS[index][2 if lang == "uz" else 3]):
        b.button(text=f"{i+1}️⃣ {option}", callback_data=f"iq:ans:{index}:{i}")
    b.button(text=bi(lang, "⛔ Testni to‘xtatish", "⛔ Остановить тест"), callback_data="nav:cancel")
    b.adjust(1)
    return b.as_markup()

def question_text(index: int, lang: str) -> str:
    category = QUESTIONS[index][0]
    diff = QUESTIONS[index][5]
    diff_text = {1: bi(lang, "Oson", "Лёгкое"), 2: bi(lang, "O‘rta", "Среднее")}.get(diff, bi(lang, "Qiyin", "Сложное"))
    title = bi(lang, "Premium IQ testi", "Премиум IQ-тест")
    q = QUESTIONS[index][1].get(lang, QUESTIONS[index][1]["uz"])
    return f"{IQ_EMOJI} <b>{title}</b>\n\n{progress(index)}\n<b>{index + 1} / {len(QUESTIONS)}</b> · {CATEGORY_NAMES[lang][category]} · {diff_text}\n\n<b>{html.escape(q)}</b>"

async def _start_test(target, state: FSMContext, lang: str, user_id: int) -> None:
    if await pay.is_locked(user_id, IQ_KEY):
        await pay.show_paywall(target.message if isinstance(target, CallbackQuery) else target, user_id, IQ_KEY, lang)
        if isinstance(target, CallbackQuery):
            await target.answer()
        return
    await state.clear()
    await state.update_data(iq_answers=[])
    await state.set_state(IQState.answering)
    await db.log_start(user_id, IQ_KEY)
    text = question_text(0, lang)
    markup = question_markup(0, lang)
    if isinstance(target, CallbackQuery):
        await target.message.edit_text(text, reply_markup=markup)
        await target.answer()
    else:
        await target.answer(text, reply_markup=markup)

@router.message(Command("iq"))
async def iq_command(message: Message, state: FSMContext, lang: str) -> None:
    price = await pay.price_for(IQ_KEY)
    if await pay.is_locked(message.from_user.id, IQ_KEY):
        await message.answer(intro(lang) + "\n\n" + bi(lang, f"🔒 Narxi: <b>{money(price)} so‘m</b> — to‘lovdan keyin darhol ochiladi.", f"🔒 Цена: <b>{money(price)} сум</b> — тест откроется сразу после оплаты."), reply_markup=menu(lang))
        return
    await message.answer(intro(lang), reply_markup=menu(lang))

@router.callback_query(F.data == "iq:start")
async def iq_start(callback: CallbackQuery, state: FSMContext, lang: str) -> None:
    await _start_test(callback, state, lang, callback.from_user.id)

@router.callback_query(IQState.answering, F.data.startswith("iq:ans:"))
async def iq_answer(callback: CallbackQuery, state: FSMContext, lang: str) -> None:
    try:
        _, _, raw_index, raw_value = callback.data.split(":")
        index, value = int(raw_index), int(raw_value)
    except (ValueError, AttributeError):
        await callback.answer()
        return
    if index < 0 or index >= len(QUESTIONS) or value < 0 or value >= 5:
        await callback.answer()
        return
    data = await state.get_data()
    answers = list(data.get("iq_answers", []))
    if index != len(answers):
        await callback.answer(bi(lang, "Bu savol allaqachon javoblangan.", "Этот вопрос уже отвечен."), show_alert=True)
        return
    answers.append(value)
    await state.update_data(iq_answers=answers)
    await callback.answer()
    if len(answers) < len(QUESTIONS):
        await callback.message.edit_text(question_text(len(answers), lang), reply_markup=question_markup(len(answers), lang))
        return

    categories: dict[str, list[bool]] = {}
    correct = 0
    for i, answer in enumerate(answers):
        category, _, _, _, expected, _ = QUESTIONS[i]
        ok = answer == expected
        correct += int(ok)
        categories.setdefault(category, []).append(ok)

    score = round(correct / len(QUESTIONS) * 100)
    iq_score = max(70, min(130, 70 + round(score * 0.6)))
    category_scores = {k: round(sum(v) / len(v) * 100) for k, v in categories.items()}
    ranked = sorted(category_scores.items(), key=lambda x: (-x[1], x[0]))
    strong = ranked[:2]
    weak = ranked[-2:][::-1]

    await db.save_result(
        callback.from_user.id,
        IQ_KEY,
        lang,
        None,
        float(iq_score),
        {
            "iq_score": iq_score,
            "percent_score": score,
            "reasoning": float(score),
            "accuracy": float(score),
            "categories": category_scores,
            "correct": correct,
            "total_questions": len(QUESTIONS),
        },
    )
    await state.clear()

    if iq_score >= 125:
        level = bi(lang, "🏆 Juda yuqori", "🏆 Очень высокий")
    elif iq_score >= 115:
        level = bi(lang, "🌟 Yuqori", "🌟 Высокий")
    elif iq_score >= 100:
        level = bi(lang, "💪 Yaxshi", "💪 Хороший")
    elif iq_score >= 85:
        level = bi(lang, "📈 O‘rtacha", "📈 Средний")
    else:
        level = bi(lang, "🌱 Rivojlantirish mumkin", "🌱 Есть над чем работать")

    text = [
        bi(lang, "🧠 <b>PREMIUM IQ NATIJASI</b>", "🧠 <b>РЕЗУЛЬТАТ ПРЕМИУМ IQ</b>"),
        "",
        bi(lang, f"🎯 <b>Sizning IQ natijangiz: {iq_score}</b>", f"🎯 <b>Ваш IQ-результат: {iq_score}</b>"),
        bi(lang, f"📊 To‘g‘ri javoblar: <b>{correct}/{len(QUESTIONS)}</b>", f"📊 Правильных ответов: <b>{correct}/{len(QUESTIONS)}</b>"),
        bi(lang, f"⭐ Daraja: <b>{level}</b>", f"⭐ Уровень: <b>{level}</b>"),
        "",
        bi(lang, "<b>Kuchli yo‘nalishlar</b>", "<b>Сильные направления</b>"),
    ]
    for key, val in strong:
        text.append(f"• {CATEGORY_NAMES[lang][key]} — <b>{val}%</b>")
    text += ["", bi(lang, "<b>Ko‘proq mashq foydali bo‘lishi mumkin</b>", "<b>Что можно потренировать</b>")]
    for key, val in weak:
        text.append(f"• {CATEGORY_NAMES[lang][key]} — <b>{val}%</b>")
    text += [
        "",
        bi(lang, "💡 Bu ko‘rsatkich ushbu 30 savollik testdagi natijadan hisoblangan. U rasmiy klinik yoki standartlashtirilgan IQ testi o‘rnini bosmaydi.", "💡 Этот показатель рассчитан по результатам данного теста из 30 заданий. Он не заменяет официальный клинический или стандартизированный IQ-тест."),
    ]

    b = InlineKeyboardBuilder()
    b.button(text=bi(lang, "🔄 Qayta topshirish", "🔄 Пройти снова"), callback_data="iq:start")
    b.button(text=bi(lang, "💰 Balans", "💰 Баланс"), callback_data="wallet:open")
    b.button(text=bi(lang, "🧠 Boshqa testlar", "🧠 Другие тесты"), callback_data="nav:menu")
    b.adjust(1)
    await callback.message.edit_text("\n".join(text), reply_markup=b.as_markup())
