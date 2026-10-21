"""Avtomatik eslatmalar (brief 7.6) — qat'iy chegaralar bilan.

Faqat ikki xil:
  * test tashlab ketilgan: ~3 soatdan keyin bitta "davom etasizmi?" xabari
    (48 soatdan eski tashlab ketilganlarga yozilmaydi);
  * to'liq tahlil oynasi ko'rsatilgan, lekin ochilmagan: ~24 soatdan keyin
    bitta xabar — bosim yo'q, faqat tugma (har bir test uchun bir marta).

Chegaralar:
  * bitta odamga 7 kunda 2 tadan ko'p avtomatik xabar yo'q;
  * 23:00–08:00 (Toshkent) oralig'ida hech narsa yuborilmaydi;
  * bloklaganlarga va "🔕 Eslatma kerak emas" deganlarga yuborilmaydi;
  * odam yaqinda botda bo'lgan bo'lsa — yozmaymiz (u o'zi ko'rib turibdi).

Admin panelda (🚀 O'sish) o'chirib qo'yish mumkin. Har bir xabar
`auto_messages` jadvaliga yoziladi — ikki marta yuborilmaydi.
"""
from __future__ import annotations

import asyncio
import contextvars
import json
import logging
from datetime import datetime, timedelta

from aiogram import Bot
from aiogram.exceptions import TelegramForbiddenError
from aiogram.utils.keyboard import InlineKeyboardBuilder

import access
import clock
import database as db
import events
from config import IQ_KEY
from locales import t
from psytests import REGISTRY

log = logging.getLogger(__name__)

UNFINISHED_AFTER = timedelta(hours=3)
UNFINISHED_UNTIL = timedelta(hours=48)
PAYWALL_AFTER = timedelta(hours=24)
PAYWALL_UNTIL = timedelta(hours=72)
#: Shu vaqt ichida botda bo'lgan odamga to'liq tahlil eslatmasi yuborilmaydi.
PAYWALL_QUIET = timedelta(hours=12)
WEEKLY_MAX = 2
QUIET_FROM, QUIET_TO = 23, 8
TICK_SECONDS = 600
START_DELAY = 60
PER_TICK = 100

UNFINISHED = "unfinished"
PAYWALL = "paywall"
OPTOUT = "optout"


async def enabled() -> bool:
    return await db.get_setting("reminders_on", "1") == "1"


def quiet(now: datetime) -> bool:
    hour = clock.local(now).hour
    return hour >= QUIET_FROM or hour < QUIET_TO


async def opt_out(user_id: int) -> None:
    conn = await db.connect()
    await conn.execute(
        "INSERT OR IGNORE INTO auto_messages (user_id, kind, ref, sent_at, ok) VALUES (?, ?, 'all', ?, 0)",
        (user_id, OPTOUT, db._now()))
    await conn.commit()


async def sent_last_week(user_id: int, now: datetime) -> int:
    conn = await db.connect()
    cursor = await conn.execute(
        "SELECT COUNT(*) FROM auto_messages WHERE user_id = ? AND kind != ? AND sent_at >= ?",
        (user_id, OPTOUT, clock.iso(now - timedelta(days=7))))
    return int((await cursor.fetchone())[0])


_NOT_OPTED_OUT = ("NOT EXISTS (SELECT 1 FROM auto_messages o WHERE o.user_id = u.user_id "
                  f"AND o.kind = '{OPTOUT}')")


async def _unfinished(now: datetime) -> list[dict]:
    conn = await db.connect()
    cursor = await conn.execute(
        f"""
        SELECT p.user_id, p.test_key, p.answers, p.updated_at, u.lang FROM progress p
        JOIN users u ON u.user_id = p.user_id
        WHERE p.answers != '[]' AND p.updated_at <= ? AND p.updated_at >= ?
          AND u.is_blocked = 0 AND u.last_seen <= ? AND {_NOT_OPTED_OUT}
          AND NOT EXISTS (SELECT 1 FROM auto_messages a WHERE a.user_id = p.user_id
                          AND a.kind = '{UNFINISHED}' AND a.ref = p.test_key || ':' || p.updated_at)
        ORDER BY p.updated_at LIMIT {PER_TICK}
        """,
        (clock.iso(now - UNFINISHED_AFTER), clock.iso(now - UNFINISHED_UNTIL),
         clock.iso(now - UNFINISHED_AFTER)))
    return [{"user_id": r[0], "test_key": r[1], "answers": json.loads(r[2] or "[]"),
             "ref": f"{r[1]}:{r[3]}", "lang": r[4] or "uz"} for r in await cursor.fetchall()]


async def _paywalls(now: datetime) -> list[dict]:
    conn = await db.connect()
    cursor = await conn.execute(
        f"""
        SELECT e.user_id, e.test_id, u.lang FROM events e
        JOIN users u ON u.user_id = e.user_id
        WHERE e.event = 'paywall_shown' AND e.created_at <= ? AND e.created_at >= ?
          AND u.is_blocked = 0 AND u.last_seen <= ? AND {_NOT_OPTED_OUT}
          AND NOT EXISTS (SELECT 1 FROM report_access r WHERE r.user_id = e.user_id AND r.test_key = e.test_id)
          AND NOT EXISTS (SELECT 1 FROM auto_messages a WHERE a.user_id = e.user_id
                          AND a.kind = '{PAYWALL}' AND a.ref = e.test_id)
        GROUP BY e.user_id, e.test_id ORDER BY MIN(e.created_at) LIMIT {PER_TICK}
        """,
        (clock.iso(now - PAYWALL_AFTER), clock.iso(now - PAYWALL_UNTIL), clock.iso(now - PAYWALL_QUIET)))
    return [{"user_id": r[0], "test_key": r[1], "ref": r[1], "lang": r[2] or "uz"} for r in await cursor.fetchall()]


def _size(test_key: str) -> int:
    if test_key == IQ_KEY:
        from psytests.iq import TOTAL
        return TOTAL
    return REGISTRY[test_key].size if test_key in REGISTRY else 0


async def _message(kind: str, item: dict) -> tuple[str, object] | None:
    from handlers.reports import test_title

    lang, key = item["lang"], item["test_key"]
    b = InlineKeyboardBuilder()
    if kind == UNFINISHED:
        total = _size(key)
        if not total:
            return None
        # Menyudagi "▶️ Testni davom ettirish (23/50)" bilan bir xil raqam.
        text = t("rem_unfinished", lang, title=test_title(key, lang),
                 n=max(1, min(len(item["answers"]), total)))
        b.button(text=t("btn_continue", lang), callback_data=f"resume:{key}")
    else:
        if await access.has(item["user_id"], key):
            return None
        row = await db.latest_result(item["user_id"], key)
        if row is None:
            return None
        text = t("rem_paywall", lang, title=test_title(key, lang))
        b.button(text=t("btn_see_result", lang), callback_data=f"rep:open:{row['id']}")
    b.button(text=t("btn_rem_off", lang), callback_data="rem:off")
    b.adjust(1)
    return text, b.as_markup()


async def _send(bot: Bot, kind: str, item: dict) -> bool:
    built = await _message(kind, item)
    if built is None:
        return False
    conn = await db.connect()
    cursor = await conn.execute(
        "INSERT OR IGNORE INTO auto_messages (user_id, kind, ref, sent_at) VALUES (?, ?, ?, ?)",
        (item["user_id"], kind, item["ref"], db._now()))
    await conn.commit()
    if cursor.rowcount == 0:
        return False
    text, markup = built
    try:
        await bot.send_message(item["user_id"], text, reply_markup=markup)
    except TelegramForbiddenError:
        from handlers.lifecycle import record_blocked
        await record_blocked(item["user_id"])
        await _mark_failed(item["user_id"], kind, item["ref"])
        return False
    except Exception as exc:  # noqa: BLE001
        log.warning("Eslatma yetmadi (%s, %s): %s", item["user_id"], kind, exc)
        await _mark_failed(item["user_id"], kind, item["ref"])
        return False
    events.track(item["user_id"], "reminder_sent", item["test_key"], kind=kind)
    return True


async def _mark_failed(user_id: int, kind: str, ref: str) -> None:
    conn = await db.connect()
    await conn.execute("UPDATE auto_messages SET ok = 0 WHERE user_id = ? AND kind = ? AND ref = ?",
                       (user_id, kind, ref))
    await conn.commit()


async def tick(bot: Bot, now: datetime | None = None) -> int:
    """Bitta aylanish: yuborilishi kerak bo'lgan eslatmalarni yuboradi. Qaytaradi: nechta yuborildi."""
    now = now or clock.utc_now()
    if not await enabled() or quiet(now):
        return 0
    sent = 0
    touched: set[int] = set()
    for kind, items in ((UNFINISHED, await _unfinished(now)), (PAYWALL, await _paywalls(now))):
        for item in items:
            user_id = item["user_id"]
            if user_id in touched or await sent_last_week(user_id, now) >= WEEKLY_MAX:
                continue
            touched.add(user_id)
            if await _send(bot, kind, item):
                sent += 1
            await asyncio.sleep(0.05)
    if sent:
        log.info("Eslatmalar: %d ta yuborildi", sent)
    return sent


async def _loop(bot: Bot) -> None:
    await asyncio.sleep(START_DELAY)
    while True:
        try:
            await tick(bot)
        except Exception:  # noqa: BLE001 — eslatma xatosi botni to'xtatmasin
            log.exception("Eslatmalar aylanishida xato")
        await asyncio.sleep(TICK_SECONDS)


def start(bot: Bot) -> asyncio.Task:
    # Bo'sh kontekst: fon vazifasi biror update o'lchoviga (perf) qo'shilib ketmasin.
    return asyncio.get_running_loop().create_task(_loop(bot), context=contextvars.Context())
