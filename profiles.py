"""Natijadan qisqa portret: eng kuchli tomon va arxetip nomi.

Sertifikat, bepul natija va to'liq tahlil shu yerdagi bitta qoidadan
foydalanadi — uchalasida bir xil nom chiqadi.

Halollik qoidasi: kuchli yorliq faqat haqiqatan yuqori ballga beriladi.
  * STRONG_MIN dan past yo'nalish "kuchli tomon" deb atalmaydi;
  * Big Five juftlik nomi faqat ikkala xususiyat ham PAIR_MIN dan yuqori
    bo'lsa; hech biri ajralib turmasa — "Muvozanatli shaxs";
  * IQ da fikrlash turi arxetipi faqat shu turda kamida yarmi to'g'ri
    yechilgan bo'lsa.
"""
from __future__ import annotations

import content
from psytests import REGISTRY
from psytests.insights import ARCHETYPES, FALLBACK, Archetype
from psytests.iq import KINDS

STRONG_MIN = 50
PAIR_MIN = 55
IQ_KIND_MIN = 0.5
BIGFIVE_ORDER = "EACSO"


def ranked(test_key: str, scales: dict) -> list[str]:
    order = list(REGISTRY[test_key].scales)
    return sorted(order, key=lambda key: (-float(scales.get(key) or 0), order.index(key)))


def top_scale(test_key: str, scales: dict) -> tuple[str, float]:
    key = ranked(test_key, scales)[0]
    return key, float(scales.get(key) or 0)


def is_strong(percent: float) -> bool:
    return percent >= STRONG_MIN


def iq_kinds(details: dict) -> list[tuple[str, int, int]]:
    """(tur, to'g'ri, jami) — yaxshidan pastga qarab."""
    order = list(KINDS)
    rows = []
    for key in order:
        ok, n = (details.get("kinds") or {}).get(key, [0, 0])
        rows.append((key, int(ok), int(n)))
    return sorted(rows, key=lambda r: (-(r[1] / r[2] if r[2] else 0), order.index(r[0])))


def iq_best(details: dict) -> str | None:
    """Eng kuchli fikrlash turi — faqat kamida yarmi to'g'ri bo'lsa."""
    for key, ok, n in iq_kinds(details):
        return key if n and ok / n >= IQ_KIND_MIN else None
    return None


def _pair(a: str, b: str) -> Archetype:
    key = "".join(sorted((a, b), key=BIGFIVE_ORDER.index))
    return Archetype(content.text("bigfive", "pairs", key, "name"),
                     content.text("bigfive", "pairs", key, "line"))


def archetype(test_key: str, details: dict) -> Archetype:
    """Natija uchun arxetip (nom + bitta qator)."""
    if test_key == "iq":
        best = iq_best(details)
        return ARCHETYPES["iq"][best] if best else FALLBACK
    order = ranked(test_key, details)
    top, second = order[0], order[1]
    top_pct, second_pct = float(details.get(top) or 0), float(details.get(second) or 0)
    if test_key == "bigfive":
        if top_pct >= PAIR_MIN and second_pct >= PAIR_MIN:
            return _pair(top, second)
        if top_pct >= PAIR_MIN:
            return ARCHETYPES["bigfive"][top]
        return Archetype(content.text("bigfive", "balanced", "name"),
                         content.text("bigfive", "balanced", "line"))
    if top_pct >= STRONG_MIN and top in ARCHETYPES.get(test_key, {}):
        return ARCHETYPES[test_key][top]
    return FALLBACK
