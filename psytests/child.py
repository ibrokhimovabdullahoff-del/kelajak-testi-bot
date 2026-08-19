"""Farzand salohiyati — ota-ona javob beradigan 24 element, 8 yo'nalish.

Bu ham **mualliflik so'rovnomasi**. Yo'nalishlar bolalikdagi omillar bo'yicha
nashr etilgan tadqiqotlarga mos keladi (Duncan 2007, Jones 2015, Moffitt
2011), lekin so'rovnomaning o'zi tekshirilmagan va tashxis o'rnini bosmaydi.
"""
from .base import Item, L, Scale, TestDef, U

SCALES = {
    "boshqaruv": Scale(
        key="boshqaruv", emoji="🧘", weight=1.3,
        name=L("O‘zini tuta olish", "Саморегуляция"),
        levels={
            "high": L(
                "Diqqatni jamlash va kutish yoshiga nisbatan kuchli — "
                "maktabdagi natija bilan eng ko‘p bog‘langan ko‘rsatkich.",
                "Умение сосредоточиться и ждать развито выше возраста — "
                "показатель, сильнее всего связанный с успехами в школе.",
            ),
            "low": L(
                "Kutishni o‘yin qilib mashq qiling: navbatli o‘yinlar, taymer "
                "bilan qisqa vazifalar, «avval ish — keyin multfilm» tartibi.",
                "Тренируйте ожидание через игру: игры с очередью, короткие "
                "задания по таймеру, правило «сначала дело — потом мультик».",
            ),
        },
    ),
    "qiziqish": Scale(
        key="qiziqish", emoji="📚", weight=1.2,
        name=L("Qiziquvchanlik", "Любознательность"),
        levels={
            "high": L(
                "O‘rganishga qiziqishi tabiiy. Bu yerda vazifa qo‘shish "
                "emas — so‘ndirmaslik.",
                "Тяга к учёбе естественная. Здесь задача не добавить, а не "
                "погасить.",
            ),
            "low": L(
                "Har kuni 15 daqiqa birga kitob o‘qing va savoliga "
                "«bilmayman, kel birga topamiz» deb javob bering.",
                "Читайте вместе по 15 минут в день и отвечайте на вопросы: "
                "«не знаю, давай найдём вместе».",
            ),
        },
    ),
    "tafakkur": Scale(
        key="tafakkur", emoji="🌱", weight=1.0,
        name=L("O‘sish tafakkuri", "Мышление роста"),
        levels={
            "high": L(
                "Qiyinchilikdan qochmaydi va xatodan uyalmaydi — uzoq "
                "muddatda bu bilimdan ham qimmatroq.",
                "Не избегает трудного и не стыдится ошибок — в долгую это "
                "дороже знаний.",
            ),
            "low": L(
                "«Sen aqllisan» o‘rniga «sen ko‘p mehnat qilding» deb "
                "maqtang. Qobiliyat uchun maqtalgan bola qiyin ishdan qocha "
                "boshlaydi (Dweck).",
                "Вместо «ты умный» хвалите «ты хорошо потрудился». Ребёнок, "
                "которого хвалят за способности, начинает избегать трудного "
                "(Dweck).",
            ),
        },
    ),
    "ijtimoiy": Scale(
        key="ijtimoiy", emoji="🤝", weight=1.2,
        name=L("Tengdoshlar bilan til topishish", "Общение со сверстниками"),
        levels={
            "high": L(
                "Tengdoshlari bilan til topishadi va achinishni biladi. "
                "Bog‘chadagi shu ko‘nikma 20 yildan keyingi natija bilan "
                "bog‘liq chiqqan (Jones, 2015).",
                "Ладит со сверстниками и умеет сочувствовать. Этот навык в "
                "детском саду оказался связан с результатами через 20 лет "
                "(Jones, 2015).",
            ),
            "low": L(
                "Birgalikdagi o‘yinni ko‘paytiring va his-tuyg‘u haqida "
                "gaplashing: «u nega xafa bo‘ldi deb o‘ylaysan?»",
                "Больше совместных игр и разговоров о чувствах: «как думаешь, "
                "почему он расстроился?»",
            ),
        },
    ),
    "mehnat": Scale(
        key="mehnat", emoji="🧹", weight=1.0,
        name=L("Mehnatsevarlik", "Трудолюбие"),
        levels={
            "high": L(
                "Mas’uliyatni his qiladi va yordam berishni yoqtiradi.",
                "Чувствует ответственность и любит помогать.",
            ),
            "low": L(
                "Yoshiga mos <b>doimiy</b> uy yumushi bering va uni bekor "
                "qilmang — o‘zingiz qilsangiz tezroq bo‘lsa ham. Bekor "
                "qilingan yumush «bu mening ishim emas» degan xulosa qoldiradi.",
                "Дайте <b>постоянную</b> домашнюю обязанность по возрасту и не "
                "отменяйте её — даже если самим быстрее. Отменённая "
                "обязанность оставляет вывод «это не моё дело».",
            ),
        },
    ),
    "oila": Scale(
        key="oila", emoji="🏡", weight=1.2,
        name=L("Uydagi muhit", "Домашняя среда"),
        levels={
            "high": L(
                "Uydagi muhit — bolangizning eng kuchli tayanchi.",
                "Домашняя среда — самая сильная опора вашего ребёнка.",
            ),
            "low": L(
                "Kuniga 20 daqiqa telefonsiz, faqat unga vaqt ajrating. "
                "Bolaga qattiqlik emas, <b>bir xillik</b> ta’sir qiladi: "
                "bugun mumkin, ertaga mumkin emas — eng buzuvchi tartib.",
                "Выделяйте 20 минут в день без телефона, только на него. На "
                "ребёнка действует не строгость, а <b>одинаковость</b>: "
                "«сегодня можно, завтра нельзя» — самый разрушительный режим.",
            ),
        },
    ),
    "sogliq": Scale(
        key="sogliq", emoji="🌙", weight=0.9,
        name=L("Uyqu va harakat", "Сон и движение"),
        levels={
            "high": L(
                "Uyqu, harakat va ekran muvozanati joyida — bu to‘g‘ridan-"
                "to‘g‘ri diqqat va xotiraga ishlaydi.",
                "Баланс сна, движения и экрана в порядке — это напрямую "
                "работает на внимание и память.",
            ),
            "low": L(
                "Uyqu vaqtini qat’iy belgilang, kechqurun ekranni cheklang. "
                "Uyqusizlik bolada diqqatsizlik va injiqlik bo‘lib "
                "ko‘rinadi — buni ko‘pincha «xarakter» deb o‘ylashadi.",
                "Установите жёсткое время сна, ограничьте экран вечером. "
                "Недосып выглядит как невнимательность и капризность — это "
                "часто принимают за «характер».",
            ),
        },
    ),
    "hissiyot": Scale(
        key="hissiyot", emoji="💛", weight=1.0,
        name=L("Hissiy holat", "Эмоциональное состояние"),
        levels={
            "high": L(
                "Nima his qilayotganini ayta oladi va yangilikdan qo‘rqmaydi.",
                "Умеет сказать, что чувствует, и не боится нового.",
            ),
            "low": L(
                "His-tuyg‘uga nom bering: «sen hozir xafa bo‘ldingmi?» "
                "Tuyg‘usini ayta oladigan bola uni boshqarishni ham o‘rganadi. "
                "«Yig‘lama, hech narsa bo‘lgani yo‘q» teskari ishlaydi.",
                "Называйте чувства: «ты сейчас расстроился?» Ребёнок, который "
                "может назвать чувство, учится им управлять. «Не плачь, ничего "
                "не случилось» работает наоборот.",
            ),
        },
    ),
}

ITEMS = [
    # O'zini tuta olish
    Item("boshqaruv", L("Farzandingiz boshlagan ishini chalg‘imasdan oxiriga yetkazadimi?",
                        "Доводит ли ваш ребёнок начатое до конца, не отвлекаясь?"),
         U("yetkazadi"), U("yetkazmaydi")),
    Item("boshqaruv", L("U navbatini kuta oladimi?",
                        "Умеет ли он дожидаться своей очереди?"),
         U("kuta oladi"), U("kuta olmaydi")),
    Item("boshqaruv", L("Xohlagani darhol bo‘lmasa, jahli chiqadimi?",
                        "Злится ли он, если желаемое не выходит сразу?"),
         U("chiqadi"), U("chiqmaydi"), reverse=True),
    # Qiziquvchanlik
    Item("qiziqish", L("U ko‘p savol beradimi?",
                       "Много ли он задаёт вопросов?"),
         U("beradi"), U("bermaydi")),
    Item("qiziqish", L("Kitob o‘qishni yoki kitob o‘qib berilishini yoqtiradimi?",
                       "Любит ли он читать или слушать, когда читают ему?"),
         U("yoqtiradi"), U("yoqtirmaydi")),
    Item("qiziqish", L("Yangi narsa o‘rganishni o‘zi xohlaydimi?",
                       "Сам ли он хочет узнавать новое?"),
         U("o‘zi xohlaydi"), U("o‘zi xohlamaydi")),
    # O'sish tafakkuri
    Item("tafakkur", L("Topshiriq qiyin bo‘lsa, darrov taslim bo‘ladimi?",
                       "Сдаётся ли он сразу, если задание трудное?"),
         U("taslim bo‘ladi"), U("taslim bo‘lmaydi"), reverse=True),
    Item("tafakkur", L("Uni natijasi uchun emas, mehnati uchun maqtaysizmi?",
                       "Хвалите ли вы его за старание, а не за результат?"),
         U("mehnati uchun maqtayman"), U("mehnati uchun maqtamayman")),
    Item("tafakkur", L("Xato qilsa, qaytadan urinib ko‘radimi?",
                       "Пробует ли он снова, если ошибся?"),
         U("urinib ko‘radi"), U("urinib ko‘rmaydi")),
    # Tengdoshlar bilan til topishish
    Item("ijtimoiy", L("Tengdoshlari bilan til topisha oladimi?",
                       "Ладит ли он со сверстниками?"),
         U("til topishadi"), U("til topisha olmaydi")),
    Item("ijtimoiy", L("Boshqaning ahvolini tushunib, achinadimi?",
                       "Понимает ли он состояние другого и сочувствует?"),
         U("achinadi"), U("achinmaydi")),
    Item("ijtimoiy", L("O‘z fikrini janjalsiz, so‘z bilan tushuntira oladimi?",
                       "Умеет ли он объяснить своё мнение словами, без скандала?"),
         U("tushuntira oladi"), U("tushuntira olmaydi")),
    # Mehnatsevarlik
    Item("mehnat", L("Uyda unga doimiy yumush biriktirilganmi?",
                     "Есть ли у него постоянные обязанности по дому?"),
         U("biriktirilgan"), U("biriktirilmagan"), kind="yesno"),
    Item("mehnat", L("Yumushini eslatmasdan bajaradimi?",
                     "Выполняет ли он обязанности без напоминаний?"),
         U("eslatmasdan bajaradi"), U("eslatmasdan bajarmaydi")),
    Item("mehnat", L("Boshqalarga yordam berishni yoqtiradimi?",
                     "Любит ли он помогать другим?"),
         U("yoqtiradi"), U("yoqtirmaydi")),
    # Uydagi muhit
    Item("oila", L("Har kuni farzandingiz bilan telefonsiz vaqt o‘tkazasizmi?",
                   "Проводите ли вы каждый день время с ребёнком без телефона?"),
         U("o‘tkazaman"), U("o‘tkazmayman")),
    Item("oila", L("Uni tinglab, fikrini so‘raysizmi?",
                   "Слушаете ли вы его и спрашиваете его мнение?"),
         U("so‘rayman"), U("so‘ramayman")),
    Item("oila", L("Oilangizda qoidalar har doim bir xil qo‘llanadimi?",
                   "Правила в вашей семье применяются всегда одинаково?"),
         U("bir xil qo‘llanadi"), U("bir xil qo‘llanmaydi")),
    # Uyqu va harakat
    Item("sogliq", L("U yetarli uxlaydimi?",
                     "Высыпается ли он?"),
         U("yetarli uxlaydi"), U("yetarli uxlamaydi")),
    Item("sogliq", L("Kuniga ekran oldida 3 soatdan ko‘p o‘tiradimi?",
                     "Проводит ли он перед экраном больше 3 часов в день?"),
         U("o‘tiradi"), U("o‘tirmaydi"), reverse=True),
    Item("sogliq", L("Sport yoki faol o‘yin bilan shug‘ullanadimi?",
                     "Занимается ли он спортом или активными играми?"),
         U("shug‘ullanadi"), U("shug‘ullanmaydi")),
    # Hissiy holat
    Item("hissiyot", L("Xafa bo‘lsa, buni sizga aytadimi?",
                       "Говорит ли он вам, когда расстроен?"),
         U("aytadi"), U("aytmaydi")),
    Item("hissiyot", L("Yangi joy yoki yangi odamdan qattiq qo‘rqadimi?",
                       "Сильно ли он боится новых мест и новых людей?"),
         U("qo‘rqadi"), U("qo‘rqmaydi"), reverse=True),
    Item("hissiyot", L("Kayfiyati keskin va tez-tez o‘zgaradimi?",
                       "Резко и часто ли меняется его настроение?"),
         U("o‘zgaradi"), U("o‘zgarmaydi"), reverse=True),
]

TEST = TestDef(
    key="child",
    emoji="👶",
    title=L("Farzand salohiyati", "Потенциал ребёнка"),
    tagline=L(
        "Ota-onalar uchun: bolangizga nima kerak",
        "Для родителей: что нужно вашему ребёнку",
    ),
    intro=L(
        "24 ta gap beriladi. Har biriga <b>farzandingizga qanchalik to‘g‘ri "
        "kelishiga</b> qarab javob bering.\n\n"
        "Bolangizni yaxshiroq ko‘rsatishga urinmang — natija sizga kerak, "
        "hech kimga ko‘rsatilmaydi.",
        "Будет 24 утверждения. Отвечайте, насколько каждое <b>про вашего "
        "ребёнка</b>.\n\n"
        "Не старайтесь показать ребёнка лучше — результат нужен вам, его "
        "никто не увидит.",
    ),
    source=L(
        "Bu — <b>mualliflik so‘rovnomasi</b>, tekshirilgan asbob emas va "
        "tashxis o‘rnini bosmaydi. Yo‘nalishlar nashr etilgan tadqiqotlarga "
        "mos: Duncan (2007) — erta ko‘nikmalar, Jones (2015) — tengdoshlar "
        "bilan muloqot, Moffitt (2011) — o‘zini tuta olish, Dweck — maqtov "
        "turi. Bolangiz rivojlanishi haqida jiddiy xavotiringiz bo‘lsa, "
        "mutaxassisga murojaat qiling.",
        "Это <b>авторский опросник</b>, а не проверенный инструмент, и он не "
        "заменяет диагностику. Направления соответствуют опубликованным "
        "исследованиям: Duncan (2007) — ранние навыки, Jones (2015) — "
        "общение со сверстниками, Moffitt (2011) — самоконтроль, Dweck — тип "
        "похвалы. Если у вас серьёзные опасения по поводу развития ребёнка, "
        "обратитесь к специалисту.",
    ),
    validated=False,
    kind="index",
    scales=SCALES,
    items=ITEMS,
    minutes=L("4–6 daqiqa", "4–6 минут"),
    ask_age=True,
    subject="child",
)
