"""CMS migratsiyasi: serverdagi eski bazaga yangi savollar to'g'ri qo'llanadimi.

Serverdagi baza birinchi CMS versiyasi bilan to'ldirilgan: savol matni bor,
javob variantlari yo'q (shuning uchun odamlar "Ha," kabi chala tugmalarni
ko'rardi) va eski matnli IQ savollari ham bazada.

Tekshiriladi:
  * tegilmagan eski baza → yangi savollar, to'liq javoblar, IQ qatorlari o'chdi
  * admin tahrirlagan test → admin matni saqlanadi, lekin tugmalar chala emas
  * yangi baza → darhol yangi versiya, migratsiya takror ishlamaydi
  * migratsiya ikki marta ishga tushsa, savollar ikkilanmaydi

Ishlatish:  ./venv/bin/python contenttest.py
"""
import asyncio
import json
import os
import sqlite3
import sys
import tempfile

DB_FILE = tempfile.mktemp(suffix=".db")
os.environ.update(BOT_TOKEN="0:test", DB_PATH=DB_FILE)

import content_cms as cms
from psytests import REGISTRY

FAILURES: list[str] = []


def check(label: str, ok: bool, detail: str = "") -> None:
    print(("  ✅ " if ok else "  ❌ ") + label + ("" if ok else f"  — {detail}"))
    if not ok:
        FAILURES.append(label)


def old_database(edit_bigfive: bool = False) -> None:
    """Serverdagi holatni qayta yaratadi: v1 seed (javobsiz) + matnli IQ."""
    if os.path.exists(DB_FILE):
        os.remove(DB_FILE)
    seed = json.loads(cms.SEED_V1.read_text(encoding="utf-8"))
    conn = sqlite3.connect(DB_FILE)
    conn.executescript(cms.SCHEMA)
    now = "2026-09-14T00:00:00"
    for key, rows in seed.items():
        for pos, (category, reverse, kind, text_uz, text_ru) in enumerate(rows):
            conn.execute(
                "INSERT INTO cms_questions (test_key,position,category,difficulty,enabled,reverse,kind,"
                "text_uz,text_ru,options_uz,options_ru,correct_index,image_url,created_at,updated_at) "
                "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (key, pos, category, 1, 1, reverse, kind, text_uz, text_ru, None, None, None, None, now, now))
    for pos in range(30):
        conn.execute(
            "INSERT INTO cms_questions (test_key,position,category,difficulty,enabled,reverse,kind,"
            "text_uz,text_ru,options_uz,options_ru,correct_index,image_url,created_at,updated_at) "
            "VALUES ('iq',?,'logic',1,1,0,'iq','Savol','Вопрос','[\"1\",\"2\",\"3\",\"4\",\"5\"]',"
            "'[\"1\",\"2\",\"3\",\"4\",\"5\"]',0,NULL,?,?)", (pos, now, now))
    if edit_bigfive:
        conn.execute("UPDATE cms_questions SET text_uz='Admin yozgan savol?' "
                     "WHERE test_key='bigfive' AND position=0")
    conn.commit()
    conn.close()


def rows(key: str) -> list[sqlite3.Row]:
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    out = conn.execute("SELECT * FROM cms_questions WHERE test_key=? ORDER BY position", (key,)).fetchall()
    conn.close()
    return out


def version() -> str | None:
    conn = sqlite3.connect(DB_FILE)
    row = conn.execute("SELECT value FROM settings WHERE key='content_version'").fetchone()
    conn.close()
    return row[0] if row else None


def broken_buttons(key: str) -> list[str]:
    bad = []
    for item in REGISTRY[key].items:
        for lang in ("uz", "ru"):
            for text in item.answers(lang):
                body = text.split(" ", 1)[1]
                if body.endswith(",") or body in ("Umuman", "Ha, aniq") or "Bilmayman" in body:
                    bad.append(f"{item.text['uz'][:30]}: {body}")
    return bad


async def main() -> int:
    originals = {key: test for key, test in REGISTRY.items()}
    code_texts = {key: [i.text["uz"] for i in test.items] for key, test in REGISTRY.items()}

    print("1. Serverdagi eski baza (tegilmagan)")
    old_database()
    await cms.migrate()
    check("versiya 2 ga ko‘tarildi", version() == "2", str(version()))
    check("eski matnli IQ savollari o‘chirildi", not rows("iq"), str(len(rows("iq"))))
    for key in REGISTRY:
        got = [r["text_uz"] for r in rows(key)]
        check(f"{key}: savollar yangilandi", got == code_texts[key],
              f"{len(got)} ta, birinchisi: {got[:1]}")
        check(f"{key}: javob variantlari yozildi",
              all(r["options_uz"] and r["options_ru"] for r in rows(key)))
    await cms.apply_all()
    for key in REGISTRY:
        check(f"{key}: botdagi tugmalar to‘liq", not broken_buttons(key), str(broken_buttons(key)[:3]))
    sample = [a.split(" ", 1)[1] for a in REGISTRY["bigfive"].items[0].answers("uz")]
    check("fe’l shakli tugmada bor", sample[3] == "Ko‘pincha jonlanadi", str(sample))

    print("2. Takror ishga tushish")
    count_before = len(rows("bigfive"))
    await cms.migrate()
    check("savollar ikkilanmadi", len(rows("bigfive")) == count_before, str(len(rows("bigfive"))))

    print("3. Admin tahrirlagan test")
    REGISTRY.update(originals)
    old_database(edit_bigfive=True)
    await cms.migrate()
    check("tahrirlangan Big Five saqlandi", rows("bigfive")[0]["text_uz"] == "Admin yozgan savol?",
          rows("bigfive")[0]["text_uz"])
    check("boshqa testlar baribir yangilandi",
          [r["text_uz"] for r in rows("future")] == code_texts["future"])
    await cms.apply_all()
    check("tahrirlangan testda ham tugmalar chala emas", not broken_buttons("bigfive"),
          str(broken_buttons("bigfive")[:3]))

    print("4. Yangi (bo‘sh) baza")
    REGISTRY.update(originals)
    os.remove(DB_FILE)
    cms._initialized = False
    await cms.init()
    check("darhol yangi versiya", version() == "2", str(version()))
    check("yangi savollar yozildi", [r["text_uz"] for r in rows("child")] == code_texts["child"])
    check("IQ bazaga yozilmadi", not rows("iq"))
    snapshot = json.loads(cms.snapshot_path(cms.CONTENT_VERSION).read_text(encoding="utf-8"))
    stale = [key for key in REGISTRY
             if not cms._untouched(key, [dict(r) for r in rows(key)], snapshot)]
    check(f"cms_seed_v{cms.CONTENT_VERSION}.json kod bilan mos (keyingi migratsiya uchun)",
          not stale, f"{stale} — `python content_cms.py snapshot` ni ishga tushiring")

    print()
    if FAILURES:
        print(f"❌ {len(FAILURES)} ta muammo: {FAILURES}")
        return 1
    print("✅ Savollar bazaga to‘g‘ri ko‘chadi.")
    return 0


sys.exit(asyncio.run(main()))
