"""Natija matnini yig'ish.

Qoida: natija bitta ekranga sig'sin. Uzun tushuntirish emas — ko'rsatkich,
ikkita kuchli tomon, ikkita aniq qadam.
"""
from __future__ import annotations

from locales import t, tr
from psytests import AGE_ADVICE, AGE_LABELS, TestDef, level_of
from psytests.base import L

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


def bar(percent: float) -> str:
    filled = max(0, min(BAR_LEN, round(percent / 100 * BAR_LEN)))
    return "█" * filled + "░" * (BAR_LEN - filled)


def _band(total: float):
    for threshold, emoji, name, note in BANDS:
        if total >= threshold:
            return emoji, name, note
    return BANDS[-1][1], BANDS[-1][2], BANDS[-1][3]


def render(test: TestDef, result: dict, lang: str, age_group: str | None) -> str:
    if test.kind == "traits":
        body = _render_traits(test, result, lang)
        disclaimer = t("disclaimer_validated", lang)
    elif test.kind == "interests":
        body = _render_interests(test, result, lang)
        disclaimer = t("disclaimer_career", lang)
    else:
        body = _render_index(test, result, lang, age_group)
        disclaimer = t("disclaimer_composite", lang)

    head = f"{test.emoji} <b>{tr(test.title, lang)}</b>"
    return f"{head}\n\n{body}\n\n{SEP}\n<i>{disclaimer}</i>"


# --- Big Five: profil -------------------------------------------------------


def _render_traits(test: TestDef, result: dict, lang: str) -> str:
    lines = []
    for key, scale in test.scales.items():
        percent = result["scales"][key]
        level = t("lvl_" + level_of(percent), lang)
        lines.append(f"{scale.emoji} <b>{tr(scale.name, lang)}</b> — {level}")
        lines.append(f"<code>{bar(percent)}</code> {percent:.0f}%")
        lines.append(tr(scale.levels[level_of(percent)], lang))
        lines.append("")
    return "\n".join(lines).rstrip()


# --- Kelajak / Farzand: umumiy indeks ---------------------------------------


def _render_index(
    test: TestDef, result: dict, lang: str, age_group: str | None
) -> str:
    total = result["total"]
    emoji, name, note = _band(total)

    lines = [
        f"{emoji} <b>{total:.0f} / 100 — {tr(name, lang)}</b>",
        tr(note, lang),
        "",
        SEP,
        "",
    ]

    for key in result["ranked"]:
        scale = test.scales[key]
        percent = result["scales"][key]
        lines.append(f"{scale.emoji} <b>{tr(scale.name, lang)}</b>")
        lines.append(f"<code>{bar(percent)}</code> {percent:.0f}%")

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
            f"{result['scales'][key]:.0f}%"
        )
        lines.append(tr(scale.levels["high"], lang))
        lines.append("")

    lines += [SEP, "", f"📊 <b>{t('res_all_areas', lang)}</b>", ""]
    for key in result["ranked"]:
        scale = test.scales[key]
        percent = result["scales"][key]
        lines.append(f"{scale.emoji} <b>{tr(scale.name, lang)}</b>")
        lines.append(f"<code>{bar(percent)}</code> {percent:.0f}%")

    return "\n".join(lines).rstrip()


# --- Tarix ------------------------------------------------------------------


def render_history(rows: list[dict], lang: str, registry: dict) -> str:
    if not rows:
        return t("history_empty", lang)

    lines = [t("history_title", lang), ""]
    for row in rows:
        test = registry.get(row["test_key"])
        title = tr(test.title, lang) if test else row["test_key"]
        emoji = test.emoji if test else "•"
        age = AGE_LABELS.get(row["age_group"] or "")
        parts = [f"{emoji} <b>{title}</b>"]
        if age:
            parts.append(tr(age, lang))
        if row["total"] is not None and test and test.kind == "index":
            parts.append(f"{row['total']:.0f} " + ("ball" if lang == "uz" else "балл"))
        when = (row["created_at"] or "")[:10]
        if when:
            parts.append(f"<i>{when}</i>")
        lines.append(" · ".join(parts))
    return "\n".join(lines)
