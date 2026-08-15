"""Interfeys matnlari — o'zbekcha va ruscha.

Yangi til qo'shish uchun L() ga uchinchi kalit qo'shish va LANGS ni
yangilash kifoya.
"""
from psytests.base import L

LANGS = {"uz": "🇺🇿 O‘zbekcha", "ru": "🇷🇺 Русский"}
DEFAULT_LANG = "uz"

STRINGS: dict[str, dict[str, str]] = {
    # --- Til ---------------------------------------------------------------
    "choose_language": L(
        "Tilni tanlang / Выберите язык:",
        "Tilni tanlang / Выберите язык:",
    ),
    "language_set": L(
        "✅ Til o‘zbekchaga o‘zgartirildi.",
        "✅ Язык переключён на русский.",
    ),
    # --- Bosh menyu --------------------------------------------------------
    "menu": L(
        "🧠 <b>Psixologik testlar</b>\n\n"
        "Bu yerda o‘ylab topilgan «bashorat» testlari yo‘q. Har bir test "
        "qaysi ilmiy manbaga asoslangani ochiq ko‘rsatilgan — va qaysi biri "
        "validatsiyadan o‘tgan asbob, qaysi biri mualliflik so‘rovnomasi "
        "ekani ham.\n\n"
        "Testni tanlang 👇",
        "🧠 <b>Психологические тесты</b>\n\n"
        "Здесь нет выдуманных «предсказаний». У каждого теста открыто указан "
        "научный источник — и то, какой из них валидированный инструмент, "
        "а какой авторский опросник.\n\n"
        "Выберите тест 👇",
    ),
    "btn_results": L("📈 Mening natijalarim", "📈 Мои результаты"),
    "btn_about": L("ℹ️ Bot haqida", "ℹ️ О боте"),
    "btn_language": L("🌐 Til / Язык", "🌐 Til / Язык"),
    "btn_menu": L("🏠 Bosh menyu", "🏠 Главное меню"),
    "btn_back": L("⬅️ Orqaga", "⬅️ Назад"),
    "btn_cancel": L("❌ Bekor qilish", "❌ Отменить"),
    "btn_start_test": L("▶️ Boshlash", "▶️ Начать"),
    "btn_retake": L("🔄 Qayta topshirish", "🔄 Пройти заново"),
    "btn_other_tests": L("🧠 Boshqa testlar", "🧠 Другие тесты"),
    "btn_share": L("📤 Do‘stlarga ulashish", "📤 Поделиться"),
    "btn_source": L("📚 Manba", "📚 Источник"),
    # --- Test kartochkasi --------------------------------------------------
    "badge_validated": L(
        "✅ Validatsiyadan o‘tgan asbob",
        "✅ Валидированный инструмент",
    ),
    "badge_composite": L(
        "📝 Mualliflik so‘rovnomasi",
        "📝 Авторский опросник",
    ),
    "card": L(
        "{emoji} <b>{title}</b>\n\n"
        "{intro}\n\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "{badge}\n"
        "📊 {count} ta savol · ⏱ {minutes}",
        "{emoji} <b>{title}</b>\n\n"
        "{intro}\n\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "{badge}\n"
        "📊 {count} вопросов · ⏱ {minutes}",
    ),
    "source_title": L("📚 <b>Manba va uslubiyot</b>", "📚 <b>Источник и методика</b>"),
    # --- Yosh --------------------------------------------------------------
    "choose_age_self": L(
        "Yoshingizni tanlang — yakuniy maslahat shunga moslashtiriladi 👇",
        "Выберите свой возраст — итоговый совет подстроится под него 👇",
    ),
    "choose_age_child": L(
        "Farzandingiz nechchi yoshda? Maslahatlar shunga moslashtiriladi 👇",
        "Сколько лет вашему ребёнку? Советы подстроятся под возраст 👇",
    ),
    # --- Savollar ----------------------------------------------------------
    "question": L(
        "❓ <b>Savol {index} / {total}</b>\n<code>{bar}</code>\n\n<b>{text}</b>",
        "❓ <b>Вопрос {index} / {total}</b>\n<code>{bar}</code>\n\n<b>{text}</b>",
    ),
    "already_answered": L(
        "Bu savolga javob berilgan.",
        "На этот вопрос уже дан ответ.",
    ),
    "stale_test": L(
        "Bu test allaqachon yakunlangan.",
        "Этот тест уже завершён.",
    ),
    "press_buttons": L(
        "Iltimos, yuqoridagi tugmalardan birini tanlang 👆",
        "Пожалуйста, выберите один из вариантов выше 👆",
    ),
    "analyzing": L("Tahlil qilinmoqda…", "Анализируем…"),
    "finished": L(
        "✅ Barcha savollarga javob berildi.",
        "✅ Все вопросы пройдены.",
    ),
    "cancelled": L(
        "❌ Test bekor qilindi.",
        "❌ Тест отменён.",
    ),
    # --- Natija ------------------------------------------------------------
    "res_strengths": L("KUCHLI TOMONLARINGIZ", "ВАШИ СИЛЬНЫЕ СТОРОНЫ"),
    "res_growth": L("NIMA USTIDA ISHLASH KERAK", "НАД ЧЕМ РАБОТАТЬ"),
    "res_advice": L("Yoshingizga mos maslahat", "Совет по вашему возрасту"),
    "res_advice_child": L(
        "Farzandingiz yoshiga mos maslahat",
        "Совет по возрасту вашего ребёнка",
    ),
    "res_code": L("SIZNING KODINGIZ", "ВАШ КОД"),
    "res_all_areas": L("BARCHA YO‘NALISHLAR", "ВСЕ НАПРАВЛЕНИЯ"),
    "lvl_high": L("yuqori", "высокий"),
    "lvl_mid": L("o‘rta", "средний"),
    "lvl_low": L("past", "низкий"),
    # --- Ogohlantirishlar ---------------------------------------------------
    "disclaimer_validated": L(
        "⚠️ Bu tashxis emas va kelajakni aytmaydi. Big Five odamni "
        "yaxshi-yomonga ajratmaydi — u odatiy xulqingizni ko‘rsatadi, "
        "xulq esa vaqt bilan o‘zgaradi.",
        "⚠️ Это не диагноз и не предсказание. Big Five не делит людей на "
        "хороших и плохих — он показывает привычное поведение, а оно со "
        "временем меняется.",
    ),
    "disclaimer_composite": L(
        "⚠️ Bu tekshirilgan asbob emas va kelajakni aytmaydi. U hozirgi "
        "odatlaringizni ko‘rsatadi: odat o‘zgarsa, ball ham o‘zgaradi.",
        "⚠️ Это не проверенный инструмент и не предсказание. Он показывает "
        "ваши нынешние привычки: изменятся привычки — изменится балл.",
    ),
    "disclaimer_career": L(
        "⚠️ Bu test qobiliyatni emas, <b>qiziqishni</b> o‘lchaydi. Kasb "
        "tanlashda mehnat bozori va ko‘nikma ham hisobga olinadi.",
        "⚠️ Тест измеряет <b>интерес</b>, а не способности. При выборе "
        "профессии учитываются ещё рынок труда и навыки.",
    ),
    # --- Tarix -------------------------------------------------------------
    "history_title": L(
        "📈 <b>Sizning natijalaringiz</b>",
        "📈 <b>Ваши результаты</b>",
    ),
    "history_empty": L(
        "Sizda hali natija yo‘q. Testni tanlash uchun /start bosing.",
        "У вас пока нет результатов. Нажмите /start, чтобы выбрать тест.",
    ),
    # --- Bot haqida --------------------------------------------------------
    "about": L(
        "ℹ️ <b>Bot haqida</b>\n\n"
        "Bu botdagi testlar ikki toifaga bo‘linadi va biz buni yashirmaymiz.\n\n"
        "✅ <b>Validatsiyadan o‘tgan asbob</b>\n"
        "«Big Five — shaxsiyat profili» testi International Personality Item "
        "Pool (IPIP) ning Big-Five Factor Markers to‘plamidan olingan "
        "(Goldberg, 1992). IPIP elementlari ochiq mulk — ular minglab ilmiy "
        "tadqiqotlarda ishlatilgan.\n\n"
        "📝 <b>Mualliflik so‘rovnomalari</b>\n"
        "«Kelajak salohiyati», «Farzand salohiyati» va «Kasb yo‘nalishi» — "
        "bizning so‘rovnomalarimiz. Ular nashr etilgan ilmiy topilmalarga "
        "tayanadi (Duckworth, Dweck, Moffitt, Rotter, Holland, Harvard Grant "
        "Study), lekin alohida psixometrik sinovdan o‘tmagan.\n\n"
        "Nega bu farq muhim? Chunki «ilmiy test» degan yorliqni har kim "
        "yopishtira oladi. Biz qaysi biri haqiqatan validatsiyadan o‘tganini "
        "ochiq aytamiz — har bir test ichida «📚 Manba» tugmasi bor.\n\n"
        "⚠️ <b>Muhim</b>\n"
        "Hech bir test kelajakni bashorat qilmaydi va tibbiy yoki psixologik "
        "tashxis qo‘ymaydi. Natija — hozirgi odatlaringiz surati, taqdir "
        "emas.",
        "ℹ️ <b>О боте</b>\n\n"
        "Тесты в этом боте делятся на две категории, и мы это не скрываем.\n\n"
        "✅ <b>Валидированный инструмент</b>\n"
        "Тест «Big Five — профиль личности» взят из набора Big-Five Factor "
        "Markers международного пула International Personality Item Pool "
        "(IPIP, Goldberg, 1992). Пункты IPIP — общественное достояние, они "
        "использованы в тысячах научных исследований.\n\n"
        "📝 <b>Авторские опросники</b>\n"
        "«Потенциал будущего», «Потенциал ребёнка» и «Профориентация» — наши "
        "опросники. Они опираются на опубликованные научные результаты "
        "(Duckworth, Dweck, Moffitt, Rotter, Holland, Гарвардское Grant "
        "Study), но отдельную психометрическую проверку не проходили.\n\n"
        "Почему эта разница важна? Потому что ярлык «научный тест» может "
        "наклеить кто угодно. Мы прямо говорим, что именно валидировано — "
        "внутри каждого теста есть кнопка «📚 Источник».\n\n"
        "⚠️ <b>Важно</b>\n"
        "Ни один тест не предсказывает будущее и не ставит медицинский или "
        "психологический диагноз. Результат — снимок ваших нынешних "
        "привычек, а не судьба.",
    ),
    "help": L(
        "<b>Buyruqlar</b>\n\n"
        "/start — testlar menyusi\n"
        "/natijalar — oldingi natijalaringiz\n"
        "/til — tilni o‘zgartirish\n"
        "/haqida — bot va manbalar haqida\n"
        "/bekor — joriy testni bekor qilish",
        "<b>Команды</b>\n\n"
        "/start — меню тестов\n"
        "/natijalar — ваши прошлые результаты\n"
        "/til — сменить язык\n"
        "/haqida — о боте и источниках\n"
        "/bekor — отменить текущий тест",
    ),
    "share_text": L(
        "Men psixologik test topshirdim 🧠 Sen ham sinab ko‘r",
        "Я прошёл психологический тест 🧠 Попробуй и ты",
    ),
}


def t(key: str, lang: str, **kwargs) -> str:
    text = STRINGS[key].get(lang) or STRINGS[key][DEFAULT_LANG]
    return text.format(**kwargs) if kwargs else text


def tr(value: dict[str, str], lang: str) -> str:
    """Ikki tilli dict dan tegishli tilni oladi."""
    return value.get(lang) or value[DEFAULT_LANG]
