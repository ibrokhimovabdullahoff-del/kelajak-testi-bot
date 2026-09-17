"""Big Five — IPIP Big-Five Factor Markers (50 element).

Manba: International Personality Item Pool (ipip.ori.org), Goldberg (1992).
IPIP elementlari **ochiq mulk (public domain)** — ruxsatsiz va to'lovsiz
nusxalash, tarjima qilish va tijorat maqsadida ishlatish mumkin.

Elementlar mazmuni asl manbadagidek, lekin ular gap emas, SAVOL shaklida
beriladi va javoblar savolning fe'lini takrorlaydi. Sabab: mavhum
"to'liq to'g'ri" shkalasini oddiy foydalanuvchi tushunmaydi.

Bu — botdagi yagona to'liq tekshirilgan asbob. Shu sababli natijada umumiy
"ball" chiqarilmaydi: Big Five odamni yaxshi-yomonga ajratmaydi.
"""
from .base import Item, L, Scale, TestDef, U

SCALES = {
    "E": Scale(
        key="E", emoji="🗣",
        name=L("Ekstraversiya", "Экстраверсия"),
        note=L(
            "Sotuv, boshqaruv va odamlar oldida gapirish kerak bo‘lgan ishda "
            "ustunlik beradi.",
            "Даёт преимущество в продажах, руководстве и работе на публику.",
        ),
        levels={
            "high": L(
                "Odamlar orasida quvvat olasiz, yangi tanishuv oson kechadi. "
                "Yolg‘iz, uzoq diqqat talab qiladigan ishda tez zerikasiz.",
                "Вы заряжаетесь среди людей, знакомства даются легко. "
                "В одиночной работе с долгой концентрацией быстро скучаете.",
            ),
            "mid": L(
                "Kerak bo‘lganda gapirasiz, kerak bo‘lganda tinglaysiz. "
                "Jamoada ham, yolg‘iz ham ishlay olasiz.",
                "Когда нужно — говорите, когда нужно — слушаете. Справляетесь "
                "и в команде, и в одиночку.",
            ),
            "low": L(
                "Quvvatni tinchlikdan olasiz, katta davra charchatadi. Chuqur "
                "diqqat kerak bo‘lgan ishda kuchlisiz, lekin aloqalarni "
                "ataylab qurishingiz kerak.",
                "Вы черпаете силы в тишине, большие компании утомляют. Сильны "
                "в работе с глубокой концентрацией, но связи придётся строить "
                "осознанно.",
            ),
        },
    ),
    "A": Scale(
        key="A", emoji="🤝",
        name=L("Kelishuvchanlik", "Доброжелательность"),
        note=L(
            "Jamoada ishlash va xizmat ko‘rsatish sohalarida muhim.",
            "Важна в командной работе и сфере обслуживания.",
        ),
        levels={
            "high": L(
                "Odamlarga ishonasiz va yordamga tayyorsiz. Xavfi: nizodan "
                "qochib, o‘z manfaatingizni himoya qilmay qolasiz.",
                "Вы доверяете людям и готовы помочь. Риск: избегая конфликта, "
                "не отстоите свои интересы.",
            ),
            "mid": L(
                "Yordam berasiz, lekin o‘zingizni ham unutmaysiz. Rahbarlik "
                "uchun qulay oraliq.",
                "Помогаете, но и о себе не забываете. Удобный диапазон для "
                "руководителя.",
            ),
            "low": L(
                "Tanqidiy fikrlaysiz, nizodan qo‘rqmaysiz. Muzokara va "
                "nazoratda ustunlik; odamlar sizni sovuq deb o‘ylashi mumkin.",
                "Мыслите критично, разногласий не боитесь. Плюс в переговорах "
                "и контроле; вас могут счесть холодным.",
            ),
        },
    ),
    "C": Scale(
        key="C", emoji="🧱",
        name=L("Vijdonlilik", "Добросовестность"),
        note=L(
            "Meta-tahlillarda ish natijasini eng ishonchli ko‘rsatadigan "
            "xususiyat (Barrick & Mount, 1991).",
            "В мета-анализах — самый надёжный предиктор рабочего результата "
            "(Barrick & Mount, 1991).",
        ),
        levels={
            "high": L(
                "Rejalashtirasiz, va’dani bajarasiz, boshlagan ishni "
                "tugatasiz. Xavfi — o‘zingizni ortiqcha yuklash.",
                "Планируете, держите слово, доводите до конца. Риск — "
                "перегрузить себя.",
            ),
            "mid": L(
                "Muhim ishni bajarasiz, lekin tartib beqaror. Bitta doimiy "
                "odat natijani sezilarli o‘zgartiradi.",
                "Важное делаете, но система нестабильна. Одна устойчивая "
                "привычка заметно изменит результат.",
            ),
            "low": L(
                "Erkinlikni tartibdan ustun qo‘yasiz, muddatlar buziladi. "
                "Yechim irodada emas: eslatma, aniq muddat, birga "
                "ishlaydigan sherik.",
                "Свободу ставите выше порядка, сроки срываются. Решение не в "
                "силе воли: напоминания, жёсткий дедлайн, напарник.",
            ),
        },
    ),
    "S": Scale(
        key="S", emoji="🛡",
        name=L("Hissiy barqarorlik", "Эмоциональная стабильность"),
        note=L(
            "Past ko‘rsatkich kasallik emas — u xavfni erta sezish bilan ham "
            "bog‘liq.",
            "Низкий показатель — не болезнь; он связан и с ранним "
            "распознаванием риска.",
        ),
        levels={
            "high": L(
                "Bosim ostida xotirjamsiz, zarbadan tez tiklanasiz. Xavfi — "
                "haqiqiy xatarni ham sezmay qolish.",
                "Спокойны под давлением, быстро восстанавливаетесь. Риск — не "
                "заметить настоящую опасность.",
            ),
            "mid": L(
                "Odatda o‘zingizni tutasiz, lekin uzoq bosim ta’sir qiladi. "
                "Uyqu va harakat sizda ko‘p narsani hal qiladi.",
                "Обычно держитесь, но длительное давление сказывается. Сон и "
                "движение решают у вас многое.",
            ),
            "low": L(
                "Tuyg‘ularni kuchli kechirasiz, xavotir tez ko‘tariladi. "
                "Xatarni erta sezasiz, lekin tiklanish sekin — uyqu rejimidan "
                "boshlang.",
                "Переживаете сильно, тревога поднимается быстро. Риск видите "
                "раньше других, но восстановление идёт медленно — начните с "
                "режима сна.",
            ),
        },
    ),
    "O": Scale(
        key="O", emoji="💡",
        name=L("Ochiqlik va intellekt", "Открытость и интеллект"),
        note=L(
            "Ijodiy va tadqiqot ishlarida asosiy omil.",
            "Ключевой фактор в творческой и исследовательской работе.",
        ),
        levels={
            "high": L(
                "Yangi g‘oya va murakkab masala sizni tortadi. Xavfi — "
                "qiziqish tarqalib, hech biri tugamay qolishi.",
                "Вас тянет к новым идеям и сложным задачам. Риск — интересы "
                "расползутся и ничто не будет закончено.",
            ),
            "mid": L(
                "Yangilikka ochiqsiz, lekin amaliyotni nazariyadan ustun "
                "qo‘yasiz.",
                "Открыты новому, но практику ставите выше теории.",
            ),
            "low": L(
                "Sinalgan va aniq usullarni afzal ko‘rasiz, xato kam "
                "qilasiz. Sohangiz o‘zgarganda kech qolmang: yiliga bitta "
                "yangi ko‘nikma.",
                "Предпочитаете проверенные методы, ошибаетесь редко. Не "
                "отстаньте, когда отрасль меняется: один новый навык в год.",
            ),
        },
    ),
}

# IPIP Big-Five Factor Markers, 50 element. Tartib asl manbadagidek.
# Gaplar savol shakliga o'tkazilgan, javoblar har bir savolning fe'lini
# takrorlaydi — mavhum "to'liq to'g'ri" o'rniga.
ITEMS = [
    Item("E", L("Davra siz bilan jonlanadimi?", "Компания оживает с вашим приходом?"),
         U("jonlanadi"), U("jonlanmaydi")),
    Item("A", L("Boshqalarning ahvoliga befarqmisiz?", "Вам безразлично, что происходит с другими?"),
         U("befarqman"), U("befarq emasman"), kind="deg", reverse=True),
    Item("C", L("Ishga yoki o‘qishga oldindan tayyorlanib kirishasizmi?",
                "Вы заранее готовитесь к делу или учёбе?"),
         U("tayyorlanib kirishaman"), U("tayyorlanmayman")),
    Item("S", L("Tez asabiylashasizmi?", "Вы легко впадаете в стресс?"),
         U("asabiylashaman"), U("asabiylashmayman"), reverse=True),
    Item("O", L("So‘z boyligingiz kattami?", "У вас богатый словарный запас?"),
         U("katta"), U("katta emas"), kind="deg"),
    Item("E", L("Tabiatan kamgap odammisiz?", "Вы по натуре немногословный человек?"),
         U("kamgapman"), U("kamgap emasman"), kind="deg", reverse=True),
    Item("A", L("Boshqa odamlar sizni qiziqtiradimi?", "Вам интересны другие люди?"),
         U("qiziqtiradi"), U("qiziqtirmaydi"), kind="deg"),
    Item("C", L("Xonangiz yoki ish joyingiz tartibsiz bo‘lib yotadimi?",
                "У вас в комнате или на рабочем месте бывает беспорядок?"),
         U("tartibsiz bo‘ladi"), U("tartibsiz bo‘lmaydi"), reverse=True),
    Item("S", L("Ko‘p vaqt o‘zingizni xotirjam his qilasizmi?", "Большую часть времени вы спокойны?"),
         U("xotirjamman"), U("xotirjam emasman"), kind="deg"),
    Item("O", L("Nazariy, falsafiy gaplarni tushunish sizga qiyinmi?",
                "Вам трудно понимать теоретические, философские рассуждения?"),
         U("qiyin"), U("qiyin emas"), kind="deg", reverse=True),
    Item("E", L("Odamlar orasida o‘zingizni erkin his qilasizmi?", "Вам комфортно среди людей?"),
         U("erkinman"), U("erkin emasman"), kind="deg"),
    Item("A", L("Odamning ko‘nglini og‘ritadigan gap aytib yuborasizmi?", "Вы можете задеть человека словом?"),
         U("aytib yuboraman"), U("aytmayman"), reverse=True),
    Item("C", L("Mayda narsalarga e’tibor berasizmi?", "Вы обращаете внимание на детали?"),
         U("e’tibor beraman"), U("e’tibor bermayman")),
    Item("S", L("Ko‘p narsadan tashvishlanasizmi?", "Вы о многом тревожитесь?"),
         U("tashvishlanaman"), U("tashvishlanmayman"), reverse=True),
    Item("O", L("Tasavvuringiz boymi?", "У вас живое воображение?"),
         U("boy"), U("boy emas"), kind="deg"),
    Item("E", L("Davrada chetroqda, jimgina turishni afzal ko‘rasizmi?",
                "В компании вы предпочитаете держаться в стороне?"),
         U("afzal ko‘raman"), U("afzal ko‘rmayman"), reverse=True),
    Item("A", L("Boshqalarning dardiga hamdard bo‘lasizmi?", "Вы сочувствуете переживаниям других?"),
         U("hamdard bo‘laman"), U("hamdard bo‘lmayman")),
    Item("C", L("Ishni chalkashtirib yuborasizmi?", "Вы всё запутываете и портите?"),
         U("chalkashtiraman"), U("chalkashtirmayman"), reverse=True),
    # Asl manbada: "Seldom feel blue" — hissiy barqarorlikka ijobiy.
    Item("S", L("Odatda kayfiyatingiz yaxshi bo‘ladimi?", "Обычно у вас хорошее настроение?"),
         U("yaxshi bo‘ladi"), U("yaxshi bo‘lmaydi")),
    Item("O", L("Hayot, inson va olam haqidagi chuqur savollar sizni qiziqtiradimi?",
                "Вас интересуют глубокие вопросы о жизни, человеке и мире?"),
         U("qiziqtiradi"), U("qiziqtirmaydi"), kind="deg"),
    Item("E", L("Suhbatni birinchi bo‘lib o‘zingiz boshlaysizmi?", "Вы первым начинаете разговор?"),
         U("boshlayman"), U("boshlamayman")),
    Item("A", L("Boshqalarning muammosidan o‘zingizni chetga olasizmi?", "Вы держитесь в стороне от чужих проблем?"),
         U("chetga olaman"), U("chetga olmayman"), reverse=True),
    Item("C", L("Yumushlarni kechiktirmay, darrov bajarasizmi?", "Вы делаете дела сразу, не откладывая?"),
         U("darrov bajaraman"), U("darrov bajarmayman")),
    Item("S", L("Kutilmagan voqeadan tez sarosimaga tushasizmi?",
                "Вас легко выбивает из колеи что-то неожиданное?"),
         U("sarosimaga tushaman"), U("sarosimaga tushmayman"), reverse=True),
    Item("O", L("Boshingizga yangi, qiziq g‘oyalar keladimi?", "Вам приходят в голову новые, интересные идеи?"),
         U("keladi"), U("kelmaydi")),
    Item("E", L("Suhbatda nima deyishni bilmay, jim qolasizmi?", "В разговоре вы молчите, не зная, что сказать?"),
         U("jim qolaman"), U("jim qolmayman"), reverse=True),
    Item("A", L("Ko‘nglingiz yumshoqmi?", "У вас мягкое сердце?"),
         U("yumshoq"), U("yumshoq emas"), kind="deg"),
    Item("C", L("Narsani ishlatib bo‘lgach, joyiga qo‘yishni unutasizmi?",
                "Вы забываете вернуть вещь на место после использования?"),
         U("unutaman"), U("unutmayman"), reverse=True),
    Item("S", L("Tez xafa bo‘lasizmi?", "Вы легко расстраиваетесь?"),
         U("xafa bo‘laman"), U("xafa bo‘lmayman"), reverse=True),
    Item("O", L("Biror narsani ko‘z oldingizga keltirish sizga qiyinmi?", "Вам трудно что-то себе представить?"),
         U("qiyin"), U("qiyin emas"), kind="deg", reverse=True),
    Item("E", L("To‘y va tadbirlarda ko‘p odam bilan gaplashasizmi?",
                "На свадьбах и мероприятиях вы общаетесь со многими людьми?"),
         U("gaplashaman"), U("gaplashmayman")),
    # Asl manbada: "Am not really interested in others" — teskari element.
    Item("A", L("Boshqalar o‘z hayoti haqida gapirsa, zerikib ketasizmi?",
                "Вам становится скучно, когда другие рассказывают о своей жизни?"),
         U("zerikib ketaman"), U("zerikmayman"), reverse=True),
    Item("C", L("Hamma narsa tartibli bo‘lishini yoqtirasizmi?", "Вам нравится, когда всё в порядке?"),
         U("yoqtiraman"), U("yoqtirmayman"), kind="deg"),
    Item("S", L("Kichik narsa ham kayfiyatingizni buzib yuboradimi?", "Даже мелочь может испортить вам настроение?"),
         U("buzib yuboradi"), U("buzmaydi"), reverse=True),
    Item("O", L("Yangi narsani tez tushunib olasizmi?", "Вы быстро схватываете новое?"),
         U("tez tushunib olaman"), U("tez tushunmayman")),
    Item("E", L("O‘zingizga e’tibor tortishdan qochasizmi?", "Вы избегаете привлекать к себе внимание?"),
         U("qochaman"), U("qochmayman"), reverse=True),
    Item("A", L("Boshqalar uchun vaqt ajratasizmi?", "Вы находите время для других?"),
         U("ajrataman"), U("ajratmayman")),
    Item("C", L("Vazifangizdan bo‘yin tovlaysizmi?", "Вы уклоняетесь от своих обязанностей?"),
         U("bo‘yin tovlayman"), U("bo‘yin tovlamayman"), reverse=True),
    Item("S", L("Bir kunning o‘zida kayfiyatingiz goh juda yaxshi, goh juda yomon bo‘ladimi?",
                "Бывает ли, что за один день настроение то очень хорошее, то очень плохое?"),
         U("shunday bo‘ladi"), U("bunday bo‘lmaydi"), reverse=True),
    Item("O", L("Gapirganda yoki yozganda kitobiy, murakkab so‘zlarni ishlatasizmi?",
                "Вы используете книжные, сложные слова в речи или на письме?"),
         U("ishlataman"), U("ishlatmayman")),
    Item("E", L("E’tibor markazida bo‘lish sizga yoqadimi?", "Вам нравится быть в центре внимания?"),
         U("yoqadi"), U("yoqmaydi"), kind="deg"),
    Item("A", L("Boshqalarning kayfiyatini sezib turasizmi?", "Вы чувствуете настроение других людей?"),
         U("sezaman"), U("sezmayman")),
    Item("C", L("Kun tartibi yoki rejaga amal qilasizmi?", "Вы придерживаетесь распорядка дня или плана?"),
         U("amal qilaman"), U("amal qilmayman")),
    Item("S", L("Tez jahlingiz chiqadimi?", "Вы легко раздражаетесь?"),
         U("chiqadi"), U("chiqmaydi"), reverse=True),
    Item("O", L("Biror narsa haqida uzoq o‘ylab o‘tirish sizga yoqadimi?",
                "Вам нравится подолгу размышлять о чём-то?"),
         U("yoqadi"), U("yoqmaydi"), kind="deg"),
    Item("E", L("Notanish odamlar oldida tortinib, kam gapirasizmi?",
                "С незнакомыми людьми вы стесняетесь и мало говорите?"),
         U("tortinib qolaman"), U("tortinmayman"), reverse=True),
    Item("A", L("Odamlar yoningizda o‘zini erkin his qiladimi?", "Рядом с вами людям спокойно?"),
         U("erkin his qiladi"), U("erkin his qilmaydi")),
    Item("C", L("Ishni puxta, xatosiz bajarishga harakat qilasizmi?",
                "Вы стараетесь делать работу тщательно, без ошибок?"),
         U("harakat qilaman"), U("harakat qilmayman")),
    Item("S", L("Ichingiz siqilib, g‘amgin bo‘lib yurasizmi?", "Вам бывает тоскливо и грустно?"),
         U("g‘amgin bo‘laman"), U("g‘amgin bo‘lmayman"), reverse=True),
    Item("O", L("Bitta muammoning bir nechta yechimini o‘ylab topa olasizmi?",
                "Можете ли вы придумать несколько решений одной проблемы?"),
         U("topa olaman"), U("topa olmayman")),
]

TEST = TestDef(
    key="bigfive",
    emoji="🧠",
    title=L("Big Five — shaxsiyat profili", "Big Five — профиль личности"),
    tagline=L(
        "Psixologiyadagi eng asosiy shaxsiyat modeli",
        "Основная модель личности в психологии",
    ),
    intro=L(
        "Bu — botdagi <b>yagona to‘liq tekshirilgan</b> test.\n\n"
        "50 ta savol beriladi. Har biriga o‘zingizga qarab javob bering — "
        "to‘g‘ri javob yo‘q. Qanday ko‘rinmoqchi ekaningizni emas, aslida "
        "qandayligingizni belgilang.\n\n"
        "Umumiy ball bo‘lmaydi: Big Five odamni yaxshi-yomonga ajratmaydi, "
        "u beshta alohida o‘lchov bo‘yicha profil beradi.",
        "Это <b>единственный полностью проверенный</b> тест в боте.\n\n"
        "Будет 50 вопросов. Отвечайте про себя — правильных ответов нет. "
        "Отмечайте не то, каким хотите казаться, а то, какой вы есть.\n\n"
        "Общего балла не будет: Big Five не делит людей на хороших и плохих, "
        "он даёт профиль по пяти отдельным шкалам.",
    ),
    source=L(
        "IPIP Big-Five Factor Markers (50 element), Goldberg, 1992. "
        "International Personality Item Pool — ochiq mulk (public domain). "
        "Big Five modeli minglab tadqiqotda sinalgan.\n\n"
        "Bir narsani ochiq aytamiz: elementlar mazmuni asl manbadan olingan, "
        "lekin ular o‘zbek tiliga o‘girilgan va savol shakliga keltirilgan, "
        "javob variantlari ham soddalashtirilgan. Bu tushunarlilikni "
        "oshiradi, lekin natija asl inglizcha variantning aynan o‘zi emas.",
        "IPIP Big-Five Factor Markers (50 пунктов), Goldberg, 1992. "
        "International Personality Item Pool — общественное достояние "
        "(public domain). Модель Big Five проверена в тысячах исследований.\n\n"
        "Скажем прямо: содержание пунктов взято из оригинала, но они "
        "переведены и переформулированы в виде вопросов, а варианты ответов "
        "упрощены. Это повышает понятность, но результат не идентичен "
        "оригинальной англоязычной версии.",
    ),
    validated=True,
    kind="traits",
    scales=SCALES,
    items=ITEMS,
    minutes=L("7–10 daqiqa", "7–10 минут"),
    ask_age=False,
)
