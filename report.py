"""Natija matnini yig'ish.

Har bir yo'nalish uchun: ko'rsatkich, u hayotda nimani anglatadi va uni
o'stiradigan bitta aniq mashq. Oxirida — keyingi qadam: bir haftadan keyin
qayta topshirib solishtirish va botdagi boshqa test.

0 foiz hech qachon raqam bilan ko'rsatilmaydi — o'rniga "o'sish nuqtasi".
Boshqalar bilan solishtirish (foiz) faqat bazadagi haqiqiy natijalardan
keladi: `peers.compare()` uni hisoblaydi va bu yerga tayyor holda beradi.
"""
from __future__ import annotations

import json

from config import IQ_EMOJI, IQ_KEY
from locales import t, tr
from psytests import AGE_ADVICE, AGE_LABELS, REGISTRY, TestDef, level_of
from psytests.base import L
from psytests.insights import INSIGHTS, NEXT_TEST
from psytests.iq import RUSHED_SECONDS_PER_PUZZLE, TOTAL as IQ_TOTAL, level_for

BAR_LEN = 10
SEP = "━━━━━━━━━━━━━━━━━━"

#: "index" turidagi testlar uchun umumiy ball izohi — bittadan jumla.
BANDS = [
    (85, "🏆", L("Juda yuqori", "Очень высокий"), L(
        "Odatlaringiz uzoq muddatli natija bilan eng kuchli bog‘langan "
        "namunaga yaqin. Asosiy xavf — o‘zingizni ortiqcha yuklash.",
        "Ваши привычки близки к набору, сильнее всего связанному с "
        "долгосрочным результатом. Главный риск — перегрузить себя.",
    )),
    (70, "🌟", L("Yuqori", "Высокий"), L(
        "Poydevor mustahkam. Eng pastdagi bitta yo‘nalishni ko‘tarsangiz, "
        "natija sezilarli tezlashadi.",
        "Фундамент крепкий. Подтяните одно самое слабое направление — "
        "результат заметно ускорится.",
    )),
    (55, "💪", L("Yaxshi", "Хороший"), L(
        "Kuchli tomonlaringiz bor, lekin ular hali tartibga tushmagan: "
        "natija kayfiyatga bog‘liq bo‘lib qolyapti.",
        "Сильные стороны есть, но они ещё не стали системой: результат "
        "зависит от настроения.",
    )),
    (40, "🌱", L("O‘rtacha", "Средний"), L(
        "Odatlar hali beqaror. Quyidagi yo‘nalishlarning hammasi "
        "o‘rganiladigan ko‘nikma — bittasidan boshlang.",
        "Привычки пока нестабильны. Все направления ниже — приобретаемые "
        "навыки, начните с одного.",
    )),
    (0, "🔧", L("Boshlang‘ich", "Начальный"), L(
        "Bu «imkoni yo‘q» degani emas — tartib hali qurilmagan. Hammasini "
        "birdan tuzatmang, bitta yo‘nalishni tanlang.",
        "Это не «шансов нет» — просто система ещё не построена. Не "
        "исправляйте всё сразу, выберите одно направление.",
    )),
]


def pct(percent: float, lang: str) -> str:
    """Foiz matni. 0 foiz o'rniga yumshoq yorliq — "0%" odamni tushkunlikka soladi."""
    return t("res_zero", lang) if round(percent) <= 0 else f"{percent:.0f}%"


def bar(percent: float) -> str:
    filled = max(0, min(BAR_LEN, round(percent / 100 * BAR_LEN)))
    return "█" * filled + "░" * (BAR_LEN - filled)


def _band(total: float):
    for threshold, emoji, name, note in BANDS:
        if total >= threshold:
            return emoji, name, note
    return BANDS[-1][1], BANDS[-1][2], BANDS[-1][3]


def render(test: TestDef, result: dict, lang: str, age_group: str | None,
           comparison: dict | None = None) -> str:
    """comparison — `peers.compare()` natijasi (odam kam bo'lsa None)."""
    if test.kind == "traits":
        body = _render_traits(test, result, lang)
        disclaimer = t("disclaimer_validated", lang)
    elif test.kind == "interests":
        body = _render_interests(test, result, lang)
        disclaimer = t("disclaimer_career", lang)
    else:
        body = _render_index(test, result, lang, age_group, comparison)
        disclaimer = t("disclaimer_composite", lang)

    head = f"{test.emoji} <b>{tr(test.title, lang)}</b>"
    return (f"{head}\n\n{body}\n\n{SEP}\n<i>{disclaimer}</i>\n\n"
            f"{next_step(test.key, lang)}")


def comparison_line(comparison: dict | None, lang: str) -> str | None:
    """"Siz ... X foizidan yaxshiroq javob berdingiz" yoki None."""
    if not comparison:
        return None
    if comparison["low"]:
        return t("res_percentile_low", lang, n=comparison["n"])
    return t("res_percentile", lang, pct=comparison["percent"], n=comparison["n"])


def insight_lines(test_key: str, scale_key: str, lang: str) -> list[str]:
    """Yo'nalish hayotda nimani anglatadi + bitta mashq."""
    item = INSIGHTS.get(test_key, {}).get(scale_key)
    if item is None:
        return []
    return [t("res_everyday", lang, text=tr(item.everyday, lang)),
            t("res_exercise", lang, text=tr(item.exercise, lang))]


def next_test_title(test_key: str, lang: str) -> tuple[str, str] | None:
    """(kalit, nom) — hisobot oxirida taklif qilinadigan test."""
    other = NEXT_TEST.get(test_key)
    if other == IQ_KEY:
        return other, t("iq_title", lang)
    if other in REGISTRY:
        return other, tr(REGISTRY[other].title, lang)
    return None


def next_step(test_key: str, lang: str) -> str:
    lines = [f"🚀 <b>{t('res_next_title', lang)}</b>", "", t("res_next_retake", lang)]
    other = next_test_title(test_key, lang)
    if other:
        lines.append(t("res_next_other", lang, title=other[1]))
    return "\n".join(lines)


# --- Big Five: profil -------------------------------------------------------


def _render_traits(test: TestDef, result: dict, lang: str) -> str:
    lines = []
    for key, scale in test.scales.items():
        percent = result["scales"][key]
        level = t("lvl_" + level_of(percent), lang)
        lines.append(f"{scale.emoji} <b>{tr(scale.name, lang)}</b> — {level}")
        lines.append(f"<code>{bar(percent)}</code> {pct(percent, lang)}")
        lines.append(tr(scale.levels[level_of(percent)], lang))
        lines += insight_lines(test.key, key, lang)
        lines.append("")
    return "\n".join(lines).rstrip()


# --- Kelajak / Farzand: umumiy indeks ---------------------------------------


def _render_index(
    test: TestDef, result: dict, lang: str, age_group: str | None,
    comparison: dict | None = None,
) -> str:
    total = result["total"]
    emoji, name, note = _band(total)
    score = f"{total:.0f} / 100" if round(total) > 0 else t("res_zero", lang)

    lines = [
        f"{emoji} <b>{score} — {tr(name, lang)}</b>",
        tr(note, lang),
    ]
    compared = comparison_line(comparison, lang)
    if compared:
        lines += ["", compared]
    lines += ["", SEP, ""]

    for key in result["ranked"]:
        scale = test.scales[key]
        percent = result["scales"][key]
        lines.append(f"{scale.emoji} <b>{tr(scale.name, lang)}</b>")
        lines.append(f"<code>{bar(percent)}</code> {pct(percent, lang)}")
        lines += insight_lines(test.key, key, lang)
        lines.append("")
    lines.pop()

    lines += ["", SEP, "", f"✅ <b>{t('res_strengths', lang)}</b>", ""]
    for key in result["top"]:
        scale = test.scales[key]
        lines.append(
            f"{scale.emoji} <b>{tr(scale.name, lang)}</b> — "
            f"{tr(scale.levels['high'], lang)}"
        )
        lines.append("")

    lines += [SEP, "", f"🎯 <b>{t('res_growth', lang)}</b>", ""]
    for key in result["bottom"]:
        scale = test.scales[key]
        lines.append(f"{scale.emoji} <b>{tr(scale.name, lang)}</b>")
        lines.append(tr(scale.levels["low"], lang))
        lines.append("")

    if age_group in AGE_ADVICE:
        label = "res_advice_child" if test.subject == "child" else "res_advice"
        lines += [
            SEP, "", f"💡 <b>{t(label, lang)}</b>",
            tr(AGE_ADVICE[age_group], lang),
        ]

    return "\n".join(lines).rstrip()


# --- RIASEC: qiziqish kodi --------------------------------------------------


def _render_interests(test: TestDef, result: dict, lang: str) -> str:
    top3 = result["ranked"][:3]
    code = "".join(top3)

    lines = [f"🧭 <b>{t('res_code', lang)}: {code}</b>", ""]
    for key in top3:
        scale = test.scales[key]
        lines.append(
            f"{scale.emoji} <b>{tr(scale.name, lang)}</b> — "
            f"{pct(result['scales'][key], lang)}"
        )
        lines.append(tr(scale.levels["high"], lang))
        lines.append("")

    lines += [SEP, "", f"📊 <b>{t('res_all_areas', lang)}</b>", ""]
    for key in result["ranked"]:
        scale = test.scales[key]
        percent = result["scales"][key]
        lines.append(f"{scale.emoji} <b>{tr(scale.name, lang)}</b>")
        lines.append(f"<code>{bar(percent)}</code> {pct(percent, lang)}")
        lines += insight_lines(test.key, key, lang)
        lines.append("")

    return "\n".join(lines).rstrip()


# --- IQ ---------------------------------------------------------------------


def duration(seconds: int, lang: str) -> str:
    minutes, sec = divmod(max(0, seconds), 60)
    return (t("dur_min_sec", lang, m=minutes, s=sec) if minutes
            else t("dur_sec", lang, s=sec))


def iq_scale(iq: int, low: int = 70, high: int = 145) -> str:
    """70 dan 145 gacha shkalada natija qayerda turgani."""
    cells = 12
    position = round((iq - low) / (high - low) * (cells - 1))
    return "".join("🔵" if i == position else "▫️" for i in range(cells))


def render_iq(correct: int, estimate: dict, seconds: int | None, lang: str,
              comparison: dict | None = None) -> str:
    """IQ natijasi. estimate — `psytests.iq.estimate_iq()` natijasi."""
    iq = estimate["iq"]
    level = level_for(iq)
    lines = [
        t("iq_res_title", lang),
        "",
        t("iq_res_estimate", lang, iq=iq),
        t("iq_res_range", lang, low=estimate["low"], high=estimate["high"]),
        f"70 {iq_scale(iq)} 145",
        "",
        t("iq_res_level", lang, emoji=level.emoji, name=tr(level.name, lang)),
        tr(level.note, lang),
        "",
        t("iq_res_correct", lang, correct=correct, total=IQ_TOTAL),
    ]
    compared = comparison_line(comparison, lang)
    if compared:
        lines.append(compared)
    if seconds is not None:
        lines.append(t("iq_res_time", lang, duration=duration(seconds, lang)))
        if seconds < IQ_TOTAL * RUSHED_SECONDS_PER_PUZZLE:
            lines.append(t("iq_res_rushed", lang))
    lines += ["", SEP, "", next_step(IQ_KEY, lang)]
    return "\n".join(lines)


# --- Tarix ------------------------------------------------------------------


def _iq_history(row: dict) -> str:
    """Rasmli testda taxminiy IQ saqlangan; eski matnli testda — faqat IQ ball."""
    try:
        details = json.loads(row.get("scales") or "{}")
    except (TypeError, ValueError):
        details = {}
    if details.get("iq"):
        return f"IQ ≈{details['iq']} ({row['total']:.0f}/20)"
    return f"IQ {row['total']:.0f}" if row["total"] > 20 else f"{row['total']:.0f}/20"


def render_history(rows: list[dict], lang: str, registry: dict) -> str:
    if not rows:
        return t("history_empty", lang)

    lines = [t("history_title", lang), ""]
    for row in rows:
        test = registry.get(row["test_key"])
        if row["test_key"] == IQ_KEY:
            title = "Premium IQ testi" if lang == "uz" else "Премиум IQ-тест"
            emoji = IQ_EMOJI
        else:
            title = tr(test.title, lang) if test else row["test_key"]
            emoji = test.emoji if test else "•"
        age = AGE_LABELS.get(row["age_group"] or "")
        parts = [f"{emoji} <b>{title}</b>"]
        if row["test_key"] == IQ_KEY and row["total"] is not None:
            parts.append(_iq_history(row))
        if age:
            parts.append(tr(age, lang))
        if row["total"] is not None and test and test.kind == "index":
            parts.append(f"{row['total']:.0f} " + ("ball" if lang == "uz" else "балл"))
        when = (row["created_at"] or "")[:10]
        if when:
            parts.append(f"<i>{when}</i>")
        lines.append(" · ".join(parts))
    return "\n".join(lines)
