"""Baza sxemasidagi o'zgarishlar — tartib raqami bilan, faqat QO'SHILADI.

Har bir migratsiya bir marta bajariladi va `schema_migrations` jadvaliga
yoziladi. Qoidalar:

  * hech qachon jadval yoki ustun o'chirilmaydi, mavjud ma'lumot
    o'zgartirilmaydi (faqat yangi ustunni to'ldirish mumkin);
  * har bir qadam qayta ishga tushsa ham xato bermasligi kerak
    (IF NOT EXISTS, ustun bor-yo'qligini tekshirish);
  * yangi o'zgarish — ro'yxat oxiriga yangi raqam bilan.

`database.init()` oxirida chaqiriladi, shuning uchun bot ham, sinov
skriptlari ham doim eng yangi sxema bilan ishlaydi.
"""
from __future__ import annotations

import logging

import aiosqlite

log = logging.getLogger(__name__)


async def _columns(conn: aiosqlite.Connection, table: str) -> set[str]:
    cursor = await conn.execute(f"PRAGMA table_info({table})")
    return {row[1] for row in await cursor.fetchall()}


async def _add_column(conn: aiosqlite.Connection, table: str, column: str, decl: str) -> None:
    if column not in await _columns(conn, table):
        await conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {decl}")


async def m1_events(conn: aiosqlite.Connection) -> None:
    """Analitika: foydalanuvchi qadamlari."""
    await conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS events (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id     INTEGER,
            event       TEXT NOT NULL,
            test_id     TEXT,
            meta        TEXT,
            created_at  TEXT NOT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_events_event_time ON events(event, created_at);
        CREATE INDEX IF NOT EXISTS idx_events_user ON events(user_id, event);
        CREATE INDEX IF NOT EXISTS idx_events_test ON events(test_id, event, created_at);
        """
    )


async def m2_user_source_and_blocks(conn: aiosqlite.Connection) -> None:
    """Foydalanuvchi qayerdan kelgani (birinchi manba) va qachon bloklagani."""
    await _add_column(conn, "users", "source", "TEXT")
    await _add_column(conn, "users", "source_at", "TEXT")
    await _add_column(conn, "users", "blocked_at", "TEXT")
    # Avval bloklaganlar uchun aniq vaqt yo'q — oxirgi faollik vaqti olinadi.
    await conn.execute(
        "UPDATE users SET blocked_at = last_seen WHERE is_blocked = 1 AND blocked_at IS NULL"
    )
    await conn.executescript(
        """
        CREATE INDEX IF NOT EXISTS idx_users_created ON users(created_at);
        CREATE INDEX IF NOT EXISTS idx_users_source ON users(source);
        """
    )


async def m3_stats_indexes(conn: aiosqlite.Connection) -> None:
    """/stats so'rovlari uchun indekslar: to'lov vaqti, mahsulot va holat."""
    await conn.executescript(
        """
        CREATE INDEX IF NOT EXISTS idx_pay_paid_at ON payments(paid_at);
        CREATE INDEX IF NOT EXISTS idx_pay_product_status ON payments(product, status);
        CREATE INDEX IF NOT EXISTS idx_starts_user ON starts(user_id, test_key);
        """
    )


MIGRATIONS = [
    (1, "events table", m1_events),
    (2, "users: source, source_at, blocked_at", m2_user_source_and_blocks),
    (3, "indexes for /stats", m3_stats_indexes),
]


async def run(conn: aiosqlite.Connection | None = None) -> list[int]:
    """Bajarilmagan migratsiyalarni bajaradi. Qaytaradi: hozir bajarilganlar raqami."""
    if conn is None:
        import database as db
        conn = await db.connect()
    await conn.execute(
        """
        CREATE TABLE IF NOT EXISTS schema_migrations (
            version     INTEGER PRIMARY KEY,
            name        TEXT NOT NULL,
            applied_at  TEXT NOT NULL
        )
        """
    )
    cursor = await conn.execute("SELECT version FROM schema_migrations")
    applied = {row[0] for row in await cursor.fetchall()}
    done = []
    for version, name, step in MIGRATIONS:
        if version in applied:
            continue
        await step(conn)
        await conn.execute(
            "INSERT INTO schema_migrations (version, name, applied_at) "
            "VALUES (?, ?, strftime('%Y-%m-%dT%H:%M:%S+00:00', 'now'))",
            (version, name),
        )
        await conn.commit()
        log.info("Migratsiya %s bajarildi: %s", version, name)
        done.append(version)
    await conn.commit()
    return done
