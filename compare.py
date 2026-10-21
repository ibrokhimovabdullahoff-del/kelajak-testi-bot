"""Do'st bilan solishtirish (2-bosqich, brief 7.2): Big Five, keyin IQ.

    natija → [👥 Do'stingiz bilan solishtiring] → havola cmp_<test>_<id>
    do'st havolani bosadi → testni bepul topshiradi → unga qisqa solishtirish

Qoidalar:
  * solishtirishni FAQAT havolani bosgan do'st ko'radi (taklif qilgan emas);
  * ikkalasi ham testni tugatgan bo'lishi shart;
  * foiz va ball ko'rsatilmaydi — faqat "kimda ko'proq" (to'liq tahlil pullik
    bo'lib qoladi, taklif qilganning raqamlari esa begonaga ochilmaydi).
"""
from __future__ import annotations

import html
import logging
import re
from urllib.parse import quote

from aiogram import Bot
from aiogram.utils.keyboard import InlineKeyboardBuilder

import database as db
import events
from config import IQ_KEY
from locales import t, tr
from psytests import REGISTRY
from psytests.iq import KINDS

log = logging.getLogger(__name__)

TESTS = ("bigfive", IQ_KEY)
#: Shundan kam farq — "taxminan teng" (foiz punktlarida).
TIE = 8
_PAYLOAD = re.compile(r"^cmp_(bigfive|iq)_(\d{1,20})$")


def link(bot_username: str, test_key: str, user_id: int) -> str:
    return f"https://t.me/{bot_username.lstrip('@')}?start=cmp_{test_key}_{user_id}"


def parse(payload: str | None) -> tuple[str, int] | None:
    match = _PAYLOAD.match((payload or "").strip())
    return (match.group(1), int(match.group(2))) if match else None


def share_url(bot_username: str, test_key: str, user_id: int, lang: str) -> str:
    url = link(bot_username, test_key, user_id)
    return f"https://t.me/share/url?url={quote(url, safe='')}&text={quote(t(f'cmp_share_{test_key}', lang))}"


def add_button(builder: InlineKeyboardBuilder, test_key: str, lang: str) -> None:
    if test_key in TESTS:
        builder.button(text=t("btn_compare", lang), callback_data=f"cmp:share:{test_key}")


async def first_name(user_id: int, lang: str) -> str:
    conn = await db.connect()
    cursor = await conn.execute("SELECT full_name FROM users WHERE user_id = ?", (user_id,))
    row = await cursor.fetchone()
    name = ((row[0] if row else "") or "").split()
    return html.escape(name[0][:20]) if name else t("cmp_friend", lang)


async def register(friend_id: int, test_key: str, inviter_id: int) -> bool:
    """Havola bosildi. Taklif qilgan testni tugatgan bo'lishi shart."""
    if friend_id == inviter_id or test_key not in TESTS:
        return False
    if await db.latest_result(inviter_id, test_key) is None:
        return False
    conn = await db.connect()
    await conn.execute(
        """
        INSERT INTO compare_invites (friend_id, test_key, inviter_id, created_at, shown_at)
        VALUES (?, ?, ?, ?, NULL)
        ON CONFLICT(friend_id, test_key) DO UPDATE SET
            inviter_id = excluded.inviter_id, created_at = excluded.created_at, shown_at = NULL
        """,
        (friend_id, test_key, inviter_id, db._now()))
    await conn.commit()
    return True


async def pending(friend_id: int, test_key: str) -> int | None:
    conn = await db.connect()
    cursor = await conn.execute(
        "SELECT inviter_id FROM compare_invites WHERE friend_id = ? AND test_key = ? AND shown_at IS NULL",
        (friend_id, test_key))
    row = await cursor.fetchone()
    return int(row[0]) if row else None


def _who(diff: float, name: str, lang: str) -> str:
    """"siz ko'proq" / "Ali ko'proq" / "taxminan teng" (diff — siz minus u)."""
    if abs(diff) < TIE:
        return t("cmp_tie", lang)
    return t("cmp_more_you", lang) if diff > 0 else t("cmp_more_them", lang, name=name)


def _bigfive(mine: dict, theirs: dict, name: str, lang: str) -> list[str]:
    test = REGISTRY["bigfive"]
    diffs = {}
    lines = []
    for key, scale in test.scales.items():
        diff = float(mine.get(key) or 0) - float(theirs.get(key) or 0)
        diffs[key] = diff
        lines.append(f"{scale.emoji} {tr(scale.name, lang)} — {_who(diff, name, lang)}")
    close = min(diffs, key=lambda k: abs(diffs[k]))
    far = max(diffs, key=lambda k: abs(diffs[k]))
    lines.append("")
    lines.append(t("cmp_closest", lang, trait=tr(test.scales[close].name, lang)))
    if abs(diffs[far]) >= TIE:
        lines.append(t("cmp_farthest", lang, trait=tr(test.scales[far].name, lang)))
    return lines


def _iq(mine: dict, theirs: dict, name: str, lang: str) -> list[str]:
    lines = []
    their_kinds = theirs.get("kinds") or {}
    for key, kind in KINDS.items():
        ok, n = (mine.get("kinds") or {}).get(key, [0, 0])
        other_ok, other_n = their_kinds.get(key, [0, 0])
        if not n or not other_n:
            continue
        diff = (ok / n - other_ok / other_n) * 100
        lines.append(f"{kind.emoji} {tr(kind.name, lang)} — {_who(diff, name, lang)}")
    total = int(mine.get("correct") or 0) - int(theirs.get("correct") or 0)
    lines.append("")
    # Umumiy natijada 1 ta topshiriq farqi ham farq — "taxminan" emas.
    lines.append(t("cmp_iq_total", lang, who=_who(total * TIE, name, lang)))
    return lines


async def text_for(friend_row: dict, inviter_row: dict, inviter_name: str, lang: str) -> str:
    key = friend_row["test_key"]
    title = "Big Five" if key == "bigfive" else t("iq_title", lang)
    body = (_bigfive if key == "bigfive" else _iq)(friend_row["scales"], inviter_row["scales"], inviter_name, lang)
    return "\n".join([t("cmp_title", lang, name=inviter_name, test=title), "", *body, "", t("cmp_footer", lang)])


async def on_test_completed(bot: Bot, friend_id: int, test_key: str, lang: str) -> bool:
    """Do'st testni tugatdi: kutilayotgan solishtirish bo'lsa — faqat unga ko'rsatadi."""
    inviter = await pending(friend_id, test_key)
    if inviter is None:
        return False
    return await show(bot, friend_id, test_key, inviter, lang)


async def show(bot: Bot, friend_id: int, test_key: str, inviter: int, lang: str) -> bool:
    mine = await db.latest_result(friend_id, test_key)
    theirs = await db.latest_result(inviter, test_key)
    if mine is None or theirs is None:
        return False
    name = await first_name(inviter, lang)
    from handlers.growth import bot_username

    b = InlineKeyboardBuilder()
    if bot_username():
        b.button(text=t("btn_compare_own", lang), url=share_url(bot_username(), test_key, friend_id, lang))
    b.button(text=t("btn_menu", lang), callback_data="nav:menu")
    b.adjust(1)
    await bot.send_message(friend_id, await text_for(mine, theirs, name, lang), reply_markup=b.as_markup())
    conn = await db.connect()
    await conn.execute("UPDATE compare_invites SET shown_at = ? WHERE friend_id = ? AND test_key = ?",
                       (db._now(), friend_id, test_key))
    await conn.commit()
    events.track(friend_id, "compare_shown", test_key, inviter=inviter)
    return True
