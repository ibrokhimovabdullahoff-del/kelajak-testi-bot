"""Adds CMS image links to regular test question cards without changing quiz flow."""
from __future__ import annotations
import html
from . import user

_original = user.question_text

def question_text(test_key: str, index: int, lang: str) -> str:
    text = _original(test_key, index, lang)
    try:
        image_url = getattr(user.REGISTRY[test_key].items[index], "image_url", None)
    except (KeyError, IndexError):
        image_url = None
    if image_url:
        label = "🖼 Rasmni ko‘rish" if lang == "uz" else "🖼 Открыть изображение"
        text += f'\n\n<a href="{html.escape(image_url, quote=True)}">{label}</a>'
    return text

user.question_text = question_text
