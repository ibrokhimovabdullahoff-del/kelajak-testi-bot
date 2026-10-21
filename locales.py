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
    # --- Natija sertifikati (rasm) ----------------------------------------
    "iq_title": L("Premium IQ testi", "Премиум IQ-тест"),
    "card_kicker": L("NATIJA SERTIFIKATI", "СЕРТИФИКАТ РЕЗУЛЬТАТА"),
    "card_label_iq": L("Taxminiy IQ", "Примерный IQ"),
    "card_label_strength": L("Eng kuchli tomoningiz", "Ваша сильная сторона"),
    "card_label_type": L("Shaxsiyat turingiz", "Ваш тип личности"),
    "card_label_child": L("Farzandingizning kuchli tomoni", "Сильная сторона ребёнка"),
    "card_label_career": L("Kasb yo‘nalishingiz", "Ваше направление"),
    "card_second": L("Yana bir kuchli tomoningiz: {name}", "Ещё одна сильная сторона: {name}"),
    "card_second_child": L("Yana bir kuchli tomoni: {name}", "Ещё одна сильная сторона: {name}"),
    "card_career_more": L("Sizga yaqin yo‘nalishlar: {first}, {second}", "Вам также близко: {first}, {second}"),
    "card_iq_best": L("Eng kuchli tomoningiz: {name}", "Сильнее всего: {name}"),
    "card_iq_generic": L(
        "Rasmli mantiq topshiriqlarida kuchingizni sinab ko‘rdingiz.",
        "Вы проверили свою силу в логических задачах в картинках.",
    ),
    "card_index": L("{score} / 100 ball", "{score} / 100 баллов"),
    "card_label_correct": L("To‘g‘ri javoblar", "Правильных ответов"),
    "card_score": L("{correct} / {total}", "{correct} / {total}"),
    "card_score_line": L(
        "{total}\u00a0ta topshiriqdan {correct}\u00a0tasini to‘g‘ri yechdingiz.",
        "Верно решено {correct} из {total}\u00a0заданий.",
    ),
    "card_holland": L("Holland kodi: {code}", "Код Холланда: {code}"),
    "card_fallback_line": L(
        "Bir haftadan keyin qayta topshirib, o‘zgarishni ko‘ring.",
        "Пройдите тест снова через неделю и увидите разницу.",
    ),
    "card_challenge": L(
        "Siz bundan ham yaxshiroq qila olasizmi?",
        "Ты сможешь лучше?",
    ),
    "card_cta": L("Testni Telegram’da topshiring", "Пройди тест в Telegram"),
    "card_caption": L(
        "🏅 <b>Sizning natija sertifikatingiz</b>\n\n"
        "Stories’ga joylang va do‘stlaringizni ham sinab ko‘ring 👇",
        "🏅 <b>Ваш сертификат результата</b>\n\n"
        "Выложите в сторис и бросьте вызов друзьям 👇",
    ),
    "card_file_caption": L("📥 Sertifikat — to‘liq sifatda", "📥 Сертификат — в полном качестве"),
    "btn_card_download": L("📥 Yuklab olish (to‘liq sifat)", "📥 Скачать (полное качество)"),
    # --- Hisobot: qo'shimchalar -------------------------------------------
    "res_percentile": L(
        "📊 Siz bu testni topshirganlarning <b>{pct} foizi</b>dan yaxshiroq javob berdingiz ({n} kishi).",
        "📊 Вы ответили лучше, чем <b>{pct}%</b> людей, прошедших этот тест ({n} чел.).",
    ),
    "res_percentile_low": L(
        "📊 Bu testni allaqachon {n} kishi topshirgan. Bir haftadan keyin qayta topshirib, natijangizni oshiring.",
        "📊 Этот тест уже прошли {n} чел. Пройдите его снова через неделю и улучшите результат.",
    ),
    "res_everyday": L("💡 <i>Hayotda:</i> {text}", "💡 <i>В жизни:</i> {text}"),
    "res_exercise": L("✍️ <i>Mashq:</i> {text}", "✍️ <i>Упражнение:</i> {text}"),
    "res_zero": L("🌱 o‘sish nuqtasi", "🌱 точка роста"),
    "res_next_title": L("KEYINGI QADAM", "СЛЕДУЮЩИЙ ШАГ"),
    "res_next_retake": L(
        "📅 Bir haftadan keyin testni qayta topshiring va natijani bugungisi bilan "
        "solishtiring — ikkalasi ham «📈 Mening natijalarim» bo‘limida saqlanadi.",
        "📅 Пройдите тест снова через неделю и сравните с сегодняшним результатом — "
        "оба сохранятся в разделе «📈 Мои результаты».",
    ),
    "res_next_other": L(
        "👉 Keyingi test: <b>{title}</b> — pastdagi tugma orqali oching.",
        "👉 Следующий тест: <b>{title}</b> — откройте кнопкой ниже.",
    ),
    "btn_next_test": L("👉 {title}", "👉 {title}"),
    # --- IQ hisoboti ------------------------------------------------------
    "iq_res_title": L("🧠 <b>PREMIUM IQ TESTI — NATIJA</b>", "🧠 <b>ПРЕМИУМ IQ-ТЕСТ — РЕЗУЛЬТАТ</b>"),
    "iq_res_estimate": L("🧠 Taxminiy IQ: <b>≈ {iq}</b>", "🧠 Примерный IQ: <b>≈ {iq}</b>"),
    "iq_res_range": L("<i>ehtimoliy oraliq: {low}–{high}</i>", "<i>вероятный диапазон: {low}–{high}</i>"),
    "iq_res_level": L("{emoji} Daraja: <b>{name}</b>", "{emoji} Уровень: <b>{name}</b>"),
    "iq_res_correct": L(
        "🎯 To‘g‘ri javoblar: <b>{correct} / {total}</b>",
        "🎯 Правильных ответов: <b>{correct} / {total}</b>",
    ),
    "iq_res_time": L("⏱ Sarflangan vaqt: {duration}", "⏱ Затраченное время: {duration}"),
    "iq_res_rushed": L(
        "⚠️ Juda tez yechdingiz — ba’zi javoblar tavakkal belgilangan bo‘lishi mumkin.",
        "⚠️ Вы ответили очень быстро — часть ответов могла быть наугад.",
    ),
    "dur_min_sec": L("{m} daqiqa {s} soniya", "{m} мин {s} сек"),
    "dur_sec": L("{s} soniya", "{s} сек"),
    # --- Do'st taklifi va xatolar tahlili ---------------------------------
    "ref_offer": L(
        "🔍 <b>Xatolaringizning batafsil tahlili tayyor!</b>\n\n"
        "Qaysi savollarda adashganingiz, to‘g‘ri javob va nima uchun aynan u "
        "to‘g‘ri ekani.\n\n"
        "🎁 Ochish uchun <b>1 ta do‘stingizni</b> taklif qiling. U shu havola "
        "orqali botni ishga tushirishi bilan tahlil siz uchun <b>butunlay</b> "
        "ochiladi:\n\n{link}",
        "🔍 <b>Подробный разбор ваших ошибок готов!</b>\n\n"
        "В каких вопросах вы ошиблись, правильный ответ и почему именно он "
        "верный.\n\n"
        "🎁 Чтобы открыть, пригласите <b>1 друга</b>. Как только он запустит "
        "бота по этой ссылке, разбор откроется для вас <b>навсегда</b>:\n\n{link}",
    ),
    "ref_offer_unlocked": L(
        "🔍 <b>Xatolaringiz tahlili siz uchun ochiq.</b>\n\n"
        "Qaysi savollarda adashganingizni va to‘g‘ri javobni ko‘ring.",
        "🔍 <b>Разбор ошибок для вас открыт.</b>\n\n"
        "Посмотрите, где вы ошиблись и какой ответ правильный.",
    ),
    "ref_share_text": L(
        "Men bu botda IQ testini topshirdim 🧠 Sen ham sinab ko‘r:",
        "Я прошёл IQ-тест в этом боте 🧠 Попробуй и ты:",
    ),
    "btn_ref_share": L("📤 Do‘stga yuborish", "📤 Отправить другу"),
    "iq_share_text": L(
        "Mening taxminiy IQ im — {iq} ({correct}/{total}). Sen ham sinab ko‘r:",
        "Мой примерный IQ — {iq} ({correct}/{total}). Попробуй и ты:",
    ),
    "btn_review": L("🔍 Xatolarni ko‘rish", "🔍 Разбор ошибок"),
    "ref_unlocked_notify": L(
        "🎉 <b>Do‘stingiz botga qo‘shildi!</b>\n\n"
        "Xatolaringizning batafsil tahlili endi siz uchun <b>butunlay ochiq</b>.",
        "🎉 <b>Ваш друг присоединился к боту!</b>\n\n"
        "Подробный разбор ошибок теперь открыт для вас <b>навсегда</b>.",
    ),
    "review_caption": L(
        "🔍 <b>Xato {pos} / {count}</b> · {num}-savol\n\n"
        "❌ Sizning javobingiz: <b>{yours}</b>\n"
        "✅ To‘g‘ri javob: <b>{correct}</b>\n\n"
        "💡 {why}",
        "🔍 <b>Ошибка {pos} / {count}</b> · вопрос {num}\n\n"
        "❌ Ваш ответ: <b>{yours}</b>\n"
        "✅ Правильный ответ: <b>{correct}</b>\n\n"
        "💡 {why}",
    ),
    "review_none": L(
        "🎉 Bu testda birorta ham xato qilmadingiz — ko‘rib chiqadigan narsa yo‘q!",
        "🎉 В этом тесте у вас нет ни одной ошибки — разбирать нечего!",
    ),
    "review_locked": L(
        "🔒 Tahlilni ochish uchun 1 ta do‘stingizni taklif qiling.",
        "🔒 Чтобы открыть разбор, пригласите 1 друга.",
    ),
    "review_missing": L("Bu natija topilmadi.", "Результат не найден."),
    "review_unavailable": L(
        "⏳ Tahlil vaqtincha mavjud emas. Birozdan keyin urinib ko‘ring.",
        "⏳ Разбор временно недоступен. Попробуйте чуть позже.",
    ),
    "btn_close": L("✖️ Yopish", "✖️ Закрыть"),
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
