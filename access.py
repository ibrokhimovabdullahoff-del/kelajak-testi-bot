"""To'liq tahlilga kirish huquqi (yangi model: test bepul, to'liq tahlil pullik).

Huquq testga beriladi, natijaga emas: bir marta ochilgan test keyingi
urinishlarda ham to'liq ko'rinadi. Huquq manbalari (`report_access.source`):

    legacy            — eski modelda testni sotib olganlar (migratsiya 5)
    click / wallet / card
    card_optimistic   — chek kelishi bilan ochilgan, admin hali ko'rmagan
    bundle            — 5 ta testning to'plami
    referral / promo  — do'st taklifi va hamkor kodi (2-bosqich)
    admin             — admin qo'lda ochgan

Tekshiruv tartibi: admin (sinov rejimi o'chiq bo'lsa) → bepul qilingan test
(admin panel: "🎁 To'liq tahlil bepul") → bazadagi huquq.
"""
from __future__ import annotations

import database as db
from config import IQ_KEY, MENU_ORDER, is_admin

#: To'liq tahlili sotiladigan testlar.
TESTS: tuple[str, ...] = tuple(MENU_ORDER)

_cache: dict[int, set[str]] = {}


def _drop(user_id: int) -> None:
    _cache.pop(user_id, None)


async def owned(user_id: int) -> set[str]:
    """Bazada ochilgan testlar (adminlik va bepul testlarsiz)."""
    cached = _cache.get(user_id)
    if cached is not None:
        return cached
    conn = await db.connect()
    cursor = await conn.execute("SELECT test_key FROM report_access WHERE user_id = ?", (user_id,))
    tests = {row[0] for row in await cursor.fetchall()}
    _cache[user_id] = tests
    return tests


async def has(user_id: int, test_key: str) -> bool:
    if is_admin(user_id) and not await db.admin_pays():
        return True
    if test_key in await db.free_tests():
        return True
    return test_key in await owned(user_id)


async def missing(user_id: int) -> list[str]:
    """Hali ochilmagan testlar (to'plam narxini ko'rsatish uchun)."""
    return [key for key in TESTS if not await has(user_id, key)]


async def grant(user_id: int, tests, source: str, payment_id: int | None = None) -> list[str]:
    """Huquq beradi. Qaytaradi: haqiqatan YANGI ochilgan testlar (hodisa shular uchun)."""
    tests = [key for key in tests if key in TESTS]
    if not tests:
        return []
    conn = await db.connect()
    now = db._now()
    new: list[str] = []
    for key in tests:
        cursor = await conn.execute(
            "INSERT OR IGNORE INTO report_access (user_id, test_key, source, payment_id, created_at) "
            "VALUES (?, ?, ?, ?, ?)",
            (user_id, key, source, payment_id, now),
        )
        if cursor.rowcount == 1:
            new.append(key)
    await conn.commit()
    _drop(user_id)
    if new:
        import events
        for key in new:
            events.track(user_id, "report_unlocked", key, source=source)
    return new


async def confirm_optimistic(payment_id: int) -> int:
    """Admin chekni tasdiqladi: "chekdan oldin ochilgan" huquq oddiy karta to'loviga aylanadi."""
    conn = await db.connect()
    cursor = await conn.execute(
        "UPDATE report_access SET source = 'card' WHERE payment_id = ? AND source = 'card_optimistic'",
        (payment_id,),
    )
    await conn.commit()
    return cursor.rowcount


async def revoke_optimistic(user_id: int, payment_id: int) -> int:
    """Admin chekni rad etdi: shu chek bilan chekdan oldin ochilgan huquq qaytariladi."""
    conn = await db.connect()
    cursor = await conn.execute(
        "DELETE FROM report_access WHERE user_id = ? AND payment_id = ? AND source = 'card_optimistic'",
        (user_id, payment_id),
    )
    await conn.execute(
        "INSERT OR IGNORE INTO optimistic_blocked (user_id, payment_id, created_at) VALUES (?, ?, ?)",
        (user_id, payment_id, db._now()),
    )
    await conn.commit()
    _drop(user_id)
    return cursor.rowcount


async def can_open_optimistically(user_id: int) -> bool:
    """Bitta tasdiqlanmagan ochilish va rad etilgan chek bo'lmagan bo'lsa."""
    conn = await db.connect()
    cursor = await conn.execute("SELECT 1 FROM optimistic_blocked WHERE user_id = ?", (user_id,))
    if await cursor.fetchone():
        return False
    cursor = await conn.execute(
        "SELECT 1 FROM report_access WHERE user_id = ? AND source = 'card_optimistic' LIMIT 1", (user_id,))
    return await cursor.fetchone() is None


def products_for(product: str) -> list[str]:
    """To'lov mahsuloti → ochiladigan testlar."""
    from config import BUNDLE_KEY
    if product in (BUNDLE_KEY, "all"):
        return list(TESTS)
    return [product] if product in TESTS else []


def is_iq(test_key: str) -> bool:
    return test_key == IQ_KEY
