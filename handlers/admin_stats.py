"""Admin: /stats (voronka, manbalar, tushum) va /perf (bot tezligi)."""
from __future__ import annotations

import time

from aiogram import F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import BaseFilter, Command
from aiogram.types import CallbackQuery, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder

import perf
import stats
from config import is_admin

router = Router()


class IsAdmin(BaseFilter):
    async def __call__(self, event: Message | CallbackQuery) -> bool:
        return bool(event.from_user) and is_admin(event.from_user.id)


router.message.filter(IsAdmin())
router.callback_query.filter(IsAdmin())


def stats_menu(period: str):
    b = InlineKeyboardBuilder()
    for key, label in stats.PERIODS.items():
        b.button(text=("• " + label + " •") if key == period else label, callback_data=f"stats:{key}")
    b.button(text="⚡️ Tezlik", callback_data="perf:show")
    b.button(text="⬅️ Admin panel", callback_data="adm:home")
    b.adjust(3, 2)
    return b.as_markup()


async def _edit(message: Message, text: str, markup) -> None:
    try:
        await message.edit_text(text, reply_markup=markup)
    except TelegramBadRequest as exc:
        if "not modified" not in str(exc):
            await message.answer(text, reply_markup=markup)


@router.message(Command("stats"))
async def stats_command(message: Message) -> None:
    data = await stats.get("7d")
    await message.answer(stats.render(data), reply_markup=stats_menu("7d"))


@router.callback_query(F.data == "adm:stats")
async def stats_button(callback: CallbackQuery) -> None:
    data = await stats.get("7d")
    await _edit(callback.message, stats.render(data), stats_menu("7d"))


@router.callback_query(F.data.startswith("stats:"))
async def stats_period(callback: CallbackQuery) -> None:
    period = callback.data.split(":", 1)[1]
    data = await stats.get(period)
    await _edit(callback.message, stats.render(data), stats_menu(data["period"]))


def render_perf(window_hours: float = 24) -> str:
    rows = perf.summary(window_hours * 3600)
    uptime_h = (time.time() - perf.STARTED_AT) / 3600
    lines = [
        "⚡️ <b>Bot tezligi</b> — server ichida, ms",
        f"<i>oxirgi {window_hours:.0f} soat · ishga tushganiga {uptime_h:.1f} soat</i>",
        "",
    ]
    if not rows:
        lines.append("Hali o‘lchov yo‘q — bot ishga tushgandan beri hech kim yozmadi.")
    else:
        lines.append("<code>nima            soni  p50  p95  max  db  tg</code>")
        for label, r in sorted(rows.items(), key=lambda kv: -kv[1]["n"])[:20]:
            lines.append(
                f"<code>{label[:15]:15} {r['n']:4} {r['p50']:4.0f} {r['p95']:4.0f} "
                f"{r['max']:4.0f} {r['db']:3.0f} {r['tg']:3.0f}</code>"
            )
    lines += ["", "Maqsad: /start &lt; 300 ms, javob tugmasi &lt; 200 ms, admin &lt; 1000 ms."]
    if perf.LOOP["lag_events"]:
        lines.append(f"⚠️ Bot {perf.LOOP['lag_events']} marta to‘xtab qoldi, eng uzuni "
                     f"{perf.LOOP['max_lag_ms']:.0f} ms.")
    else:
        lines.append("✅ Bot hech qachon to‘xtab qolmadi (event loop bloklanmadi).")
    return "\n".join(lines)


def perf_menu():
    b = InlineKeyboardBuilder()
    b.button(text="🔄 Yangilash", callback_data="perf:show")
    b.button(text="📊 Statistika", callback_data="stats:7d")
    b.adjust(2)
    return b.as_markup()


@router.message(Command("perf"))
async def perf_command(message: Message) -> None:
    await message.answer(render_perf(), reply_markup=perf_menu())


@router.callback_query(F.data == "perf:show")
async def perf_button(callback: CallbackQuery) -> None:
    await _edit(callback.message, render_perf(), perf_menu())
