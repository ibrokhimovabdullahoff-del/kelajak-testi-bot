"""Small compatibility patch for the IQ presentation layer."""
from __future__ import annotations
import html
import sqlite3
from config import DB_PATH
from . import iq

def _image_url(index: int):
    try:
        conn=sqlite3.connect(DB_PATH)
        row=conn.execute("SELECT image_url FROM cms_questions WHERE test_key='iq' AND position=? AND enabled=1",(index,)).fetchone()
        conn.close(); return row[0] if row else None
    except Exception:
        return None

def question_text(index: int, lang: str) -> str:
    title=iq.bi(lang,"Premium IQ testi","Премиум IQ-тест")
    q=iq.QUESTIONS[index][1].get(lang,iq.QUESTIONS[index][1]["uz"])
    text=(f"{iq.IQ_EMOJI} <b>{title}</b>\n\n" f"{iq.progress(index)}\n" f"<b>{index+1} / {len(iq.QUESTIONS)}</b>\n\n" f"<b>{html.escape(q)}</b>")
    image_url=_image_url(index)
    if image_url:
        label="🖼 Rasmni ko‘rish" if lang=="uz" else "🖼 Открыть изображение"
        text+=f'\n\n<a href="{html.escape(image_url,quote=True)}">{label}</a>'
    return text

_original_bi=iq.bi
def bi(lang: str, uz: str, ru: str) -> str:
    if uz.startswith("💡 Bu ko‘rsatkich ushbu 30 savollik testdagi natijadan"): return ""
    if ru.startswith("💡 Этот показатель рассчитан по результатам данного теста"): return ""
    return _original_bi(lang,uz,ru)

iq.question_text=question_text
iq.bi=bi
