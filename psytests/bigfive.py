"""Big Five — IPIP Big-Five Factor Markers (50 element).

Manba: International Personality Item Pool (ipip.ori.org), Goldberg (1992).
IPIP elementlari **ochiq mulk (public domain)** — ruxsatsiz va to'lovsiz
nusxalash, tarjima qilish va tijorat maqsadida ishlatish mumkin.

Bu — botdagi yagona to'liq validatsiyadan o'tgan asbob. Shu sababli natijada
umumiy "ball" chiqarilmaydi: Big Five odamni yaxshi-yomonga ajratmaydi.
"""
from .base import Item, L, Scale, TestDef

ANCHORS = [
    L("1️⃣ Umuman to‘g‘ri emas", "1️⃣ Совсем не про меня"),
    L("2️⃣ Ko‘proq to‘g‘ri emas", "2️⃣ Скорее не про меня"),
    L("3️⃣ Bilmayman", "3️⃣ Не знаю"),
    L("4️⃣ Ko‘proq to‘g‘ri", "4️⃣ Скорее про меня"),
    L("5️⃣ To‘liq to‘g‘ri", "5️⃣ Точно про меня"),
]

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
ITEMS = [
    Item("E", L("Davra men bilan jonlanadi.", "С моим приходом компания оживает.")),
    Item("A", L("Boshqalarning ahvoli meni kam qiziqtiradi.",
                "Меня мало волнует, что происходит с другими."), reverse=True),
    Item("C", L("Har doim tayyor bo‘laman.", "Я всегда подготовлен.")),
    Item("S", L("Tez asabga tegaman.", "Я легко впадаю в стресс."), reverse=True),
    Item("O", L("So‘z boyligim katta.", "У меня богатый словарный запас.")),
    Item("E", L("Ko‘p gapirmayman.", "Я мало говорю."), reverse=True),
    Item("A", L("Odamlar menga qiziq.", "Мне интересны люди.")),
    Item("C", L("Narsalarimni joyiga qo‘ymay tashlab ketaman.",
                "Я разбрасываю свои вещи."), reverse=True),
    Item("S", L("Ko‘p vaqt o‘zimni tinch his qilaman.",
                "Большую часть времени я спокоен.")),
    Item("O", L("Mavhum fikrlarni tushunish menga qiyin.",
                "Мне трудно понимать абстрактные идеи."), reverse=True),
    Item("E", L("Odamlar orasida o‘zimni erkin his qilaman.",
                "Мне комфортно среди людей.")),
    Item("A", L("Odamning ko‘nglini og‘ritadigan gap aytib yuboraman.",
                "Я могу задеть человека словом."), reverse=True),
    Item("C", L("Mayda narsalarga ham e’tibor beraman.",
                "Я обращаю внимание на детали.")),
    Item("S", L("Ko‘p narsadan tashvishlanaman.",
                "Я много о чём тревожусь."), reverse=True),
    Item("O", L("Xayolim boy.", "У меня живое воображение.")),
    Item("E", L("Ko‘zga tashlanmay, chetda turishni yoqtiraman.",
                "Предпочитаю оставаться в тени."), reverse=True),
    Item("A", L("Boshqalarning ahvoliga achinaman.",
                "Я сочувствую переживаниям других.")),
    Item("C", L("Ishni chalkashtirib yuboraman.",
                "Я всё запутываю и порчу."), reverse=True),
    Item("S", L("Kayfiyatim kamdan-kam tushadi.", "Мне редко бывает грустно.")),
    Item("O", L("Mavhum fikrlar meni qiziqtirmaydi.",
                "Абстрактные идеи меня не интересуют."), reverse=True),
    Item("E", L("Gapni birinchi bo‘lib o‘zim boshlayman.",
                "Я первым начинаю разговор.")),
    Item("A", L("Boshqalarning muammosi bilan qiziqmayman.",
                "Меня не интересуют чужие проблемы."), reverse=True),
    Item("C", L("Yumushlarni darrov bajaraman.", "Я сразу выполняю дела.")),
    Item("S", L("Meni osongina bezovta qilish mumkin.",
                "Меня легко вывести из равновесия."), reverse=True),
    Item("O", L("Menda zo‘r fikrlar paydo bo‘ladi.",
                "У меня появляются отличные идеи.")),
    Item("E", L("Aytadigan gapim kam bo‘ladi.",
                "Мне обычно нечего сказать."), reverse=True),
    Item("A", L("Ko‘nglim yumshoq.", "У меня мягкое сердце.")),
    Item("C", L("Narsani joyiga qaytarib qo‘yishni ko‘pincha unutaman.",
                "Я часто забываю класть вещи на место."), reverse=True),
    Item("S", L("Tez xafa bo‘laman.", "Я легко расстраиваюсь."), reverse=True),
    Item("O", L("Xayolim unchalik kuchli emas.",
                "Воображение у меня слабое."), reverse=True),
    Item("E", L("To‘yu tadbirlarda ko‘p odam bilan gaplashaman.",
                "На мероприятиях я общаюсь со многими людьми.")),
    Item("A", L("Ochig‘i, boshqalar meni qiziqtirmaydi.",
                "По правде говоря, другие люди мне неинтересны."), reverse=True),
    Item("C", L("Tartibni yoqtiraman.", "Я люблю порядок.")),
    Item("S", L("Kayfiyatim tez-tez o‘zgaradi.",
                "Моё настроение часто меняется."), reverse=True),
    Item("O", L("Narsalarni tez tushunaman.", "Я быстро всё схватываю.")),
    Item("E", L("O‘zimga e’tibor tortishni yoqtirmayman.",
                "Я не люблю привлекать к себе внимание."), reverse=True),
    Item("A", L("Boshqalar uchun vaqt ajrataman.", "Я нахожу время для других.")),
    Item("C", L("Vazifamdan bo‘yin tovlayman.",
                "Я уклоняюсь от своих обязанностей."), reverse=True),
    Item("S", L("Kayfiyatim keskin o‘zgarib turadi.",
                "У меня бывают резкие перепады настроения."), reverse=True),
    Item("O", L("Og‘ir so‘zlarni ishlataman.", "Я использую сложные слова.")),
    Item("E", L("E’tibor markazida bo‘lish meni qiynamaydi.",
                "Быть в центре внимания меня не смущает.")),
    Item("A", L("Boshqalarning kayfiyatini sezib turaman.",
                "Я чувствую настроение других людей.")),
    Item("C", L("Belgilangan jadvalga amal qilaman.",
                "Я придерживаюсь расписания.")),
    Item("S", L("Tez jahlim chiqadi.", "Я легко раздражаюсь."), reverse=True),
    Item("O", L("O‘ylanib o‘tirishni yoqtiraman.",
                "Я люблю размышлять над вещами.")),
    Item("E", L("Notanish odam oldida kamgap bo‘lib qolaman.",
                "С незнакомыми людьми я молчалив."), reverse=True),
    Item("A", L("Odamlar mening yonimda o‘zini erkin his qiladi.",
                "Рядом со мной людям спокойно.")),
    Item("C", L("Ishimda aniqlikni talab qilaman.",
                "В работе я требователен к точности.")),
    Item("S", L("Ko‘pincha xafa bo‘lib yuraman.",
                "Мне часто бывает тоскливо."), reverse=True),
    Item("O", L("Boshim fikrlarga to‘la.", "Я полон идей.")),
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
        "Har bir gap sizga qanchalik <b>to‘g‘ri kelishini</b> belgilang. "
        "To‘g‘ri javob yo‘q — o‘zingizni qanday ko‘rsatmoqchi ekaningizni "
        "emas, aslida qandayligingizni belgilang.\n\n"
        "Umumiy ball bo‘lmaydi: Big Five odamni yaxshi-yomonga ajratmaydi, "
        "u beshta alohida o‘lchov bo‘yicha profil beradi.",
        "Это <b>единственный полностью проверенный</b> тест в боте.\n\n"
        "Отметьте, насколько каждое утверждение <b>про вас</b>. Правильных "
        "ответов нет — отмечайте не то, каким хотите казаться, а то, какой вы "
        "есть.\n\n"
        "Общего балла не будет: Big Five не делит людей на хороших и плохих, "
        "он даёт профиль по пяти отдельным шкалам.",
    ),
    source=L(
        "IPIP Big-Five Factor Markers (50 element), Goldberg, 1992. "
        "International Personality Item Pool — ochiq mulk (public domain). "
        "Big Five modeli minglab tadqiqotda sinalgan va bugungi akademik "
        "psixologiyada shaxsiyatning asosiy modeli hisoblanadi.",
        "IPIP Big-Five Factor Markers (50 пунктов), Goldberg, 1992. "
        "International Personality Item Pool — общественное достояние "
        "(public domain). Модель Big Five проверена в тысячах исследований и "
        "является основной моделью личности в современной академической "
        "психологии.",
    ),
    validated=True,
    kind="traits",
    anchors=ANCHORS,
    scales=SCALES,
    items=ITEMS,
    minutes=L("7–10 daqiqa", "7–10 минут"),
    ask_age=False,
)
