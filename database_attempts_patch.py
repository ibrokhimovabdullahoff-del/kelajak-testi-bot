"""One paid test purchase = one completed attempt.

This keeps payments permanently recorded as paid for accounting/history while
separately marking the paid attempt as consumed after a completed result.
"""
from __future__ import annotations

import asyncio
from datetime import datetime, timezone

import database as db
from config import is_admin


_lock = asyncio.Lock()
_ready = False


async def _ensure_schema() -> None:
    global _ready
    if _ready:
        return
    async with _lock:
        if _ready:
            return
        conn = await db.connect()
        await conn.execute(
            """
            CREATE TABLE IF NOT EXISTS payment_attempts_used (
                payment_id INTEGER PRIMARY KEY,
                user_id INTEGER NOT NULL,
                product TEXT NOT NULL,
                consumed_at TEXT NOT NULL
            )
            """
        )
        await conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_attempts_used_user "
            "ON payment_attempts_used(user_id)"
        )
        await conn.commit()
        _ready = True


async def _unconsumed_payment_id(user_id: int, test_key: str) -> int | None:
    conn = await db.connect()
    cur = await conn.execute(
        """
        SELECT p.id
        FROM payments p
        LEFT JOIN payment_attempts_used u ON u.payment_id = p.id
        WHERE p.user_id = ?
          AND p.status = 'paid'
          AND u.payment_id IS NULL
          AND p.product IN (?, ?)
        ORDER BY CASE WHEN p.product = ? THEN 0 ELSE 1 END, p.id ASC
        LIMIT 1
        """,
        (user_id, test_key, db.ALL_PRODUCTS, test_key),
    )
    row = await cur.fetchone()
    return int(row[0]) if row else None


async def _consume(payment_id: int, user_id: int, product: str) -> None:
    conn = await db.connect()
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    await conn.execute(
        """
        INSERT OR IGNORE INTO payment_attempts_used
            (payment_id, user_id, product, consumed_at)
        VALUES (?, ?, ?, ?)
        """,
        (payment_id, user_id, product, now),
    )
    await conn.commit()


async def paid_products(user_id: int) -> set[str]:
    await _ensure_schema()
    conn = await db.connect()
    cur = await conn.execute(
        """
        SELECT DISTINCT p.product
        FROM payments p
        LEFT JOIN payment_attempts_used u ON u.payment_id = p.id
        WHERE p.user_id = ?
          AND p.status = 'paid'
          AND u.payment_id IS NULL
        """,
        (user_id,),
    )
    return {row[0] for row in await cur.fetchall()}


async def save_result(
    user_id: int,
    test_key: str,
    lang: str,
    age_group: str | None,
    total: float | None,
    scales: dict,
) -> None:
    """Save a result and consume one paid attempt when this test is paid."""
    await _ensure_schema()
    async with _lock:
        conn = await db.connect()
        consume = test_key not in await db.free_tests()
        if consume and is_admin(user_id) and not await db.admin_pays():
            consume = False

        payment_id = None
        if consume:
            payment_id = await _unconsumed_payment_id(user_id, test_key)

        now = db._now()
        await conn.execute(
            """
            INSERT INTO results
                (user_id, test_key, lang, age_group, total, scales, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                user_id,
                test_key,
                lang,
                age_group,
                total,
                db.json.dumps(scales, ensure_ascii=False),
                now,
            ),
        )
        if payment_id is not None:
            await conn.execute(
                """
                INSERT OR IGNORE INTO payment_attempts_used
                    (payment_id, user_id, product, consumed_at)
                VALUES (?, ?, ?, ?)
                """,
                (payment_id, user_id, test_key, now),
            )
        await conn.commit()


_original = db.paid_products
_original_save_result = db.save_result


async def install() -> None:
    """Install the one-attempt DB behavior and initialize its table."""
    await _ensure_schema()
    db.paid_products = paid_products
    db.save_result = save_result


# Keep references available for debugging/backward compatibility.
original_paid_products = _original
original_save_result = _original_save_result
