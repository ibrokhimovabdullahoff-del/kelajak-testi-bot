"""0-bosqich tekshiruvi: tezlik o'lchovi, analitika, manbalar, bloklar, /stats.

Haqiqiy Telegram'siz: soxta sessiya, vaqtinchalik baza.

Ishlatish:  ./venv/bin/python phase0test.py
"""
import asyncio
import json
import os
import sqlite3
import sys
import tempfile
import time
from datetime import datetime

DB_FILE = tempfile.mktemp(suffix=".db")
os.environ.update(BOT_TOKEN="0:test", ADMIN_ID="1000001", DB_PATH=DB_FILE,
                  BOT_USERNAME="kelajak_test_bot", IQ_ANSWERS="ABCD" * 5,
                  CLICK_SERVICE_ID="1", CLICK_MERCHANT_ID="1", CLICK_SECRET_KEY="x",
                  PUBLIC_URL="https://example.test")

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.client.session.base import BaseSession
from aiogram.enums import ParseMode
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import (CallbackQuery, Chat, ChatMemberBanned, ChatMemberMember,
                           ChatMemberUpdated, Message, PhotoSize, Update, User)

import database as db
import events
import migrations
import perf
import stats
from handlers import build_router
from handlers.growth import set_bot_username
from handlers.lifecycle import record_blocked

ADMIN = 1000001
CALLS: list = []
FAILURES: list[str] = []
BLOCKED_CHATS: set[int] = set()
NOT_MODIFIED = {"on": False}
RTT = {"ms": 0}
_ids = [100]


def check(label: str, ok: bool, detail: str = "") -> None:
    print(("  ✅ " if ok else "  ❌ ") + label + ("" if ok else f"  — {detail}"))
    if not ok:
        FAILURES.append(label)


def user(uid: int, lang: str = "uz") -> User:
    return User(id=uid, is_bot=False, first_name="T", language_code=lang)


def msg(uid: int, text: str | None = "x", photo: bool = False) -> Message:
    _ids[0] += 1
    extra = {"photo": [PhotoSize(file_id="f", file_unique_id="u", width=1, height=1)]} if photo else {}
    return Message(message_id=_ids[0], date=datetime.now(), chat=Chat(id=uid, type="private"),
                   from_user=user(uid), text=None if photo else text, **extra)


class FakeSession(BaseSession):
    async def make_request(self, bot, method, timeout=None):
        name = type(method).__name__
        if name == "GetMe":
            return User(id=1, is_bot=True, first_name="Bot", username="kelajak_test_bot")
        if RTT["ms"]:
            await asyncio.sleep(RTT["ms"] / 1000)
        CALLS.append((name, method, time.perf_counter()))
        chat = getattr(method, "chat_id", None)
        if name in ("SendMessage", "SendPhoto", "CopyMessage") and chat in BLOCKED_CHATS:
            raise TelegramForbiddenError(method=method, message="Forbidden: bot was blocked by the user")
        if name == "EditMessageText" and NOT_MODIFIED["on"]:
            raise TelegramBadRequest(method=method, message="Bad Request: message is not modified")
        if name in ("SendPhoto", "EditMessageMedia"):
            return msg(int(chat) if isinstance(chat, int) else 1, photo=True)
        if name in ("SendMessage", "EditMessageText", "SendDocument"):
            return msg(int(chat) if isinstance(chat, int) else 1, getattr(method, "text", "") or "x")
        return True

    async def stream_content(self, *a, **k):
        yield b""

    async def close(self):
        pass


def calls(name: str) -> list:
    return [m for n, m, _ in CALLS if n == name]


def schema() -> dict:
    conn = sqlite3.connect(DB_FILE)
    try:
        tables = dict(conn.execute("SELECT name, sql FROM sqlite_master WHERE type='table'").fetchall())
        cols = {row[1] for row in conn.execute("PRAGMA table_info(users)")}
        return {"tables": tables, "user_cols": cols}
    finally:
        conn.close()


async def query(sql: str, args: tuple = ()) -> list:
    await events.flush()
    conn = await db.connect()
    cursor = await conn.execute(sql, args)
    return list(await cursor.fetchall())


async def main() -> int:
    print("1. Migratsiyalar")
    await db.init()
    import content_cms as cms
    import referrals
    import wallet
    await referrals.init()
    await wallet.init()
    await cms.init()
    await cms.apply_all()
    s = schema()
    check("events va schema_migrations jadvallari", {"events", "schema_migrations"} <= set(s["tables"]))
    check("users: source, source_at, blocked_at ustunlari", {"source", "source_at", "blocked_at"} <= s["user_cols"])
    await db.upsert_user(42, "eski", "Eski", force=True)
    before = await query("SELECT * FROM users WHERE user_id = 42")
    again = await migrations.run()
    check("ikkinchi marta hech narsa qilinmaydi", again == [], str(again))
    check("mavjud foydalanuvchi o‘zgarmadi", await query("SELECT * FROM users WHERE user_id = 42") == before)
    versions = [r[0] for r in await query("SELECT version FROM schema_migrations ORDER BY version")]
    check("hamma migratsiya yozildi", versions == [v for v, _, _ in migrations.MIGRATIONS], str(versions))

    bot = Bot("0:test", session=FakeSession(), default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher(storage=MemoryStorage())
    dp.include_router(build_router())
    perf.install(dp, bot)
    perf.on_blocked = record_blocked
    set_bot_username("kelajak_test_bot")
    upd = [0]

    async def send(uid: int, text: str, lang: str = "uz") -> None:
        upd[0] += 1
        m = msg(uid, text)
        m = m.model_copy(update={"from_user": user(uid, lang)})
        await dp.feed_update(bot, Update(update_id=upd[0], message=m))

    async def press(uid: int, data: str, photo: bool = False) -> None:
        upd[0] += 1
        cb = CallbackQuery(id=f"q{upd[0]}", from_user=user(uid), chat_instance="ci", data=data,
                           message=msg(uid, "prev", photo=photo))
        await dp.feed_update(bot, Update(update_id=upd[0], callback_query=cb))

    print("2. Manba (deep link)")
    check("payload tahlili", events.parse_source("src_Instagram") == ("instagram", {})
          and events.parse_source("src_tgads_kanal_1") == ("tgads_kanal_1", {})
          and events.parse_source("ref_77") == ("ref", {"ref": 77})
          and events.parse_source("promo_MAKTAB-5") == ("promo", {"code": "maktab5"})
          and events.parse_source(None) == (None, {})
          and events.parse_source("src_<script>") == ("script", {}))
    await send(501, "/start src_instagram")
    await send(501, "/start src_youtube")
    await send(502, "/start")
    await send(42, "/start src_tiktok")  # eski foydalanuvchi
    await send(503, "/start ref_501")
    rows = dict(await query("SELECT user_id, source FROM users WHERE user_id IN (42, 501, 502, 503)"))
    check("birinchi manba saqlandi va o‘zgarmadi", rows.get(501) == "instagram", str(rows))
    check("havolasiz yangi foydalanuvchi — direct", rows.get(502) == "direct", str(rows))
    check("eski foydalanuvchining manbasi yozilmadi", rows.get(42) is None, str(rows))
    check("do‘st havolasi — ref", rows.get(503) == "ref", str(rows))
    starts = await query("SELECT user_id, meta FROM events WHERE event = 'start' ORDER BY id")
    check("har bir /start hodisa bo‘lib yozildi", len(starts) == 5, str(starts))
    check("start hodisasida manba bor", json.loads(starts[0][1]) == {"new": True, "src": "instagram"}, starts[0][1])
    joined = await query("SELECT user_id, meta FROM events WHERE event = 'referral_joined'")
    check("do‘st qo‘shilgani yozildi", joined and joined[0][0] == 503 and json.loads(joined[0][1]) == {"referrer": 501},
          str(joined))

    print("3. Voronka hodisalari")
    uid = 601
    await send(uid, "/start")
    await press(uid, "lang:uz")
    await press(uid, "test:future")              # pullik: kartochka + narx
    await press(uid, "go:future")                # paywall
    await press(uid, "pay:future")               # Click tugmasi
    await db.grant_access(uid, "future", ADMIN)
    await press(uid, "test:future")
    await press(uid, "go:future")
    await press(uid, "age:a_19_25")
    from psytests import REGISTRY
    size = REGISTRY["future"].size
    for i in range(size // 2):
        await press(uid, f"ans:{i}:3")
    await press(uid, "back")                     # orqaga va yana oldinga — bosqich takrorlanmasin
    await press(uid, f"ans:{size // 2 - 1}:3")
    for i in range(size // 2, size):
        await press(uid, f"ans:{i}:2")
    names = [r[0] for r in await query("SELECT event FROM events WHERE user_id = ? ORDER BY id", (uid,))]
    for name in ("lang_set", "test_opened", "paywall_shown", "pay_clicked", "test_started",
                 "q_answered", "test_completed", "certificate_sent"):
        check(f"hodisa: {name}", name in names, str(names))
    pcts = [r[0] for r in await query(
        "SELECT CAST(json_extract(meta, '$.pct') AS INTEGER) FROM events "
        "WHERE user_id = ? AND event = 'q_answered' ORDER BY id", (uid,))]
    check("test ichidagi bosqichlar: 25, 50, 75 — bittadan", pcts == [25, 50, 75], str(pcts))
    paywalls = await query("SELECT test_id, meta FROM events WHERE user_id = ? AND event = 'paywall_shown'", (uid,))
    check("paywall: kartochka va to‘lov oynasi", {json.loads(m)["where"] for _, m in paywalls} == {"card", "paywall"},
          str(paywalls))

    print("4. IQ hodisalari")
    iq_user = 602
    await send(iq_user, "/start")
    await press(iq_user, "lang:uz")
    await db.grant_access(iq_user, "iq", ADMIN)
    await press(iq_user, "iq:card")
    await press(iq_user, "iq:start")
    await press(iq_user, "iqage:i_18_29")
    for i in range(20):
        await press(iq_user, f"iq:a:{i}:A", photo=True)
    rows = await query("SELECT event, test_id FROM events WHERE user_id = ? ORDER BY id", (iq_user,))
    seq = [e for e, _ in rows]
    check("IQ: ochdi → boshladi → 25/50/75 → tugatdi",
          seq.count("q_answered") == 3 and seq.index("test_opened") < seq.index("test_started")
          < seq.index("test_completed")
          and all(t == "iq" for e, t in rows if e not in ("start", "lang_set", "certificate_sent")), str(seq))
    leaks = await query("SELECT meta FROM events WHERE meta LIKE '%\"A\"%' OR meta LIKE '%answers%'")
    check("hodisalarda javoblar yozilmaydi", not leaks, str(leaks))

    print("5. To‘lov hodisalari")
    pid = await db.create_payment(701, "bigfive", 2490, "click")
    await db.mark_paid(pid)
    await db.mark_paid(pid)  # Click takrorlasa — ikkinchi hodisa yo‘q
    ok = await query("SELECT user_id, test_id, meta FROM events WHERE event = 'payment_success' AND user_id = 701")
    check("payment_success bir marta, summa va usul bilan",
          len(ok) == 1 and ok[0][1] == "bigfive" and json.loads(ok[0][2]) == {"method": "click", "amount": 2490}, str(ok))

    print("6. Bloklash")
    await send(801, "/start")
    upd[0] += 1
    kicked = ChatMemberUpdated(
        chat=Chat(id=801, type="private"), from_user=user(801), date=datetime.now(),
        old_chat_member=ChatMemberMember(user=user(1)),
        new_chat_member=ChatMemberBanned(user=user(1), until_date=datetime.fromtimestamp(0)))
    await dp.feed_update(bot, Update(update_id=upd[0], my_chat_member=kicked))
    row = (await query("SELECT is_blocked, blocked_at FROM users WHERE user_id = 801"))[0]
    check("botni bloklaganda belgilandi (vaqti bilan)", row[0] == 1 and row[1], str(row))
    check("tarqatishda o‘tkazib yuboriladi", 801 not in await db.all_user_ids())
    await send(801, "/start")
    row = (await query("SELECT is_blocked, blocked_at FROM users WHERE user_id = 801"))[0]
    check("qaytib /start bossa — blok olib tashlandi", row == (0, None), str(row))
    await send(802, "/start")
    BLOCKED_CHATS.add(802)
    try:
        await bot.send_message(802, "salom")
    except TelegramForbiddenError:
        pass
    row = (await query("SELECT is_blocked FROM users WHERE user_id = 802"))[0]
    check("xabar yuborilmasa (Forbidden) — bloklagan deb belgilandi", row[0] == 1, str(row))
    blocked_events = await query("SELECT user_id FROM events WHERE event = 'blocked' ORDER BY id")
    check("blocked hodisasi — har biri bir marta", [r[0] for r in blocked_events] == [801, 802], str(blocked_events))

    print("7. Tugma javobi va tezlik")
    CALLS.clear()
    await press(uid, "nav:menu")
    answers = calls("AnswerCallbackQuery")
    check("bitta bosishga Telegram'ga bitta javob", len(answers) == 1, str(len(answers)))
    CALLS.clear()
    await press(uid, f"ans:0:1")  # test tugagan: eski tugma → ogohlantirish
    answers = calls("AnswerCallbackQuery")
    check("handlerning ogohlantirishi saqlandi (bo‘sh javob uni bosib ketmadi)",
          len(answers) == 1 and answers[0].show_alert and answers[0].text, str([(a.text, a.show_alert) for a in answers]))
    RTT["ms"] = 40
    CALLS.clear()
    t0 = time.perf_counter()
    await press(uid, "test:bigfive")
    took = (time.perf_counter() - t0) * 1000
    RTT["ms"] = 0
    check(f"tugma: javob va tahrir parallel ({took:.0f} ms, 1 round trip ≈ 40 ms)", took < 75, f"{took:.0f} ms")
    labels = {row[1] for row in perf.RECENT}
    check("o‘lchovda nom bor, shaxsiy ma’lumot yo‘q",
          {"/start", "cb:test:future", "cb:iq:a"} <= labels and not any("601" in l or ":A" in l for l in labels),
          str(sorted(labels))[:200])
    summary = perf.summary()
    check("/perf uchun p50/p95", "/start" in summary and summary["/start"]["n"] >= 5, str(summary.get("/start")))
    handlers = {row[2] for row in perf.RECENT if row[1] == "cb:test:bigfive"}
    check("handler nomi yozildi", handlers == {"show_card"}, str(handlers))

    print("8. Xabar o‘zgarmagan xatosi")
    NOT_MODIFIED["on"] = True
    errors = []
    import logging

    class Catch(logging.Handler):
        def emit(self, record):
            if record.levelno >= logging.ERROR:
                errors.append(record.getMessage())
    catcher = Catch()
    logging.getLogger("aiogram").addHandler(catcher)
    await press(ADMIN, "adm:home")
    logging.getLogger("aiogram").removeHandler(catcher)
    NOT_MODIFIED["on"] = False
    check("«message is not modified» xato sifatida yozilmaydi", not errors, str(errors))

    print("9. Sozlamalar keshi")
    await db.set_setting("free_tests", "career")
    sample = perf.Sample("test")
    token = perf._current.set(sample)
    value = await db.get_setting("free_tests")
    perf._current.reset(token)
    check("o‘qish bazaga bormaydi va yangi qiymatni beradi", value == "career" and sample.db_n == 0,
          f"{value} db_n={sample.db_n}")
    await db.set_setting("free_tests", "")

    print("10. /stats")
    CALLS.clear()
    await send(ADMIN, "/stats")
    text = calls("SendMessage")[-1].text if calls("SendMessage") else ""
    check("statistika chiqdi", "Statistika — 7 kun" in text and "Yangi foydalanuvchilar" in text, text[:120])
    check("manbalar ko‘rsatildi", "instagram 1" in text and "ref 1" in text, text[:300])
    check("voronka: Kelajak salohiyati", "Kelajak salohiyati" in text and "test ichida: 25% 1" in text, text)
    check("tushum: Big Five sotuvi", "Big Five" in text and "2 490" in text, text)
    check("bloklar ko‘rsatildi", "Bloklagan: <b>1</b>" in text, text[-160:])
    CALLS.clear()
    await send(601, "/stats")
    check("oddiy foydalanuvchi /stats ko‘rmaydi", not any("Statistika" in (m.text or "") for m in calls("SendMessage")))
    sample = perf.Sample("test")
    token = perf._current.set(sample)
    await stats.get("7d")
    perf._current.reset(token)
    check("60 soniya kesh: qayta hisoblanmaydi", sample.db_n == 0, str(sample.db_n))
    CALLS.clear()
    await press(ADMIN, "stats:today")
    edited = calls("EditMessageText")
    check("davrni almashtirish (bugun)", edited and "Statistika — Bugun" in edited[-1].text, str(edited[-1:]))
    CALLS.clear()
    await send(ADMIN, "/perf")
    text = calls("SendMessage")[-1].text if calls("SendMessage") else ""
    check("/perf jadvali", "Bot tezligi" in text and "/start" in text, text[:200])

    await events.flush()
    await bot.session.close()
    print()
    if FAILURES:
        print(f"❌ {len(FAILURES)} ta muammo: {FAILURES}")
        return 1
    print("✅ 0-bosqich joyida.")
    return 0


async def _guarded() -> int:
    try:
        return await main()
    finally:
        await db.close()


sys.exit(asyncio.run(_guarded()))
