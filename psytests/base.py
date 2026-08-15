"""Testlar uchun umumiy tuzilma: element, shkala, test ta'rifi va ball hisobi.

Bu yerda hech qanday matn yo'q — faqat mexanika. Har bir test o'z faylida
ta'riflanadi va `psytests/__init__.py` dagi REGISTRY ga qo'shiladi.
"""
from __future__ import annotations

from dataclasses import dataclass, field

LANGS = ("uz", "ru")


def L(uz: str, ru: str) -> dict[str, str]:
    """Ikki tilli matn."""
    return {"uz": uz, "ru": ru}


@dataclass(frozen=True)
class Item:
    """Bitta savol (element)."""

    scale: str
    text: dict[str, str]
    #: True bo'lsa javob teskari hisoblanadi: (max - javob).
    reverse: bool = False


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
    #: Ixtiyoriy: shkala nima bashorat qilishi haqida bir jumla.
    note: dict[str, str] | None = None


@dataclass(frozen=True)
class TestDef:
    key: str
    emoji: str
    title: dict[str, str]
    #: Menyudagi bir qatorlik izoh.
    tagline: dict[str, str]
    #: Testdan oldingi ko'rsatma.
    intro: dict[str, str]
    #: Savollar qayerdan olingani — foydalanuvchiga ochiq ko'rsatiladi.
    source: dict[str, str]
    #: True — nashr etilgan, validatsiyadan o'tgan asbob.
    #: False — ilmiy topilmalarga asoslangan mualliflik so'rovnomasi.
    validated: bool
    #: "traits"    — profil, umumiy ball chiqarilmaydi (Big Five)
    #: "index"     — og'irlangan umumiy ball chiqariladi
    #: "interests" — eng yuqori 3 ta yo'nalish kodi (RIASEC)
    kind: str
    #: Javob variantlari matni (past -> yuqori tartibda).
    anchors: list[dict[str, str]]
    scales: dict[str, Scale]
    items: list[Item]
    minutes: dict[str, str]
    #: Ixtiyoriy: yosh guruhini so'rash kerakmi.
    ask_age: bool = True
    #: Ixtiyoriy: kimning nomidan javob berilishi ("self" yoki "child").
    subject: str = "self"

    @property
    def max_answer(self) -> int:
        return len(self.anchors) - 1

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
        value = test.max_answer - answer if item.reverse else answer
        raw[item.scale].append(value)

    per_scale = {
        key: (sum(v) / (len(v) * test.max_answer) * 100) if v else 0.0
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
            / weights,
            1,
        )
    return result


def level_of(percent: float) -> str:
    """Foizni "low" / "mid" / "high" darajasiga o'tkazadi.

    Chegaralar Big Five uchun odatdagi taqsimotga yaqin olingan: aholining
    katta qismi o'rta oraliqqa tushadi, chetlar esa ancha tor.
    """
    if percent >= 65:
        return "high"
    if percent <= 35:
        return "low"
    return "mid"
