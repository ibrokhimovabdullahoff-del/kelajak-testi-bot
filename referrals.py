"""Do'st taklifi (referral) va IQ xatolar tahlilini ochish.

Har bir foydalanuvchining shaxsiy havolasi bor:

    https://t.me/<bot>?start=ref_<telegram_id>

Shu havola orqali botni BIRINCHI MARTA ishga tushirgan yangi odam taklif
qilgan odamga yoziladi. Kamida bitta shunday odam bo'lsa, taklif qilgan
odam uchun IQ xatolar tahlili butunlay ochiladi.

Aldashga qarshi qoidalar (bazaning o'zida ham, kodda ham):
  * o'zini o'zi taklif qilib bo'lmaydi (CHECK referrer_id <> referred_id);
  * bitta yangi odam faqat bir marta hisoblanadi (referred_id UNIQUE) —
    ikkinchi havolani bossa ham, birinchisi qoladi;
  * faqat HAQIQATAN yangi odam hisoblanadi: botni oldin ishga tushirgan
    odam havolani bossa, hech narsa yozilmaydi — aks holda ikki eski
    foydalanuvchi bir-birining havolasini bosib tahlilni ochib olardi;
  * taklif qilgan odam botda bo'lishi shart (soxta ID li havola ishlamaydi).

Jadvallar faqat QO'SHILADI — mavjud jadvallarning birortasi o'zgarmaydi.
"""
from __future__ import annotations

import asyncio
import re

import database as db

SCHEMA = """
-- Kim kimni taklif qildi. Bitta yangi foydalanuvchi faqat bir marta
-- hisoblanadi (referred_id UNIQUE), o'zini taklif qilish taqiqlangan.
CREATE TABLE IF NOT EXISTS referrals (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    referrer_id  INTEGER NOT NULL,
    referred_id  INTEGER NOT NULL UNIQUE,
    created_at   TEXT    NOT NULL,
    CHECK (referrer_id <> referred_id)
);
CREATE INDEX IF NOT EXISTS idx_referrals_referrer ON referrals(referrer_id);

-- Xatolar tahlili kimga ochilgan. Bir marta yozilgan qator o'chirilmaydi:
-- ochilish butunlay. Birlamchi kalit xabarni ham bir martaga cheklaydi —
-- ikkinchi do'st kelganda "ochildi" xabari qayta yuborilmaydi.
CREATE TABLE IF NOT EXISTS review_unlocks (
    user_id      INTEGER PRIMARY KEY,
    referral_id  INTEGER REFERENCES referrals(id),
    unlocked_at  TEXT    NOT NULL
);
"""

PREFIX = "ref_"
_PAYLOAD = re.compile(r"^ref_(\d{1,20})$")

#: record() natijalari.
UNLOCKED = "unlocked"          # birinchi do'st keldi — tahlil ochildi, xabar yuborish kerak
COUNTED = "counted"            # do'st yozildi, lekin tahlil avvaldan ochiq edi
NOT_NEW = "ignored:not_new"    # bu odam botda avval ham bo'lgan
SELF = "ignored:self"          # o'z havolasini bosgan
UNKNOWN = "ignored:unknown"    # bunday taklif qiluvchi botda yo'q
DUPLICATE = "ignored:duplicate"  # bu yangi odam allaqachon kimdandir hisoblangan

_lock = asyncio.Lock()
#: Ochilish butunlay, shuning uchun "ochiq" javobini keshlab qo'ysa bo'ladi.
_unlocked: set[int] = set()


async def init() -> None:
    conn = await db.connect()
    await conn.executescript(SCHEMA)
    await conn.commit()


def link(bot_username: str, user_id: int) -> str:
    return f"https://t.me/{bot_username.lstrip('@')}?start={PREFIX}{user_id}"


def parse(payload: str | None) -> int | None:
    """"/start ref_123" dagi "ref_123" → 123. Boshqa narsa bo'lsa — None."""
    match = _PAYLOAD.match((payload or "").strip())
    return int(match.group(1)) if match else None


async def record(referrer_id: int, new_user_id: int, is_new_user: bool) -> str:
    """Havola orqali kelgan odamni yozadi. Natija — yuqoridagi konstantalardan biri."""
    if referrer_id == new_user_id:
        return SELF
    if not is_new_user:
        return NOT_NEW
    async with _lock:
        conn = await db.connect()
        cursor = await conn.execute("SELECT 1 FROM users WHERE user_id = ?", (referrer_id,))
        if await cursor.fetchone() is None:
            return UNKNOWN
        now = db._now()
        cursor = await conn.execute(
            "INSERT OR IGNORE INTO referrals (referrer_id, referred_id, created_at) VALUES (?, ?, ?)",
            (referrer_id, new_user_id, now),
        )
        if cursor.rowcount == 0:
            await conn.commit()
            return DUPLICATE
        referral_id = cursor.lastrowid
        cursor = await conn.execute(
            "INSERT OR IGNORE INTO review_unlocks (user_id, referral_id, unlocked_at) VALUES (?, ?, ?)",
            (referrer_id, referral_id, now),
        )
        first_unlock = cursor.rowcount == 1
        await conn.commit()
    _unlocked.add(referrer_id)
    return UNLOCKED if first_unlock else COUNTED


async def is_unlocked(user_id: int) -> bool:
    if user_id in _unlocked:
        return True
    conn = await db.connect()
    cursor = await conn.execute("SELECT 1 FROM review_unlocks WHERE user_id = ?", (user_id,))
    if await cursor.fetchone() is None:
        return False
    _unlocked.add(user_id)
    return True


async def invited_count(referrer_id: int) -> int:
    conn = await db.connect()
    cursor = await conn.execute("SELECT COUNT(*) FROM referrals WHERE referrer_id = ?", (referrer_id,))
    return int((await cursor.fetchone())[0])
