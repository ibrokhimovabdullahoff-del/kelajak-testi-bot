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
    Item("C", L("Ishga tayyor holda kirishasizmi?", "Вы приступаете к делу подготовленным?"),
         U("tayyor bo‘laman"), U("tayyor bo‘lmayman")),
    Item("S", L("Tez asabiylashasizmi?", "Вы легко впадаете в стресс?"),
         U("asabiylashaman"), U("asabiylashmayman"), reverse=True),
    Item("O", L("So‘z boyligingiz kattami?", "У вас богатый словарный запас?"),
         U("katta"), U("katta emas"), kind="deg"),
    Item("E", L("Kamgapmisiz?", "Вы немногословны?"),
         U("kamgapman"), U("kamgap emasman"), kind="deg", reverse=True),
    Item("A", L("Odamlar sizga qiziqmi?", "Вам интересны люди?"),
         U("qiziq"), U("qiziq emas"), kind="deg"),
    Item("C", L("Narsalaringizni joyiga qo‘ymay tashlab ketasizmi?", "Вы разбрасываете свои вещи?"),
         U("tashlab ketaman"), U("tashlab ketmayman"), reverse=True),
    Item("S", L("O‘zingizni tinch his qilasizmi?", "Вы чувствуете себя спокойно?"),
         U("tinchman"), U("tinch emasman"), kind="deg"),
    Item("O", L("Mavhum fikrlarni tushunish sizga qiyinmi?", "Вам трудно понимать абстрактные идеи?"),
         U("qiyin"), U("qiyin emas"), kind="deg", reverse=True),
    Item("E", L("Odamlar orasida o‘zingizni erkin his qilasizmi?", "Вам комфортно среди людей?"),
         U("erkinman"), U("erkin emasman"), kind="deg"),
    Item("A", L("Odamning ko‘nglini og‘ritadigan gap aytib yuborasizmi?", "Вы можете задеть человека словом?"),
         U("aytib yuboraman"), U("aytmayman"), reverse=True),
    Item("C", L("Mayda narsalarga e’tibor berasizmi?", "Вы обращаете внимание на детали?"),
         U("e’tibor beraman"), U("e’tibor bermayman")),
    Item("S", L("Har narsadan tashvishlanasizmi?", "Вы тревожитесь по любому поводу?"),
         U("tashvishlanaman"), U("tashvishlanmayman"), reverse=True),
    Item("O", L("Xayolingiz boymi?", "У вас живое воображение?"),
         U("boy"), U("boy emas"), kind="deg"),
    Item("E", L("Chetda, ko‘zga tashlanmay turishni yoqtirasizmi?", "Вы предпочитаете оставаться в тени?"),
         U("yoqtiraman"), U("yoqtirmayman"), reverse=True),
    Item("A", L("Boshqalarning ahvoliga achinasizmi?", "Вы сочувствуете переживаниям других?"),
         U("achinaman"), U("achinmayman")),
    Item("C", L("Ishni chalkashtirib yuborasizmi?", "Вы всё запутываете и портите?"),
         U("chalkashtiraman"), U("chalkashtirmayman"), reverse=True),
    Item("S", L("Kayfiyatingiz tushib ketadimi?", "У вас портится настроение?"),
         U("tushadi"), U("tushmaydi"), reverse=True),
    Item("O", L("Chuqur, mavhum mavzular sizni qiziqtiradimi?", "Вас занимают глубокие, отвлечённые темы?"),
         U("qiziqtiradi"), U("qiziqtirmaydi")),
    Item("E", L("Gapni birinchi bo‘lib o‘zingiz boshlaysizmi?", "Вы первым начинаете разговор?"),
         U("boshlayman"), U("boshlamayman")),
    Item("A", L("Boshqalarning muammosidan o‘zingizni chetga olasizmi?", "Вы держитесь в стороне от чужих проблем?"),
         U("chetga olaman"), U("chetga olmayman"), reverse=True),
    Item("C", L("Yumushlarni darrov bajarasizmi?", "Вы сразу выполняете дела?"),
         U("bajaraman"), U("bajarmayman")),
    Item("S", L("Sizni bezovta qilish osonmi?", "Вас легко вывести из равновесия?"),
         U("oson"), U("oson emas"), kind="deg", reverse=True),
    Item("O", L("Sizda zo‘r fikrlar paydo bo‘ladimi?", "У вас появляются отличные идеи?"),
         U("paydo bo‘ladi"), U("paydo bo‘lmaydi")),
    Item("E", L("Aytadigan gapingiz kammi?", "Вам обычно нечего сказать?"),
         U("kam"), U("kam emas"), kind="deg", reverse=True),
    Item("A", L("Ko‘nglingiz yumshoqmi?", "У вас мягкое сердце?"),
         U("yumshoq"), U("yumshoq emas"), kind="deg"),
    Item("C", L("Narsani joyiga qaytarib qo‘yishni unutasizmi?", "Вы забываете класть вещи на место?"),
         U("unutaman"), U("unutmayman"), reverse=True),
    Item("S", L("Tez xafa bo‘lasizmi?", "Вы легко расстраиваетесь?"),
         U("xafa bo‘laman"), U("xafa bo‘lmayman"), reverse=True),
    Item("O", L("Xayolingiz kuchsizmi?", "Воображение у вас слабое?"),
         U("kuchsiz"), U("kuchsiz emas"), kind="deg", reverse=True),
    Item("E", L("To‘yu tadbirlarda ko‘p odam bilan gaplashasizmi?", "На мероприятиях вы общаетесь со многими людьми?"),
         U("gaplashaman"), U("gaplashmayman")),
    Item("A", L("Boshqalarning hayoti sizga qiziqmi?", "Вам интересна жизнь других людей?"),
         U("qiziq"), U("qiziq emas"), kind="deg"),
    Item("C", L("Tartibni yoqtirasizmi?", "Вы любите порядок?"),
         U("yoqtiraman"), U("yoqtirmayman")),
    Item("S", L("Kayfiyatingiz o‘zgarib turadimi?", "Ваше настроение меняется?"),
         U("o‘zgaradi"), U("o‘zgarmaydi"), reverse=True),
    Item("O", L("Narsalarni tez tushunasizmi?", "Вы быстро всё схватываете?"),
         U("tushunaman"), U("tushunmayman")),
    Item("E", L("O‘zingizga e’tibor tortishdan qochasizmi?", "Вы избегаете привлекать к себе внимание?"),
         U("qochaman"), U("qochmayman"), reverse=True),
    Item("A", L("Boshqalar uchun vaqt ajratasizmi?", "Вы находите время для других?"),
         U("ajrataman"), U("ajratmayman")),
    Item("C", L("Vazifangizdan bo‘yin tovlaysizmi?", "Вы уклоняетесь от своих обязанностей?"),
         U("bo‘yin tovlayman"), U("bo‘yin tovlamayman"), reverse=True),
    Item("S", L("Kayfiyatingiz keskin o‘zgaradimi?", "У вас бывают резкие перепады настроения?"),
         U("keskin o‘zgaradi"), U("keskin o‘zgarmaydi"), reverse=True),
    Item("O", L("Og‘ir, murakkab so‘zlarni ishlatasizmi?", "Вы используете сложные слова?"),
         U("ishlataman"), U("ishlatmayman")),
    Item("E", L("E’tibor markazida bo‘lishni yoqtirasizmi?", "Вам нравится быть в центре внимания?"),
         U("yoqtiraman"), U("yoqtirmayman")),
    Item("A", L("Boshqalarning kayfiyatini sezib turasizmi?", "Вы чувствуете настроение других людей?"),
         U("sezaman"), U("sezmayman")),
    Item("C", L("Belgilangan jadvalga amal qilasizmi?", "Вы придерживаетесь расписания?"),
         U("amal qilaman"), U("amal qilmayman")),
    Item("S", L("Tez jahlingiz chiqadimi?", "Вы легко раздражаетесь?"),
         U("chiqadi"), U("chiqmaydi"), reverse=True),
    Item("O", L("O‘ylanib o‘tirishni yoqtirasizmi?", "Вы любите размышлять?"),
         U("yoqtiraman"), U("yoqtirmayman")),
    Item("E", L("Notanish odam oldida kamgap bo‘lasizmi?", "С незнакомыми людьми вы молчаливы?"),
         U("kamgap bo‘laman"), U("kamgap bo‘lmayman"), reverse=True),
    Item("A", L("Odamlar yoningizda o‘zini erkin his qiladimi?", "Рядом с вами людям спокойно?"),
         U("erkin his qiladi"), U("erkin his qilmaydi")),
    Item("C", L("Ishingizda aniqlikni talab qilasizmi?", "В работе вы требовательны к точности?"),
         U("talab qilaman"), U("talab qilmayman")),
    Item("S", L("Ichingiz siqiladimi?", "Вам бывает тоскливо?"),
         U("siqiladi"), U("siqilmaydi"), reverse=True),
    Item("O", L("Boshingiz fikrlarga to‘lami?", "Вы полны идей?"),
         U("to‘la"), U("to‘la emas"), kind="deg"),
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
