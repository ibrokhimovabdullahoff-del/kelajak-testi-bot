"""Test o'rtasidagi javoblar bazada saqlanadi.

Foydalanuvchi testni tashlab ketsa yoki bot qayta ishga tushsa (deploy),
javoblar yo'qolmaydi: /start menyusining tepasida "▶️ Testni davom
ettirish (23/50)" tugmasi chiqadi, eski savol tugmasi bosilsa ham test
shu joydan davom etadi. Test tugagach yozuv o'chiriladi.
"""
from __future__ import annotations

import json

import database as db


async def save(user_id: int, test_key: str, answers: list, age_group: str | None = None,
               extra: dict | None = None) -> None:
    conn = await db.connect()
    await conn.execute(
        """
        INSERT INTO progress (user_id, test_key, answers, age_group, extra, updated_at)
        VALUES (?, ?, ?, ?, ?, ?)
        ON CONFLICT(user_id, test_key) DO UPDATE SET
            answers = excluded.answers, age_group = excluded.age_group,
            extra = excluded.extra, updated_at = excluded.updated_at
        """,
        (user_id, test_key, json.dumps(answers), age_group,
         json.dumps(extra or {}, ensure_ascii=False), db._now()),
    )
    await conn.commit()


def _row(row) -> dict:
    return {
        "user_id": row[0], "test_key": row[1], "answers": json.loads(row[2] or "[]"),
        "age_group": row[3], "extra": json.loads(row[4] or "{}"), "updated_at": row[5],
    }


async def load(user_id: int, test_key: str) -> dict | None:
    conn = await db.connect()
    cursor = await conn.execute(
        "SELECT user_id, test_key, answers, age_group, extra, updated_at FROM progress "
        "WHERE user_id = ? AND test_key = ?", (user_id, test_key))
    row = await cursor.fetchone()
    return _row(row) if row else None


async def latest(user_id: int) -> dict | None:
    """Eng oxirgi tugallanmagan test (bitta ham javob berilgan bo'lsa)."""
    conn = await db.connect()
    cursor = await conn.execute(
        "SELECT user_id, test_key, answers, age_group, extra, updated_at FROM progress "
        "WHERE user_id = ? AND answers != '[]' ORDER BY updated_at DESC LIMIT 1", (user_id,))
    row = await cursor.fetchone()
    return _row(row) if row else None


async def clear(user_id: int, test_key: str) -> None:
    conn = await db.connect()
    await conn.execute("DELETE FROM progress WHERE user_id = ? AND test_key = ?", (user_id, test_key))
    await conn.commit()
