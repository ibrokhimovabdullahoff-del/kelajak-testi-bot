"""Hamkorlar uchun promo kodlar (2-bosqich, brief 7.3).

Ikki tur:
  * free     — ko'rsatilgan testlarning to'liq tahlili darhol ochiladi;
  * discount — keyingi BITTA to'lovga chegirma (foiz). To'lov oynasida narx
               o'zi kamayadi; to'lov o'tgach chegirma ishlatilgan bo'ladi.

Kod admin panelda yaratiladi (🚀 O'sish → 🎟 Promo kodlar): turi, qiymati,
nechta odam ishlata olishi (0 — cheksiz), muddati va izoh (masalan, o'quv
markaz nomi). Odam kodni havola orqali (/start promo_KOD) yoki /promo
buyrug'i bilan kiritadi. Bitta odam bitta kodni bir marta ishlata oladi.
/stats da har bir kod o'z manbasi ostida (promo_<kod>) ko'rinadi.
"""
from __future__ import annotations

import asyncio
import re
from datetime import timedelta

import access
import clock
import database as db
import events

FREE = "free"
DISCOUNT = "discount"
MAX_PERCENT = 90

#: redeem() natijalari.
OK = "ok"
NOT_FOUND = "not_found"
INACTIVE = "inactive"
EXPIRED = "expired"
USED_UP = "used_up"
ALREADY = "already"

_CODE = re.compile(r"^[a-z0-9_]{3,24}$")
_lock = asyncio.Lock()


def normalize(raw: str | None) -> str | None:
    """"Maktab-5 " → "maktab5". Yaroqsiz bo'lsa — None."""
    code = re.sub(r"[^a-z0-9_]", "", (raw or "").strip().lower())
    return code if _CODE.match(code) else None


def tests_of(row: dict) -> list[str]:
    return [key for key in (row.get("tests") or "").split(",") if key in access.TESTS]


async def get(code: str) -> dict | None:
    conn = await db.connect()
    cursor = await conn.execute("SELECT * FROM promo_codes WHERE code = ?", (code,))
    rows = await db._dicts(cursor)
    return rows[0] if rows else None


async def all_codes() -> list[dict]:
    conn = await db.connect()
    cursor = await conn.execute("SELECT * FROM promo_codes ORDER BY active DESC, created_at DESC")
    return await db._dicts(cursor)


async def create(code: str, kind: str, *, percent: int = 0, tests: list[str] | None = None,
                 max_uses: int = 0, days: int = 0, label: str = "", admin_id: int | None = None) -> bool:
    """Yangi kod. Shu nomli kod bor bo'lsa — False (eskisi o'zgarmaydi)."""
    if kind not in (FREE, DISCOUNT):
        raise ValueError(kind)
    expires = clock.iso(clock.utc_now() + timedelta(days=days)) if days > 0 else None
    conn = await db.connect()
    cursor = await conn.execute(
        "INSERT OR IGNORE INTO promo_codes (code, label, kind, percent, tests, max_uses, expires_at, "
        "created_by, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (code, label, kind, percent if kind == DISCOUNT else 0, ",".join(tests or []) if kind == FREE else "",
         max(0, max_uses), expires, admin_id, db._now()))
    await conn.commit()
    return cursor.rowcount == 1


async def set_active(code: str, active: bool) -> None:
    conn = await db.connect()
    await conn.execute("UPDATE promo_codes SET active = ? WHERE code = ?", (int(active), code))
    await conn.commit()


def _expired(row: dict) -> bool:
    return bool(row.get("expires_at")) and row["expires_at"] <= db._now()


async def redeem(user_id: int, raw: str | None) -> tuple[str, dict | None]:
    """Kodni ishlatadi. Qaytaradi: (natija, kod qatori)."""
    code = normalize(raw)
    row = await get(code) if code else None
    if row is None:
        return NOT_FOUND, None
    if not row["active"]:
        return INACTIVE, row
    if _expired(row):
        return EXPIRED, row
    async with _lock:
        conn = await db.connect()
        cursor = await conn.execute("SELECT 1 FROM promo_redemptions WHERE code = ? AND user_id = ?",
                                    (code, user_id))
        if await cursor.fetchone():
            return ALREADY, row
        cursor = await conn.execute(
            "UPDATE promo_codes SET uses = uses + 1 WHERE code = ? AND (max_uses = 0 OR uses < max_uses)",
            (code,))
        if cursor.rowcount == 0:
            await conn.commit()
            return USED_UP, row
        await conn.execute("INSERT INTO promo_redemptions (code, user_id, created_at) VALUES (?, ?, ?)",
                           (code, user_id, db._now()))
        await conn.commit()
    if row["kind"] == FREE:
        await access.grant(user_id, tests_of(row), "promo")
        await consume(user_id, code, None)
    events.track(user_id, "promo_used", code=code, kind=row["kind"])
    return OK, row


async def active_discount(user_id: int) -> dict | None:
    """Ishlatilmagan chegirma (eng oxirgisi): {"code", "percent"} yoki None."""
    conn = await db.connect()
    cursor = await conn.execute(
        """
        SELECT p.code, p.percent, p.expires_at FROM promo_redemptions r
        JOIN promo_codes p ON p.code = r.code
        WHERE r.user_id = ? AND r.used_at IS NULL AND p.kind = 'discount' AND p.percent > 0
        ORDER BY r.created_at DESC
        """, (user_id,))
    for code, percent, expires_at in await cursor.fetchall():
        if not expires_at or expires_at > db._now():
            return {"code": code, "percent": int(percent)}
    return None


def apply(price: int, percent: int) -> int:
    """Chegirmali narx — 10 so'mgacha yaxlitlanadi, hech qachon 0 bo'lmaydi."""
    percent = max(0, min(MAX_PERCENT, percent))
    return max(10, int(round(price * (100 - percent) / 100 / 10)) * 10) if price > 0 else price


async def consume(user_id: int, code: str, payment_id: int | None) -> None:
    conn = await db.connect()
    await conn.execute(
        "UPDATE promo_redemptions SET payment_id = ?, used_at = ? WHERE code = ? AND user_id = ? AND used_at IS NULL",
        (payment_id, db._now(), code, user_id))
    await conn.commit()


async def usage(since: str) -> list[tuple[str, str, int]]:
    """/stats uchun: (kod, izoh, shu davrda ishlatganlar)."""
    conn = await db.connect()
    cursor = await conn.execute(
        "SELECT r.code, COALESCE(p.label, ''), COUNT(*) FROM promo_redemptions r "
        "LEFT JOIN promo_codes p ON p.code = r.code WHERE r.created_at >= ? GROUP BY r.code ORDER BY 3 DESC",
        (since,))
    return [(c, label, int(n)) for c, label, n in await cursor.fetchall()]
