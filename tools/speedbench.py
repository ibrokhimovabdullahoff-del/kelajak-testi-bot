"""Server-side speed benchmark: how long each handler keeps the user waiting.

Telegram is replaced by a fake session that waits RTT_MS on every API call,
so the result shows how many *sequential* round trips a handler makes on top
of its own DB/CPU work. The database is a temporary file. Nothing is sent to
Telegram and the real database is never touched.

    python tools/speedbench.py            # table
    python tools/speedbench.py --json     # machine-readable, for before/after
"""
from __future__ import annotations

import asyncio
import json
import os
import statistics
import sys
import tempfile
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

ADMIN = 1000001
USER = 2000002
os.environ.update(
    BOT_TOKEN="0:bench",
    ADMIN_ID=str(ADMIN),
    DB_PATH=tempfile.mktemp(suffix=".db"),
    CLICK_SERVICE_ID="1", CLICK_MERCHANT_ID="1", CLICK_SECRET_KEY="bench",
    PUBLIC_URL="https://example.test",
    # Dummy key so the IQ flow runs. NOT the real answer key.
    IQ_ANSWERS="ABCD" * 5,
)

RTT_MS = float(os.getenv("BENCH_RTT_MS", "40"))
ROUNDS = int(os.getenv("BENCH_ROUNDS", "5"))

from datetime import datetime  # noqa: E402

from aiogram import Bot, Dispatcher  # noqa: E402
from aiogram.client.default import DefaultBotProperties  # noqa: E402
from aiogram.client.session.base import BaseSession  # noqa: E402
from aiogram.enums import ParseMode  # noqa: E402
from aiogram.fsm.storage.memory import MemoryStorage  # noqa: E402
from aiogram.types import CallbackQuery, Chat, Message, PhotoSize, Update, User  # noqa: E402

CALLS: list[str] = []
_ids = [10_000]


def _user(uid: int) -> User:
    return User(id=uid, is_bot=False, first_name="Bench", language_code="uz")


def _msg(uid: int, text: str = "x", photo: bool = False) -> Message:
    _ids[0] += 1
    extra = {"photo": [PhotoSize(file_id="f", file_unique_id="u", width=1, height=1)]} if photo else {}
    return Message(message_id=_ids[0], date=datetime.now(), chat=Chat(id=uid, type="private"),
                   from_user=_user(uid), text=None if photo else text, **extra)


class LatencySession(BaseSession):
    """Every API call costs RTT_MS, like a real round trip to Telegram."""

    async def make_request(self, bot, method, timeout=None):
        name = type(method).__name__
        if name == "GetMe":
            return User(id=1, is_bot=True, first_name="Bot", username="bench_bot")
        CALLS.append(name)
        await asyncio.sleep(RTT_MS / 1000)
        chat = getattr(method, "chat_id", None) or USER
        if name in ("SendPhoto", "EditMessageMedia"):
            return _msg(int(chat) if str(chat).lstrip("-").isdigit() else USER, photo=True)
        if name in ("SendMessage", "EditMessageText", "CopyMessage", "SendDocument"):
            return _msg(int(chat) if str(chat).lstrip("-").isdigit() else USER, getattr(method, "text", "") or "x")
        return True

    async def stream_content(self, *a, **k):
        yield b""

    async def close(self):
        pass


async def main() -> None:
    import database as db
    import referrals
    import wallet
    import content_cms as cms
    from handlers import build_router
    from handlers.growth import set_bot_username

    await db.init()
    await referrals.init()
    await wallet.init()
    await cms.init()
    await cms.apply_all()
    try:  # newer code: migrations + analytics; older code simply has no such module
        import migrations
        await migrations.run()
    except ImportError:
        pass

    bot = Bot("0:bench", session=LatencySession(), default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher(storage=MemoryStorage())
    dp.include_router(build_router())
    set_bot_username("bench_bot")
    try:
        import perf
        perf.install(dp, bot)
    except ImportError:
        pass

    # Paid access so the bench reaches the questions (prices are not the point here).
    await db.grant_access(USER, "bigfive", ADMIN)
    await db.grant_access(USER, "iq", ADMIN)
    await db.set_lang(USER, "uz")
    await db.set_lang(ADMIN, "uz")

    upd = [0]

    async def feed(uid: int, *, text: str | None = None, data: str | None = None, photo: bool = False) -> float:
        upd[0] += 1
        if text is not None:
            update = Update(update_id=upd[0], message=_msg(uid, text))
        else:
            cb = CallbackQuery(id=str(upd[0]), from_user=_user(uid), chat_instance="ci", data=data,
                               message=_msg(uid, "prev", photo=photo))
            update = Update(update_id=upd[0], callback_query=cb)
        before = len(CALLS)
        t0 = time.perf_counter()
        await dp.feed_update(bot, update)
        elapsed = (time.perf_counter() - t0) * 1000
        return elapsed, len(CALLS) - before

    scenarios: dict[str, list[tuple[float, int]]] = {}

    def rec(name: str, value: tuple[float, int]) -> None:
        scenarios.setdefault(name, []).append(value)

    for _ in range(ROUNDS):
        rec("/start", await feed(USER, text="/start"))
        rec("menu: open test card", await feed(USER, data="test:bigfive"))
        rec("menu: back to menu", await feed(USER, data="nav:menu"))
        await feed(USER, data="go:bigfive")
        await feed(USER, data="age:a_19_25")
        for i in range(3):
            rec("test: answer question", await feed(USER, data=f"ans:{i}:3"))
        await feed(USER, data="nav:cancel")
        await feed(USER, data="iq:card")
        await feed(USER, data="iq:start")
        await feed(USER, data="iqage:i_18_29", photo=False)
        for i in range(3):
            rec("IQ: answer puzzle", await feed(USER, data=f"iq:a:{i}:A", photo=True))
        await feed(USER, data="iq:stop", photo=True)
        rec("admin: /admin", await feed(ADMIN, text="/admin"))
        rec("admin: statistics", await feed(ADMIN, data="adm:stats"))
        rec("admin: payments", await feed(ADMIN, data="adm:pay"))

    out = {}
    for name, values in scenarios.items():
        times = [v[0] for v in values]
        out[name] = {
            "median_ms": round(statistics.median(times), 1),
            "max_ms": round(max(times), 1),
            "api_calls": round(statistics.median(v[1] for v in values), 1),
            "round_trips": round(statistics.median(times) / RTT_MS, 1),
        }
    await bot.session.close()
    await db.close()
    if "--json" in sys.argv:
        print(json.dumps({"rtt_ms": RTT_MS, "results": out}, ensure_ascii=False))
        return
    print(f"Simulated Telegram round trip: {RTT_MS:.0f} ms\n")
    print(f"{'scenario':26} {'median':>8} {'max':>8} {'API calls':>10} {'≈ sequential RTTs':>18}")
    for name, r in out.items():
        print(f"{name:26} {r['median_ms']:>6.0f}ms {r['max_ms']:>6.0f}ms {r['api_calls']:>10} {r['round_trips']:>18}")


if __name__ == "__main__":
    asyncio.run(main())
