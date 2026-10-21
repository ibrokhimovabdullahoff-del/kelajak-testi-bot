"""Tezlikni o'lchash: har bir yangilanish (update) qancha vaqt oldi.

Har bir update uchun bitta qator yoziladi:

    perf cb:ans handler=answer total=46ms db=1.2ms/3 tg=41ms/2 [EditMessageText,AnswerCallbackQuery]

  * total — bot shu updateni boshidan oxirigacha qayta ishlagan vaqt;
  * db    — SQLite'da o'tgan vaqt / so'rovlar soni;
  * tg    — Telegram API'ni kutgan vaqt / chaqiruvlar soni.

Oxirgi natijalar xotirada (RECENT) — admin /perf buyrug'i ularni p50/p95
ko'rinishida chiqaradi. Hech qanday shaxsiy ma'lumot yozilmaydi: tugma
ma'lumotidan faqat birinchi qismi olinadi ("iq:a:3:B" emas, "cb:iq:a").

Shu yerda yana uchta kichik vazifa bajariladi, chunki ular ham Telegram
so'rovlari oqimida turadi:

  * tugma javobi (answerCallbackQuery) kutilmaydi: so'rov fonda ketadi,
    handler esa shu zahoti ishini davom ettiradi. Bitta bosishga faqat bitta
    javob yuboriladi — Telegram baribir faqat birinchisini ko'rsatadi,
    qolganlari esa har biri bitta behuda round trip edi;
  * bloklanganlarni aniqlash — "bot was blocked by the user" xatosi kelsa,
    foydalanuvchi bloklagan deb belgilanadi (on_blocked chaqiriladi);
  * event loop kechikishi — biror kod butun botni to'xtatib qo'ysa (sinxron
    I/O, og'ir hisob), bu log'da "loop blocked" bo'lib ko'rinadi.
"""
from __future__ import annotations

import asyncio
import contextvars
import logging
import time
from collections import OrderedDict, deque
from dataclasses import dataclass, field
from typing import Any, Awaitable, Callable

import aiosqlite
from aiogram import BaseMiddleware
from aiogram.client.session.middlewares.base import BaseRequestMiddleware
from aiogram.exceptions import TelegramForbiddenError
from aiogram.methods import AnswerCallbackQuery
from aiogram.types import TelegramObject, Update

log = logging.getLogger("perf")

#: Shundan sekin updatelar WARNING bo'lib yoziladi.
SLOW_MS = 1000
#: Event loop shuncha ms dan ko'p to'xtab qolsa, log'ga yoziladi.
LOOP_LAG_MS = 150


@dataclass
class Sample:
    label: str
    started: float = field(default_factory=time.perf_counter)
    handler: str = "-"
    db_ms: float = 0.0
    db_n: int = 0
    tg_ms: float = 0.0
    tg_n: int = 0
    tg_methods: list[str] = field(default_factory=list)
    #: Fonda ketayotgan tugma javoblari — update tugashidan oldin kutiladi.
    pending: list[asyncio.Task] = field(default_factory=list)


_current: contextvars.ContextVar[Sample | None] = contextvars.ContextVar("perf_sample", default=None)

#: (unix vaqt, label, handler, total_ms, db_ms, tg_ms, tg_n)
RECENT: deque[tuple[float, str, str, float, float, float, int]] = deque(maxlen=5000)
LOOP = {"max_lag_ms": 0.0, "lag_events": 0}
STARTED_AT = time.time()


def current() -> Sample | None:
    return _current.get()


def set_handler(name: str) -> None:
    sample = _current.get()
    if sample is not None and sample.handler == "-":
        sample.handler = name


# --- SQLite -----------------------------------------------------------------

_db_patched = False


def _patch_sqlite() -> None:
    """aiosqlite'ning ichki `_execute` metodini o'raydi.

    Barcha amallar (execute, commit, fetch*) shu metod orqali ishchi
    oqimga yuboriladi — bitta joyda o'lchash hammasini qamraydi.
    """
    global _db_patched
    if _db_patched:
        return
    original = aiosqlite.Connection._execute

    async def _execute(self, fn, *args, **kwargs):
        sample = _current.get()
        if sample is None:
            return await original(self, fn, *args, **kwargs)
        t0 = time.perf_counter()
        try:
            return await original(self, fn, *args, **kwargs)
        finally:
            sample.db_ms += (time.perf_counter() - t0) * 1000
            sample.db_n += 1

    aiosqlite.Connection._execute = _execute
    _db_patched = True


# --- Telegram API -----------------------------------------------------------

#: Bloklagan foydalanuvchi aniqlanganda chaqiriladi: async fn(user_id).
on_blocked: Callable[[int], Awaitable[None]] | None = None

_answered: OrderedDict[str, None] = OrderedDict()
_ANSWERED_MAX = 5000
#: Shu tugma bosilishini qayta ishlash davomida javob berilgan so'rovlar.
#: UserContext middleware har bir bosish uchun yangi to'plam ochadi.
_answered_here: contextvars.ContextVar[set[str] | None] = contextvars.ContextVar(
    "perf_answered", default=None)
#: Hozir qayta ishlanayotgan tugma bosilishining id si.
_query_here: contextvars.ContextVar[str | None] = contextvars.ContextVar("perf_query", default=None)


def begin_callback(query_id: str | None = None) -> contextvars.Token:
    _query_here.set(query_id)
    return _answered_here.set(set())


def end_callback(token: contextvars.Token) -> None:
    _answered_here.reset(token)
_SENDING = {"SendMessage", "SendPhoto", "SendDocument", "CopyMessage", "SendMediaGroup",
            "SendVideo", "SendAnimation", "ForwardMessage"}


def _remember_answer(query_id: str) -> bool:
    """True — bu so'rovga birinchi marta javob berilyapti."""
    scope = _answered_here.get()
    if scope is not None:
        if query_id in scope:
            return False
        scope.add(query_id)
        return True
    if query_id in _answered:
        return False
    _answered[query_id] = None
    if len(_answered) > _ANSWERED_MAX:
        _answered.popitem(last=False)
    return True


def already_answered(query_id: str) -> bool:
    scope = _answered_here.get()
    if scope is not None:
        return query_id in scope
    return query_id in _answered


async def _send_answer(make_request, bot, method, sample: Sample | None) -> None:
    t0 = time.perf_counter()
    try:
        await make_request(bot, method)
    except Exception as exc:  # noqa: BLE001 — eskirgan tugma va h.k.: foydalanuvchi baribir ko'radi
        log.debug("answerCallbackQuery: %s", exc)
    finally:
        if sample is not None:
            sample.tg_ms += (time.perf_counter() - t0) * 1000
            sample.tg_n += 1
            sample.tg_methods.append("AnswerCallbackQuery")


class TelegramTimer(BaseRequestMiddleware):
    async def __call__(self, make_request, bot, method):
        name = type(method).__name__
        if name == "GetUpdates":  # long polling — bu kutish, ish emas
            return await make_request(bot, method)
        sample = _current.get()
        if name == "AnswerCallbackQuery":
            if not _remember_answer(method.callback_query_id):
                return True  # Telegram faqat birinchi javobni ko'rsatadi
            if sample is not None:
                # Kutmaymiz: javob fonda ketadi, update tugashidan oldin yakunlanadi.
                sample.pending.append(asyncio.ensure_future(_send_answer(make_request, bot, method, sample)))
                return True
        elif sample is not None:
            # Handler javob bermay turib xabarni tahrirlashga o'tdi — demak
            # ogohlantirish bo'lmaydi. Bo'sh javobni shu so'rov bilan PARALLEL
            # yuboramiz: tugmadagi soat belgisi tahrir bilan bir vaqtda yo'qoladi.
            query_id = _query_here.get()
            if query_id and _remember_answer(query_id):
                answer = AnswerCallbackQuery(callback_query_id=query_id)
                sample.pending.append(asyncio.ensure_future(_send_answer(make_request, bot, answer, sample)))
        t0 = time.perf_counter()
        try:
            return await make_request(bot, method)
        except TelegramForbiddenError:
            chat_id = getattr(method, "chat_id", None)
            if name in _SENDING and isinstance(chat_id, int) and chat_id > 0 and on_blocked:
                try:
                    await on_blocked(chat_id)
                except Exception:  # noqa: BLE001 — statistika xatosi xabar yuborishni buzmasin
                    log.exception("on_blocked xatosi")
            raise
        finally:
            if sample is not None:
                sample.tg_ms += (time.perf_counter() - t0) * 1000
                sample.tg_n += 1
                sample.tg_methods.append(name)


# --- Update darajasi --------------------------------------------------------


def _label(update: Update) -> str:
    """Updatening qisqa nomi. Shaxsiy ma'lumot yo'q: faqat buyruq yoki tugma prefiksi."""
    if update.message:
        text = update.message.text or ""
        if text.startswith("/"):
            return text.split()[0].split("@")[0][:24]
        if update.message.photo:
            return "msg:photo"
        return "msg:text"
    if update.callback_query:
        data = update.callback_query.data or ""
        parts = [p for p in data.split(":") if p and not p.lstrip("-").isdigit()]
        return "cb:" + ":".join(parts[:2])[:24]
    for kind in ("my_chat_member", "edited_message", "inline_query", "pre_checkout_query"):
        if getattr(update, kind, None) is not None:
            return kind
    return "update"


class UpdateTimer(BaseMiddleware):
    """Dispatcher.update ga tashqi middleware: har bir update uchun bitta o'lchov."""

    async def __call__(self, handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
                       event: TelegramObject, data: dict[str, Any]) -> Any:
        sample = Sample(_label(event) if isinstance(event, Update) else type(event).__name__)
        token = _current.set(sample)
        try:
            return await handler(event, data)
        finally:
            while sample.pending:
                pending, sample.pending = sample.pending, []
                await asyncio.gather(*pending, return_exceptions=True)
            _current.reset(token)
            total = (time.perf_counter() - sample.started) * 1000
            RECENT.append((time.time(), sample.label, sample.handler, total,
                           sample.db_ms, sample.tg_ms, sample.tg_n))
            level = logging.WARNING if total >= SLOW_MS else logging.INFO
            log.log(level, "perf %s handler=%s total=%.0fms db=%.1fms/%d tg=%.0fms/%d [%s]",
                    sample.label, sample.handler, total, sample.db_ms, sample.db_n,
                    sample.tg_ms, sample.tg_n, ",".join(sample.tg_methods))


# --- Event loop kechikishi --------------------------------------------------


async def _watch_loop(interval: float = 0.25) -> None:
    loop = asyncio.get_running_loop()
    while True:
        t0 = loop.time()
        await asyncio.sleep(interval)
        lag = (loop.time() - t0 - interval) * 1000
        if lag > LOOP_LAG_MS:
            LOOP["lag_events"] += 1
            LOOP["max_lag_ms"] = max(LOOP["max_lag_ms"], lag)
            log.warning("loop blocked %.0fms", lag)


_watcher: asyncio.Task | None = None


def ensure_session(bot) -> None:
    """Telegram so'rovlari middleware'i shu sessiyada bir marta ulanadi."""
    session = bot.session
    if not getattr(session, "_kelajak_timer", False):
        session.middleware(TelegramTimer())
        session._kelajak_timer = True


def install(dispatcher, bot, watch_loop: bool = False) -> None:
    """Hammasini ulaydi. main.py va sinov skriptlari chaqiradi."""
    global _watcher
    _patch_sqlite()
    dispatcher.update.outer_middleware(UpdateTimer())
    ensure_session(bot)
    if watch_loop and _watcher is None:
        _watcher = asyncio.get_running_loop().create_task(_watch_loop())


# --- Hisobot ----------------------------------------------------------------


def _q(values: list[float], p: float) -> float:
    ordered = sorted(values)
    return ordered[min(len(ordered) - 1, int(p * len(ordered)))]


def summary(since_seconds: float | None = None) -> dict:
    """Label bo'yicha p50/p95/max va o'rtacha DB/Telegram vaqti."""
    cutoff = time.time() - since_seconds if since_seconds else 0
    groups: dict[str, list[tuple]] = {}
    for row in RECENT:
        if row[0] >= cutoff:
            groups.setdefault(row[1], []).append(row)
    out = {}
    for label, rows in groups.items():
        totals = [r[3] for r in rows]
        out[label] = {
            "n": len(rows),
            "p50": _q(totals, 0.5),
            "p95": _q(totals, 0.95),
            "max": max(totals),
            "db": sum(r[4] for r in rows) / len(rows),
            "tg": sum(r[5] for r in rows) / len(rows),
            "tg_n": sum(r[6] for r in rows) / len(rows),
            "handler": rows[-1][2],
        }
    return out
