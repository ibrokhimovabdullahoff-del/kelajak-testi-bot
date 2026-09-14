"""Database-backed question CMS and runtime content overrides."""
from __future__ import annotations

import json
from dataclasses import replace
from datetime import datetime, timezone

import aiosqlite

from config import DB_PATH, IQ_KEY
from psytests import REGISTRY

SCHEMA = """
CREATE TABLE IF NOT EXISTS cms_questions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    test_key TEXT NOT NULL,
    position INTEGER NOT NULL,
    category TEXT NOT NULL,
    difficulty INTEGER NOT NULL DEFAULT 1 CHECK(difficulty BETWEEN 1 AND 5),
    enabled INTEGER NOT NULL DEFAULT 1 CHECK(enabled IN (0,1)),
    reverse INTEGER NOT NULL DEFAULT 0 CHECK(reverse IN (0,1)),
    kind TEXT NOT NULL DEFAULT 'freq',
    text_uz TEXT NOT NULL,
    text_ru TEXT NOT NULL,
    options_uz TEXT,
    options_ru TEXT,
    correct_index INTEGER,
    image_url TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    UNIQUE(test_key, position)
);
CREATE INDEX IF NOT EXISTS idx_cms_questions_test ON cms_questions(test_key, enabled, position);
"""

_initialized = False

def _now() -> str:
    return datetime.now(timezone.utc).isoformat()

class CMSItem:
    """Runtime-compatible Item with optional CMS answer/image overrides."""
    def __init__(self, scale, text, kind="freq", reverse=False, answers_override=None, image_url=None):
        self.scale = scale
        self.text = text
        self.kind = kind
        self.reverse = reverse
        self.answers_override = answers_override
        self.image_url = image_url

    def answers(self, lang: str) -> list[str]:
        if self.answers_override and self.answers_override.get(lang):
            return [f"{i + 1}️⃣ {x}" for i, x in enumerate(self.answers_override[lang])]
        from psytests.base import Item
        return Item(self.scale, self.text, kind=self.kind, reverse=self.reverse).answers(lang)

async def init() -> None:
    global _initialized
    if _initialized:
        return
    async with aiosqlite.connect(DB_PATH) as conn:
        await conn.executescript(SCHEMA)
        await conn.commit()
    await seed()
    _initialized = True

def _static_rows():
    rows = []
    for key, test in REGISTRY.items():
        for pos, item in enumerate(test.items):
            rows.append((key, pos, item.scale, 1, 1, int(item.reverse), item.kind,
                         item.text.get("uz", ""), item.text.get("ru", ""), None, None, None, None))
    from handlers import iq
    for pos, q in enumerate(iq.QUESTIONS):
        category, text, uz, ru, correct, difficulty = q
        rows.append((IQ_KEY, pos, category, difficulty, 1, 0, "iq",
                     text.get("uz", ""), text.get("ru", ""),
                     json.dumps(uz, ensure_ascii=False), json.dumps(ru, ensure_ascii=False), correct, None))
    return rows

async def seed() -> None:
    async with aiosqlite.connect(DB_PATH) as conn:
        cur = await conn.execute("SELECT COUNT(*) FROM cms_questions")
        if (await cur.fetchone())[0]:
            return
        now = _now()
        for row in _static_rows():
            await conn.execute(
                """INSERT OR IGNORE INTO cms_questions
                (test_key,position,category,difficulty,enabled,reverse,kind,text_uz,text_ru,
                 options_uz,options_ru,correct_index,image_url,created_at,updated_at)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (*row, now, now))
        await conn.commit()

async def rows(test_key: str, include_disabled: bool = True) -> list[dict]:
    where = "" if include_disabled else " AND enabled=1"
    async with aiosqlite.connect(DB_PATH) as conn:
        conn.row_factory = aiosqlite.Row
        cur = await conn.execute(f"SELECT * FROM cms_questions WHERE test_key=?{where} ORDER BY position,id", (test_key,))
        return [dict(r) for r in await cur.fetchall()]

async def get(question_id: int) -> dict | None:
    async with aiosqlite.connect(DB_PATH) as conn:
        conn.row_factory = aiosqlite.Row
        cur = await conn.execute("SELECT * FROM cms_questions WHERE id=?", (question_id,))
        row = await cur.fetchone()
        return dict(row) if row else None

async def create(data: dict) -> int:
    async with aiosqlite.connect(DB_PATH) as conn:
        cur = await conn.execute("SELECT COALESCE(MAX(position),-1)+1 FROM cms_questions WHERE test_key=?", (data["test_key"],))
        pos = (await cur.fetchone())[0]
        now = _now()
        cur = await conn.execute(
            """INSERT INTO cms_questions
            (test_key,position,category,difficulty,enabled,reverse,kind,text_uz,text_ru,
             options_uz,options_ru,correct_index,image_url,created_at,updated_at)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (data["test_key"], pos, data.get("category", "logic"), data.get("difficulty", 1), 1,
             int(data.get("reverse", False)), data.get("kind", "freq"), data.get("text_uz", ""),
             data.get("text_ru", ""),
             json.dumps(data.get("options_uz"), ensure_ascii=False) if data.get("options_uz") else None,
             json.dumps(data.get("options_ru"), ensure_ascii=False) if data.get("options_ru") else None,
             data.get("correct_index"), data.get("image_url"), now, now))
        await conn.commit()
        return int(cur.lastrowid)

async def update(question_id: int, **fields) -> bool:
    allowed = {"category", "difficulty", "enabled", "reverse", "kind", "text_uz", "text_ru",
               "options_uz", "options_ru", "correct_index", "image_url", "position"}
    fields = {k: v for k, v in fields.items() if k in allowed}
    if not fields:
        return False
    for key in ("options_uz", "options_ru"):
        if key in fields and isinstance(fields[key], list):
            fields[key] = json.dumps(fields[key], ensure_ascii=False)
    fields["updated_at"] = _now()
    sql = ", ".join(f"{key}=?" for key in fields)
    async with aiosqlite.connect(DB_PATH) as conn:
        await conn.execute(f"UPDATE cms_questions SET {sql} WHERE id=?", (*fields.values(), question_id))
        await conn.commit()
    return True

async def delete(question_id: int) -> bool:
    async with aiosqlite.connect(DB_PATH) as conn:
        cur = await conn.execute("SELECT test_key,position FROM cms_questions WHERE id=?", (question_id,))
        row = await cur.fetchone()
        if not row:
            return False
        await conn.execute("DELETE FROM cms_questions WHERE id=?", (question_id,))
        await conn.execute("UPDATE cms_questions SET position=position-1 WHERE test_key=? AND position>?", (row[0], row[1]))
        await conn.commit()
    return True

def _opts(row: dict, lang: str):
    raw = row.get("options_uz" if lang == "uz" else "options_ru")
    if not raw:
        return None
    try:
        return json.loads(raw)
    except Exception:
        return None

async def apply_all() -> None:
    """Apply enabled DB content to the in-memory registry and IQ list."""
    await init()
    from psytests import REGISTRY as registry
    for key, test in list(registry.items()):
        rr = await rows(key, include_disabled=False)
        if not rr:
            continue
        items = []
        for row in rr:
            uz, ru = _opts(row, "uz"), _opts(row, "ru")
            override = {"uz": uz or [], "ru": ru or []} if (uz or ru) else None
            items.append(CMSItem(row["category"], {"uz": row["text_uz"], "ru": row["text_ru"]},
                                 kind=row["kind"], reverse=bool(row["reverse"]),
                                 answers_override=override, image_url=row["image_url"]))
        registry[key] = replace(test, items=items)
    from handlers import iq
    rr = await rows(IQ_KEY, include_disabled=False)
    if rr:
        iq.QUESTIONS = [
            (row["category"], {"uz": row["text_uz"], "ru": row["text_ru"]},
             _opts(row, "uz") or [], _opts(row, "ru") or [], int(row["correct_index"] or 0),
             int(row["difficulty"] or 1)) for row in rr
        ]
