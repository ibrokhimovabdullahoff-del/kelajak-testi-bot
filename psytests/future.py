"""Kelajak salohiyati — 28 element, 9 yo'nalish.

Bu **mualliflik so'rovnomasi**, tekshirilgan asbob emas. Har bir yo'nalish
uzoq muddatli kuzatuvlarda hayotdagi natija bilan bog'liqligi topilgan
xususiyatga mos keladi, lekin so'rovnomaning o'zi alohida psixometrik
sinovdan o'tmagan. Bu foydalanuvchiga ham ochiq aytiladi.
"""
from .base import Item, L, Scale, TestDef

ANCHORS = [
    L("1️⃣ Umuman to‘g‘ri emas", "1️⃣ Совсем не про меня"),
    L("2️⃣ Kamdan-kam", "2️⃣ Редко"),
    L("3️⃣ Ba’zan", "3️⃣ Иногда"),
    L("4️⃣ Ko‘pincha", "4️⃣ Часто"),
    L("5️⃣ To‘liq to‘g‘ri", "5️⃣ Точно про меня"),
]

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
    Item("maqsad", L(
        "Katta maqsadim bor — oylab, yillab bo‘lsa ham men undan voz "
        "kechmayman.",
        "У меня есть большая цель, и я не отказываюсь от неё, даже если идти "
        "к ней месяцами и годами.")),
    Item("maqsad", L(
        "Boshlagan ishimni qiyinlashsa ham oxiriga yetkazaman.",
        "Начатое я довожу до конца, даже если стало трудно.")),
    Item("maqsad", L(
        "Yangi qiziq narsa chiqishi bilan eski maqsadimni tashlab ketaman.",
        "Как только появляется что-то новое и интересное, я бросаю прежнюю "
        "цель."), reverse=True),
    # Intizom
    Item("intizom", L(
        "Kunimni oldindan rejalashtiraman va rejaga amal qilaman.",
        "Я планирую день заранее и следую плану.")),
    Item("intizom", L(
        "Bergan va’damni o‘z vaqtida bajaraman.",
        "Я выполняю обещания в срок.")),
    Item("intizom", L(
        "Muhim ishni oxirgi kunga qoldiraman.",
        "Важные дела я откладываю на последний день."), reverse=True),
    # O'sish va o'rganish
    Item("tafakkur", L(
        "Qobiliyat tug‘ma emas — mehnat bilan o‘stirsa bo‘ladi deb "
        "hisoblayman.",
        "Я считаю, что способности не даны от рождения — их можно развить "
        "трудом.")),
    Item("tafakkur", L(
        "Xatolarim meni to‘xtatmaydi, men ulardan saboq olaman.",
        "Ошибки меня не останавливают, я извлекаю из них урок.")),
    Item("tafakkur", L(
        "Har hafta yangi bir narsa o‘rganaman (kitob, kurs, amaliyot).",
        "Каждую неделю я узнаю что-то новое (книга, курс, практика).")),
    # O'zini tuta olish
    Item("nazorat", L(
        "Katta natija uchun bugungi zavqdan voz kecha olaman.",
        "Ради большого результата я могу отказаться от удовольствия "
        "сегодня.")),
    Item("nazorat", L(
        "Telefon va ijtimoiy tarmoq meni ishimdan tez chalg‘itadi.",
        "Телефон и соцсети быстро отвлекают меня от работы."), reverse=True),
    Item("nazorat", L(
        "Jahlim chiqqanda ham o‘zimni tuta olaman.",
        "Даже разозлившись, я могу себя сдержать.")),
    # O'ziga bog'liqlik hissi
    Item("mustaqillik", L(
        "Hayotimdagi natija ko‘p jihatdan mening qarorimga bog‘liq.",
        "Результаты в моей жизни во многом зависят от моих решений.")),
    Item("mustaqillik", L(
        "Ishim yurishmasa, avval o‘zimdan sabab qidiraman.",
        "Если не получается, причину я ищу сначала в себе.")),
    Item("mustaqillik", L(
        "Ahvolim ko‘proq omadga va boshqa odamlarga bog‘liq deb o‘ylayman.",
        "Я думаю, что моё положение больше зависит от удачи и других людей."),
        reverse=True),
    # Odamlar bilan aloqa
    Item("muloqot", L(
        "Qiyin paytda menga rostdan yordam beradigan yaqinlarim bor.",
        "У меня есть близкие, которые в трудный момент помогут по-настоящему.")),
    Item("muloqot", L(
        "Yangi odam bilan tanishish men uchun oson.",
        "Мне легко знакомиться с новыми людьми.")),
    Item("muloqot", L(
        "Menda o‘zimdan tajribaliroq ustoz yoki maslahatchi bor.",
        "У меня есть наставник или советчик опытнее меня.")),
    # Bardoshlilik
    Item("bardosh", L(
        "Ishim yurishmay qolsa, tez o‘zimni qo‘lga olaman.",
        "После неудачи я быстро прихожу в себя.")),
    Item("bardosh", L(
        "Vaziyat og‘ir bo‘lsa ham aniq fikrlay olaman.",
        "Даже в тяжёлой ситуации я сохраняю ясность мышления.")),
    Item("bardosh", L(
        "Kelajak haqida o‘ylasam, ko‘proq xavotir bosadi.",
        "Когда я думаю о будущем, чаще всего накрывает тревога."),
        reverse=True),
    # Uyqu va tana
    Item("uyqu", L(
        "Har kuni deyarli bir vaqtda yotib, bir vaqtda turaman.",
        "Я ложусь и встаю примерно в одно и то же время.")),
    Item("uyqu", L(
        "Ertalab o‘zimni dam olgan va tetik his qilaman.",
        "По утрам я чувствую себя отдохнувшим.")),
    Item("uyqu", L(
        "Uxlash vaqti kelganda ham telefonni qo‘ymayman.",
        "Когда пора спать, я всё равно не откладываю телефон."), reverse=True),
    Item("uyqu", L(
        "Haftada kamida uch marta jismoniy harakat qilaman.",
        "Я двигаюсь физически хотя бы три раза в неделю.")),
    # Ichki boylik
    Item("ichki", L(
        "Hayotimda aniq ma’no va yo‘nalish bor.",
        "В моей жизни есть ясный смысл и направление.")),
    Item("ichki", L(
        "Borimga shukr qilaman, boshqalarnikiga qarab o‘zimni kam his "
        "qilmayman.",
        "Я благодарен за то, что имею, и не чувствую себя хуже, глядя на "
        "других.")),
    Item("ichki", L(
        "Baxt ko‘proq pul va narsalarga bog‘liq deb o‘ylayman.",
        "Я думаю, что счастье больше зависит от денег и вещей."),
        reverse=True),
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
    anchors=ANCHORS,
    scales=SCALES,
    items=ITEMS,
    minutes=L("5–7 daqiqa", "5–7 минут"),
    ask_age=True,
)
