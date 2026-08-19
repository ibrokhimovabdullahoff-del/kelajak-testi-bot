"""Eski bazadan ko'chishni sinaydi.

Bu alohida skript, chunki selftest va flowtest har doim TOZA bazadan
boshlaydi — ular eski sxemadagi muammoni ko'rmaydi. Aynan shu bo'shliq
tufayli `results.mode NOT NULL` xatosi ishlab turgan botga chiqib ketgan
edi: migratsiya ustun qo'shgan, lekin eski NOT NULL ustunlarni olib
tashlamagan va yangi natija umuman saqlanmagan.

Ishlatish:  ./venv/bin/python migrationtest.py
"""
import asyncio
import json
import os
import sqlite3
import sys
import tempfile

os.environ["BOT_TOKEN"] = "0:test"

#: Sinov uchun soxta foydalanuvchi — haqiqiy Telegram ID emas.
TEST_USER = 1000001
DB = tempfile.mktemp(suffix=".db")
os.environ["DB_PATH"] = DB

import database as db  # noqa: E402  (DB_PATH dan keyin import qilinishi shart)

FAILURES: list[str] = []

# Botning eng eski ishlagan sxemasi.
# DIQQAT: bu f-string EMAS — ichida JSON qavslari bor, f-string ularni format
# ko'rsatmasi deb o'qib matnni buzadi. ID oddiy almashtirish bilan qo'yiladi.
OLD_SCHEMA = """
CREATE TABLE users (
    user_id INTEGER PRIMARY KEY, username TEXT, full_name TEXT,
    created_at TEXT NOT NULL, last_seen TEXT NOT NULL,
    is_blocked INTEGER NOT NULL DEFAULT 0
);
CREATE TABLE results (
    id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL,
    mode TEXT NOT NULL, age_group TEXT, total REAL NOT NULL,
    dims TEXT NOT NULL, created_at TEXT NOT NULL
);
INSERT INTO users VALUES
    (:uid,'testuser','Test User','2026-08-14T10:00:00','2026-08-14T10:00:00',0);
INSERT INTO results (user_id,mode,age_group,total,dims,created_at) VALUES
    (:uid,'adult','a_14_18',58.9,'{"maqsad":50}','2026-08-14T16:40:00'),
    (:uid,'kid','k_7_10',71.0,'{"oila":80}','2026-08-14T16:45:00');
""".replace(":uid", str(TEST_USER))


def check(label: str, ok: bool, detail: str = "") -> None:
    print(("  ✅ " if ok else "  ❌ ") + label + ("" if ok else f"  — {detail}"))
    if not ok:
        FAILURES.append(label)


async def main() -> int:
    con = sqlite3.connect(DB)
    con.executescript(OLD_SCHEMA)
    con.commit()
    con.close()

    print("1. Ko‘chirish")
    await db.init()
    await db.init()  # ikkinchi marta ham xatosiz o‘tishi kerak
    check("init ikki marta ishladi", True)

    rows = await db.user_history(TEST_USER)
    keys = {r["test_key"] for r in rows}
    check("eski natijalar saqlandi", len(rows) == 2, str(len(rows)))
    check("mode -> test_key ko‘chdi", keys == {"future", "child"}, str(keys))
    check("ballar joyida", {r["total"] for r in rows} == {58.9, 71.0},
          str({r["total"] for r in rows}))
    check("yosh guruhi joyida",
          {r["age_group"] for r in rows} == {"a_14_18", "k_7_10"})
    check("tildan bir marta so‘raladi", await db.get_lang(TEST_USER) is None)

    # dims -> scales ko'chganda JSON buzilmasligi kerak
    con = sqlite3.connect(DB)
    saved = [r[0] for r in con.execute("SELECT scales FROM results")]
    con.close()
    try:
        parsed = [json.loads(v) for v in saved]
        ok = {"maqsad": 50} in parsed and {"oila": 80} in parsed
    except (TypeError, ValueError) as exc:
        parsed, ok = exc, False
    check("shkala qiymatlari JSON holida ko‘chdi", ok, str(saved))

    print("2. Eski NOT NULL ustunlar olib tashlandi")
    con = sqlite3.connect(DB)
    cols = {r[1] for r in con.execute("PRAGMA table_info(results)")}
    not_null = {r[1] for r in con.execute("PRAGMA table_info(results)") if r[3]}
    con.close()
    check("`mode` ustuni yo‘q", "mode" not in cols, str(sorted(cols)))
    check("`dims` ustuni yo‘q", "dims" not in cols, str(sorted(cols)))
    check("`total` endi NOT NULL emas", "total" not in not_null, str(sorted(not_null)))

    print("3. Ko‘chgan bazaga yangi natija yoziladi")
    # Indeksli test — umumiy ball bor
    await db.save_result(TEST_USER, "future", "uz", "a_19_25", 62.5, {"maqsad": 70})
    # Big Five — umumiy ball YO‘Q (aynan shu holat ishlab turgan botni buzgan)
    await db.save_result(TEST_USER, "bigfive", "ru", None, None, {"E": 55.0})
    await db.save_result(TEST_USER, "career", "uz", None, None, {"S": 80.0})

    rows = await db.user_history(TEST_USER)
    check("yangi yozuvlar qo‘shildi", len(rows) == 5, str(len(rows)))
    # rows yangidan eskiga qarab keladi — birinchi uchragani eng yangisi.
    latest: dict[str, dict] = {}
    for row in rows:
        latest.setdefault(row["test_key"], row)
    check("Big Five ballsiz saqlandi",
          "bigfive" in latest and latest["bigfive"]["total"] is None)
    check("indeksli test bali saqlandi",
          latest.get("future", {}).get("total") == 62.5)

    print("4. Statistika ishlaydi")
    stats = await db.stats()
    check("jami testlar 5 ta", int(stats["tests"]) == 5, str(stats["tests"]))
    per = {r["key"]: r["count"] for r in stats["per_test"]}
    check("test bo‘yicha bo‘lindi", per.get("future") == 2 and per.get("bigfive") == 1,
          str(per))
    check("ommaviy xabar ro‘yxati ishlaydi",
          await db.all_user_ids() == [TEST_USER])

    await db.close()

    print()
    if FAILURES:
        print(f"❌ {len(FAILURES)} ta muammo: {FAILURES}")
        return 1
    print("✅ Ko‘chirish muammosiz.")
    return 0


sys.exit(asyncio.run(main()))
