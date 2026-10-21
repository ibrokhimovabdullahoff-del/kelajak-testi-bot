"""Analitika: foydalanuvchi qadamlari `events` jadvaliga yoziladi.

    events.track(user_id, "test_started", "bigfive")
    events.track(user_id, "q_answered", "bigfive", pct=50)

Yozish botni sekinlashtirmaydi: hodisa xotiradagi navbatga qo'shiladi va
fon vazifasi ularni har soniyada bitta so'rov bilan bazaga yozadi. Analitika
xatosi hech qachon foydalanuvchi oqimini buzmaydi — eng yomon holatda bitta
partiya yo'qoladi va log'ga yoziladi.

Shaxsiy ma'lumot yozilmaydi: `meta` ga faqat test, foiz, manba nomi, summa
kabi narsalar tushadi — javoblar, ism yoki matn emas.
"""
from __future__ import annotations

import asyncio
import contextvars
import json
import logging
import math
import re

import database as db

log = logging.getLogger(__name__)

#: Ruxsat etilgan hodisalar (brief, 3-bo'lim). Boshqa nom kelsa — log'da ogohlantirish.
NAMES = {
    "start", "lang_set", "test_opened", "test_started", "q_answered", "test_completed",
    "free_result_shown", "certificate_sent", "certificate_shared", "paywall_shown",
    "pay_clicked", "payment_success", "payment_failed", "report_unlocked",
    "referral_joined", "referral_rewarded", "promo_used", "blocked",
}

#: Test ichidagi bosqichlar: faqat shu foizlar yoziladi (har bir javob emas).
MILESTONES = (25, 50, 75)

FLUSH_DELAY = 1.0

_buffer: list[tuple] = []
_writer: asyncio.Task | None = None
_flush_lock = asyncio.Lock()


def track(user_id: int | None, event: str, test_id: str | None = None, **meta) -> None:
    """Hodisani navbatga qo'yadi. Hech qachon xato bermaydi va kutmaydi."""
    try:
        if event not in NAMES:
            log.warning("Noma'lum hodisa: %s", event)
        payload = json.dumps(meta, ensure_ascii=False, separators=(",", ":")) if meta else None
        _buffer.append((user_id, event, test_id, payload, db._now()))
        _ensure_writer()
    except Exception:  # noqa: BLE001
        log.exception("Hodisa yozilmadi: %s", event)


def _ensure_writer() -> None:
    global _writer
    if _writer is not None and not _writer.done():
        return
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        return
    # Bo'sh kontekst: yozish vaqti tasodifan biror update o'lchoviga qo'shilmasin.
    _writer = loop.create_task(_write_loop(), context=contextvars.Context())


async def _write_loop() -> None:
    while _buffer:
        await asyncio.sleep(FLUSH_DELAY)
        await flush()


async def flush() -> int:
    """Navbatdagi hamma hodisani bazaga yozadi. Qaytaradi: nechtasi yozildi."""
    async with _flush_lock:
        if not _buffer:
            return 0
        batch = _buffer[:]
        del _buffer[:len(batch)]
        try:
            conn = await db.connect()
            await conn.executemany(
                "INSERT INTO events (user_id, event, test_id, meta, created_at) VALUES (?, ?, ?, ?, ?)",
                batch,
            )
            await conn.commit()
            return len(batch)
        except Exception:  # noqa: BLE001
            log.exception("%d ta hodisa bazaga yozilmadi", len(batch))
            return 0


def crossed_milestones(answered: int, total: int, reached: list[int] | None) -> list[int]:
    """Shu javob bilan yangi kesib o'tilgan bosqichlar (25/50/75 %)."""
    if total <= 0:
        return []
    reached = reached or []
    return [m for m in MILESTONES if answered >= math.ceil(total * m / 100) and m not in reached]


# --- Manba (deep link) ------------------------------------------------------

_SAFE = re.compile(r"[^a-z0-9_]+")


def parse_source(payload: str | None) -> tuple[str | None, dict]:
    """/start payload → (manba, qo'shimcha).

        src_instagram       → ("instagram", {})
        src_tgads_kanal     → ("tgads_kanal", {})
        ref_123             → ("ref", {"ref": 123})
        promo_MAKTAB5       → ("promo", {"code": "maktab5"})
        (bo'sh)             → (None, {})
    """
    raw = (payload or "").strip()
    if not raw:
        return None, {}
    low = raw.lower()
    if low.startswith("src_"):
        name = _SAFE.sub("", low[4:])[:40]
        return (name or "other"), {}
    if low.startswith("ref_") and low[4:].isdigit():
        return "ref", {"ref": int(low[4:])}
    if low.startswith("promo_"):
        code = _SAFE.sub("", low[6:])[:32]
        return "promo", ({"code": code} if code else {})
    return "other", {}
