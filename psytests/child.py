"""Farzand salohiyati — ota-ona javob beradigan 24 element, 8 yo'nalish.

Bu ham **mualliflik so'rovnomasi**. Yo'nalishlar bolalikdagi omillar bo'yicha
nashr etilgan tadqiqotlarga mos keladi (Duncan 2007, Jones 2015, Moffitt
2011), lekin so'rovnomaning o'zi tekshirilmagan va tashxis o'rnini bosmaydi.
"""
from .base import Item, L, Scale, TestDef

ANCHORS = [
    L("1️⃣ Umuman to‘g‘ri emas", "1️⃣ Совсем не так"),
    L("2️⃣ Kamdan-kam", "2️⃣ Редко"),
    L("3️⃣ Ba’zan", "3️⃣ Иногда"),
    L("4️⃣ Ko‘pincha", "4️⃣ Часто"),
    L("5️⃣ To‘liq to‘g‘ri", "5️⃣ Точно так"),
]

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
    Item("boshqaruv", L(
        "Farzandim biror ishni boshlasa, chalg‘imasdan oxiriga yetkazadi.",
        "Начав дело, мой ребёнок доводит его до конца, не отвлекаясь.")),
    Item("boshqaruv", L(
        "U navbatini kuta oladi va «hozir emas» degan javobni qabul qiladi.",
        "Он умеет ждать своей очереди и принимает ответ «не сейчас».")),
    Item("boshqaruv", L(
        "Xohlagan narsasini darhol olmasa, jahli chiqadi.",
        "Если не получает желаемое сразу, он злится."), reverse=True),
    Item("qiziqish", L(
        "U ko‘p savol beradi va nima uchunligini bilishni xohlaydi.",
        "Он много спрашивает и хочет знать, почему всё так.")),
    Item("qiziqish", L(
        "Kitob o‘qishni yoki kitob o‘qib berilishini yoqtiradi.",
        "Он любит читать или слушать, когда читают ему.")),
    Item("qiziqish", L(
        "Yangi narsa o‘rganishni o‘zi xohlaydi, majburlash shart emas.",
        "Он сам хочет узнавать новое, заставлять не приходится.")),
    Item("tafakkur", L(
        "Topshiriq qiyin bo‘lsa, «men qila olmayman» deb darrov taslim "
        "bo‘ladi.",
        "Если задание трудное, он сразу сдаётся: «у меня не получится»."),
        reverse=True),
    Item("tafakkur", L(
        "Men uni natijasi uchun emas, mehnati uchun maqtayman.",
        "Я хвалю его не за результат, а за старание.")),
    Item("tafakkur", L(
        "Xato qilsa uyalib qolmaydi, qaytadan urinib ko‘radi.",
        "Ошибившись, он не стыдится, а пробует снова.")),
    Item("ijtimoiy", L(
        "Tengdoshlari bilan yaxshi til topisha oladi.",
        "Он хорошо ладит со сверстниками.")),
    Item("ijtimoiy", L(
        "Boshqaning ahvolini tushunadi va achinadi.",
        "Он понимает состояние другого и сочувствует.")),
    Item("ijtimoiy", L(
        "O‘z fikrini janjalsiz, so‘z bilan tushuntira oladi.",
        "Он умеет объяснить своё мнение словами, без скандала.")),
    Item("mehnat", L(
        "Uyda unga doimiy yumush biriktirilgan.",
        "У него есть постоянные обязанности по дому.")),
    Item("mehnat", L(
        "Yumushini eslatmasdan bajaradi.",
        "Свои обязанности он выполняет без напоминаний.")),
    Item("mehnat", L(
        "Boshqalarga yordam berishni yoqtiradi.",
        "Он любит помогать другим.")),
    Item("oila", L(
        "Har kuni farzandim bilan telefonsiz vaqt o‘tkazaman.",
        "Каждый день я провожу с ребёнком время без телефона.")),
    Item("oila", L(
        "Uni tinglayman va fikrini so‘rayman, faqat buyruq bermayman.",
        "Я слушаю его и спрашиваю его мнение, а не только распоряжаюсь.")),
    Item("oila", L(
        "Oilamizda qoidalar aniq va har doim bir xil qo‘llanadi.",
        "В нашей семье правила понятные и всегда применяются одинаково.")),
    Item("sogliq", L(
        "U yetarli uxlaydi, uyqu vaqti har kuni bir xil.",
        "Он высыпается, время сна каждый день одинаковое.")),
    Item("sogliq", L(
        "Kuniga ekran oldida 3 soatdan ko‘p o‘tiradi.",
        "Он проводит перед экраном больше 3 часов в день."), reverse=True),
    Item("sogliq", L(
        "Harakatchan — sport yoki faol o‘yin bilan shug‘ullanadi.",
        "Он подвижен — занимается спортом или активными играми.")),
    Item("hissiyot", L(
        "Xafa bo‘lsa, buni menga aytadi.",
        "Расстроившись, он говорит мне об этом.")),
    Item("hissiyot", L(
        "Yangi joy yoki yangi odamdan qattiq qo‘rqmaydi.",
        "Он не сильно боится новых мест и новых людей.")),
    Item("hissiyot", L(
        "Kayfiyati keskin va tez-tez o‘zgaradi.",
        "Его настроение резко и часто меняется."), reverse=True),
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
    anchors=ANCHORS,
    scales=SCALES,
    items=ITEMS,
    minutes=L("4–6 daqiqa", "4–6 минут"),
    ask_age=True,
    subject="child",
)
