"""Rasmli IQ testi: 20 ta matritsa topshirig'i (Raven uslubida).

Bu yerda faqat ma'lumot va ball hisobi — Telegram bilan ishlash
`handlers/iq.py` da. Shunday bo'lgani uchun tekshiruv skriptlari testni
botsiz ham sinay oladi.

Rasmlar `assets/iq/` da. Har bir rasmda A–D variantlari rasmning o'zida
chizilgan, bot faqat harf tugmalarini beradi. Javoblar kaliti kodda emas —
pastdagi ANSWER_KEY_ENV ga qarang. Savollar oddiydan murakkabga
qarab tartiblangan: boshida ishonch paydo bo'ladi, oxirida esa kuchli
odamlar ham o'ylab ko'radi.

TAXMINIY IQ QANDAY HISOBLANADI
------------------------------
IQ — odamning natijasi o'z tengdoshlari orasida qayerda turishi: 100 —
o'rtacha, har 15 ball — bitta standart og'ish. Shuning uchun test boshida
yosh so'raladi.

  * Yetarli natija to'planguncha (yosh guruhida MIN_PEERS tadan kam)
    boshlang'ich me'yor ishlatiladi: PRIOR_NORMS dagi o'rtacha va og'ish.
  * To'planganidan keyin me'yor botning o'z ishtirokchilaridan olinadi:
    shu yoshdagilarning BIRINCHI urinishlari orasidagi o'rin → IQ.

20 ta topshiriqli test aniq raqam bera olmaydi, shuning uchun natija oraliq
bilan ko'rsatiladi (±IQ_MARGIN) va "taxminiy" deb aytiladi.
"""
from __future__ import annotations

import hashlib
import os
from dataclasses import dataclass
from pathlib import Path
from statistics import NormalDist

from .base import L

ASSETS = Path(__file__).resolve().parent.parent / "assets" / "iq"
LETTERS = ("A", "B", "C", "D")


@dataclass(frozen=True)
class Kind:
    """Topshiriq turi. Foydalanuvchiga ko'rsatilmaydi — bazada statistika uchun saqlanadi."""

    emoji: str
    name: dict[str, str]


KINDS: dict[str, Kind] = {
    "change": Kind("📈", L("O‘zgarish qonuniyati", "Закономерность изменений")),
    "combine": Kind("➕", L("Shakllarni qo‘shish", "Сложение фигур")),
    "spatial": Kind("🔄", L("Fazoviy tasavvur", "Пространственное мышление")),
    "rows": Kind("🔢", L("Qatorlar mantig‘i", "Логика рядов")),
}


@dataclass(frozen=True)
class Puzzle:
    file: str
    kind: str

    @property
    def path(self) -> Path:
        return ASSETS / self.file

    @property
    def digest(self) -> str:
        """Rasm o'zgarsa, Telegram'dagi eski nusxasi ishlatilmasligi uchun."""
        return hashlib.sha1(self.path.read_bytes()).hexdigest()[:12]


#: Oddiydan murakkabga qarab.
PUZZLES: list[Puzzle] = [
    Puzzle("07.png", "change"),
    Puzzle("13.png", "change"),
    Puzzle("14.png", "change"),
    Puzzle("04.png", "spatial"),
    Puzzle("01.png", "rows"),
    Puzzle("03.png", "spatial"),
    Puzzle("15.png", "rows"),
    Puzzle("02.png", "combine"),
    Puzzle("20.png", "rows"),
    Puzzle("09.png", "change"),
    Puzzle("16.png", "spatial"),
    Puzzle("08.png", "combine"),
    Puzzle("12.png", "spatial"),
    Puzzle("05.png", "spatial"),
    Puzzle("06.png", "spatial"),
    Puzzle("10.png", "rows"),
    Puzzle("11.png", "rows"),
    Puzzle("17.png", "combine"),
    Puzzle("19.png", "rows"),
    Puzzle("18.png", "combine"),
]

TOTAL = len(PUZZLES)

#: JAVOBLAR KALITI KODDA SAQLANMAYDI. Repozitoriy ochiq (public) — kalit kodda
#: bo'lsa, istalgan odam GitHub'dan ko'chirib olardi. Kalit serverda muhit
#: o'zgaruvchisida turadi: PUZZLES tartibida 20 ta harf, masalan
#: IQ_ANSWERS=ABCD... Kalit va har bir javobning qoidasi — egasidagi maxfiy
#: IQ_JAVOBLAR.md faylida (u .gitignore da).
ANSWER_KEY_ENV = "IQ_ANSWERS"


def answer_key() -> list[str] | None:
    """Muhitdan kalit. Noto'g'ri yoki yo'q bo'lsa — None (test ochilmaydi)."""
    raw = "".join(ch for ch in os.getenv(ANSWER_KEY_ENV, "").upper() if ch.isalpha())
    if len(raw) != TOTAL or any(ch not in LETTERS for ch in raw):
        return None
    return list(raw)


AGE_GROUPS = [
    ("i_10_13", L("10–13 yosh", "10–13 лет")),
    ("i_14_17", L("14–17 yosh", "14–17 лет")),
    ("i_18_29", L("18–29 yosh", "18–29 лет")),
    ("i_30p", L("30 yosh va katta", "30 лет и старше")),
]
AGE_CODES = {code for code, _ in AGE_GROUPS}
DEFAULT_AGE = "i_18_29"

#: Boshlang'ich me'yor: yosh guruhi → (o'rtacha to'g'ri javob, standart og'ish).
#: Topshiriqlar qiyinligiga qarab baholangan: kattalar oson 8 tasini deyarli
#: hammasini, o'rtadagi 6 tasining uchdan ikkisini, qiyin 6 tasining
#: taxminan yarmini yechadi. Bolalarda o'rtacha pastroq — shuning uchun bir
#: xil to'g'ri javobda bolaning IQ si kattanikidan yuqori chiqadi.
PRIOR_NORMS: dict[str, tuple[float, float]] = {
    "i_10_13": (10.0, 3.8),
    "i_14_17": (11.5, 3.6),
    "i_18_29": (12.5, 3.5),
    "i_30p": (12.0, 3.6),
}

IQ_MIN, IQ_MAX = 70, 145
#: 20 ta topshiriqli testning o'lchov xatosi taxminan ±7 IQ ball.
IQ_MARGIN = 7

#: Shu yosh guruhida shuncha ishtirokchi to'plangach, me'yor va foiz botning
#: o'z natijalaridan olinadi. Undan kam bo'lsa, foiz tasodifiy chiqadi.
MIN_PEERS = 50

#: O'rtacha shundan tez yechilgan bo'lsa, javoblar tavakkal bosilgan
#: bo'lishi ehtimoli katta — natijada buni aytamiz.
RUSHED_SECONDS_PER_PUZZLE = 5


@dataclass(frozen=True)
class Level:
    min_iq: int
    emoji: str
    name: dict[str, str]
    note: dict[str, str]


LEVELS: list[Level] = [
    Level(130, "🏆", L("Juda yuqori", "Очень высокий"), L(
        "Bunday natija taxminan har 50 kishidan 1 tasida uchraydi. Murakkab "
        "qonuniyatlarni ham tez va aniq ko‘rasiz.",
        "Такой результат встречается примерно у 1 человека из 50. Вы быстро "
        "и точно видите даже сложные закономерности.")),
    Level(120, "🌟", L("Yuqori", "Высокий"), L(
        "Bunday natija taxminan har 10 kishidan 1 tasida uchraydi. Mantiqiy "
        "fikrlashingiz kuchli.",
        "Такой результат встречается примерно у 1 человека из 10. "
        "Логическое мышление у вас сильное.")),
    Level(110, "💪", L("O‘rtachadan yuqori", "Выше среднего"), L(
        "Qonuniyatlarni ko‘pchilik tengdoshlaringizdan yaxshiroq ko‘ryapsiz.",
        "Закономерности вы видите лучше большинства сверстников.")),
    Level(90, "📈", L("O‘rtacha", "Средний"), L(
        "Odamlarning taxminan yarmi shu oraliqda. Bunday topshiriqlarni ko‘proq "
        "yechsangiz, natija sezilarli oshadi.",
        "Примерно половина людей находится в этом диапазоне. Если решать "
        "больше таких задач, результат заметно вырастет.")),
    Level(80, "🌱", L("O‘rtachadan biroz past", "Немного ниже среднего"), L(
        "Bunday topshiriqlar hozircha qiyin kechyapti. Ular mashq qilsa tez "
        "o‘sadigan ko‘nikma.",
        "Такие задания пока даются непросто. Это навык, который быстро растёт "
        "с практикой.")),
    Level(0, "🌱", L("O‘rtachadan past", "Ниже среднего"), L(
        "Bir martalik natija charchoq, shoshilish va e’tiborga ham bog‘liq. "
        "Dam olib, shoshmasdan yechilganda natija ancha boshqacha chiqishi mumkin.",
        "Разовый результат зависит и от усталости, спешки и внимания. Если "
        "решать отдохнувшим и без спешки, результат может сильно отличаться.")),
]


def level_for(iq: int) -> Level:
    for level in LEVELS:
        if iq >= level.min_iq:
            return level
    return LEVELS[-1]


def _clamp(value: float) -> int:
    return max(IQ_MIN, min(IQ_MAX, round(value)))


def grade(answers: list[str], key: list[str]) -> dict:
    """Javoblardan natija: to'g'ri javoblar soni va topshiriq turlari kesimi."""
    if len(answers) != TOTAL or len(key) != TOTAL:
        raise ValueError(f"{TOTAL} ta javob kutilgan, {len(answers)}/{len(key)} ta keldi")
    marks = [answer == correct for answer, correct in zip(answers, key)]
    kinds: dict[str, list[bool]] = {key: [] for key in KINDS}
    for ok, puzzle in zip(marks, PUZZLES):
        kinds[puzzle.kind].append(ok)
    return {
        "correct": sum(marks),
        "marks": marks,
        "kinds": {key: [sum(v), len(v)] for key, v in kinds.items()},
        "mistakes": [i for i, ok in enumerate(marks) if not ok],
    }


def _share_below(correct: int, peers: list[float]) -> float:
    below = sum(1 for p in peers if p < correct)
    equal = sum(1 for p in peers if p == correct)
    return (below + equal / 2) / len(peers)


def percentile(correct: int, peers: list[float]) -> int | None:
    """Ishtirokchilarning necha foizidan yuqori natija (teng natija — yarmi)."""
    if len(peers) < MIN_PEERS:
        return None
    return round(_share_below(correct, peers) * 100)


def estimate_iq(correct: int, age_group: str | None, peers: list[float]) -> dict:
    """Taxminiy IQ va uning oralig'i.

    peers — shu yosh guruhidagi boshqa ishtirokchilarning birinchi urinishdagi
    to'g'ri javoblari soni. Ular yetarli bo'lsa, me'yor ulardan olinadi.
    """
    if len(peers) >= MIN_PEERS:
        share = min(0.99, max(0.01, _share_below(correct, peers)))
        z, source = NormalDist().inv_cdf(share), "peers"
    else:
        mean, sd = PRIOR_NORMS.get(age_group or DEFAULT_AGE, PRIOR_NORMS[DEFAULT_AGE])
        z, source = (correct - mean) / sd, "prior"
    iq = _clamp(100 + 15 * z)
    return {
        "iq": iq,
        "low": max(IQ_MIN, iq - IQ_MARGIN),
        "high": min(IQ_MAX, iq + IQ_MARGIN),
        "source": source,
    }
