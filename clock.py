"""Toshkent vaqti: oylik chegara, "tungi soatlar" va shunga o'xshashlar uchun."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from config import TIMEZONE


def tz():
    try:
        return ZoneInfo(TIMEZONE)
    except (ZoneInfoNotFoundError, ValueError):
        return timezone(timedelta(hours=5))  # Toshkent: yozgi vaqt yo'q


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def local(moment: datetime | None = None) -> datetime:
    return (moment or utc_now()).astimezone(tz())


def month_key(moment: datetime | None = None) -> str:
    """"2026-10" — Toshkent vaqti bo'yicha joriy oy."""
    return local(moment).strftime("%Y-%m")


def iso(moment: datetime) -> str:
    """Bazadagi vaqt ko'rinishi (UTC ISO) — `database._now()` bilan solishtirsa bo'ladi."""
    return moment.astimezone(timezone.utc).isoformat(timespec="seconds")
