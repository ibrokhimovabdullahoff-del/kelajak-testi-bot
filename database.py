"""SQLite qatlami.

DB_PATH muhit o'zgaruvchisi orqali beriladi, shuning uchun serverda doimiy
diskka yo'naltirish yetarli — kodni o'zgartirish shart emas.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone

import aiosqlite

from config import DB_PATH

_SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    user_id     INTEGER PRIMARY KEY,
    username    TEXT,
    full_name   TEXT,
    -- NULL = foydalanuvchi hali tilni tanlamagan. Shu sababli DEFAULT yo'q:
    -- aks holda yangi kelgan odamdan til so'ralmay qolardi.
    lang        TEXT,
    created_at  TEXT NOT NULL,
    last_seen   TEXT NOT NULL,
    is_blocked  INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS results (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id     INTEGER NOT NULL,
    test_key    TEXT NOT NULL,
    lang        TEXT NOT NULL DEFAULT 'uz',
    age_group   TEXT,
    total       REAL,
    scales      TEXT NOT NULL,
    created_at  TEXT NOT NULL
);
"""

# Indekslar jadval ustunlari ko'chirilgandan KEYIN yaratiladi — eski bazada
# test_key ustuni hali bo'lmasligi mumkin.
_INDEXES = """
CREATE INDEX IF NOT EXISTS idx_results_user ON results(user_id);
CREATE INDEX IF NOT EXISTS idx_results_created ON results(created_at);
CREATE INDEX IF NOT EXISTS idx_results_test ON results(test_key);
"""

#: Eski sxemadan yangisiga ko'chirish uchun ustun nomlari.
_LEGACY_MODE_MAP = {"adult": "future", "kid": "child"}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


async def _columns(db: aiosqlite.Connection, table: str) -> set[str]:
    cursor = await db.execute(f"PRAGMA table_info({table})")
    return {row[1] for row in await cursor.fetchall()}


async def _rebuild_results(db: aiosqlite.Connection, cols: set[str]) -> None:
    """Eski `results` jadvalini yangi sxema bilan qaytadan quradi.

    ALTER TABLE bilan cheklanib bo'lmaydi: eski jadvalda `mode` va `dims`
    ustunlari NOT NULL, `total` ham NOT NULL. Ular qolsa yangi yozuv
    qo'shilmaydi (Big Five'da total umuman bo'lmaydi). SQLite ustunni
    o'chira olmaydi, shuning uchun jadval nusxalab qayta yaratiladi.
    """
    if "mode" in cols:
        case = " ".join(
            f"WHEN '{legacy}' THEN '{new}'" for legacy, new in _LEGACY_MODE_MAP.items()
        )
        mode_expr = f"CASE mode {case} ELSE mode END"
    else:
        mode_expr = "'future'"

    test_key = f"COALESCE(test_key, {mode_expr})" if "test_key" in cols else mode_expr
    scales = "scales" if "scales" in cols else None
    if "dims" in cols:
        scales = f"COALESCE({scales}, dims)" if scales else "dims"
    scales = f"COALESCE({scales}, '{{}}')" if scales else "'{}'"
    lang = "COALESCE(lang, 'uz')" if "lang" in cols else "'uz'"

    await db.executescript(_SCHEMA.replace("results", "results_new"))
    await db.execute(
        f"""
        INSERT INTO results_new
            (user_id, test_key, lang, age_group, total, scales, created_at)
        SELECT user_id, {test_key}, {lang}, age_group, total, {scales}, created_at
        FROM results
        """
    )
    await db.execute("DROP TABLE results")
    await db.execute("ALTER TABLE results_new RENAME TO results")


async def init() -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.executescript(_SCHEMA)

        user_cols = await _columns(db, "users")
        if "lang" not in user_cols:
            # DEFAULT ataylab qo'yilmadi: eski foydalanuvchilardan ham til
            # bir marta so'ralsin — ular rus tili qo'shilganini bilmaydi.
            await db.execute("ALTER TABLE users ADD COLUMN lang TEXT")

        result_cols = await _columns(db, "results")
        if {"mode", "dims"} & result_cols:
            await _rebuild_results(db, result_cols)

        await db.executescript(_INDEXES)
        await db.commit()


# --- Foydalanuvchilar -------------------------------------------------------


async def upsert_user(user_id: int, username: str | None, full_name: str) -> None:
    now = _now()
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """
            INSERT INTO users (user_id, username, full_name, created_at, last_seen)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                username   = excluded.username,
                full_name  = excluded.full_name,
                last_seen  = excluded.last_seen,
                is_blocked = 0
            """,
            (user_id, username, full_name, now, now),
        )
        await db.commit()


async def get_lang(user_id: int) -> str | None:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "SELECT lang FROM users WHERE user_id = ?", (user_id,)
        )
        row = await cursor.fetchone()
    return row[0] if row and row[0] else None


async def set_lang(user_id: int, lang: str) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE users SET lang = ? WHERE user_id = ?", (lang, user_id)
        )
        await db.commit()


async def mark_blocked(user_id: int) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE users SET is_blocked = 1 WHERE user_id = ?", (user_id,)
        )
        await db.commit()


async def all_user_ids(
    include_blocked: bool = False, lang: str | None = None
) -> list[int]:
    conditions, args = [], []
    if not include_blocked:
        conditions.append("is_blocked = 0")
    if lang:
        conditions.append("lang = ?")
        args.append(lang)
    query = "SELECT user_id FROM users"
    if conditions:
        query += " WHERE " + " AND ".join(conditions)
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(query, tuple(args))
        rows = await cursor.fetchall()
    return [row[0] for row in rows]


# --- Natijalar --------------------------------------------------------------


async def save_result(
    user_id: int,
    test_key: str,
    lang: str,
    age_group: str | None,
    total: float | None,
    scales: dict,
) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """
            INSERT INTO results
                (user_id, test_key, lang, age_group, total, scales, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (user_id, test_key, lang, age_group, total,
             json.dumps(scales, ensure_ascii=False), _now()),
        )
        await db.commit()


async def user_history(user_id: int, limit: int = 10) -> list[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            """
            SELECT test_key, age_group, total, created_at
            FROM results WHERE user_id = ?
            ORDER BY id DESC LIMIT ?
            """,
            (user_id, limit),
        )
        rows = await cursor.fetchall()
    return [dict(row) for row in rows]


# --- Statistika -------------------------------------------------------------


async def stats() -> dict:
    today = datetime.now(timezone.utc).date().isoformat()
    async with aiosqlite.connect(DB_PATH) as db:
        async def one(query: str, args: tuple = ()) -> float:
            cursor = await db.execute(query, args)
            row = await cursor.fetchone()
            return row[0] if row and row[0] is not None else 0

        data = {
            "users": await one("SELECT COUNT(*) FROM users"),
            "blocked": await one("SELECT COUNT(*) FROM users WHERE is_blocked = 1"),
            "new_today": await one(
                "SELECT COUNT(*) FROM users WHERE substr(created_at, 1, 10) = ?",
                (today,),
            ),
            "uz": await one("SELECT COUNT(*) FROM users WHERE lang = 'uz'"),
            "ru": await one("SELECT COUNT(*) FROM users WHERE lang = 'ru'"),
            "tests": await one("SELECT COUNT(*) FROM results"),
            "tests_today": await one(
                "SELECT COUNT(*) FROM results WHERE substr(created_at, 1, 10) = ?",
                (today,),
            ),
        }

        cursor = await db.execute(
            """
            SELECT test_key, COUNT(*), AVG(total)
            FROM results GROUP BY test_key ORDER BY COUNT(*) DESC
            """
        )
        data["per_test"] = [
            {"key": row[0], "count": row[1], "avg": row[2]}
            for row in await cursor.fetchall()
        ]
    return data
