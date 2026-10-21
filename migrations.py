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


async def m4_reports_and_progress(conn: aiosqlite.Connection) -> None:
    """To'liq tahlilga kirish huquqi va test o'rtasida saqlangan javoblar."""
    await conn.executescript(
        """
        -- Kim qaysi testning TO'LIQ tahlilini ocha oladi. Bir test — bir qator:
        -- ochilish butunlay (keyingi urinishlarga ham).
        --   source: legacy | click | wallet | card | card_optimistic | bundle
        --           | referral | promo | admin
        CREATE TABLE IF NOT EXISTS report_access (
            user_id     INTEGER NOT NULL,
            test_key    TEXT NOT NULL,
            source      TEXT NOT NULL,
            payment_id  INTEGER,
            created_at  TEXT NOT NULL,
            PRIMARY KEY (user_id, test_key)
        );
        CREATE INDEX IF NOT EXISTS idx_report_access_payment ON report_access(payment_id);

        -- Test o'rtasida to'xtatilsa yoki bot qayta ishga tushsa ham javoblar
        -- yo'qolmasin: har bir javobdan keyin yoziladi, test tugagach o'chadi.
        CREATE TABLE IF NOT EXISTS progress (
            user_id     INTEGER NOT NULL,
            test_key    TEXT NOT NULL,
            answers     TEXT NOT NULL,
            age_group   TEXT,
            extra       TEXT,
            updated_at  TEXT NOT NULL,
            PRIMARY KEY (user_id, test_key)
        );

        -- Rad etilgan chekdan keyin bu foydalanuvchiga "chekdan oldin ochish" yo'q.
        CREATE TABLE IF NOT EXISTS optimistic_blocked (
            user_id     INTEGER PRIMARY KEY,
            payment_id  INTEGER,
            created_at  TEXT NOT NULL
        );
        """
    )


#: Pullik test bo'lgan mahsulotlar — migratsiya o'z vaqtidagi ro'yxatni ishlatadi.
_LEGACY_TESTS = ("iq", "bigfive", "future", "career", "child")


async def m5_keep_paid_access(conn: aiosqlite.Connection) -> None:
    """Avval testni sotib olganlar o'sha testning to'liq tahlilini bepul ko'radi.

    Eski model: to'lov = bitta urinish. Yangi model: test bepul, to'lov =
    to'liq tahlil. Kim qachondir to'lagan (Click, balans yoki admin ochgan)
    bo'lsa — o'sha test uchun to'liq tahlil ochiq. "all" paketi — hamma test.
    """
    tests = ",".join(f"'{key}'" for key in _LEGACY_TESTS)
    await conn.execute(
        f"""
        INSERT OR IGNORE INTO report_access (user_id, test_key, source, payment_id, created_at)
        SELECT user_id, product, 'legacy', MIN(id), strftime('%Y-%m-%dT%H:%M:%S+00:00', 'now')
        FROM payments WHERE status = 'paid' AND product IN ({tests})
        GROUP BY user_id, product
        """
    )
    union = " UNION ALL ".join(f"SELECT '{key}' AS key" for key in _LEGACY_TESTS)
    await conn.execute(
        f"""
        INSERT OR IGNORE INTO report_access (user_id, test_key, source, payment_id, created_at)
        SELECT p.user_id, t.key, 'legacy', MIN(p.id), strftime('%Y-%m-%dT%H:%M:%S+00:00', 'now')
        FROM payments p JOIN ({union}) t
        WHERE p.status = 'paid' AND p.product = 'all'
        GROUP BY p.user_id, t.key
        """
    )


async def m6_growth(conn: aiosqlite.Connection) -> None:
    """2-bosqich: do'st mukofoti, promo kodlar, solishtirish, eslatmalar, e'lonlar."""
    await conn.executescript(
        """
        -- Bepul ochish huquqi ("1 ta to'liq tahlil — o'zingiz tanlaysiz").
        -- Ishlatilganda used_test/used_at to'ladi; yozuv o'chirilmaydi.
        --   source: referral | promo | admin
        CREATE TABLE IF NOT EXISTS unlock_credits (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id     INTEGER NOT NULL,
            source      TEXT NOT NULL,
            ref         TEXT NOT NULL,
            created_at  TEXT NOT NULL,
            used_test   TEXT,
            used_at     TEXT,
            UNIQUE (source, ref)
        );
        CREATE INDEX IF NOT EXISTS idx_credits_user ON unlock_credits(user_id, used_at);

        -- Taklif qilingan odam testni tugatdi: mukofot bir marta (referred_id PK).
        --   status: rewarded | capped (oylik chegara to'lgan) | off (o'chirilgan edi)
        CREATE TABLE IF NOT EXISTS referral_rewards (
            referred_id INTEGER PRIMARY KEY,
            referrer_id INTEGER NOT NULL,
            test_key    TEXT NOT NULL,
            month       TEXT NOT NULL,
            status      TEXT NOT NULL,
            created_at  TEXT NOT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_ref_rewards_referrer ON referral_rewards(referrer_id, month, status);

        -- Hamkorlar uchun promo kod. kind: discount (percent %) | free (tests).
        -- max_uses = 0 — cheksiz; expires_at NULL — muddatsiz.
        CREATE TABLE IF NOT EXISTS promo_codes (
            code        TEXT PRIMARY KEY,
            label       TEXT NOT NULL DEFAULT '',
            kind        TEXT NOT NULL,
            percent     INTEGER NOT NULL DEFAULT 0,
            tests       TEXT NOT NULL DEFAULT '',
            max_uses    INTEGER NOT NULL DEFAULT 0,
            uses        INTEGER NOT NULL DEFAULT 0,
            expires_at  TEXT,
            active      INTEGER NOT NULL DEFAULT 1,
            created_by  INTEGER,
            created_at  TEXT NOT NULL
        );

        -- Kim qaysi kodni ishlatdi (bitta odam — bitta kod bir marta).
        -- Chegirma keyingi to'lovda ishlatiladi: payment_id/used_at shunda to'ladi.
        CREATE TABLE IF NOT EXISTS promo_redemptions (
            code        TEXT NOT NULL,
            user_id     INTEGER NOT NULL,
            created_at  TEXT NOT NULL,
            payment_id  INTEGER,
            used_at     TEXT,
            PRIMARY KEY (code, user_id)
        );
        CREATE INDEX IF NOT EXISTS idx_promo_red_user ON promo_redemptions(user_id, used_at);

        -- "Do'stingiz bilan solishtiring" havolasi orqali kelgan odam.
        -- Solishtirish faqat shu odamga (havolani bosganga) ko'rsatiladi.
        CREATE TABLE IF NOT EXISTS compare_invites (
            friend_id   INTEGER NOT NULL,
            test_key    TEXT NOT NULL,
            inviter_id  INTEGER NOT NULL,
            created_at  TEXT NOT NULL,
            shown_at    TEXT,
            PRIMARY KEY (friend_id, test_key)
        );

        -- Avtomatik xabarlar (eslatmalar): 7 kunda 2 tadan oshmasligi shu yerdan sanaladi.
        CREATE TABLE IF NOT EXISTS auto_messages (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id     INTEGER NOT NULL,
            kind        TEXT NOT NULL,
            ref         TEXT NOT NULL,
            sent_at     TEXT NOT NULL,
            ok          INTEGER NOT NULL DEFAULT 1,
            UNIQUE (user_id, kind, ref)
        );
        CREATE INDEX IF NOT EXISTS idx_auto_user_time ON auto_messages(user_id, sent_at);

        -- Admin yuborgan har bir xabar: nechtasi yetdi, nechtasi bloklagan.
        CREATE TABLE IF NOT EXISTS broadcasts (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            kind        TEXT NOT NULL,
            admin_id    INTEGER,
            target      TEXT,
            started_at  TEXT NOT NULL,
            finished_at TEXT,
            total       INTEGER NOT NULL DEFAULT 0,
            sent        INTEGER NOT NULL DEFAULT 0,
            blocked     INTEGER NOT NULL DEFAULT 0,
            failed      INTEGER NOT NULL DEFAULT 0
        );
        """
    )


MIGRATIONS = [
    (1, "events table", m1_events),
    (2, "users: source, source_at, blocked_at", m2_user_source_and_blocks),
    (3, "indexes for /stats", m3_stats_indexes),
    (4, "report_access, progress, optimistic_blocked", m4_reports_and_progress),
    (5, "keep full-report access for everyone who already paid", m5_keep_paid_access),
    (6, "growth: credits, referral rewards, promo codes, compare, reminders, broadcasts", m6_growth),
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
