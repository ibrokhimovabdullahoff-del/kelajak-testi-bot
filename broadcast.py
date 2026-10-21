"""Ko'pchilikka xabar yuborish: admin xabari va bir martalik yangilik e'loni.

  * bloklagan foydalanuvchilarga yuborilmaydi (`users.is_blocked = 0`);
  * Telegram chegarasi: soniyasiga ~20 ta xabar, "RetryAfter" kelsa kutadi;
  * "bot was blocked" — foydalanuvchi bloklagan deb belgilanadi;
  * har bir yuborish `broadcasts` jadvaliga va log'ga yoziladi:
    nechtasi yetdi, nechtasi bloklagan, nechtasida xato.
"""
from __future__ import annotations

import asyncio
import logging
from collections.abc import Awaitable, Callable

from aiogram.exceptions import TelegramForbiddenError, TelegramRetryAfter

import database as db

log = logging.getLogger(__name__)

#: Xabarlar orasidagi pauza (soniya) — Telegram cheklovidan ancha past.
PAUSE = 0.05


async def _start(kind: str, admin_id: int | None, target: str | None, total: int) -> int:
    conn = await db.connect()
    cursor = await conn.execute(
        "INSERT INTO broadcasts (kind, admin_id, target, started_at, total) VALUES (?, ?, ?, ?, ?)",
        (kind, admin_id, target, db._now(), total))
    await conn.commit()
    return int(cursor.lastrowid)


async def _finish(broadcast_id: int, counts: dict) -> None:
    conn = await db.connect()
    await conn.execute(
        "UPDATE broadcasts SET finished_at = ?, sent = ?, blocked = ?, failed = ? WHERE id = ?",
        (db._now(), counts["sent"], counts["blocked"], counts["failed"], broadcast_id))
    await conn.commit()


async def send_all(user_ids: list[int], send_one: Callable[[int], Awaitable], *, kind: str,
                   admin_id: int | None = None, target: str | None = None) -> dict:
    """Hammaga yuboradi. Qaytaradi: {"id", "total", "sent", "blocked", "failed"}."""
    from handlers.lifecycle import record_blocked

    counts = {"total": len(user_ids), "sent": 0, "blocked": 0, "failed": 0}
    counts["id"] = await _start(kind, admin_id, target, len(user_ids))
    log.info("Broadcast #%s (%s) boshlandi: %d ta", counts["id"], kind, len(user_ids))
    for user_id in user_ids:
        for attempt in range(2):
            try:
                await send_one(user_id)
                counts["sent"] += 1
            except TelegramRetryAfter as exc:
                if attempt == 0:
                    await asyncio.sleep(exc.retry_after + 1)
                    continue
                counts["failed"] += 1
            except TelegramForbiddenError:
                await record_blocked(user_id)
                counts["blocked"] += 1
            except Exception as exc:  # noqa: BLE001 — bitta odam xatosi qolganlarga to'sqinlik qilmasin
                log.warning("Broadcast #%s: %s ga yetmadi: %s", counts["id"], user_id, exc)
                counts["failed"] += 1
            break
        await asyncio.sleep(PAUSE)
    await _finish(counts["id"], counts)
    log.info("Broadcast #%s (%s) tugadi: yetdi %d, bloklagan %d, xato %d", counts["id"], kind,
             counts["sent"], counts["blocked"], counts["failed"])
    return counts


async def get(broadcast_id: int) -> dict | None:
    conn = await db.connect()
    cursor = await conn.execute("SELECT * FROM broadcasts WHERE id = ?", (broadcast_id,))
    rows = await db._dicts(cursor)
    return rows[0] if rows else None
