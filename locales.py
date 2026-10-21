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
        "🧠 <b>Kelajak Testi</b>\n"
        "Jahon psixologiyasidagi testlar — o‘zbek tilida.\n\n"
        "✅ Testni topshirish — bepul\n"
        "🎖 Qisqa natija va sertifikat — bepul\n"
        "📊 To‘liq shaxsiy tahlil — {price} so‘mdan\n\n"
        "🔒 Javoblaringizni hech kim ko‘rmaydi.\n\n"
        "Qaysi biridan boshlaymiz? 👇",
        "🧠 <b>Kelajak Testi</b>\n"
        "Тесты мировой психологии — на русском языке.\n\n"
        "✅ Пройти тест — бесплатно\n"
        "🎖 Краткий результат и сертификат — бесплатно\n"
        "📊 Полный личный разбор — от {price} сум\n\n"
        "🔒 Ваши ответы никто не увидит.\n\n"
        "С какого начнём? 👇",
    ),
    "menu_iq": L("🧩 IQ’ingiz qancha? · 10 daqiqa", "🧩 Какой у вас IQ? · 10 минут"),
    "menu_bigfive": L("🧠 Siz qanday insonsiz? · Big Five", "🧠 Какой вы человек? · Big Five"),
    "menu_career": L("🧭 Qaysi kasb sizga mos?", "🧭 Какая профессия вам подходит?"),
    "menu_future": L("🎯 Kelajak salohiyatingiz", "🎯 Ваш потенциал будущего"),
    "menu_child": L("👶 Farzandim uchun · ota-onalarga", "👶 Для моего ребёнка · родителям"),
    "btn_resume": L(
        "▶️ Testni davom ettirish ({done}/{total})",
        "▶️ Продолжить тест ({done}/{total})",
    ),
    "btn_restart": L("🔄 Yangidan boshlash", "🔄 Начать заново"),
    "btn_invite": L("🎁 Do‘stni taklif qilish", "🎁 Пригласить друга"),
    "btn_results": L("📈 Natijalarim", "📈 Мои результаты"),
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
        "{emoji} <b>{title}</b>\n"
        "{count} ta savol · ⏱ {minutes} · {badge}\n\n"
        "{instruction}\n\n"
        "🆓 <b>Bepul:</b> {free}\n"
        "{paid_line}",
        "{emoji} <b>{title}</b>\n"
        "{count} вопросов · ⏱ {minutes} · {badge}\n\n"
        "{instruction}\n\n"
        "🆓 <b>Бесплатно:</b> {free}\n"
        "{paid_line}",
    ),
    "card_iq_count": L("{count} ta rasmli topshiriq", "{count} заданий с картинками"),
    "card_iq": L(
        "{emoji} <b>{title}</b>\n"
        "{count} ta rasmli topshiriq · ⏱ {minutes}\n\n"
        "{instruction}\n\n"
        "🆓 <b>Bepul:</b> {free}\n"
        "{paid_line}",
        "{emoji} <b>{title}</b>\n"
        "{count} заданий с картинками · ⏱ {minutes}\n\n"
        "{instruction}\n\n"
        "🆓 <b>Бесплатно:</b> {free}\n"
        "{paid_line}",
    ),
    "card_paid": L("💎 <b>To‘liq tahlil — {price} so‘m:</b> {paid}", "💎 <b>Полный разбор — {price} сум:</b> {paid}"),
    "card_owned": L("✅ <b>To‘liq tahlil sizda ochiq:</b> {paid}", "✅ <b>Полный разбор у вас открыт:</b> {paid}"),
    "card_report_free": L("🎁 <b>To‘liq tahlil hozir bepul:</b> {paid}", "🎁 <b>Полный разбор сейчас бесплатно:</b> {paid}"),
    "card_progress": L(
        "\n\n⏸ Siz bu testni {done}-savolda to‘xtatgansiz.",
        "\n\n⏸ Вы остановились на {done}-м вопросе.",
    ),
    "instr_self": L(
        "To‘g‘ri yoki noto‘g‘ri javob yo‘q. Qanday ko‘rinmoqchi ekaningizni emas, aslida qandayligingizni belgilang.",
        "Правильных и неправильных ответов нет. Отмечайте не то, каким хотите казаться, а то, какой вы есть.",
    ),
    "instr_career": L(
        "Har bir mashg‘ulot sizga qanchalik qiziq ekanini belgilang. Qobiliyat emas — qiziqish muhim.",
        "Отметьте, насколько вам интересно каждое занятие. Важны не способности, а интерес.",
    ),
    "instr_child": L(
        "Farzandingizning odatiy xulqiga qarab javob bering — qanday bo‘lishini istaganingizga emas.",
        "Отвечайте по обычному поведению ребёнка, а не по тому, каким вы хотите его видеть.",
    ),
    "instr_iq": L(
        "Har bir rasmda qonuniyatni toping va «?» o‘rniga mos variantni tanlang. Shoshmang, lekin bitta savolda qotib qolmang.",
        "В каждой картинке найдите закономерность и выберите вариант вместо «?». Не спешите, но и не застревайте на одном вопросе.",
    ),
    "iq_minutes": L("10–15 daqiqa", "10–15 минут"),
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
    "interest_prompt": L("Bu mashg‘ulot sizga qanchalik qiziq?", "Насколько вам интересно это занятие?"),
    "ms_25": L("🔥 Chorak yo‘l bosildi — davom eting", "🔥 Четверть пути позади — продолжайте"),
    "ms_50": L("🔥 Yarmidan o‘tdingiz — natijangiz shakllanyapti", "🔥 Вы прошли половину — результат складывается"),
    "ms_75": L("🏁 Oz qoldi — natija tayyor bo‘lyapti", "🏁 Осталось чуть-чуть — результат почти готов"),
    "cancel_confirm": L(
        "⏸ <b>Testni to‘xtatasizmi?</b>\n\n"
        "Javoblaringiz saqlanadi — keyin /start orqali shu joydan davom ettirasiz.",
        "⏸ <b>Остановить тест?</b>\n\n"
        "Ответы сохранятся — потом продолжите с этого места через /start.",
    ),
    "btn_quit_yes": L("⏸ Ha, to‘xtatish", "⏸ Да, остановить"),
    "btn_quit_no": L("▶️ Davom etish", "▶️ Продолжить"),
    "test_paused": L(
        "⏸ Test to‘xtatildi. Javoblaringiz saqlandi — /start orqali davom ettirasiz.",
        "⏸ Тест остановлен. Ответы сохранены — продолжите через /start.",
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
        "Психологические тесты на узбекском и русском 🧠 Попробуй и ты",
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
    "card_label_parent": L("Farzandim uchun", "Для моего ребёнка"),
    "card_parent_name": L("G‘amxo‘r ota-ona", "Заботливый родитель"),
    "card_parent_line": L(
        "Farzandimning kuchli tomonlarini bilish uchun test topshirdim.",
        "Я прошёл тест, чтобы узнать сильные стороны своего ребёнка.",
    ),
    "card_parent_line2": L("Bola o‘sishi e’tibordan boshlanadi.", "Рост ребёнка начинается с внимания."),
    "btn_card_hide": L("🙈 Ballni yashirish", "🙈 Скрыть балл"),
    "btn_card_show": L("👁 Ballni ko‘rsatish", "👁 Показать балл"),
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
    # --- To'lov: to'liq tahlil ---------------------------------------------
    "btn_unlock": L("🔓 To‘liq tahlilni ochish — {price} so‘m", "🔓 Открыть полный разбор — {price} сум"),
    "btn_bundle": L("📦 5 ta testning to‘liq tahlili — {price} so‘m", "📦 Полный разбор всех 5 тестов — {price} сум"),
    "btn_ref_unlock": L("🎁 Do‘st taklif qilib bepul ochish", "🎁 Открыть бесплатно — пригласить друга"),
    "btn_open_report": L("📊 To‘liq tahlilni ko‘rish", "📊 Смотреть полный разбор"),
    "pay_screen": L(
        "🔓 <b>{title} — to‘liq tahlil</b>\n"
        "💳 Narxi: <b>{price} so‘m</b>\n\n"
        "Click orqali to‘lasangiz, tahlil shu yerda darhol ochiladi.\n"
        "Karta orqali — chek yuborasiz, odatda 15 daqiqada tasdiqlanadi.",
        "🔓 <b>{title} — полный разбор</b>\n"
        "💳 Цена: <b>{price} сум</b>\n\n"
        "При оплате через Click разбор откроется здесь сразу.\n"
        "Картой — отправите чек, обычно его подтверждают за 15 минут.",
    ),
    "pay_screen_bundle": L(
        "📦 <b>5 ta testning to‘liq tahlili</b>\n"
        "💳 Narxi: <b>{price} so‘m</b> (alohida olinsa — {full} so‘m)\n\n"
        "Hammasi bir yo‘la ochiladi — topshirgan va keyin topshiradigan testlaringiz uchun.\n"
        "Click orqali to‘lasangiz, darhol ochiladi. Karta orqali — chek yuborasiz.",
        "📦 <b>Полный разбор всех 5 тестов</b>\n"
        "💳 Цена: <b>{price} сум</b> (по отдельности — {full} сум)\n\n"
        "Открывается сразу всё — для пройденных и будущих тестов.\n"
        "Через Click — откроется сразу. Картой — отправите чек.",
    ),
    "btn_pay_click": L("💳 Click orqali to‘lash — {price} so‘m", "💳 Оплатить через Click — {price} сум"),
    "btn_pay_card": L("🏦 Karta orqali (UZCARD/HUMO)", "🏦 Картой (UZCARD/HUMO)"),
    "btn_pay_wallet": L("💰 Balansdan to‘lash ({balance} so‘m)", "💰 Оплатить с баланса ({balance} сум)"),
    "pay_card": L(
        "💳 <b>{price} so‘m o‘tkazing</b>\n"
        "<code>{card}</code>\n"
        "👤 {holder}\n\n"
        "📸 To‘lagach, chek rasmini shu chatga yuboring.",
        "💳 <b>Переведите {price} сум</b>\n"
        "<code>{card}</code>\n"
        "👤 {holder}\n\n"
        "📸 После оплаты отправьте фото чека в этот чат.",
    ),
    "receipt_ok": L(
        "✅ Chek qabul qilindi. Odatda 15 daqiqa ichida tasdiqlanadi.\n\n"
        "Kutayotganda boshqa testni bepul topshiring 👇",
        "✅ Чек принят. Обычно его подтверждают в течение 15 минут.\n\n"
        "Пока ждёте — пройдите другой тест бесплатно 👇",
    ),
    "receipt_ok_open": L(
        "✅ Chek qabul qilindi — to‘liq tahlil ochildi 👇\nAdmin chekni tez orada tekshiradi.",
        "✅ Чек принят — полный разбор открыт 👇\nАдминистратор скоро проверит чек.",
    ),
    "receipt_photo_only": L(
        "📸 Iltimos, chekni rasm (skrinshot) sifatida yuboring.",
        "📸 Пожалуйста, отправьте чек фотографией (скриншотом).",
    ),
    "receipt_approved": L(
        "✅ To‘lov tasdiqlandi — {title} to‘liq tahlili ochildi 👇",
        "✅ Оплата подтверждена — полный разбор «{title}» открыт 👇",
    ),
    "receipt_rejected": L(
        "❌ Chek tasdiqlanmadi. Summa va karta raqamini tekshirib, qayta urinib ko‘ring yoki Click orqali to‘lang.",
        "❌ Чек не подтверждён. Проверьте сумму и номер карты и попробуйте снова или оплатите через Click.",
    ),
    "receipt_rejected_open": L(
        "❌ Chek tasdiqlanmadi, shuning uchun to‘liq tahlil yopildi. Qayta urinib ko‘ring yoki Click orqali to‘lang.",
        "❌ Чек не подтверждён, поэтому полный разбор закрыт. Попробуйте снова или оплатите через Click.",
    ),
    "btn_retry_pay": L("🔄 Qayta urinish", "🔄 Попробовать снова"),
    "pay_report_ok": L(
        "✅ <b>To‘lov qabul qilindi!</b>\n{title} — to‘liq tahlil ochildi 👇",
        "✅ <b>Оплата принята!</b>\n{title} — полный разбор открыт 👇",
    ),
    "pay_bundle_ok": L(
        "✅ <b>To‘lov qabul qilindi!</b>\n5 ta testning to‘liq tahlili ochildi — har bir test natijasida darhol ko‘rasiz.",
        "✅ <b>Оплата принята!</b>\nПолный разбор всех 5 тестов открыт — увидите его сразу в результате каждого теста.",
    ),
    "pay_no_result": L(
        "Bu testni hali topshirmagansiz. Topshirishingiz bilan to‘liq tahlil darhol ochiladi 👇",
        "Вы ещё не проходили этот тест. Как только пройдёте — полный разбор откроется сразу 👇",
    ),
    "pay_failed": L(
        "❌ To‘lov o‘tmadi yoki bekor qilindi. Pulingiz yechilmagan bo‘lsa, qayta urinib ko‘ring 👇",
        "❌ Оплата не прошла или отменена. Если деньги не списались — попробуйте снова 👇",
    ),
    "btn_check_again": L("🔄 Qayta tekshirish", "🔄 Проверить ещё раз"),
    "wallet_low": L("❌ Balans yetarli emas.", "❌ Недостаточно средств на балансе."),
    "report_already": L("✅ Bu test uchun to‘liq tahlil sizda allaqachon ochiq.", "✅ Полный разбор этого теста у вас уже открыт."),
    "topup_ok": L(
        "✅ Balans to‘ldirildi: <b>+{amount} so‘m</b>.\n💰 Yangi balans: <b>{balance} so‘m</b>",
        "✅ Баланс пополнен: <b>+{amount} сум</b>.\n💰 Новый баланс: <b>{balance} сум</b>",
    ),
    "history_hint": L("Natijani ochish uchun tugmani bosing 👇", "Нажмите, чтобы открыть результат 👇"),
    "history_balance": L("💰 Balans: <b>{balance} so‘m</b>", "💰 Баланс: <b>{balance} сум</b>"),
    "btn_wallet": L("💰 Balans", "💰 Баланс"),
    # --- Bepul natija va to'liq tahlil ------------------------------------
    "res_done": L("✅ <b>Test yakunlandi!</b>", "✅ <b>Тест завершён!</b>"),
    "res_type": L("Shaxsiyat turingiz: <b>{name}</b>", "Ваш тип личности: <b>{name}</b>"),
    "res_top_strong": L(
        "Eng kuchli tomoningiz: {emoji} <b>{name}</b>",
        "Ваша сильная сторона: {emoji} <b>{name}</b>",
    ),
    "res_top_plain": L(
        "Eng yuqori natijangiz: {emoji} <b>{name}</b>",
        "Самый высокий результат: {emoji} <b>{name}</b>",
    ),
    "res_top_child": L(
        "Farzandingizning eng kuchli tomoni: {emoji} <b>{name}</b>",
        "Самая сильная сторона ребёнка: {emoji} <b>{name}</b>",
    ),
    "res_top_career": L(
        "Sizga eng yaqin yo‘nalish: {emoji} <b>{name}</b>",
        "Самое близкое вам направление: {emoji} <b>{name}</b>",
    ),
    "res_locked": L("{emoji} {name} — ░░░░░ 🔒", "{emoji} {name} — ░░░░░ 🔒"),
    "res_locked_more": L(
        "🔒 Yana {n} ta yo‘nalish — to‘liq tahlilda",
        "🔒 Ещё {n} направлений — в полном разборе",
    ),
    "res_in_full": L("📊 <b>To‘liq tahlilda:</b>", "📊 <b>В полном разборе:</b>"),
    "res_index_line": L(
        "{emoji} Umumiy indeks: <b>{score} — {band}</b>",
        "{emoji} Общий индекс: <b>{score} — {band}</b>",
    ),
    "res_iq_locked": L("🧠 Taxminiy IQ — ░░░░░ 🔒", "🧠 Примерный IQ — ░░░░░ 🔒"),
    "res_iq_locked_kinds": L(
        "📊 4 ta fikrlash turi bo‘yicha natija — ░░░░░ 🔒",
        "📊 Результат по 4 типам мышления — ░░░░░ 🔒",
    ),
    "res_full_badge": L("🔓 <b>To‘liq tahlil</b>", "🔓 <b>Полный разбор</b>"),
    "res_step": L("✅ <i>Qadam:</i> {text}", "✅ <i>Шаг:</i> {text}"),
    "res_research": L("🔬 <i>Tadqiqotlar:</i> {text}", "🔬 <i>Исследования:</i> {text}"),
    "res_tip": L("👪 <i>Maslahat:</i> {text}", "👪 <i>Совет:</i> {text}"),
    "res_meaning": L("💡 <i>Bu nima:</i> {text}", "💡 <i>Что это:</i> {text}"),
    "res_risks": L("XAVF ZONALARI", "ЗОНЫ РИСКА"),
    "res_env": L("SIZGA MOS MUHIT", "ПОДХОДЯЩАЯ ВАМ СРЕДА"),
    "res_habit": L(
        "NATIJANI ENG KO‘P O‘ZGARTIRADIGAN ODAT",
        "ПРИВЫЧКА, КОТОРАЯ ИЗМЕНИТ БОЛЬШЕ ВСЕГО",
    ),
    "res_work_on": L("USTIDA ISHLASH KERAK BO‘LGAN 3 YO‘NALISH", "3 НАПРАВЛЕНИЯ ДЛЯ РАБОТЫ"),
    "res_jobs": L("MOS KASBLAR", "ПОДХОДЯЩИЕ ПРОФЕССИИ"),
    "res_study": L("QAYERDA O‘QISH MUMKIN", "ГДЕ УЧИТЬСЯ"),
    "res_next_month": L("KEYINGI OYDA NIMANI SINAB KO‘RISH KERAK", "ЧТО ПОПРОБОВАТЬ В БЛИЖАЙШИЙ МЕСЯЦ"),
    "res_iq_kinds": L("FIKRLASH TURLARI", "ТИПЫ МЫШЛЕНИЯ"),
    "res_iq_kind": L("{emoji} <b>{name}</b> — {ok} / {n}", "{emoji} <b>{name}</b> — {ok} / {n}"),
    "res_none_strong": L(
        "Hozircha biror yo‘nalish ajralib turmadi — bu ham ma’lumot: o‘sish uchun joy ko‘p.",
        "Пока ни одно направление не выделяется — это тоже информация: есть куда расти.",
    ),
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
    # --- Do'st taklifi -------------------------------------------------------
    "ref_share_text": L(
        "Men bu botda IQ testini topshirdim 🧠 Sen ham sinab ko‘r:",
        "IQ-тест с картинками в этом боте 🧠 Попробуй и ты:",
    ),
    "btn_ref_share": L("📤 Do‘stga yuborish", "📤 Отправить другу"),
    "invite_plain": L(
        "🎁 <b>Do‘stni taklif qilish</b>\n\n"
        "Testlar bepul — do‘stlaringiz ham o‘zini sinab ko‘rsin. Shaxsiy havolangiz:\n\n{link}",
        "🎁 <b>Пригласить друга</b>\n\n"
        "Тесты бесплатные — пусть друзья тоже проверят себя. Ваша личная ссылка:\n\n{link}",
    ),
    "invite_share_text": L(
        "Psixologik testlar bepul — o‘zingizni sinab ko‘ring 👇",
        "Психологические тесты бесплатно — проверьте себя 👇",
    ),
    "iq_share_text": L(
        "Mening taxminiy IQ im — {iq} ({correct}/{total}). Sen ham sinab ko‘r:",
        "Мой примерный IQ — {iq} ({correct}/{total}). Попробуй и ты:",
    ),
    "review_missing": L("Bu natija topilmadi.", "Результат не найден."),
    "review_gone": L(
        "Bu bo‘lim endi mavjud emas.",
        "Этот раздел больше недоступен.",
    ),
    "btn_close": L("✖️ Yopish", "✖️ Закрыть"),
    # --- 2-bosqich: do'st mukofoti -----------------------------------------
    "ref_menu": L(
        "🎁 <b>Do‘stni taklif qilish</b>\n\n"
        "Do‘stingiz shu havola orqali botga kelib, birorta testni oxirigacha topshirsa — "
        "sizga <b>1 ta to‘liq tahlil bepul</b> (qaysi test ekanini o‘zingiz tanlaysiz).\n"
        "Botga birinchi marta kelgan do‘stlar hisoblanadi, oyiga {cap} tagacha.\n\n"
        "Sizning havolangiz:\n{link}\n\n"
        "👥 Taklif qilganlaringiz: <b>{invited}</b> · testni tugatgan: <b>{done}</b>\n"
        "🎁 Bepul tahlil: <b>{credits} ta</b>",
        "🎁 <b>Пригласить друга</b>\n\n"
        "Если друг придёт по этой ссылке и пройдёт любой тест до конца — "
        "вы получите <b>1 полный разбор бесплатно</b> (какой тест — выбираете сами).\n"
        "Считаются друзья, которые открыли бота впервые, до {cap} в месяц.\n\n"
        "Ваша ссылка:\n{link}\n\n"
        "👥 Приглашено: <b>{invited}</b> · прошли тест: <b>{done}</b>\n"
        "🎁 Бесплатных разборов: <b>{credits}</b>",
    ),
    "ref_rewarded": L(
        "🎉 <b>Do‘stingiz testni tugatdi!</b>\n"
        "Sizga 1 ta to‘liq tahlil bepul berildi — qaysi test ekanini o‘zingiz tanlaysiz.",
        "🎉 <b>Ваш друг прошёл тест!</b>\n"
        "Вам начислен 1 полный разбор бесплатно — какой тест, выбираете сами.",
    ),
    "btn_credit_pick": L("🔓 Tahlilni tanlash", "🔓 Выбрать разбор"),
    "btn_credit_use": L("🔓 Bepul tahlilni ochish ({n})", "🔓 Открыть бесплатный разбор ({n})"),
    "btn_credit_paywall": L("🎁 Bepul ochish (sizda {n} ta)", "🎁 Открыть бесплатно (у вас {n})"),
    "credit_menu": L(
        "🎁 <b>Bepul to‘liq tahlil</b>\n\nSizda: <b>{n} ta</b>. Qaysi testning to‘liq tahlilini ochamiz?",
        "🎁 <b>Бесплатный полный разбор</b>\n\nУ вас: <b>{n}</b>. Разбор какого теста открыть?",
    ),
    "credit_none": L("Bepul tahlil qolmagan.", "Бесплатных разборов не осталось."),
    "credit_all_open": L(
        "Hamma testlarning to‘liq tahlili sizda allaqachon ochiq ✅",
        "У вас уже открыты полные разборы всех тестов ✅",
    ),
    "credit_used": L("✅ {title} — to‘liq tahlil ochildi (bepul).", "✅ {title} — полный разбор открыт (бесплатно)."),
    "credit_used_take": L(
        "✅ {title} — to‘liq tahlil ochildi.\nTestni topshiring — natijangiz darhol to‘liq chiqadi.",
        "✅ {title} — полный разбор открыт.\nПройдите тест — результат сразу будет полным.",
    ),
    "history_credits": L("🎁 Bepul to‘liq tahlil: <b>{n} ta</b>", "🎁 Бесплатных полных разборов: <b>{n}</b>"),
    # --- 2-bosqich: do'st bilan solishtirish -----------------------------------
    "btn_compare": L("👥 Do‘stingiz bilan solishtiring", "👥 Сравниться с другом"),
    "btn_compare_own": L("👥 O‘z do‘stlaringiz bilan solishtiring", "👥 Сравниться со своими друзьями"),
    "btn_compare_send": L("📤 Havolani yuborish", "📤 Отправить ссылку"),
    "cmp_share_screen": L(
        "👥 <b>Do‘stingiz bilan solishtiring</b>\n\n"
        "Havolani do‘stingizga yuboring. U testni bepul topshirgach, natijalaringiz yonma-yon "
        "ko‘rsatiladi — faqat unga va foizlarsiz. Sizning to‘liq tahlilingiz va raqamlaringiz yopiq qoladi.",
        "👥 <b>Сравнитесь с другом</b>\n\n"
        "Отправьте ссылку другу. Когда он бесплатно пройдёт тест, ваши результаты покажутся рядом — "
        "только ему и без процентов. Ваш полный разбор и цифры останутся закрытыми.",
    ),
    "cmp_share_bigfive": L(
        "Big Five: qaysi tomonlarimiz o‘xshash? Testni topshir — natijalarimizni solishtiramiz 👇",
        "Big Five: в чём мы похожи? Пройди тест — сравним результаты 👇",
    ),
    "cmp_share_iq": L(
        "IQ topshiriqlari: kim qaysi turda kuchliroq? Sinab ko‘r — solishtiramiz 👇",
        "IQ-задания: кто в чём сильнее? Попробуй — сравним 👇",
    ),
    "cmp_intro": L(
        "👥 <b>{name} sizni solishtirishga taklif qildi</b>\n\n"
        "{test} testini bepul topshiring — keyin ikkalangizning natijangiz yonma-yon chiqadi (foizlarsiz).",
        "👥 <b>{name} приглашает вас сравниться</b>\n\n"
        "Пройдите тест «{test}» бесплатно — потом ваши результаты покажутся рядом (без процентов).",
    ),
    "cmp_need_result": L("Avval testni o‘zingiz topshiring.", "Сначала пройдите тест сами."),
    "cmp_friend": L("do‘stingiz", "друг"),
    "cmp_title": L("👥 <b>Siz va {name} — {test}</b>", "👥 <b>Вы и {name} — {test}</b>"),
    "cmp_tie": L("taxminan teng", "примерно поровну"),
    "cmp_more_you": L("siz ko‘proq", "у вас выше"),
    "cmp_more_them": L("{name} ko‘proq", "у {name} выше"),
    "cmp_iq_total": L("🧩 Umumiy natija: {who}", "🧩 В целом: {who}"),
    "cmp_closest": L("🔗 Eng o‘xshash tomoningiz: {trait}", "🔗 Больше всего вы похожи: {trait}"),
    "cmp_farthest": L("⚡️ Eng katta farq: {trait}", "⚡️ Самое большое различие: {trait}"),
    "cmp_footer": L(
        "<i>Qisqa solishtirish: foiz va ballar ko‘rsatilmaydi, har kimning to‘liq tahlili o‘ziga. Bu tashxis emas.</i>",
        "<i>Короткое сравнение: проценты и баллы не показываются, полный разбор у каждого свой. Это не диагноз.</i>",
    ),
    # --- 2-bosqich: sertifikat ostidagi ulashish matni -------------------------
    "cert_share": L("Men «{name}» chiqdim. Siz-chi? 👉", "У меня вышло «{name}». А у вас? 👉"),
    "cert_share_child": L(
        "«{title}» — ota-onalar uchun foydali test. Sinab ko‘ring 👉",
        "«{title}» — полезный тест для родителей. Попробуйте 👉",
    ),
    "cert_share_plain": L(
        "Kelajak Testida o‘zimni sinab ko‘rdim. Siz ham sinab ko‘ring 👉",
        "Бесплатные психологические тесты Kelajak Testi — попробуйте 👉",
    ),
    # --- 2-bosqich: promo kod ----------------------------------------------
    "btn_promo": L("🎟 Promo kod", "🎟 Промокод"),
    "promo_ask": L(
        "🎟 Promo kodni yuboring (masalan: <code>MAKTAB5</code>).\nBekor qilish: /bekor",
        "🎟 Отправьте промокод (например: <code>MAKTAB5</code>).\nОтмена: /bekor",
    ),
    "promo_ok_free": L(
        "🎟 <b>Promo kod qabul qilindi!</b>\nTo‘liq tahlil siz uchun ochildi: {tests}\n\n"
        "Testni topshiring — natijangiz darhol to‘liq chiqadi.",
        "🎟 <b>Промокод принят!</b>\nДля вас открыт полный разбор: {tests}\n\n"
        "Пройдите тест — результат сразу будет полным.",
    ),
    "promo_ok_discount": L(
        "🎟 <b>Promo kod qabul qilindi!</b>\n"
        "Keyingi to‘liq tahlilga <b>{pct}% chegirma</b> — narx to‘lov oynasida o‘zi kamayadi.",
        "🎟 <b>Промокод принят!</b>\n"
        "Скидка <b>{pct}%</b> на следующий полный разбор — цена уменьшится сама в окне оплаты.",
    ),
    "promo_not_found": L("Bunday promo kod topilmadi.", "Такой промокод не найден."),
    "promo_inactive": L("Bu promo kod hozir ishlamaydi.", "Этот промокод сейчас не действует."),
    "promo_expired": L("Bu promo kodning muddati tugagan.", "Срок действия этого промокода истёк."),
    "promo_used_up": L("Bu promo kod limiti tugagan.", "Лимит этого промокода исчерпан."),
    "promo_already": L("Siz bu promo kodni allaqachon ishlatgansiz.", "Вы уже использовали этот промокод."),
    "pay_discount_line": L(
        "\n🎟 Promo kod <b>{code}</b>: −{pct}% — {full} o‘rniga <b>{price} so‘m</b>",
        "\n🎟 Промокод <b>{code}</b>: −{pct}% — <b>{price} сум</b> вместо {full}",
    ),
    # --- 2-bosqich: eslatmalar ---------------------------------------------
    "rem_unfinished": L(
        "⏸ {title}: testni {n}-savolda to‘xtatdingiz. Davom etasizmi?",
        "⏸ {title}: вы остановились на {n}-м вопросе. Продолжим?",
    ),
    "rem_paywall": L(
        "📊 {title}: to‘liq tahlilingiz tayyor. Xohlasangiz, shu yerda ochishingiz mumkin.",
        "📊 {title}: ваш полный разбор готов. Если захотите — его можно открыть здесь.",
    ),
    "btn_continue": L("▶️ Davom ettirish", "▶️ Продолжить"),
    "btn_see_result": L("📊 Natijani ko‘rish", "📊 Посмотреть результат"),
    "btn_rem_off": L("🔕 Eslatma kerak emas", "🔕 Не напоминать"),
    "rem_off_ok": L(
        "🔕 Boshqa eslatma yubormaymiz. Testlar menyusi doim /start da.",
        "🔕 Больше не будем напоминать. Меню тестов всегда в /start.",
    ),
    # --- 2-bosqich: bir martalik yangilik e'loni ------------------------------
    "announce_text": L(
        "Assalomu alaykum! 👋\n"
        "Kelajak Testida yangilik: endi barcha testlarni bepul topshirish mumkin.\n"
        "Qisqa natija va sertifikat ham bepul. To‘liq tahlil — xohlasangiz.\n\n"
        "🧩 IQ’ingiz qancha? 20 ta topshiriq, 10 daqiqa.",
        "Здравствуйте! 👋\n"
        "Новость в Kelajak Testi: теперь все тесты можно пройти бесплатно.\n"
        "Краткий результат и сертификат — тоже бесплатно. Полный разбор — по желанию.\n\n"
        "🧩 Какой у вас IQ? 20 заданий, 10 минут.",
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
