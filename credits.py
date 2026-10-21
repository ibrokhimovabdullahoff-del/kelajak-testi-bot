"""Bepul ochish huquqi: "1 ta to'liq tahlil — o'zingiz tanlaysiz".

Do'st taklifi mukofoti shu yerga tushadi (`referral_rewards.py`). Huquq
ishlatilganda tanlangan test `access.grant()` orqali ochiladi; yozuv
o'chirilmaydi — `used_test` / `used_at` to'ladi, shunda kim nimani qachon
ochgani ko'rinib turadi.
"""
from __future__ import annotations

import asyncio

import access
import database as db

_lock = asyncio.Lock()


async def add(user_id: int, source: str, ref: str) -> bool:
    """Bitta huquq qo'shadi. (source, ref) takrorlansa — qo'shilmaydi (False)."""
    conn = await db.connect()
    cursor = await conn.execute(
        "INSERT OR IGNORE INTO unlock_credits (user_id, source, ref, created_at) VALUES (?, ?, ?, ?)",
        (user_id, source, ref, db._now()),
    )
    await conn.commit()
    return cursor.rowcount == 1


async def available(user_id: int) -> int:
    conn = await db.connect()
    cursor = await conn.execute(
        "SELECT COUNT(*) FROM unlock_credits WHERE user_id = ? AND used_at IS NULL", (user_id,))
    return int((await cursor.fetchone())[0])


async def use(user_id: int, test_key: str) -> bool:
    """Eng eski ishlatilmagan huquq bilan testning to'liq tahlilini ochadi.

    Test allaqachon ochiq bo'lsa yoki huquq qolmagan bo'lsa — False, huquq
    sarflanmaydi.
    """
    if test_key not in access.TESTS or await access.has(user_id, test_key):
        return False
    async with _lock:
        conn = await db.connect()
        cursor = await conn.execute(
            "SELECT id, source FROM unlock_credits WHERE user_id = ? AND used_at IS NULL ORDER BY id LIMIT 1",
            (user_id,))
        row = await cursor.fetchone()
        if row is None:
            return False
        credit_id, source = row
        await conn.execute(
            "UPDATE unlock_credits SET used_test = ?, used_at = ? WHERE id = ? AND used_at IS NULL",
            (test_key, db._now(), credit_id))
        await conn.commit()
    await access.grant(user_id, [test_key], source)
    return True
