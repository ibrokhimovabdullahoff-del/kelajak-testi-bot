"""SQLite qatlami.

DB_PATH muhit o'zgaruvchisi orqali beriladi, shuning uchun serverda doimiy
diskka yo'naltirish yetarli — kodni o'zgartirish shart emas.
"""
from __future__ import annotations

import asyncio
import json
from datetime import datetime, timedelta, timezone

import aiosqlite

from config import DB_PATH

#: Bitta umumiy ulanish. Avval har bir so'rov uchun yangi ulanish ochilardi —
#: bu sekin edi va yuk ko'tarilganda "database is locked" xatosini berardi.
_conn: aiosqlite.Connection | None = None
_lock = asyncio.Lock()

#: Foydalanuvchi qachon oxirgi marta bazaga yozilgani. Har bir tugma bosishda
#: yozish shart emas — soatiga bir marta yetadi.
_seen: dict[int, datetime] = {}
_SEEN_TTL = timedelta(hours=1)

#: Tanlangan til xotirada saqlanadi — har bosishda bazadan o'qish shart emas.
#: Til faqat foydalanuvchining o'zi o'zgartirganda yangilanadi.
_lang_cache: dict[int, str] = {}


async def connect() -> aiosqlite.Connection:
    """Umumiy ulanishni qaytaradi, kerak bo'lsa ochadi."""
    global _conn
    if _conn is None:
        async with _lock:
            if _conn is None:
                conn = await aiosqlite.connect(DB_PATH)
                # WAL: o'qish va yozish bir-birini bloklamaydi. Busy timeout:
                # baza band bo'lsa darrov xato bermay, kutib turadi.
                await conn.execute("PRAGMA journal_mode=WAL")
                await conn.execute("PRAGMA synchronous=NORMAL")
                await conn.execute("PRAGMA busy_timeout=5000")
                await conn.commit()
                _conn = conn
    return _conn


async def close() -> None:
    global _conn
    if _conn is not None:
        await _conn.close()
        _conn = None

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

CREATE TABLE IF NOT EXISTS settings (
    key         TEXT PRIMARY KEY,
    value       TEXT NOT NULL
);

-- Test BOSHLANGANI yoziladi. Natijalar jadvali faqat TUGATGANLARNI biladi;
-- ikkalasini solishtirib, qanchasi yarim yo'lda tashlab ketganini ko'ramiz.
CREATE TABLE IF NOT EXISTS starts (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id     INTEGER NOT NULL,
    test_key    TEXT NOT NULL,
    created_at  TEXT NOT NULL
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

-- To'lovlar. Har bir yozuv — bitta urinish; huquq faqat status='paid'
-- bo'lgan yozuvdan kelib chiqadi.
CREATE TABLE IF NOT EXISTS payments (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id       INTEGER NOT NULL,
    -- Nimaga to'landi: test kaliti ("bigfive") yoki "all" — barcha testlar.
    product       TEXT NOT NULL,
    amount        INTEGER NOT NULL,
    -- "click" | "manual" (admin qo'lda ochgan)
    method        TEXT NOT NULL,
    -- "pending" (havola berildi) | "prepared" (Click tasdiqlashni boshladi)
    -- | "paid" | "cancelled" | "revoked"
    status        TEXT NOT NULL,
    click_trans_id   TEXT,
    click_prepare_id INTEGER,
    click_confirm_id TEXT,
    note          TEXT,
    reviewed_by   INTEGER,
    created_at    TEXT NOT NULL,
    paid_at       TEXT
);
"""

# Indekslar jadval ustunlari ko'chirilgandan KEYIN yaratiladi — eski bazada
# test_key ustuni hali bo'lmasligi mumkin.
_INDEXES = """
CREATE INDEX IF NOT EXISTS idx_pay_user ON payments(user_id);
CREATE INDEX IF NOT EXISTS idx_pay_status ON payments(status);
-- Bitta Click tranzaksiyasi ikki marta yozilmasin: Click Complete so'rovini
-- takror yuborishi mumkin va u holda odamdan ikki marta pul yechilgandek
-- ko'rinib qolardi.
CREATE UNIQUE INDEX IF NOT EXISTS idx_pay_click
    ON payments(click_trans_id) WHERE click_trans_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_results_user ON results(user_id);
CREATE INDEX IF NOT EXISTS idx_results_created ON results(created_at);
CREATE INDEX IF NOT EXISTS idx_results_test ON results(test_key);
CREATE INDEX IF NOT EXISTS idx_starts_created ON starts(created_at);
CREATE INDEX IF NOT EXISTS idx_starts_test ON starts(test_key);
"""

#: Eski sxemadan yangisiga ko'chirish uchun ustun nomlari.
_LEGACY_MODE_MAP = {"adult": "future", "kid": "child"}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


async def _dicts(cursor) -> list[dict]:
    """Natijani lug'atlar ro'yxatiga aylantiradi.

    `connection.row_factory` ni o'zgartirmaymiz: ulanish umumiy, sozlama
    global qolib ketardi va boshqa so'rovlarga ta'sir qilardi.
    """
    columns = [c[0] for c in cursor.description]
    return [dict(zip(columns, row)) for row in await cursor.fetchall()]


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
    db = await connect()
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


async def upsert_user(
    user_id: int, username: str | None, full_name: str, force: bool = False
) -> None:
    """Foydalanuvchini saqlaydi.

    Har bir tugma bosishda yozish shart emas: agar shu foydalanuvchi oxirgi
    soat ichida yozilgan bo'lsa, yozuv o'tkazib yuboriladi. Bu tugma
    bosishdagi bazaga murojaatni deyarli nolga tushiradi.
    """
    stamp = datetime.now(timezone.utc)
    if not force:
        last = _seen.get(user_id)
        if last is not None and stamp - last < _SEEN_TTL:
            return
    _seen[user_id] = stamp

    now = _now()
    db = await connect()
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
    """Tanlangan til. Kesh tufayli odatda bazaga umuman borilmaydi."""
    if user_id in _lang_cache:
        return _lang_cache[user_id]
    db = await connect()
    cursor = await db.execute("SELECT lang FROM users WHERE user_id = ?", (user_id,))
    row = await cursor.fetchone()
    lang = row[0] if row and row[0] else None
    if lang:
        _lang_cache[user_id] = lang
    return lang


async def set_lang(user_id: int, lang: str) -> None:
    _lang_cache[user_id] = lang
    db = await connect()
    await db.execute(
        "UPDATE users SET lang = ? WHERE user_id = ?", (lang, user_id)
    )
    await db.commit()


async def mark_blocked(user_id: int) -> None:
    db = await connect()
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
    db = await connect()
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
    db = await connect()
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
    db = await connect()
    cursor = await db.execute(
        """
        SELECT test_key, age_group, total, created_at
        FROM results WHERE user_id = ?
        ORDER BY id DESC LIMIT ?
        """,
        (user_id, limit),
    )
    return await _dicts(cursor)


# --- Statistika -------------------------------------------------------------


async def stats() -> dict:
    today = datetime.now(timezone.utc).date().isoformat()
    db = await connect()
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


# --- Sozlamalar (admin boshqaruvi) ------------------------------------------


async def get_setting(key: str, default: str | None = None) -> str | None:
    db = await connect()
    cursor = await db.execute("SELECT value FROM settings WHERE key = ?", (key,))
    row = await cursor.fetchone()
    return row[0] if row else default


async def set_setting(key: str, value: str) -> None:
    db = await connect()
    await db.execute(
        "INSERT INTO settings (key, value) VALUES (?, ?) "
        "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
        (key, value),
    )
    await db.commit()


async def disabled_tests() -> set[str]:
    """Admin o'chirib qo'ygan testlar."""
    raw = await get_setting("disabled_tests", "")
    return {x for x in (raw or "").split(",") if x}


async def toggle_test(test_key: str) -> bool:
    """Testni yoqadi/o'chiradi. Qaytaradi: endi yoqiqmi."""
    off = await disabled_tests()
    if test_key in off:
        off.discard(test_key)
        enabled = True
    else:
        off.add(test_key)
        enabled = False
    await set_setting("disabled_tests", ",".join(sorted(off)))
    return enabled


# --- Test boshlanishi va tugallanish voronkasi ------------------------------


async def log_start(user_id: int, test_key: str) -> None:
    db = await connect()
    await db.execute(
        "INSERT INTO starts (user_id, test_key, created_at) VALUES (?, ?, ?)",
        (user_id, test_key, _now()),
    )
    await db.commit()


async def funnel() -> list[dict]:
    """Har bir test bo'yicha: boshlagan, tugatgan, tugatish foizi."""
    db = await connect()
    cursor = await db.execute("SELECT test_key, COUNT(*) FROM starts GROUP BY test_key")
    starts = dict(await cursor.fetchall())
    cursor = await db.execute(
        "SELECT test_key, COUNT(*), AVG(total) FROM results GROUP BY test_key"
    )
    rows = await cursor.fetchall()
    done = {r[0]: (r[1], r[2]) for r in rows}

    out = []
    for key in set(starts) | set(done):
        began = starts.get(key, 0)
        finished, avg = done.get(key, (0, None))
        out.append({
            "key": key,
            "starts": began,
            "done": finished,
            "avg": avg,
            "rate": (finished / began * 100) if began else None,
        })
    return sorted(out, key=lambda r: r["done"], reverse=True)


async def active_now(minutes: int = 20) -> int:
    """Oxirgi daqiqalarda testni boshlagan, lekin hali tugatmaganlar soni."""
    since = (datetime.now(timezone.utc) - timedelta(minutes=minutes)).isoformat(
        timespec="seconds")
    db = await connect()
    cursor = await db.execute(
        """
        SELECT COUNT(*) FROM starts s
        WHERE s.created_at >= ?
          AND NOT EXISTS (
              SELECT 1 FROM results r
              WHERE r.user_id = s.user_id AND r.test_key = s.test_key
                AND r.created_at >= s.created_at
          )
        """,
        (since,),
    )
    row = await cursor.fetchone()
    return row[0] if row else 0


async def recent_users(limit: int = 15) -> list[dict]:
    db = await connect()
    cursor = await db.execute(
        """
        SELECT u.user_id, u.username, u.full_name, u.lang, u.created_at,
               (SELECT COUNT(*) FROM results r WHERE r.user_id = u.user_id) AS tests
        FROM users u ORDER BY u.created_at DESC LIMIT ?
        """,
        (limit,),
    )
    return await _dicts(cursor)


async def daily(days: int = 7) -> list[tuple[str, int, int]]:
    """Kunlik: sana, yangi foydalanuvchi, tugatilgan test."""
    db = await connect()
    cursor = await db.execute(
        """
        SELECT d, SUM(u), SUM(r) FROM (
            SELECT substr(created_at,1,10) d, 1 u, 0 r FROM users
            UNION ALL
            SELECT substr(created_at,1,10) d, 0 u, 1 r FROM results
        ) GROUP BY d ORDER BY d DESC LIMIT ?
        """,
        (days,),
    )
    return list(await cursor.fetchall())


async def export_results() -> list[tuple]:
    """Barcha natijalar — CSV uchun."""
    db = await connect()
    cursor = await db.execute(
        """
        SELECT r.created_at, r.user_id, u.username, r.lang, r.test_key,
               r.age_group, r.total, r.scales
        FROM results r LEFT JOIN users u ON u.user_id = r.user_id
        ORDER BY r.id DESC
        """
    )
    return list(await cursor.fetchall())


# --- To'lovlar --------------------------------------------------------------

#: "Barcha testlar" paketi. Test kalitlari bilan bir xil maydonda yashaydi,
#: shuning uchun hech qaysi test shu nom bilan atalmasligi kerak.
ALL_PRODUCTS = "all"

#: Kim nimaga huquq olgani. Huquq faqat to'lov tasdiqlanganda o'zgaradi,
#: shuning uchun keshni har safar tekshirib o'tirish shart emas — testni
#: boshlashdagi bazaga murojaat butunlay yo'qoladi.
_access_cache: dict[int, set[str]] = {}


def _drop_access_cache(user_id: int) -> None:
    _access_cache.pop(user_id, None)


async def paid_products(user_id: int) -> set[str]:
    """Foydalanuvchi sotib olgan mahsulotlar to'plami."""
    cached = _access_cache.get(user_id)
    if cached is not None:
        return cached
    db = await connect()
    cursor = await db.execute(
        "SELECT DISTINCT product FROM payments WHERE user_id = ? AND status = 'paid'",
        (user_id,),
    )
    products = {row[0] for row in await cursor.fetchall()}
    _access_cache[user_id] = products
    return products


async def has_access(user_id: int, test_key: str) -> bool:
    """Shu testni ochish huquqi bormi.

    Bepul qilib qo'yilgan testda bu funksiya chaqirilmaydi — tekshiruv
    handlerda `free_tests()` bilan boshlanadi.
    """
    products = await paid_products(user_id)
    return ALL_PRODUCTS in products or test_key in products


async def create_payment(
    user_id: int, product: str, amount: int, method: str
) -> int:
    """Yangi to'lov urinishini ochadi va uning raqamini qaytaradi.

    Shu raqam Click uchun `merchant_trans_id` bo'lib xizmat qiladi.
    """
    db = await connect()
    cursor = await db.execute(
        """
        INSERT INTO payments (user_id, product, amount, method, status, created_at)
        VALUES (?, ?, ?, ?, 'pending', ?)
        """,
        (user_id, product, amount, method, _now()),
    )
    await db.commit()
    return cursor.lastrowid


async def open_payment(user_id: int, product: str, amount: int) -> dict | None:
    """Shu mahsulot uchun hali boshlanmagan to'lov bor-yo'qligini qaraydi.

    Odam "To'lash" tugmasini bir necha marta bosishi mumkin. Har safar yangi
    buyurtma ochsak, bazada axlat yig'iladi va Click kabinetida qaysi raqam
    haqiqiy ekani chalkashadi. Shuning uchun tegilmagan buyurtmani qayta
    ishlatamiz — Click tasdiqlashni boshlagani ("prepared") esa qayta
    ishlatilmaydi.
    """
    db = await connect()
    cursor = await db.execute(
        """
        SELECT * FROM payments
        WHERE user_id = ? AND product = ? AND amount = ? AND status = 'pending'
        ORDER BY id DESC LIMIT 1
        """,
        (user_id, product, amount),
    )
    rows = await _dicts(cursor)
    return rows[0] if rows else None


async def get_payment(payment_id: int) -> dict | None:
    db = await connect()
    cursor = await db.execute("SELECT * FROM payments WHERE id = ?", (payment_id,))
    rows = await _dicts(cursor)
    return rows[0] if rows else None


async def mark_paid(
    payment_id: int,
    click_confirm_id: str | None = None,
    reviewed_by: int | None = None,
) -> bool:
    """To'lovni "to'langan" deb belgilaydi.

    Qaytaradi: shu chaqiruv haqiqatan holatni o'zgartirdimi. False bo'lsa —
    to'lov allaqachon to'langan. Click Complete so'rovini takror yuborishi
    mumkin; u holda foydalanuvchiga ikkinchi marta "to'lov qabul qilindi"
    xabari ketmasligi kerak.
    """
    db = await connect()
    cursor = await db.execute(
        """
        UPDATE payments
        SET status = 'paid', paid_at = ?, click_confirm_id = ?, reviewed_by = ?
        WHERE id = ? AND status != 'paid'
        """,
        (_now(), click_confirm_id, reviewed_by, payment_id),
    )
    await db.commit()
    if cursor.rowcount:
        row = await get_payment(payment_id)
        if row:
            _drop_access_cache(row["user_id"])
        return True
    return False


async def set_status(payment_id: int, status: str, reviewed_by: int | None = None) -> None:
    db = await connect()
    await db.execute(
        "UPDATE payments SET status = ?, reviewed_by = ? WHERE id = ?",
        (status, reviewed_by, payment_id),
    )
    await db.commit()


async def set_click_prepare(payment_id: int, click_trans_id: str) -> None:
    """Click Prepare bosqichida tranzaksiya raqamini bog'laydi."""
    db = await connect()
    await db.execute(
        """
        UPDATE payments
        SET click_trans_id = ?, click_prepare_id = ?, status = 'prepared'
        WHERE id = ?
        """,
        (click_trans_id, payment_id, payment_id),
    )
    await db.commit()


async def grant_access(user_id: int, product: str, admin_id: int) -> None:
    """Admin qo'lda huquq beradi — pul boshqa yo'l bilan kelgan holatlar uchun."""
    db = await connect()
    await db.execute(
        """
        INSERT INTO payments
            (user_id, product, amount, method, status, reviewed_by, created_at, paid_at)
        VALUES (?, ?, 0, 'manual', 'paid', ?, ?, ?)
        """,
        (user_id, product, admin_id, _now(), _now()),
    )
    await db.commit()
    _drop_access_cache(user_id)


async def revoke_access(user_id: int, product: str) -> int:
    """Huquqni bekor qiladi. Qaytaradi: nechta yozuv o'zgardi."""
    db = await connect()
    cursor = await db.execute(
        """
        UPDATE payments SET status = 'revoked'
        WHERE user_id = ? AND product = ? AND status = 'paid'
        """,
        (user_id, product),
    )
    await db.commit()
    _drop_access_cache(user_id)
    return cursor.rowcount


async def payment_stats() -> dict:
    today = datetime.now(timezone.utc).date().isoformat()
    db = await connect()

    async def one(query: str, args: tuple = ()) -> float:
        cursor = await db.execute(query, args)
        row = await cursor.fetchone()
        return row[0] if row and row[0] is not None else 0

    paid = "status = 'paid' AND method != 'manual'"
    return {
        "count": await one(f"SELECT COUNT(*) FROM payments WHERE {paid}"),
        "sum": await one(f"SELECT SUM(amount) FROM payments WHERE {paid}"),
        "today": await one(
            f"SELECT COUNT(*) FROM payments WHERE {paid} "
            "AND substr(paid_at, 1, 10) = ?", (today,),
        ),
        "today_sum": await one(
            f"SELECT SUM(amount) FROM payments WHERE {paid} "
            "AND substr(paid_at, 1, 10) = ?", (today,),
        ),
        "started": await one("SELECT COUNT(*) FROM payments WHERE method = 'click'"),
        "manual": await one("SELECT COUNT(*) FROM payments WHERE method = 'manual'"),
    }


async def recent_payments(limit: int = 15) -> list[dict]:
    db = await connect()
    cursor = await db.execute(
        """
        SELECT p.*, u.username, u.full_name
        FROM payments p LEFT JOIN users u ON u.user_id = p.user_id
        ORDER BY p.id DESC LIMIT ?
        """,
        (limit,),
    )
    return await _dicts(cursor)


# --- Pullik testlar va narxlar (admin boshqaruvi) ---------------------------


async def free_tests() -> set[str]:
    """Pul so'ralmaydigan testlar.

    Sukut bo'yicha ro'yxat BO'SH — ya'ni hamma test pullik. Admin ayrim
    testni ochiq qilib qo'ymoqchi bo'lsa (masalan reklama uchun), uni shu
    ro'yxatga qo'shadi.
    """
    raw = await get_setting("free_tests", "")
    return {x for x in (raw or "").split(",") if x}


async def toggle_free_test(test_key: str) -> bool:
    """Testni bepul/pullik qiladi. Qaytaradi: endi bepulmi."""
    free = await free_tests()
    if test_key in free:
        free.discard(test_key)
        now_free = False
    else:
        free.add(test_key)
        now_free = True
    await set_setting("free_tests", ",".join(sorted(free)))
    return now_free


async def price_of(product: str, default: int) -> int:
    """Mahsulot narxi. Admin o'zgartirmagan bo'lsa .env dagi qiymat."""
    raw = await get_setting(f"price:{product}")
    if raw and raw.isdigit():
        return int(raw)
    return default


async def set_price(product: str, amount: int) -> None:
    await set_setting(f"price:{product}", str(amount))
