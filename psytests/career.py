"""Kasb yo'nalishi — RIASEC (Holland) modeli asosida, 30 element.

Model: John Holland'ning kasbiy qiziqishlar nazariyasi (RIASEC) — dunyoda
kasb tanlash bo'yicha eng keng qo'llanadigan tizim; AQSh Mehnat vazirligining
O*NET bazasi ham shu modelga qurilgan.

Muhim: elementlar matni bizniki. Model ochiq va ilmiy, lekin bu aynan
so'rovnoma alohida validatsiyadan o'tgan asbob emas — u qiziqish yo'nalishini
ko'rsatadi, qobiliyatni yoki muvaffaqiyatni o'lchamaydi. Shu narsa
foydalanuvchiga ham ochiq aytiladi.
"""
from .base import Item, L, Scale, TestDef

SCALES = {
    "R": Scale(
        key="R", emoji="🔧",
        name=L("Amaliy (Realistic)", "Практик (Realistic)"),
        levels={"high": L(
            "Qo‘l bilan qilinadigan, natijasi ko‘rinib turadigan ish sizniki.\n"
            "<b>Kasblar:</b> muhandis, mexanik, elektrik, quruvchi, logist, "
            "fermer, texnik xizmat mutaxassisi.",
            "Ваше — работа руками с видимым результатом.\n"
            "<b>Профессии:</b> инженер, механик, электрик, строитель, логист, "
            "фермер, техник по обслуживанию.",
        )},
    ),
    "I": Scale(
        key="I", emoji="🔬",
        name=L("Tadqiqotchi (Investigative)", "Исследователь (Investigative)"),
        levels={"high": L(
            "Sizni sabab, ma’lumot va murakkab masala qiziqtiradi.\n"
            "<b>Kasblar:</b> dasturchi, ma’lumot tahlilchisi, shifokor, olim, "
            "farmatsevt, moliyaviy analitik, kiberxavfsizlik mutaxassisi.",
            "Вас занимают причины, данные и сложные задачи.\n"
            "<b>Профессии:</b> программист, аналитик данных, врач, учёный, "
            "фармацевт, финансовый аналитик, специалист по кибербезопасности.",
        )},
    ),
    "A": Scale(
        key="A", emoji="🎨",
        name=L("Ijodkor (Artistic)", "Творец (Artistic)"),
        levels={"high": L(
            "Sizga erkinlik va qat’iy qolipsiz muhit kerak; yangi narsa "
            "yaratishning o‘zi zavq beradi.\n"
            "<b>Kasblar:</b> dizayner, kontent yaratuvchi, videograf, "
            "arxitektor, jurnalist, marketolog, SMM mutaxassisi.",
            "Вам нужны свобода и среда без жёстких рамок; создание нового само "
            "по себе в радость.\n"
            "<b>Профессии:</b> дизайнер, создатель контента, видеограф, "
            "архитектор, журналист, маркетолог, SMM-специалист.",
        )},
    ),
    "S": Scale(
        key="S", emoji="❤️",
        name=L("Ijtimoiy (Social)", "Помогающий (Social)"),
        levels={"high": L(
            "Odamlarga foyda keltirganingizda quvvat olasiz; natijani "
            "ularning o‘zgarishida ko‘rasiz.\n"
            "<b>Kasblar:</b> o‘qituvchi, psixolog, shifokor, hamshira, "
            "murabbiy, HR mutaxassisi, ijtimoiy xodim.",
            "Вы наполняетесь, когда приносите людям пользу; результат видите в "
            "их изменениях.\n"
            "<b>Профессии:</b> учитель, психолог, врач, медсестра, тренер, "
            "HR-специалист, социальный работник.",
        )},
    ),
    "E": Scale(
        key="E", emoji="📈",
        name=L("Tadbirkor (Enterprising)", "Предприниматель (Enterprising)"),
        levels={"high": L(
            "Boshqarish va natija uchun javob berish sizni qiziqtiradi, "
            "xavfdan qo‘rqmaysiz.\n"
            "<b>Kasblar:</b> tadbirkor, sotuv menejeri, loyiha rahbari, "
            "advokat, rieltor, mahsulot menejeri.",
            "Вас притягивают управление и ответственность за результат, риска "
            "вы не боитесь.\n"
            "<b>Профессии:</b> предприниматель, менеджер по продажам, "
            "руководитель проектов, юрист, риелтор, продакт-менеджер.",
        )},
    ),
    "C": Scale(
        key="C", emoji="📋",
        name=L("Tartibli (Conventional)", "Организатор (Conventional)"),
        levels={"high": L(
            "Aniqlik va tartibni qadrlaysiz; xatoni sezish sizda tabiiy "
            "chiqadi.\n"
            "<b>Kasblar:</b> buxgalter, moliyachi, auditor, bank xodimi, "
            "hujjat aylanmasi mutaxassisi, sifat nazoratchisi.",
            "Вы цените точность и порядок; ошибки замечаете естественно.\n"
            "<b>Профессии:</b> бухгалтер, финансист, аудитор, банковский "
            "работник, специалист по документообороту, контролёр качества.",
        )},
    ),
}

ITEMS = [
    # R
    Item("R", L("Buzilgan texnikani ochib, o‘zingiz ta’mirlash.",
                "Разобрать сломанную технику и починить её самому."), kind="interest"),
    Item("R", L("Uskuna yoki asbob bilan aniq o‘lchab ishlash.",
                "Работать с инструментом, выполняя точные замеры."), kind="interest"),
    Item("R", L("Ochiq havoda, jismoniy harakat talab qiladigan ish.",
                "Работа на воздухе, требующая физической активности."), kind="interest"),
    Item("R", L("Chizmaga qarab biror narsani yig‘ish yoki qurish.",
                "Собрать или построить что-то по чертежу."), kind="interest"),
    Item("R", L("Transport, texnika yoki jihozlarni boshqarish.",
                "Управлять транспортом, техникой или оборудованием."), kind="interest"),
    # I
    Item("I", L("Muammoning sababini raqamlar orqali aniqlash.",
                "Находить причину проблемы через цифры."), kind="interest"),
    Item("I", L("Ilmiy maqola yoki tadqiqot natijalarini o‘qish.",
                "Читать научные статьи и результаты исследований."), kind="interest"),
    Item("I", L("Murakkab masalani uzoq vaqt yechib o‘tirish.",
                "Долго сидеть над сложной задачей."), kind="interest"),
    Item("I", L("Tajriba o‘tkazib, faraz to‘g‘riligini tekshirish.",
                "Ставить эксперимент и проверять гипотезу."), kind="interest"),
    Item("I", L("Katta ma’lumot to‘plamidan qonuniyat topish.",
                "Искать закономерность в большом массиве данных."), kind="interest"),
    # A
    Item("A", L("Dizayn, rasm yoki video ustida ishlash.",
                "Работать над дизайном, изображением или видео."), kind="interest"),
    Item("A", L("Matn, ssenariy yoki musiqa yozish.",
                "Писать текст, сценарий или музыку."), kind="interest"),
    Item("A", L("Tayyor qolipsiz, o‘z uslubingizda ishlash.",
                "Работать без готовых шаблонов, в своём стиле."), kind="interest"),
    Item("A", L("Biror g‘oyani ko‘rinadigan shaklga aylantirish.",
                "Превращать идею в то, что можно увидеть."), kind="interest"),
    Item("A", L("Ko‘rgazma, konsert yoki ijodiy tadbirda qatnashish.",
                "Участвовать в выставке, концерте или творческом событии."), kind="interest"),
    # S
    Item("S", L("Biror narsani boshqa odamga tushuntirib berish.",
                "Объяснять что-то другому человеку."), kind="interest"),
    Item("S", L("Qiyin ahvoldagi odamni qo‘llab-quvvatlash.",
                "Поддерживать человека в трудной ситуации."), kind="interest"),
    Item("S", L("Bolalar yoki o‘smirlar bilan ishlash.",
                "Работать с детьми или подростками."), kind="interest"),
    Item("S", L("Jamoadagi kelishmovchilikni yarashtirish.",
                "Улаживать разногласия в коллективе."), kind="interest"),
    Item("S", L("Odamlarning sog‘lig‘i yoki farovonligiga xizmat qilish.",
                "Заботиться о здоровье или благополучии людей."), kind="interest"),
    # E
    Item("E", L("Mahsulot yoki xizmatni sotish.",
                "Продавать товар или услугу."), kind="interest"),
    Item("E", L("Jamoani boshqarish va natija uchun javob berish.",
                "Руководить командой и отвечать за результат."), kind="interest"),
    Item("E", L("O‘z biznesingizni ochish va yuritish.",
                "Открыть и вести собственный бизнес."), kind="interest"),
    Item("E", L("Muzokara olib borib, o‘z shartingizni qabul qildirish.",
                "Вести переговоры и добиваться своих условий."), kind="interest"),
    Item("E", L("Yangi loyihani noldan ko‘tarib chiqish.",
                "Поднимать новый проект с нуля."), kind="interest"),
    # C
    Item("C", L("Hujjat va hisobotlarni tartibga solish.",
                "Приводить в порядок документы и отчёты."), kind="interest"),
    Item("C", L("Jadval bilan ishlash, hisob-kitob yuritish.",
                "Работать с таблицами и вести расчёты."), kind="interest"),
    Item("C", L("Aniq qoida va yo‘riqnoma bo‘yicha ishlash.",
                "Работать по чёткому правилу и инструкции."), kind="interest"),
    Item("C", L("Xatolarni topib, ma’lumotni tekshirish.",
                "Находить ошибки и проверять данные."), kind="interest"),
    Item("C", L("Ish jarayonini tizimga solib, tartib o‘rnatish.",
                "Выстраивать процесс и наводить в нём порядок."), kind="interest"),
]

TEST = TestDef(
    key="career",
    emoji="🧭",
    title=L("Kasb yo‘nalishi (RIASEC)", "Профориентация (RIASEC)"),
    tagline=L(
        "Qaysi sohada ishlaganda charchamaysiz",
        "В какой сфере вы не будете выгорать",
    ),
    intro=L(
        "30 ta mashg‘ulot beriladi. Har biri sizga <b>qanchalik "
        "qiziqligini</b> belgilang.\n\n"
        "Muhim: <b>qila olaman-yo‘qligingiz emas, qiziqish</b> so‘ralyapti. "
        "Hozir bilmasangiz ham, qiziq bo‘lsa — qiziq deb belgilang.\n\n"
        "Natijada uch harfli <b>Holland kodi</b> va shu kodga mos kasblar "
        "ro‘yxati chiqadi.",
        "Будет 30 занятий. Отметьте, насколько каждое вам <b>интересно</b>.\n\n"
        "Важно: спрашивается <b>интерес, а не умение</b>. Даже если пока не "
        "умеете — отмечайте «интересно», если это так.\n\n"
        "В результате вы получите трёхбуквенный <b>код Холланда</b> и список "
        "профессий под него.",
    ),
    source=L(
        "John Holland'ning RIASEC modeli — kasb tanlash bo‘yicha dunyodagi "
        "eng keng tarqalgan ilmiy tizim; AQSh Mehnat vazirligining O*NET "
        "bazasi ham shunga qurilgan. Savollar matni bizniki: model ilmiy, "
        "lekin bu aynan so‘rovnoma alohida validatsiyadan o‘tgan emas. "
        "Test qiziqishni ko‘rsatadi, qobiliyatni o‘lchamaydi.",
        "Модель RIASEC Джона Холланда — самая распространённая научная "
        "система профориентации; на ней построена база O*NET Министерства "
        "труда США. Формулировки пунктов наши: модель научная, но именно этот "
        "опросник отдельную валидацию не проходил. Тест показывает интерес, "
        "а не способности.",
    ),
    validated=False,
    kind="interests",
    scales=SCALES,
    items=ITEMS,
    minutes=L("4–6 daqiqa", "4–6 минут"),
    ask_age=False,
)
