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
        "Jahon psixologiyasida qo‘llanadigan testlar — o‘zbek tilida.\n\n"
        "✅ Har bir test qaysi ilmiy manbadan olingani ochiq yozilgan\n"
        "⚡️ Natijani darhol olasiz\n"
        "🔒 Javoblaringizni hech kim ko‘rmaydi\n\n"
        "Qaysi biridan boshlaymiz? 👇",
        "🧠 <b>Психологические тесты</b>\n\n"
        "Тесты, которые используют в мировой психологии — на русском.\n\n"
        "✅ У каждого теста открыто указан научный источник\n"
        "⚡️ Результат сразу после теста\n"
        "🔒 Ваши ответы никто не увидит\n\n"
        "С какого начнём? 👇",
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
    # --- To'lov ------------------------------------------------------------
    "paywall": L(
        "🔒 <b>{title}</b>\n\n"
        "Bu test pullik.\n\n"
        "💳 Narxi: <b>{price} so‘m</b>\n"
        "♾ To‘lov bir marta — test siz uchun doim ochiq qoladi\n"
        "⚡️ To‘lovdan so‘ng darhol ochiladi\n\n"
        "To‘lov <b>Click</b> orqali: bank kartasi yoki Click Up ilovasi.",
        "🔒 <b>{title}</b>\n\n"
        "Этот тест платный.\n\n"
        "💳 Цена: <b>{price} сум</b>\n"
        "♾ Оплата разовая — тест останется открытым навсегда\n"
        "⚡️ Откроется сразу после оплаты\n\n"
        "Оплата через <b>Click</b>: банковская карта или приложение Click Up.",
    ),
    "paywall_all": L(
        "\n\n🎁 <b>Barcha testlar paketi — {price} so‘m</b>\n"
        "Bittalab olgandan arzonroq: hamma test bir yo‘la ochiladi.",
        "\n\n🎁 <b>Пакет «Все тесты» — {price} сум</b>\n"
        "Дешевле, чем по одному: открываются сразу все тесты.",
    ),
    "pay_title_all": L("Barcha testlar", "Все тесты"),
    "btn_pay": L("💳 Click orqali to‘lash", "💳 Оплатить через Click"),
    "btn_pay_all": L("🎁 Barcha testlar — {price} so‘m", "🎁 Все тесты — {price} сум"),
    "btn_pay_open": L("💳 To‘lovga o‘tish", "💳 Перейти к оплате"),
    "btn_pay_invoice": L("📲 Click Up ilovamga yuborish", "📲 Отправить в Click Up"),
    "btn_pay_check": L("✅ To‘ladim, tekshirish", "✅ Я оплатил, проверить"),
    "pay_created": L(
        "💳 <b>To‘lov</b>\n\n"
        "{product}\n"
        "Summa: <b>{price} so‘m</b>\n"
        "Buyurtma: <code>#{payment_id}</code>\n\n"
        "1️⃣ «To‘lovga o‘tish» tugmasini bosing\n"
        "2️⃣ Click sahifasida to‘lovni yakunlang\n"
        "3️⃣ Botga qayting — test o‘zi ochiladi\n\n"
        "<i>To‘lov o‘tishi bilan bot sizga xabar beradi. Agar 1–2 daqiqada "
        "xabar kelmasa, «To‘ladim» tugmasini bosing.</i>",
        "💳 <b>Оплата</b>\n\n"
        "{product}\n"
        "Сумма: <b>{price} сум</b>\n"
        "Заказ: <code>#{payment_id}</code>\n\n"
        "1️⃣ Нажмите «Перейти к оплате»\n"
        "2️⃣ Завершите оплату на странице Click\n"
        "3️⃣ Вернитесь в бот — тест откроется сам\n\n"
        "<i>Бот сообщит, как только оплата пройдёт. Если через 1–2 минуты "
        "сообщения нет — нажмите «Я оплатил».</i>",
    ),
    "pay_success": L(
        "✅ <b>To‘lov qabul qilindi!</b>\n\n"
        "{product} ochildi. Omad tilaymiz 👇",
        "✅ <b>Оплата принята!</b>\n\n"
        "{product} — доступ открыт. Удачи 👇",
    ),
    "pay_pending": L(
        "⏳ To‘lov hali tasdiqlanmadi.\n\n"
        "Endigina to‘lagan bo‘lsangiz, bir daqiqa kuting va qayta bosing. "
        "Pul yechilgan bo‘lsa-yu test ochilmasa, /yordam orqali yozing.",
        "⏳ Оплата пока не подтверждена.\n\n"
        "Если вы только что оплатили, подождите минуту и нажмите снова. "
        "Если деньги списаны, а тест не открылся — напишите через /yordam.",
    ),
    "pay_unavailable": L(
        "⚠️ To‘lov tizimi hozircha ishlamayapti. Birozdan keyin urinib ko‘ring.",
        "⚠️ Платёжная система временно недоступна. Попробуйте чуть позже.",
    ),
    "pay_already": L(
        "✅ Bu test sizda allaqachon ochiq.",
        "✅ Этот тест у вас уже открыт.",
    ),
    "pay_ask_phone": L(
        "📲 Click Up ilovangizga hisob yuboramiz.\n\n"
        "Click'ga bog‘langan telefon raqamingizni yuboring:\n"
        "<code>998901234567</code> yoki <code>+998 90 123 45 67</code>",
        "📲 Отправим счёт в ваше приложение Click Up.\n\n"
        "Пришлите номер телефона, привязанный к Click:\n"
        "<code>998901234567</code> или <code>+998 90 123 45 67</code>",
    ),
    "pay_phone_bad": L(
        "❌ Raqam noto‘g‘ri. O‘zbekiston raqamini yuboring, masalan "
        "<code>998901234567</code>.",
        "❌ Неверный номер. Пришлите узбекистанский номер, например "
        "<code>998901234567</code>.",
    ),
    "pay_invoice_sent": L(
        "📲 Hisob <b>{phone}</b> raqamiga yuborildi.\n\n"
        "Click Up ilovasini oching va to‘lovni tasdiqlang. To‘lov o‘tishi "
        "bilan test shu yerda ochiladi.",
        "📲 Счёт отправлен на номер <b>{phone}</b>.\n\n"
        "Откройте приложение Click Up и подтвердите оплату. Как только "
        "оплата пройдёт, тест откроется здесь.",
    ),
    "pay_invoice_failed": L(
        "❌ Hisob yuborilmadi. Yuqoridagi «To‘lovga o‘tish» tugmasidan "
        "foydalaning — u har doim ishlaydi.",
        "❌ Счёт не отправлен. Воспользуйтесь кнопкой «Перейти к оплате» "
        "выше — она работает всегда.",
    ),
    "btn_open_test": L("▶️ Testni boshlash", "▶️ Начать тест"),
    "card_price": L(
        "\n💳 Narxi: <b>{price} so‘m</b> (bir marta)",
        "\n💳 Цена: <b>{price} сум</b> (разово)",
    ),
    "card_free": L("\n🎁 <b>Bepul</b>", "\n🎁 <b>Бесплатно</b>"),
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


def money(amount: int) -> str:
    """9900 -> "9 900". Uch xonadan ajratib yozilgan raqam o'qishga oson."""
    return f"{amount:,}".replace(",", " ")
