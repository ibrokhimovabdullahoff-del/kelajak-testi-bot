"""Small compatibility patch for the IQ presentation layer."""
from __future__ import annotations

import html

from . import iq


def question_text(index: int, lang: str) -> str:
    title = iq.bi(lang, "Premium IQ testi", "Премиум IQ-тест")
    q = iq.QUESTIONS[index][1].get(lang, iq.QUESTIONS[index][1]["uz"])
    return (
        f"{iq.IQ_EMOJI} <b>{title}</b>\n\n"
        f"{iq.progress(index)}\n"
        f"<b>{index + 1} / {len(iq.QUESTIONS)}</b>\n\n"
        f"<b>{html.escape(q)}</b>"
    )


_original_bi = iq.bi


def bi(lang: str, uz: str, ru: str) -> str:
    if uz.startswith("💡 Bu ko‘rsatkich ushbu 30 savollik testdagi natijadan"):
        return ""
    if ru.startswith("💡 Этот показатель рассчитан по результатам данного теста"):
        return ""
    return _original_bi(lang, uz, ru)


# The registered handlers resolve these globals at runtime, so replacing the helpers
# removes the labels/disclaimer without duplicating the 30-question handler.
iq.question_text = question_text
iq.bi = bi
