"""Testlar uchun umumiy tuzilma: element, shkala, test ta'rifi va ball hisobi.

Bu yerda hech qanday savol matni yo'q — faqat mexanika. Har bir test o'z
faylida ta'riflanadi va `psytests/__init__.py` dagi REGISTRY ga qo'shiladi.

JAVOB VARIANTLARI HAQIDA
------------------------
Avval hamma savolga bir xil mavhum javob berilardi ("To'liq to'g'ri").
Psixolog mutaxassis to'g'ri ta'kidladi: oddiy odam bunday shkalani tushunmaydi,
chunki gapni eslab turib, uning ustiga "to'g'ri/noto'g'ri" ni joylashtirish
kerak bo'ladi.

Endi har bir savol SAVOL shaklida beriladi va javoblar o'sha savolning
fe'lini takrorlaydi:

    "Davra siz bilan jonlanadimi?"
        Hech qachon jonlanmaydi / Kamdan-kam jonlanadi / Ba'zan jonlanadi /
        Ko'pincha jonlanadi / Doim jonlanadi

Buning uchun har bir element `yes` va `no` shakllarini beradi, javoblar esa
shablondan yig'iladi. Ikki xil shablon bor:

    "freq" — xatti-harakat uchun (necha marta): Hech qachon / Ba'zan / Doim
    "deg"  — holat yoki xususiyat uchun (qanchalik): Umuman / O'rtacha / Juda

Ball hisobi o'zgarmadi: baribir 0..4, shuning uchun eski natijalar bilan
solishtirsa bo'ladi.
"""
from __future__ import annotations

from dataclasses import dataclass, field

LANGS = ("uz", "ru")

#: Javob shablonlari. {yes} va {no} har bir savolning o'z shakli bilan
#: almashtiriladi. Bo'sh joy qolmasligi uchun ortiqcha probel tozalanadi.
TEMPLATES = {
    # O'rtadagi variant "Bilmayman" emas: odam savolga "bilmayman" deb emas,
    # "ba'zan" yoki "o'rtacha" deb javob beradi. "Bilmayman" 2 ball olardi,
    # lekin odam aslida boshqa narsani nazarda tutgan bo'lardi.
    "freq": {
        "uz": ["Hech qachon {no}", "Kamdan-kam {yes}", "Ba’zan {yes}",
               "Ko‘pincha {yes}", "Doim {yes}"],
        "ru": ["Никогда", "Редко", "Иногда", "Часто", "Всегда"],
    },
    "deg": {
        "uz": ["Umuman {no}", "Unchalik {no}", "O‘rtacha", "Ha, {yes}",
               "Ha, juda {yes}"],
        "ru": ["Совсем нет", "Скорее нет", "Отчасти", "Да", "Да, очень"],
    },
    # "Bormi?" turidagi savollar uchun.
    "yesno": {
        "uz": ["Yo‘q", "Deyarli yo‘q", "Qisman", "Ha, {yes}", "Ha, albatta {yes}"],
        "ru": ["Нет", "Скорее нет", "Отчасти", "Да", "Да, точно"],
    },
    # Fikr so'ralganda ("... deb hisoblaysizmi?") fe'lni takrorlash
    # g'aliz chiqadi — oddiy rozilik darajasi.
    "agree": {
        "uz": ["Yo‘q", "Unchalik emas", "Qisman", "Ha", "Ha, albatta"],
        "ru": ["Нет", "Скорее нет", "Отчасти", "Да", "Да, конечно"],
    },
    # Qiziqish so'ralganda (kasb testi) fe'l takrorlanmaydi — savolning o'zi
    # mashg'ulot nomi bo'ladi.
    "interest": {
        "uz": ["Umuman qiziq emas", "Unchalik qiziq emas", "Farqi yo‘q",
               "Qiziq", "Juda qiziq"],
        "ru": ["Совсем не интересно", "Не очень интересно", "Нейтрально",
               "Интересно", "Очень интересно"],
    },
}

#: Fe'l shakli berilmagan savollar uchun (masalan, admin CMS orqali
#: qo'shgan savol). Bo'lmasa "Ha," yoki "Umuman" kabi chala tugma chiqadi.
GENERIC = {
    "freq": {"uz": ["Hech qachon", "Kamdan-kam", "Ba’zan", "Ko‘pincha", "Doim"]},
    "deg": {"uz": ["Umuman yo‘q", "Unchalik emas", "O‘rtacha", "Ha", "Ha, juda"]},
    "yesno": {"uz": ["Yo‘q", "Deyarli yo‘q", "Qisman", "Ha", "Ha, albatta"]},
}

#: Javob tugmalari oldidagi raqamlar.
DIGITS = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣"]

MAX_ANSWER = len(DIGITS) - 1


def L(uz: str, ru: str) -> dict[str, str]:
    """Ikki tilli matn."""
    return {"uz": uz, "ru": ru}


def U(uz: str) -> dict[str, str]:
    """Faqat o'zbekcha shakl.

    Javob variantlaridagi fe'l takrori faqat o'zbek tilida kerak: rus tilida
    savolga "Совсем нет / Часто / Да, всегда" deb javob berish o'z-o'zidan
    tabiiy chiqadi, fe'lni takrorlash shart emas.
    """
    return {"uz": uz}


@dataclass(frozen=True)
class Item:
    """Bitta savol.

    text — savol shaklida ("... -mi?")
    yes  — tasdiq shakli, javobga qo'yiladi ("jonlanadi")
    no   — inkor shakli ("jonlanmaydi")
    kind — "freq" (necha marta), "deg" (qanchalik), "yesno" (bormi),
           "agree" (fikr), "interest" yoki "custom"
    options — "custom" savollar uchun tayyor 5 ta javob (masalan, soatlar
           soni). Raqamli savolga "Ko'pincha" deb javob berib bo'lmaydi.
    """

    scale: str
    text: dict[str, str]
    yes: dict[str, str] | None = None
    no: dict[str, str] | None = None
    kind: str = "freq"
    #: True bo'lsa javob teskari hisoblanadi: (MAX_ANSWER - javob).
    reverse: bool = False
    options: dict[str, list[str]] | None = None

    def answers(self, lang: str) -> list[str]:
        """Shu savol uchun javob variantlari matni."""
        if self.options and self.options.get(lang):
            return [f"{DIGITS[i]} {text}" for i, text in enumerate(self.options[lang])]
        kind = self.kind if self.kind in TEMPLATES else "deg"
        template = TEMPLATES[kind][lang]
        yes = (self.yes or {}).get(lang, "")
        no = (self.no or {}).get(lang, "")
        if lang in GENERIC.get(kind, {}) and not (yes and no):
            template = GENERIC[kind][lang]
        out = []
        for i, raw in enumerate(template):
            text = raw.format(yes=yes, no=no)
            text = " ".join(text.split())  # ortiqcha probellarni olib tashlash
            out.append(f"{DIGITS[i]} {text}")
        return out


@dataclass(frozen=True)
class Scale:
    """O'lchanadigan bitta xususiyat."""

    key: str
    emoji: str
    name: dict[str, str]
    #: Daraja bo'yicha izoh. Kalitlar: "high", "mid", "low".
    levels: dict[str, dict[str, str]] = field(default_factory=dict)
    #: Umumiy indeksga qo'shadigan hissasi ("index" turidagi testlar uchun).
    weight: float = 1.0
    #: Ixtiyoriy: shkala nima ko'rsatishi haqida bir jumla.
    note: dict[str, str] | None = None


@dataclass(frozen=True)
class TestDef:
    key: str
    emoji: str
    title: dict[str, str]
    tagline: dict[str, str]
    intro: dict[str, str]
    source: dict[str, str]
    #: True — nashr etilgan, tekshirilgan asbob.
    validated: bool
    #: "traits" | "index" | "interests"
    kind: str
    scales: dict[str, Scale]
    items: list[Item]
    minutes: dict[str, str]
    ask_age: bool = True
    subject: str = "self"

    @property
    def max_answer(self) -> int:
        return MAX_ANSWER

    @property
    def size(self) -> int:
        return len(self.items)


# --- Ball hisobi ------------------------------------------------------------


def score(test: TestDef, answers: list[int]) -> dict:
    """Javoblardan shkala foizlarini va (kerak bo'lsa) umumiy indeksni chiqaradi."""
    if len(answers) != test.size:
        raise ValueError(f"{test.size} ta javob kutilgan, {len(answers)} ta keldi")

    raw: dict[str, list[int]] = {key: [] for key in test.scales}
    for item, answer in zip(test.items, answers):
        value = MAX_ANSWER - answer if item.reverse else answer
        raw[item.scale].append(value)

    per_scale = {
        key: (sum(v) / (len(v) * MAX_ANSWER) * 100) if v else 0.0
        for key, v in raw.items()
    }

    ordered = sorted(per_scale.items(), key=lambda kv: kv[1], reverse=True)
    result: dict = {
        "scales": per_scale,
        "ranked": [key for key, _ in ordered],
        "top": [key for key, _ in ordered[:2]],
        "bottom": [key for key, _ in ordered[-2:]][::-1],
    }

    if test.kind == "index":
        weights = sum(test.scales[key].weight for key in per_scale)
        result["total"] = round(
            sum(per_scale[key] * test.scales[key].weight for key in per_scale)
            / weights, 1)
    return result


def level_of(percent: float) -> str:
    """Foizni "low" / "mid" / "high" darajasiga o'tkazadi."""
    if percent >= 65:
        return "high"
    if percent <= 35:
        return "low"
    return "mid"
