"""Database-backed question CMS and runtime content overrides."""
from __future__ import annotations

import json
import logging
from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path

import aiosqlite

from config import DB_PATH, IQ_KEY
from psytests import REGISTRY

log = logging.getLogger(__name__)

#: Savollar matni kod bilan birga yangilanganda shu raqam oshiriladi.
#: Oshirishdan OLDIN joriy savollarning nusxasini saqlang:
#:     python content_cms.py snapshot
#: Migratsiya bazadagi test aynan shu nusxadagidek qolganini (admin
#: tahrirlamaganini) tekshiradi va faqat shunda yangi matnni qo'llaydi.
CONTENT_VERSION = 2
SNAPSHOTS = Path(__file__).parent / "psytests"


def snapshot_path(version: int) -> Path:
    return SNAPSHOTS / f"cms_seed_v{version}.json"


SEED_V1 = snapshot_path(1)

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
CREATE TABLE IF NOT EXISTS settings (
    key         TEXT PRIMARY KEY,
    value       TEXT NOT NULL
);
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
    await migrate()
    _initialized = True

def _static_rows(test_key: str | None = None):
    """Koddagi savollar — bazaga yoziladigan ko'rinishda.

    Javob variantlari ham tayyor holda yoziladi. Avval faqat savol matni
    yozilardi va bot javoblarni fe'l shaklisiz yig'ardi — natijada odamlar
    "Ha," yoki "Umuman" degan chala tugmalarni ko'rardi.

    IQ bu yerda yo'q: u rasmli test va savollari kodda (handlers/iq.py).
    """
    rows = []
    for key, test in REGISTRY.items():
        if test_key is not None and key != test_key:
            continue
        for pos, item in enumerate(test.items):
            options = {
                lang: [text.split(" ", 1)[1] for text in item.answers(lang)]
                for lang in ("uz", "ru")
            }
            rows.append((key, pos, item.scale, 1, 1, int(item.reverse), item.kind,
                         item.text.get("uz", ""), item.text.get("ru", ""),
                         json.dumps(options["uz"], ensure_ascii=False),
                         json.dumps(options["ru"], ensure_ascii=False), None, None))
    return rows

async def _insert_rows(conn, rows) -> None:
    now = _now()
    for row in rows:
        await conn.execute(
            """INSERT OR IGNORE INTO cms_questions
            (test_key,position,category,difficulty,enabled,reverse,kind,text_uz,text_ru,
             options_uz,options_ru,correct_index,image_url,created_at,updated_at)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (*row, now, now))

async def seed() -> None:
    async with aiosqlite.connect(DB_PATH) as conn:
        cur = await conn.execute("SELECT COUNT(*) FROM cms_questions")
        if (await cur.fetchone())[0]:
            return
        await _insert_rows(conn, _static_rows())
        # Yangi baza darhol eng so'nggi matn bilan to'ladi — migratsiya kerak emas.
        await conn.execute(
            "INSERT INTO settings (key, value) VALUES ('content_version', ?) "
            "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
            (str(CONTENT_VERSION),))
        await conn.commit()

def _untouched(test_key: str, db_rows: list[dict], snapshot: dict) -> bool:
    """Bazadagi test o'sha versiya seed qilgan holatida qolganmi.

    v1 nusxasida javob variantlari yo'q (5 ustun), keyingilarida bor (7 ustun).
    """
    expected = snapshot.get(test_key)
    if expected is None or len(expected) != len(db_rows):
        return False
    for row, saved in zip(db_rows, expected):
        category, reverse, kind, text_uz, text_ru = saved[:5]
        options_uz, options_ru = (saved[5], saved[6]) if len(saved) == 7 else (None, None)
        if (row["category"], row["reverse"], row["kind"], row["text_uz"], row["text_ru"],
                row["options_uz"] or None, row["options_ru"] or None) != \
                (category, reverse, kind, text_uz, text_ru, options_uz, options_ru):
            return False
        if row["enabled"] != 1 or row["image_url"]:
            return False
    return True


def write_snapshot(version: int = CONTENT_VERSION) -> Path:
    """Koddagi joriy savollarni keyingi migratsiya uchun nusxa qilib saqlaydi."""
    data: dict[str, list] = {}
    for key, _pos, category, _d, _e, reverse, kind, tuz, tru, ouz, oru, _c, _i in _static_rows():
        data.setdefault(key, []).append([category, reverse, kind, tuz, tru, ouz, oru])
    path = snapshot_path(version)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    return path

async def migrate() -> None:
    """Kod bilan kelgan yangi savol matnini mavjud bazaga qo'llaydi.

    Faqat admin CMS orqali tegmagan testlar yangilanadi: agar biror savol
    qo'lda tahrirlangan bo'lsa, o'sha test butunligicha qoldiriladi — adminning
    ishi hech qachon jimgina o'chib ketmasligi kerak.
    """
    async with aiosqlite.connect(DB_PATH) as conn:
        conn.row_factory = aiosqlite.Row
        cur = await conn.execute("SELECT value FROM settings WHERE key='content_version'")
        row = await cur.fetchone()
        current = int(row["value"]) if row else 1
        if current >= CONTENT_VERSION:
            return
        path = snapshot_path(current)
        if not path.exists():
            log.error("CMS: %s topilmadi — savollar yangilanmadi.", path.name)
            return
        snapshot = json.loads(path.read_text(encoding="utf-8"))
        # Eski matnli IQ savollari: IQ endi rasmli va savollari bazada emas.
        await conn.execute("DELETE FROM cms_questions WHERE test_key=?", (IQ_KEY,))
        for key in REGISTRY:
            cur = await conn.execute(
                "SELECT * FROM cms_questions WHERE test_key=? ORDER BY position,id", (key,))
            db_rows = [dict(r) for r in await cur.fetchall()]
            if db_rows and not _untouched(key, db_rows, snapshot):
                log.warning("CMS: «%s» testi qo‘lda tahrirlangan — yangi savollar "
                            "qo‘llanmadi, admin tahriri saqlandi.", key)
                continue
            await conn.execute("DELETE FROM cms_questions WHERE test_key=?", (key,))
            await _insert_rows(conn, _static_rows(key))
            log.info("CMS: «%s» testi yangi savollar bilan yangilandi.", key)
        await conn.execute(
            "INSERT INTO settings (key, value) VALUES ('content_version', ?) "
            "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
            (str(CONTENT_VERSION),))
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
    """Apply enabled DB content to the in-memory test registry."""
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


if __name__ == "__main__":
    import sys

    if sys.argv[1:] == ["snapshot"]:
        print(f"Saqlandi: {write_snapshot()}")
    else:
        print("Ishlatish: python content_cms.py snapshot")
