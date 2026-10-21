"""Yangi modullar tekshiruvi: sertifikat rasmi, do'st taklifi, foiz, IQ hisoboti.

Telegram'siz ishlaydi, vaqtinchalik bazaga yozadi.

Ishlatish:  ./venv/bin/python growthtest.py
"""
import asyncio
import io
import json
import os
import re
import sqlite3
import sys
import tempfile
from datetime import date

DB_FILE = tempfile.mktemp(suffix=".db")
os.environ.update(BOT_TOKEN="0:test", ADMIN_ID="999", DB_PATH=DB_FILE)

from PIL import Image

import database as db
import peers
import referrals
import report
import result_image as ri
from locales import tr as tr_
from psytests import ORDER, REGISTRY
from psytests import iq as iqdata

FAILURES: list[str] = []


def check(label: str, ok: bool, detail: str = "") -> None:
    print(("  ✅ " if ok else "  ❌ ") + label + ("" if ok else f"  — {detail}"))
    if not ok:
        FAILURES.append(label)


def schema(conn: sqlite3.Connection) -> dict[str, str]:
    return dict(conn.execute("SELECT name, sql FROM sqlite_master WHERE type='table'").fetchall())


async def migration() -> None:
    print("1. Migratsiya")
    await db.init()
    before = schema(sqlite3.connect(DB_FILE))
    await referrals.init()
    await referrals.init()  # ikkinchi marta ham xatosiz
    after = schema(sqlite3.connect(DB_FILE))
    check("yangi jadvallar yaratildi", {"referrals", "review_unlocks"} <= set(after), str(set(after)))
    check("eski jadvallarning birortasi o‘zgarmadi",
          all(after.get(name) == sql for name, sql in before.items()))


async def referral_rules() -> None:
    print("2. Do‘st taklifi")
    for uid in (1, 2, 3, 4, 5):
        await db.upsert_user(uid, None, f"U{uid}", force=True)
    check("havola formati", referrals.link("@kelajak_testi_bot", 42) == "https://t.me/kelajak_testi_bot?start=ref_42")
    check("payload o‘qiladi", referrals.parse("ref_42") == 42 and referrals.parse(" ref_7 ") == 7)
    check("begona payload rad etiladi",
          all(referrals.parse(x) is None for x in (None, "", "ref_", "ref_abc", "x_ref_1", "ref_1; DROP")))

    check("o‘zini taklif qilib bo‘lmaydi", await referrals.record(1, 1, True) == referrals.SELF)
    check("eski foydalanuvchi hisoblanmaydi", await referrals.record(1, 2, False) == referrals.NOT_NEW)
    check("botda yo‘q taklif qiluvchi rad etiladi", await referrals.record(777, 10, True) == referrals.UNKNOWN)
    check("birinchi do‘st hisoblandi", await referrals.record(1, 11, True) == referrals.COUNTED)
    check("ikkinchi do‘st ham hisoblandi", await referrals.record(1, 12, True) == referrals.COUNTED)
    check("bitta yangi odam ikki marta hisoblanmaydi (boshqa havola)",
          await referrals.record(2, 11, True) == referrals.DUPLICATE)
    check("taklif qilganlar soni 2", await referrals.invited_count(1) == 2)
    check("do‘sti yo‘q odamda 0", await referrals.invited_count(2) == 0)
    conn = sqlite3.connect(DB_FILE)
    try:
        conn.execute("INSERT INTO referrals (referrer_id, referred_id, created_at) VALUES (5, 5, 'x')")
        self_ok = False
    except sqlite3.IntegrityError:
        self_ok = True
    conn.rollback()  # aks holda ochiq tranzaksiya bazani qulflab qo'yadi
    check("baza darajasida ham o‘zini taklif qilish taqiqlangan", self_ok)
    rows = conn.execute("SELECT COUNT(*) FROM review_unlocks").fetchone()[0]
    conn.close()
    check("xatolar tahlili endi ochilmaydi (review_unlocks ga yozilmaydi)", rows == 0, str(rows))


async def percentile_rules() -> None:
    print("3. Boshqalar bilan solishtirish")
    conn = await db.connect()
    for uid in range(100, 100 + peers.MIN_SAMPLE):
        await conn.execute("INSERT INTO results (user_id, test_key, lang, total, scales, created_at) "
                           "VALUES (?, 'future', 'uz', ?, '{}', 'x')", (uid, float(uid - 100)))
        # Qayta topshirish (yuqori ball) — hisoblanmasligi kerak.
        await conn.execute("INSERT INTO results (user_id, test_key, lang, total, scales, created_at) "
                           "VALUES (?, 'future', 'uz', 99, '{}', 'y')", (uid,))
    await conn.execute("INSERT INTO results (user_id, test_key, lang, total, scales, created_at) "
                       "VALUES (999, 'future', 'uz', 0, '{}', 'x')")  # admin
    await conn.commit()
    others = await peers.others("future", user_id=5000)
    check("har odamdan faqat birinchi urinish", sorted(others) == [float(i) for i in range(peers.MIN_SAMPLE)],
          str(sorted(others)))
    check("admin hisoblanmaydi", len(others) == peers.MIN_SAMPLE)
    check("o‘zi hisoblanmaydi", len(await peers.others("future", user_id=100)) == peers.MIN_SAMPLE - 1)
    top = await peers.compare("future", 5000, 50)
    check("hammadan yaxshi → 100%", top == {"percent": 100, "n": peers.MIN_SAMPLE, "low": False}, str(top))
    mid = await peers.compare("future", 5000, 10)
    check("qat’iy «yaxshiroq» hisoblanadi (tenglar emas)", mid["percent"] == 50, str(mid))
    check("past foiz — yumshoq jumla", (await peers.compare("future", 5000, 0))["low"])
    check("odam kam bo‘lsa — ko‘rsatilmaydi", await peers.compare("child", 5000, 50) is None)
    check("Big Five solishtirilmaydi", await peers.compare("bigfive", 5000, 50) is None)
    await conn.execute("INSERT INTO results (user_id, test_key, lang, total, scales, created_at) "
                       "VALUES (300, 'iq', 'uz', 101, '{\"iq_score\": 101}', 'x')")  # eski matnli IQ
    await conn.commit()
    check("eski matnli IQ natijalari aralashmaydi", await peers.others("iq", 5000) == [])


def card_rules() -> None:
    print("4. Sertifikat mazmuni")
    kinds = {"change": [3, 4], "combine": [1, 4], "spatial": [2, 6], "rows": [0, 6]}
    low = ri.build_card("iq", 9, {"iq": 92, "kinds": kinds}, "uz", full=True)
    check("IQ < 100 — raqam yozilmaydi", not low.number and not re.search(r"\d", low.headline + (low.pill or "")),
          str(low))
    high = ri.build_card("iq", 17, {"iq": 124, "correct": 17, "total": 20, "kinds": kinds}, "ru", full=True)
    check("to‘liq tahlil ochiq, IQ ≥ 100 — raqam va daraja", high.number and high.headline == "124" and high.pill,
          str(high))
    free = ri.build_card("iq", 17, {"iq": 124, "correct": 17, "total": 20, "kinds": kinds}, "ru")
    check("bepul sertifikatda taxminiy IQ yo‘q (u — to‘liq tahlilda)", not free.number and "124" not in str(free),
          str(free))
    check("to‘g‘ri javoblar alohida ko‘rsatkich sifatida",
          ri.build_card("iq", 17, {"iq": 124, "correct": 17, "total": 20, "kinds": kinds}, "uz").stat
          == ("To‘g‘ri javoblar", "17 / 20"))
    hidden = ri.build_card("iq", 17, {"iq": 124, "correct": 17, "total": 20, "kinds": kinds}, "uz",
                           full=True, show_score=False)
    check("«Ballni yashirish»: hech qanday raqam yo‘q", not hidden.number and hidden.stat is None
          and not re.search(r"\d", hidden.headline + " ".join(hidden.lines)), str(hidden))
    low_scored = ri.build_card("iq", 9, {"iq": 92, "correct": 9, "total": 20, "kinds": kinds}, "uz")
    check("yarmidan kam — ball katta raqam emas, oddiy qator",
          low_scored.stat is None and any("9\u00a0tasini" in line for line in low_scored.lines), str(low_scored))
    parent = ri.build_card("child", 80, {k: 90 for k in REGISTRY["child"].scales}, "uz")
    check("farzand testi: sertifikatda bolaning natijasi yo‘q", not re.search(r"\d", str(parent))
          and not any(tr_(sc.name, "uz") in str(parent) for sc in REGISTRY["child"].scales.values()), str(parent))

    # Joylashuv: katta raqam, daraja va to'g'ri javoblar bir-birini bosmasin.
    # (Xato bo'lgan: chizuvchi lambda keyinroq o'zgargan o'zgaruvchini o'qirdi.)
    class Recorder:
        def __init__(self):
            self.ops = []
        def text(self, y, line, font, fill, tracking=0, glow=False):
            box = font.getbbox(line, anchor="ma")
            self.ops.append(("text", line, y + box[1], y + box[3]))
        def pill(self, y, line, font):
            self.ops.append(("pill", line, y, y + 60))
        def divider(self, y, half=130):
            pass
    for iq_value in (100, 124, 138, 145):
        numbered = ri.build_card("iq", 17, {"iq": iq_value, "correct": 17, "total": 20, "kinds": kinds}, "uz")
        _, parts = ri._middle(numbered, "Siz bundan ham yaxshiroq qila olasizmi?", 1.0)
        rec, y = Recorder(), 0
        for height, painter in parts:
            painter(rec, y)
            y += height
        boxes = sorted((top, bottom, line) for _, line, top, bottom in rec.ops)
        overlaps = [(a[2], b[2]) for a, b in zip(boxes, boxes[1:]) if b[0] < a[1] - 2]
        check(f"IQ {iq_value}: sertifikat elementlari ustma-ust tushmaydi", not overlaps, str(overlaps))

    zero = ri.build_card("iq", 0, {"iq": 70, "kinds": {k: [0, n] for k, (_, n) in kinds.items()}}, "uz")
    check("0 to‘g‘ri — kuchli tomon deb aytilmaydi", "kuchli tomoningiz:" not in " ".join(zero.lines).lower())

    scales = {"maqsad": 20, "intizom": 0, "tafakkur": 55, "nazorat": 0, "mustaqillik": 30,
              "muloqot": 45, "bardosh": 25, "uyqu": 0, "ichki": 40}
    idx = ri.build_card("future", 31, scales, "uz")
    check("past indeks (31) yozilmaydi", "31" not in idx.headline + (idx.pill or "") + " ".join(idx.lines), str(idx))
    check("indeks 70+ — ball ko‘rsatiladi", "82" in (ri.build_card("future", 82, scales, "uz").pill or ""))
    only_one = ri.build_card("bigfive", None, {"E": 60, "A": 0, "C": 0, "S": 0, "O": 0}, "ru")
    names = [REGISTRY["bigfive"].scales[k].name["ru"] for k in "ACSO"]
    check("0 foizli yo‘nalish kuchli tomon deb yozilmaydi",
          not any(n in " ".join(only_one.lines) for n in names), str(only_one.lines))
    check("hamma 0 — halol «yo‘l boshida»", ri.build_card("future", 0, {k: 0 for k in REGISTRY["future"].scales},
                                                          "uz").headline == "Yo‘l boshida")
    check("past ballga «kuchli» nom berilmaydi", ri.build_card("future", 30, {k: 30 for k in REGISTRY["future"].scales},
                                                               "uz").headline == "Yo‘l boshida")
    check("ism: emoji olib tashlanadi", ri.clean_name("🔥 Aziza 🔥") == "Aziza")
    check("ism: faqat emoji → ism yo‘q", ri.clean_name("😎🔥") is None)
    check("ism: o‘zbek kirill saqlanadi", ri.clean_name("Ҳусан Ўринов") == "Ҳусан Ўринов")
    check("ism: uzun ism qisqartiriladi", len(ri.clean_name("A" * 80)) <= ri.NAME_MAX)
    # Rasmdagi hamma sarlavha va test nomi — ikkala tilda, rasmdagi o'lchamda.
    from psytests.insights import ARCHETYPES, FALLBACK
    texts = [(tr_(arch.name, lang), 112, 60, 3) for group in ARCHETYPES.values()
             for arch in group.values() for lang in ("uz", "ru")]
    texts += [(tr_(FALLBACK.name, lang), 112, 60, 3) for lang in ("uz", "ru")]
    texts += [(tr_(REGISTRY[k].title, lang), 72, 48, 2) for k in ORDER for lang in ("uz", "ru")]
    broken = []
    for text, size, min_size, max_lines in texts:
        _, lines = ri._fit(text, ri.SERIF, 800, size, min_size, max_lines)
        if not all(part in text.split(" ") for line in lines for part in line.split(" ")):
            broken.append(lines)
        elif len(lines) > max_lines:
            broken.append(lines)
    check(f"{len(texts)} ta sarlavha: so‘z o‘rtasidan bo‘linmaydi, qatorga sig‘adi",
          not broken, str(broken[:3]))


def render_all() -> None:
    print("5. Hamma testlar uchun rasm")
    samples = {key: {k: (i * 37) % 101 for i, k in enumerate(REGISTRY[key].scales)} for key in ORDER}
    problems = []
    for lang in ("uz", "ru"):
        for key in ORDER + ["iq"]:
            if key == "iq":
                details, total = {"iq": 118, "kinds": {"change": [4, 4], "combine": [2, 4],
                                                       "spatial": [4, 6], "rows": [4, 6]}}, 14
            else:
                details, total = samples[key], 64.0
            card = ri.build_card(key, total, details, lang)
            png = ri.render(card, lang, "kelajak_testi_bot", name="Muhammadali Abdurahmonov",
                            when=date(2026, 9, 25))
            image = Image.open(io.BytesIO(png))
            if image.size != (1080, 1920) or image.format != "PNG":
                problems.append(f"{key}/{lang}: {image.size} {image.format}")
            if len(png) > 9_000_000:
                problems.append(f"{key}/{lang}: {len(png)} bayt")
    check("hamma rasm 1080×1920 PNG, Telegram cheklovidan kichik", not problems, str(problems))


def review_removed() -> None:
    print("6. Xatolar tahlili olib tashlangan")
    check("IQ modulida tushuntirishlar yo‘q",
          not hasattr(iqdata, "explanations") and not hasattr(iqdata, "pick_mistakes"))
    check("hisobotda tahlil matni yo‘q", not hasattr(report, "review_caption"))


def iq_report() -> None:
    print("7. IQ hisoboti")
    est = iqdata.estimate_iq(15, "i_18_29", [])
    for lang in ("uz", "ru"):
        text = report.render_iq(15, est, 900, lang, comparison={"percent": 64, "n": 51, "low": False})
        check(f"{lang}: foiz, keyingi qadam, rasmiy emas degan izoh yo‘q",
              "64" in text and text.endswith(report.next_step("iq", lang))
              and "rasmiy" not in text and "официаль" not in text)
    fast = report.render_iq(15, est, 30, "uz")
    check("juda tez yechilgani aytiladi", "Juda tez" in fast)
    check("keyingi test IQ dan boshqa", report.next_test_title("iq", "uz")[0] != "iq")


async def main() -> int:
    try:
        await migration()
        await referral_rules()
        await percentile_rules()
        card_rules()
        render_all()
        review_removed()
        iq_report()
    finally:
        # Xato bilan to'xtasa ham ulanish yopilsin — aks holda skript osilib qoladi.
        await db.close()
    print()
    if FAILURES:
        print(f"❌ {len(FAILURES)} ta muammo: {FAILURES}")
        return 1
    print("✅ Yangi modullar joyida.")
    return 0


sys.exit(asyncio.run(main()))
