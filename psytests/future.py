"""Kelajak salohiyati — 28 element, 9 yo'nalish.

Bu **mualliflik so'rovnomasi**, tekshirilgan asbob emas. Har bir yo'nalish
uzoq muddatli kuzatuvlarda hayotdagi natija bilan bog'liqligi topilgan
xususiyatga mos keladi, lekin so'rovnomaning o'zi alohida psixometrik
sinovdan o'tmagan. Bu foydalanuvchiga ham ochiq aytiladi.
"""
from .base import Item, L, Scale, TestDef, U

SCALES = {
    "maqsad": Scale(
        key="maqsad", emoji="🎯", weight=1.2,
        name=L("Maqsad va qat’iyat", "Цель и упорство"),
        levels={
            "high": L(
                "Bitta maqsadga yillab intila olasiz — bu kam odamda bor.",
                "Вы можете идти к одной цели годами — это есть у немногих.",
            ),
            "low": L(
                "Bitta maqsad tanlang va 90 kun davomida yangisiga o‘tmang. "
                "Qat’iyat tug‘ma emas, u aynan shunday cheklov bilan o‘sadi.",
                "Выберите одну цель и 90 дней не переключайтесь на новую. "
                "Упорство не врождённое — оно растёт именно через такое "
                "ограничение.",
            ),
        },
    ),
    "intizom": Scale(
        key="intizom", emoji="🧱", weight=1.3,
        name=L("Intizom va mas’uliyat", "Дисциплина и ответственность"),
        levels={
            "high": L(
                "Rejaga amal qilasiz va va’dani bajarasiz — natijani eng "
                "ishonchli ko‘rsatadigan xususiyat shu.",
                "Следуете плану и держите слово — это самый надёжный "
                "предиктор результата.",
            ),
            "low": L(
                "Kunni oldingi kechqurun rejalashtiring va ertalab eng og‘ir "
                "ishdan boshlang. Kechiktirish irodadan emas, tashqi tartibdan "
                "tuzaladi: aniq muddat, eslatma, hisobot beradigan odam.",
                "Планируйте день накануне и начинайте утро с самого тяжёлого. "
                "Прокрастинация лечится не силой воли, а внешним порядком: "
                "срок, напоминание, человек, перед которым отчитываетесь.",
            ),
        },
    ),
    "tafakkur": Scale(
        key="tafakkur", emoji="🌱", weight=1.0,
        name=L("O‘sish va o‘rganish", "Рост и обучение"),
        levels={
            "high": L(
                "Xatoni o‘sish uchun ishlatasiz va o‘rganishni to‘xtatmagansiz — "
                "qiyin sohaga kirishda eng katta ustunlik.",
                "Ошибки обращаете в рост и не бросили учиться — главное "
                "преимущество при входе в сложную сферу.",
            ),
            "low": L(
                "«Men buni <b>hali</b> bilmayman» deb gapirishga o‘rganing va "
                "haftasiga bitta yangi narsa o‘rganib boring. Qobiliyatni "
                "o‘zgarmas deb bilgan odam qiyinchilikdan qochadi.",
                "Приучите себя говорить «я этого <b>пока</b> не умею» и "
                "осваивайте одну новую вещь в неделю. Тот, кто считает "
                "способности неизменными, начинает избегать трудного.",
            ),
        },
    ),
    "nazorat": Scale(
        key="nazorat", emoji="🧘", weight=1.2,
        name=L("O‘zini tuta olish", "Самоконтроль"),
        levels={
            "high": L(
                "Bugungi zavqni ertangi natijaga almashtira olasiz — 32 yillik "
                "Dunedin kuzatuvida aynan shu ko‘nikma keyingi sog‘liq va "
                "daromadni ko‘rsatgan.",
                "Умеете менять сегодняшнее удовольствие на завтрашний "
                "результат — в 32-летнем наблюдении Данидин именно этот навык "
                "предсказывал здоровье и доход.",
            ),
            "low": L(
                "Iroda bilan kurashmang — muhitni o‘zgartiring. Telefonni "
                "boshqa xonaga qo‘yish «o‘zimni tutaman» degan qarordan bir "
                "necha barobar kuchli ishlaydi.",
                "Не боритесь силой воли — меняйте среду. Убрать телефон в "
                "другую комнату работает в разы сильнее, чем решение «я себя "
                "сдержу».",
            ),
        },
    ),
    "mustaqillik": Scale(
        key="mustaqillik", emoji="🧭", weight=1.0,
        name=L("O‘ziga bog‘liqlik hissi", "Опора на себя"),
        levels={
            "high": L(
                "Natija uchun javobgarlikni o‘zingiz olasiz — o‘zgarish uchun "
                "eng ishonchli poydevor.",
                "Ответственность за результат берёте на себя — самая надёжная "
                "основа для перемен.",
            ),
            "low": L(
                "Har muvaffaqiyatsizlikdan keyin bitta savolga yozma javob "
                "bering: «men nimani boshqacha qila olardim?» Aybni tashqariga "
                "chiqarish qulay, lekin u boshqaruvni ham tashqariga beradi.",
                "После каждой неудачи письменно ответьте на один вопрос: «что я "
                "мог сделать иначе?» Выносить вину вовне удобно, но вместе с "
                "ней вы выносите и управление.",
            ),
        },
    ),
    "muloqot": Scale(
        key="muloqot", emoji="🤝", weight=1.1,
        name=L("Odamlar bilan aloqa", "Связи с людьми"),
        levels={
            "high": L(
                "Atrofingizdagi mustahkam aloqa — eng qimmatli boyligingiz. "
                "80 yillik Harvard kuzatuvida sog‘liq va baxtni aynan shu "
                "belgilagan.",
                "Крепкие связи вокруг — самое ценное, что у вас есть. В "
                "80-летнем гарвардском наблюдении именно они определяли "
                "здоровье и счастье.",
            ),
            "low": L(
                "Haftada bitta odam bilan chin dildan gaplashing va bitta "
                "ustoz qidiring. Ish ham, mijoz ham, maslahat ham odam orqali "
                "keladi.",
                "Раз в неделю поговорите с кем-то по-настоящему и найдите "
                "одного наставника. И работа, и клиенты, и совет приходят "
                "через людей.",
            ),
        },
    ),
    "bardosh": Scale(
        key="bardosh", emoji="🛡", weight=1.0,
        name=L("Bardoshlilik", "Стрессоустойчивость"),
        levels={
            "high": L(
                "Zarbadan tez tiklanasiz va bosim ostida aniq fikrlaysiz.",
                "После удара быстро восстанавливаетесь и под давлением "
                "мыслите ясно.",
            ),
            "low": L(
                "Tiklanish tezligi ustida ishlang: barqaror uyqu, kunlik "
                "harakat va gaplashadigan bitta odam. Uchtasi birga ishlaydi, "
                "alohida deyarli ta’sir bermaydi.",
                "Работайте над скоростью восстановления: стабильный сон, "
                "движение каждый день и один человек, с которым можно "
                "поговорить. Втроём работают, по отдельности почти нет.",
            ),
        },
    ),
    "uyqu": Scale(
        key="uyqu", emoji="😴", weight=0.9,
        name=L("Uyqu va tana", "Сон и тело"),
        levels={
            "high": L(
                "Uyqu rejimingiz barqaror va tanangiz harakatda. Bu diqqat, "
                "xotira va kayfiyatga to‘g‘ridan-to‘g‘ri ishlaydi.",
                "Режим сна стабильный, тело в движении. Это напрямую работает "
                "на внимание, память и настроение.",
            ),
            "low": L(
                "Avval uyquni tuzating: har kuni bir vaqtda yoting va "
                "telefonni yotoqdan chiqaring. Uyqusizlik dangasalik va "
                "irodasizlik bo‘lib ko‘rinadi — aslida tana yetishmayapti.",
                "Сначала наладьте сон: ложитесь в одно время и уберите телефон "
                "из постели. Недосып выглядит как лень и безволие — на самом "
                "деле телу просто не хватает ресурса.",
            ),
        },
    ),
    "ichki": Scale(
        key="ichki", emoji="🕊", weight=1.0,
        name=L("Ichki boylik", "Внутреннее богатство"),
        levels={
            "high": L(
                "Hayotingizda ma’no bor va boringizga shukr qila olasiz. Uzoq "
                "kuzatuvlarda hayotida ma’no ko‘rgan odamlar sog‘lomroq va "
                "uzoqroq yashagan.",
                "В вашей жизни есть смысл, и вы умеете быть благодарным за то, "
                "что имеете. В длительных наблюдениях люди, видящие смысл, "
                "жили дольше и здоровее.",
            ),
            "low": L(
                "Har kuni uchta minnatdor bo‘ladigan narsani yozib boring va "
                "o‘zingizni boshqalarning boriga qarab o‘lchamang. Taqqoslash — "
                "qanoatni eng tez yeydigan odat.",
                "Каждый день записывайте три вещи, за которые благодарны, и не "
                "меряйте себя чужим достатком. Сравнение — привычка, которая "
                "быстрее всего съедает удовлетворённость.",
            ),
        },
    ),
}

ITEMS = [
    # Maqsad va qat'iyat
    Item("maqsad", L("Yillab intiladigan katta maqsadingiz bormi?",
                     "Есть ли у вас большая цель, к которой вы идёте годами?"),
         U("bor"), U("yo‘q"), kind="yesno"),
    Item("maqsad", L("Boshlagan ishingizni qiyinlashsa ham oxiriga yetkazasizmi?",
                     "Доводите ли вы начатое до конца, даже когда стало трудно?"),
         U("yetkazaman"), U("yetkazmayman")),
    Item("maqsad", L("Yangi qiziq narsa chiqishi bilan eski maqsadingizni tashlab ketasizmi?",
                     "Бросаете ли вы прежнюю цель, как только появляется что-то новое?"),
         U("tashlab ketaman"), U("tashlab ketmayman"), reverse=True),
    # Intizom va mas'uliyat
    Item("intizom", L("Kuningizni oldindan rejalashtirasizmi?",
                      "Планируете ли вы день заранее?"),
         U("rejalashtiraman"), U("rejalashtirmayman")),
    Item("intizom", L("Bergan va’dangizni o‘z vaqtida bajarasizmi?",
                      "Выполняете ли вы обещания в срок?"),
         U("bajaraman"), U("bajarmayman")),
    Item("intizom", L("Muhim ishni oxirgi kunga qoldirasizmi?",
                      "Откладываете ли вы важные дела на последний день?"),
         U("qoldiraman"), U("qoldirmayman"), reverse=True),
    # O'sish va o'rganish
    Item("tafakkur", L("Qobiliyatni mehnat bilan o‘stirsa bo‘ladi deb hisoblaysizmi?",
                       "Считаете ли вы, что способности можно развить трудом?"),
         U("hisoblayman"), U("hisoblamayman"), kind="yesno"),
    Item("tafakkur", L("Xatolaringizdan saboq olasizmi?",
                       "Извлекаете ли вы урок из своих ошибок?"),
         U("saboq olaman"), U("saboq olmayman")),
    Item("tafakkur", L("Har hafta yangi bir narsa o‘rganasizmi?",
                       "Узнаёте ли вы каждую неделю что-то новое?"),
         U("o‘rganaman"), U("o‘rganmayman")),
    # O'zini tuta olish
    Item("nazorat", L("Katta natija uchun bugungi zavqdan voz kecha olasizmi?",
                      "Можете ли отказаться от удовольствия сегодня ради большого результата?"),
         U("voz kecha olaman"), U("voz kecha olmayman")),
    Item("nazorat", L("Telefon va ijtimoiy tarmoq sizni ishdan chalg‘itadimi?",
                      "Отвлекают ли вас телефон и соцсети от работы?"),
         U("chalg‘itadi"), U("chalg‘itmaydi"), reverse=True),
    Item("nazorat", L("Jahlingiz chiqqanda o‘zingizni tuta olasizmi?",
                      "Можете ли вы сдержаться, когда разозлились?"),
         U("tuta olaman"), U("tuta olmayman")),
    # O'ziga bog'liqlik hissi
    Item("mustaqillik", L("Hayotingizdagi natija ko‘proq o‘z qaroringizga bog‘liqmi?",
                          "Результат в вашей жизни больше зависит от ваших решений?"),
         U("bog‘liq"), U("bog‘liq emas"), kind="deg"),
    Item("mustaqillik", L("Ishingiz yurishmasa, avval o‘zingizdan sabab qidirasizmi?",
                          "Если не получается, ищете ли вы причину сначала в себе?"),
         U("qidiraman"), U("qidirmayman")),
    Item("mustaqillik", L("Ahvolingiz ko‘proq omadga va boshqalarga bog‘liq deb o‘ylaysizmi?",
                          "Думаете ли вы, что ваше положение больше зависит от удачи и других?"),
         U("shunday o‘ylayman"), U("unday o‘ylamayman"), kind="yesno", reverse=True),
    # Odamlar bilan aloqa
    Item("muloqot", L("Qiyin paytda rostdan yordam beradigan yaqinlaringiz bormi?",
                      "Есть ли близкие, которые в трудный момент правда помогут?"),
         U("bor"), U("yo‘q"), kind="yesno"),
    Item("muloqot", L("Yangi odam bilan tanishish sizga osonmi?",
                      "Легко ли вам знакомиться с новыми людьми?"),
         U("oson"), U("oson emas"), kind="deg"),
    Item("muloqot", L("Sizdan tajribaliroq ustoz yoki maslahatchingiz bormi?",
                      "Есть ли у вас наставник или советчик опытнее вас?"),
         U("bor"), U("yo‘q"), kind="yesno"),
    # Bardoshlilik
    Item("bardosh", L("Ishingiz yurishmay qolsa, tez o‘zingizni qo‘lga olasizmi?",
                      "Быстро ли вы приходите в себя после неудачи?"),
         U("qo‘lga olaman"), U("qo‘lga ololmayman")),
    Item("bardosh", L("Vaziyat og‘ir bo‘lsa ham aniq fikrlay olasizmi?",
                      "Сохраняете ли вы ясность мышления в тяжёлой ситуации?"),
         U("fikrlay olaman"), U("fikrlay olmayman")),
    Item("bardosh", L("Kelajak haqida o‘ylasangiz, xavotir bosadimi?",
                      "Когда думаете о будущем, накрывает ли тревога?"),
         U("bosadi"), U("bosmaydi"), reverse=True),
    # Uyqu va tana
    Item("uyqu", L("Uyqu vaqtingiz har kuni bir xilmi?",
                   "Одинаковое ли у вас время сна каждый день?"),
         U("bir xil"), U("bir xil emas"), kind="yesno"),
    Item("uyqu", L("Ertalab o‘zingizni dam olgan his qilasizmi?",
                   "Чувствуете ли вы себя отдохнувшим по утрам?"),
         U("dam olgan bo‘laman"), U("dam olgan bo‘lmayman")),
    Item("uyqu", L("Uxlash vaqti kelganda ham telefonda o‘tirib qolasizmi?",
                   "Засиживаетесь ли вы в телефоне, когда уже пора спать?"),
         U("o‘tirib qolaman"), U("o‘tirib qolmayman"), reverse=True),
    Item("uyqu", L("Haftada kamida uch marta jismoniy harakat qilasizmi?",
                   "Двигаетесь ли вы физически хотя бы три раза в неделю?"),
         U("qilaman"), U("qilmayman")),
    # Ichki boylik
    Item("ichki", L("Hayotingizda aniq ma’no va yo‘nalish bormi?",
                    "Есть ли в вашей жизни ясный смысл и направление?"),
         U("bor"), U("yo‘q"), kind="yesno"),
    Item("ichki", L("Boringizga shukr qila olasizmi?",
                    "Умеете ли вы быть благодарным за то, что имеете?"),
         U("shukr qilaman"), U("shukr qilmayman")),
    Item("ichki", L("Baxt ko‘proq pul va narsalarga bog‘liq deb o‘ylaysizmi?",
                    "Думаете ли вы, что счастье больше зависит от денег и вещей?"),
         U("shunday o‘ylayman"), U("unday o‘ylamayman"), kind="yesno", reverse=True),
]

TEST = TestDef(
    key="future",
    emoji="🎯",
    title=L("Kelajak salohiyati", "Потенциал будущего"),
    tagline=L(
        "Odatlaringiz uzoq muddatda nima beradi",
        "Что ваши привычки дадут в долгую",
    ),
    intro=L(
        "28 ta gap beriladi. Har biriga <b>o‘zingizga qanchalik to‘g‘ri "
        "kelishiga</b> qarab javob bering.\n\n"
        "To‘g‘ri javob yo‘q. Eng foydali natija eng halol javobdan chiqadi — "
        "o‘zingizni yaxshiroq ko‘rsatsangiz, natija ham foydasiz bo‘ladi.",
        "Будет 28 утверждений. Отвечайте, насколько каждое <b>про вас</b>.\n\n"
        "Правильных ответов нет. Самый полезный результат даёт самый честный "
        "ответ — если приукрашивать, результат окажется бесполезным.",
    ),
    source=L(
        "Bu — <b>mualliflik so‘rovnomasi</b>, tekshirilgan asbob emas. Har "
        "bir yo‘nalish uzoq muddatli kuzatuvlarda natija bilan bog‘liqligi "
        "topilgan xususiyatga mos keladi: Duckworth (qat’iyat), Big Five "
        "vijdonliligi, Dweck (o‘sish tafakkuri), Moffitt/Dunedin (o‘zini "
        "tuta olish), Rotter, Harvard Grant Study (aloqalar), Hill va Turiano "
        "(hayot ma’nosi va umr davomiyligi, 2014), Emmons va McCullough "
        "(shukronalik, 2003), uyqu va diqqat bo‘yicha uyqu tadqiqotlari. "
        "Lekin so‘rovnomaning o‘zi alohida psixometrik sinovdan o‘tmagan.",
        "Это <b>авторский опросник</b>, а не проверенный инструмент. Каждое "
        "направление соответствует черте, связь которой с результатами "
        "найдена в длительных наблюдениях: Duckworth (упорство), "
        "добросовестность Big Five, Dweck (мышление роста), Moffitt/Данидин "
        "(самоконтроль), Rotter, Гарвардское Grant Study (связи), Hill и "
        "Turiano (смысл жизни и продолжительность жизни, 2014), Emmons и "
        "McCullough (благодарность, 2003), исследования сна и внимания. Но "
        "сам опросник отдельную психометрическую проверку не проходил.",
    ),
    validated=False,
    kind="index",
    scales=SCALES,
    items=ITEMS,
    minutes=L("5–7 daqiqa", "5–7 минут"),
    ask_age=True,
)
