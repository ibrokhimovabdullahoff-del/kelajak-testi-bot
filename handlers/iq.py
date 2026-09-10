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
    ("sequence", L("Ketma-ketlikni davom ettiring: 3, 8, 15, 24, 35, ?", "Продолжите ряд: 3, 8, 15, 24, 35, ?"), ['48', '46', '50', '52', '54'], ['48', '46', '50', '52', '54'], 0, 1),
    ("logic", L("Barcha TARlar NOK. Hech bir NOK ko‘k emas. TAR ko‘k bo‘lishi mumkinmi?", "Все TAR являются NOK. Ни один NOK не синий. Может ли TAR быть синим?"), ['Ha, albatta', 'Yo‘q, mumkin emas', 'Faqat ayrimlari', 'Ma’lumot yetarli emas', 'Faqat kechasi'], ['Да, обязательно', 'Нет, невозможно', 'Только некоторые', 'Данных недостаточно', 'Только ночью'], 1, 2),
    ("logic", L("Ali Bekdan balandroq. Bek Diyordan balandroq. Eng past bo‘yli kim?", "Али выше Бека. Бек выше Диёра. Кто самый низкий?"), ['Ali', 'Bek', 'Diyor', 'Aniqlab bo‘lmaydi', 'Uchovlari teng'], ['Али', 'Бек', 'Диёp', 'Нельзя определить', 'Все трое равны'], 2, 2),
    ("sequence", L("B, E, J, Q, ? qatorida keyingi harf qaysi?", "Какая буква следующая: B, E, J, Q, ?"), ['X', 'Y', 'A', 'Z', 'C'], ['X', 'Y', 'A', 'Z', 'C'], 3, 1),
    ("numeric", L("Qaysi son boshqalaridan farq qiladi: 27, 64, 125, 216, 250?", "Какое число отличается: 27, 64, 125, 216, 250?"), ['27', '64', '125', '216', '250'], ['27', '64', '125', '216', '250'], 4, 1),
    ("numeric", L("3 ta bir xil quti 24 kg. Shu qutilarning bittasi necha kg?", "3 одинаковые коробки весят 24 кг. Сколько весит одна коробка?"), ['8', '6', '10', '12', '14'], ['8', '6', '10', '12', '14'], 0, 1),
    ("sequence", L("2, 5, 10, 17, 26, ? ketma-ketlikda keyingi son?", "Какое число следующее: 2, 5, 10, 17, 26, ?"), ['36', '37', '38', '39', '40'], ['36', '37', '38', '39', '40'], 1, 1),
    ("logic", L("Agar karta qizil bo‘lsa, unda uchburchak bor. Kartada uchburchak yo‘q. Qaysi xulosa aniq?", "Если карта красная, на ней есть треугольник. На карте нет треугольника. Какой вывод точен?"), ['Karta ko‘k', 'Karta bo‘sh', 'Karta qizil emas', 'Buni bilib bo‘lmaydi', 'Karta albatta qizil'], ['Карта синяя', 'Карта пустая', 'Карта не красная', 'Нельзя определить', 'Карта обязательно красная'], 2, 2),
    ("logic", L("Uch kishi haqida: Ali “Bek yolg‘on gapiryapti” deydi. Bek “Diyor yolg‘on gapiryapti” deydi. Diyor “Ali va Bek ikkalasi ham yolg‘on gapiryapti” deydi. Faqat bittasi yolg‘onchi. Kim?", "Трое говорят: Али: «Бек лжёт». Бек: «Диёp лжёт». Диёp: «Али и Бек оба лгут». Лжёт только один. Кто?"), ['Ali', 'Diyor', 'Aniqlab bo‘lmaydi', 'Bek', 'Uchovlari'], ['Али', 'Диёp', 'Нельзя определить', 'Бек', 'Все трое'], 3, 2),
    ("spatial", L("Soat 4:40 da soat strelkasi qayerda bo‘ladi?", "Где находится часовая стрелка в 4:40?"), ['Aynan 4 da', '3 va 4 oralig‘ida', 'Aynan 5 da', '5 va 6 oralig‘ida', '4 va 5 oralig‘ida, 5 ga yaqin'], ['Ровно на 4', 'Между 3 и 4', 'Ровно на 5', 'Между 5 и 6', 'Между 4 и 5, ближе к 5'], 4, 2),
    ("verbal", L("Xarita : joylashuv = soat : ?"), ["Vaqt", "Sana", "Masofa", "Ob-havo", "Tezlik"], ["Время", "Дата", "Расстояние", "Погода", "Скорость"], 0, 1),
    ("applied", L("4 ta printer 6 daqiqada 24 bet chiqarsa, bir xil tezlikda 3 ta printer 8 daqiqada nechta bet chiqaradi?", "Если 4 принтера за 6 минут печатают 24 страницы, сколько напечатают 3 принтера за 8 минут при той же скорости?"), ["18", "24", "30", "32", "36"], ["18", "24", "30", "32", "36"], 1, 1),
    ("probability", L("Ikki tanga bir marta tashlanganda kamida bittasi gerb tushish ehtimoli qancha?", "При броске двух монет какова вероятность, что выпадет хотя бы один орёл?"), ["1/2", "1/4", "3/4", "1/3", "2/3"], ["1/2", "1/4", "3/4", "1/3", "2/3"], 2, 1),
    ("spatial", L("Sharqqa qarab turibsiz. Chapga, keyin o‘ngga burildingiz. Hozir qaysi tomonga qarayapsiz?", "Вы смотрите на восток. Поворачиваете налево, затем направо. Куда смотрите?"), ['G‘arb', 'Shimol', 'Sharq', 'Janub', 'Shimoli-sharq'], ['Запад', 'Север', 'Восток', 'Юг', 'Северо-восток'], 2, 2),
    ("verbal", L("Bir odamning singlisining o‘g‘li unga kim bo‘ladi?", "Кем человеку приходится сын его сестры?"), ['Amaki', 'Aka-uka', 'Jiyan', 'Amakivachcha', 'Ota'], ['Дядя', 'Брат', 'Племянник', 'Двоюродный брат', 'Отец'], 2, 1),
    ("numeric", L("4 → 18, 5 → 27, 6 → 38, 7 → ? qaysi qoida mos?", "4 → 18, 5 → 27, 6 → 38, 7 → ? Какое правило подходит?"), ['49', '50', '51', '52', '53'], ['49', '50', '51', '52', '53'], 2, 1),
    ("logic", L("Ba’zi A lar B. Barcha B lar C. Qaysi xulosa aniq?", "Некоторые A являются B. Все B являются C. Какой вывод точен?"), ['Ba’zi A lar C', 'Barcha A lar C', 'Hech bir A C emas', 'Barcha C lar A', 'Ma’lumot yetarli emas'], ['Некоторые A являются C', 'Все A являются C', 'Ни один A не является C', 'Все C являются A', 'Данных недостаточно'], 0, 2),
    ("verbal", L("CAT → DBU qoidasi bo‘yicha CHAIR qanday yoziladi?", "По правилу CAT → DBU как будет записано CHAIR?"), ['DJBIS', 'DIBJR', 'DIBJS', 'EJCKT', 'CHBHQ'], ['DJBIS', 'DIBJR', 'DIBJS', 'EJCKT', 'CHBHQ'], 2, 2),
    ("spatial", L("Qog‘oz bir marta teng ikkiga buklandi. Buklangan qog‘oz teshib qo‘yildi. Ochilganda nechta teshik bo‘ladi?", "Лист бумаги сложили пополам один раз и пробили. Сколько отверстий будет после разворачивания?"), ['2 ta', '1 ta', '3 ta', '4 ta', 'Hech biri'], ['2', '1', '3', '4', 'Ни одного'], 0, 2),
    ("sequence", L("1, 4, 10, 19, 31, ? ketma-ketlikda keyingi son?", "Какое число следующее: 1, 4, 10, 19, 31, ?"), ['45', '47', '48', '49', '46'], ['45', '47', '48', '49', '46'], 4, 1),
    ("logic", L("A, B, C, D, E tartibida: A C dan oldin, B D dan oldin, C E dan oldin. Kim birinchi bo‘lishi mumkin?", "В порядке A, B, C, D, E: A раньше C, B раньше D, C раньше E. Кто может быть первым?"), ['A yoki B', 'Faqat A', 'Faqat B', 'C', 'E'], ['A или B', 'Только A', 'Только B', 'C', 'E'], 0, 2),
    ("numeric", L("Otaning yoshi o‘g‘lining yoshidan 3 baravar katta. 8 yildan keyin ota o‘g‘lidan 2 baravar katta bo‘ladi. O‘g‘il hozir nechada?", "Отец втрое старше сына. Через 8 лет отец будет вдвое старше сына. Сколько лет сыну сейчас?"), ['6', '8', '10', '12', '14'], ['6', '8', '10', '12', '14'], 1, 1),
    ("sequence", L("1, 2, 6, 24, 120, ? ketma-ketlikda keyingi son?", "Какое число следующее: 1, 2, 6, 24, 120, ?"), ['240', '480', '720', '600', '840'], ['240', '480', '720', '600', '840'], 2, 1),
    ("logic", L("Ba’zi mushuklar qora. Hech bir qora narsa oq emas. Qaysi xulosa aniq?", "Некоторые кошки чёрные. Ни одна чёрная вещь не белая. Какой вывод точен?"), ['Ba’zi mushuklar oq emas', 'Barcha mushuklar oq emas', 'Hech bir mushuk qora emas', 'Barcha oq narsalar mushuk', 'Ma’lumot yetarli emas'], ['Некоторые кошки не белые', 'Все кошки не белые', 'Ни одна кошка не чёрная', 'Все белые вещи — кошки', 'Данных недостаточно'], 0, 2),
    ("applied", L("Poyezd 14:35 da jo‘nab, 16:20 da yetib keldi. Yo‘l qancha davom etgan?", "Поезд отправился в 14:35 и прибыл в 16:20. Сколько длилась поездка?"), ['1 soat 35 daqiqa', '2 soat', '1 soat 55 daqiqa', '1 soat 45 daqiqa', '2 soat 15 daqiqa'], ['1 час 35 минут', '2 часа', '1 час 55 минут', '1 час 45 минут', '2 часа 15 минут'], 3, 1),
    ("numeric", L("Ketma-ket keladigan uchta toq sonning yig‘indisi 45. O‘rtadagi son nechaga teng?", "Сумма трёх последовательных нечётных чисел равна 45. Чему равно среднее число?"), ['13', '17', '11', '19', '15'], ['13', '17', '11', '19', '15'], 4, 1),
    ("logic", L("Faqat bittasi emas, aynan ikkita gap rost: A: “B yolg‘on”. B: “C yolg‘on”. C: “A rost”. Qaysi gap yolg‘on?", "Ровно два утверждения истинны: A: «B лжёт». B: «C лжёт». C: «A говорит правду». Какое утверждение ложно?"), ['A', 'B', 'C', 'Hammasi rost', 'Aniqlab bo‘lmaydi'], ['A', 'B', 'C', 'Все истинны', 'Нельзя определить'], 1, 2),
    ("numeric", L("Har bir qatorda uchinchi son birinchi ikki sonning yig‘indisi: 2,3,5; 4,6,10; 7,8, ? . Noma’lum son nechaga teng?", "В каждой строке третье число равно сумме первых двух: 2,3,5; 4,6,10; 7,8, ?. Чему равно неизвестное?"), ['14', '16', '15', '17', '18'], ['14', '16', '15', '17', '18'], 2, 2),
    ("spatial", L("3 km shimolga, 3 km sharqqa, 3 km janubga yurdingiz. Boshlang‘ich nuqtaga nisbatan qayerdasiz?", "Вы прошли 3 км на север, 3 км на восток и 3 км на юг. Где вы относительно старта?"), ['G‘arbda', 'Sharqda', 'Shimolda', 'Janubda', 'Boshlang‘ich joyda'], ['На западе', 'На востоке', 'На севере', 'На юге', 'На старте'], 1, 2),
    ("logic", L("Qaysi biri boshqalardan farq qiladi: kvadrat, uchburchak, doira, to‘g‘ri to‘rtburchak, kub?", "Что отличается: квадрат, треугольник, круг, прямоугольник, куб?"), ['Kvadrat', 'Uchburchak', 'Doira', 'To‘g‘ri to‘rtburchak', 'Kub'], ['Квадрат', 'Треугольник', 'Круг', 'Прямоугольник', 'Куб'], 4, 2),
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
    title = bi(lang, "Premium IQ testi", "Премиум IQ-тест")
    q = QUESTIONS[index][1].get(lang, QUESTIONS[index][1]["uz"])
    return f"{IQ_EMOJI} <b>{title}</b>\n\n{progress(index)}\n<b>{index + 1} / {len(QUESTIONS)}</b>\n\n<b>{html.escape(q)}</b>"

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

    b = InlineKeyboardBuilder()
    b.button(text=bi(lang, "🔄 Qayta topshirish", "🔄 Пройти снова"), callback_data="iq:start")
    b.button(text=bi(lang, "💰 Balans", "💰 Баланс"), callback_data="wallet:open")
    b.button(text=bi(lang, "🧠 Boshqa testlar", "🧠 Другие тесты"), callback_data="nav:menu")
    b.adjust(1)
    await callback.message.edit_text("\n".join(text), reply_markup=b.as_markup())
