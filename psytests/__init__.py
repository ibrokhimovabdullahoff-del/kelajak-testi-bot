"""Testlar reyestri.

Yangi test qo'shish uchun: yangi fayl yarating, unda `TEST` nomli `TestDef`
e'lon qiling va uni quyidagi REGISTRY va ORDER ga qo'shing. Boshqa hech
qayerni o'zgartirish shart emas — menyu, ball hisobi, natija va statistika
o'zi moslashadi.
"""
from .base import Item, L, Scale, TestDef, level_of, score
from . import bigfive, career, child, future

REGISTRY: dict[str, TestDef] = {
    t.key: t for t in (bigfive.TEST, future.TEST, career.TEST, child.TEST)
}

#: Menyudagi tartib.
ORDER = ["bigfive", "future", "career", "child"]

#: Yosh guruhlari — javob beruvchi kim ekaniga qarab ("self" yoki "child").
AGE_GROUPS = {
    "self": [
        ("a_14_18", L("14–18 yosh", "14–18 лет")),
        ("a_19_25", L("19–25 yosh", "19–25 лет")),
        ("a_26_35", L("26–35 yosh", "26–35 лет")),
        ("a_36p", L("36+ yosh", "36+ лет")),
    ],
    "child": [
        ("k_3_6", L("3–6 yosh", "3–6 лет")),
        ("k_7_10", L("7–10 yosh", "7–10 лет")),
        ("k_11_14", L("11–14 yosh", "11–14 лет")),
        ("k_15_18", L("15–18 yosh", "15–18 лет")),
    ],
}

AGE_LABELS = {code: label for groups in AGE_GROUPS.values() for code, label in groups}

#: Yoshga mos yakuniy maslahat — bittadan qisqa jumla.
AGE_ADVICE = {
    "a_14_18": L(
        "Bu yoshda eng kuchli sarmoya — o‘qish odati va bitta chuqur "
        "qiziqish; hozirgi natija emas, yo‘nalish muhim.",
        "В этом возрасте самая сильная инвестиция — привычка учиться и один "
        "глубокий интерес; важен не результат, а направление.",
    ),
    "a_19_25": L(
        "Hozir xato qilish eng arzon davr: ko‘proq sinang, lekin bittasini "
        "oxirigacha olib boring.",
        "Сейчас ошибки стоят дешевле всего: пробуйте больше, но одно "
        "доводите до конца.",
    ),
    "a_26_35": L(
        "Bu davrda tezlikdan ko‘ra yo‘nalish muhim: bitta kuchli ko‘nikma "
        "bir nechta o‘rtachadan qimmatroq turadi.",
        "Здесь направление важнее скорости: один сильный навык стоит дороже "
        "нескольких средних.",
    ),
    "a_36p": L(
        "Tajribangiz katta boylik — uni tizimga solish va boshqalarga "
        "uzatish shu yoshda eng ko‘p natija beradi.",
        "Ваш опыт — большой капитал; систематизировать его и передавать "
        "дальше в этом возрасте даёт больше всего.",
    ),
    "k_3_6": L(
        "Bu yoshda o‘yin, suhbat va uyqu hal qiladi — erta o‘qitish emas, "
        "iliq muhit natija beradi.",
        "В этом возрасте решают игра, разговор и сон — результат даёт не "
        "раннее обучение, а тёплая среда.",
    ),
    "k_7_10": L(
        "O‘qish odati va mustaqil yumush aynan shu yoshda mustahkamlanadi: "
        "baho uchun emas, mehnat uchun maqtang.",
        "Привычка читать и самостоятельные обязанности закрепляются именно "
        "сейчас: хвалите за труд, а не за оценку.",
    ),
    "k_11_14": L(
        "Bu davrda tengdoshlar fikri kuchayadi — bu normal; asosiy vazifa "
        "ishonchni saqlash: ko‘proq tinglang, kamroq baho bering.",
        "Сейчас мнение сверстников усиливается — это нормально; главная "
        "задача сохранить доверие: больше слушайте, меньше оценивайте.",
    ),
    "k_15_18": L(
        "Mustaqillikka tayyorlash vaqti: qaror qabul qilishga, pul "
        "boshqarishga va oqibatga javob berishga o‘rgating.",
        "Время готовить к самостоятельности: учите принимать решения, "
        "распоряжаться деньгами и отвечать за последствия.",
    ),
}

__all__ = [
    "AGE_ADVICE", "AGE_GROUPS", "AGE_LABELS", "Item", "L", "ORDER",
    "REGISTRY", "Scale", "TestDef", "level_of", "score",
]
