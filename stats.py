"""Admin /stats: yangi foydalanuvchilar, voronka, tushum, bloklar.

Hammasi SQL COUNT/SUM bilan hisoblanadi (jadval xotiraga yuklanmaydi) va
60 soniya keshlanadi. Manbalar:

  * opened, paywall, test ichidagi bosqichlar — `events` (yangi analitika);
  * started — `starts`, completed — `results`, paid — `payments`: bular bot
    boshidan bor jadvallar, shuning uchun voronka eski davr uchun ham to'g'ri.

Hamma son — ODAM soni (bitta odam testni ikki marta ochsa ham bitta).
"""
from __future__ import annotations

import time
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import database as db
from config import IQ_KEY, TIMEZONE
from locales import money, tr
from psytests import ORDER, REGISTRY

CACHE_SECONDS = 60
PERIODS = {"today": "Bugun", "7d": "7 kun", "30d": "30 kun"}
#: Testlar tartibi /stats da: IQ birinchi.
TESTS = [IQ_KEY, *ORDER]
#: Pul tushgan to'lov usullari. "manual" — admin qo'lda ochgani (pul yo'q).
CASH_METHODS = ("click", "manual_card")
SALE_METHODS = ("click", "wallet")
BUNDLES = ("all", "bundle")

_cache: dict[str, tuple[float, dict]] = {}


def _tz():
    try:
        return ZoneInfo(TIMEZONE)
    except (ZoneInfoNotFoundError, ValueError):
        return timezone(timedelta(hours=5))


def period_start(period: str, now: datetime | None = None) -> str:
    """Davr boshlanishi — bazadagi kabi UTC ISO matn."""
    now = now or datetime.now(timezone.utc)
    if period == "today":
        local = now.astimezone(_tz())
        start = local.replace(hour=0, minute=0, second=0, microsecond=0)
    else:
        start = now - timedelta(days=30 if period == "30d" else 7)
    return start.astimezone(timezone.utc).isoformat(timespec="seconds")


def title(test_key: str) -> str:
    if test_key == IQ_KEY:
        return "🧩 Premium IQ"
    test = REGISTRY.get(test_key)
    return f"{test.emoji} {tr(test.title, 'uz')}" if test else test_key


async def _rows(query: str, args: tuple) -> list[tuple]:
    conn = await db.connect()
    cursor = await conn.execute(query, args)
    return list(await cursor.fetchall())


async def _one(query: str, args: tuple = ()) -> float:
    rows = await _rows(query, args)
    return rows[0][0] if rows and rows[0][0] is not None else 0


async def compute(period: str) -> dict:
    since = period_start(period)
    data: dict = {"period": period, "since": since}

    data["new_users"] = int(await _one("SELECT COUNT(*) FROM users WHERE created_at >= ?", (since,)))
    data["sources"] = await _rows(
        "SELECT COALESCE(source, 'noma’lum'), COUNT(*) FROM users WHERE created_at >= ? "
        "GROUP BY 1 ORDER BY 2 DESC", (since,))

    async def by_test(query: str) -> dict[str, int]:
        return {key: int(n) for key, n in await _rows(query, (since,))}

    opened = await by_test("SELECT test_id, COUNT(DISTINCT user_id) FROM events "
                           "WHERE event = 'test_opened' AND created_at >= ? GROUP BY test_id")
    started = await by_test("SELECT test_key, COUNT(DISTINCT user_id) FROM starts "
                            "WHERE created_at >= ? GROUP BY test_key")
    completed = await by_test("SELECT test_key, COUNT(DISTINCT user_id) FROM results "
                              "WHERE created_at >= ? GROUP BY test_key")
    paywall = await by_test("SELECT test_id, COUNT(DISTINCT user_id) FROM events "
                            "WHERE event = 'paywall_shown' AND created_at >= ? GROUP BY test_id")
    methods = ",".join(f"'{m}'" for m in SALE_METHODS)
    paid = await by_test(f"SELECT product, COUNT(DISTINCT user_id) FROM payments "
                         f"WHERE status = 'paid' AND method IN ({methods}) AND paid_at >= ? GROUP BY product")
    milestones: dict[str, dict[int, int]] = {}
    for test_id, pct, n in await _rows(
            "SELECT test_id, CAST(json_extract(meta, '$.pct') AS INTEGER), COUNT(DISTINCT user_id) "
            "FROM events WHERE event = 'q_answered' AND created_at >= ? GROUP BY 1, 2", (since,)):
        milestones.setdefault(test_id, {})[pct] = int(n)

    data["funnel"] = {
        key: {
            "opened": opened.get(key, 0), "started": started.get(key, 0),
            "completed": completed.get(key, 0), "paywall": paywall.get(key, 0),
            "paid": paid.get(key, 0), "milestones": milestones.get(key, {}),
        }
        for key in TESTS
    }

    cash = ",".join(f"'{m}'" for m in CASH_METHODS)
    data["cash"] = await _rows(
        f"SELECT method, COUNT(*), COALESCE(SUM(amount), 0) FROM payments "
        f"WHERE status = 'paid' AND method IN ({cash}) AND paid_at >= ? GROUP BY method", (since,))
    data["sales"] = await _rows(
        f"SELECT product, COUNT(*), COALESCE(SUM(amount), 0) FROM payments "
        f"WHERE status = 'paid' AND method IN ({methods}) AND paid_at >= ? "
        f"AND product NOT LIKE 'wallet_topup%' GROUP BY product ORDER BY 3 DESC", (since,))

    events_count = dict(await _rows(
        "SELECT event, COUNT(*) FROM events WHERE created_at >= ? "
        "AND event IN ('referral_joined', 'referral_rewarded', 'report_unlocked', 'certificate_sent') "
        "GROUP BY event", (since,)))
    data["events"] = {k: int(v) for k, v in events_count.items()}

    data["users_total"] = int(await _one("SELECT COUNT(*) FROM users"))
    data["langs"] = dict(await _rows("SELECT COALESCE(lang, '?'), COUNT(*) FROM users GROUP BY 1", ()))
    data["blocked_total"] = int(await _one("SELECT COUNT(*) FROM users WHERE is_blocked = 1"))
    data["blocked_new"] = int(await _one("SELECT COUNT(*) FROM users WHERE blocked_at >= ?", (since,)))
    return data


async def get(period: str) -> dict:
    """Keshlangan natija: 60 soniya ichida qayta hisoblanmaydi."""
    period = period if period in PERIODS else "7d"
    hit = _cache.get(period)
    if hit and time.monotonic() - hit[0] < CACHE_SECONDS:
        return hit[1]
    data = await compute(period)
    _cache[period] = (time.monotonic(), data)
    return data


def drop_cache() -> None:
    _cache.clear()


def _pct(part: int, whole: int) -> str:
    return f"{part * 100 // whole}%" if whole else "—"


def render(data: dict) -> str:
    """Telegram uchun HTML matn (o'zbekcha — admin uchun)."""
    lines = [f"📊 <b>Statistika — {PERIODS[data['period']]}</b>", ""]

    sources = " · ".join(f"{name} {n}" for name, n in data["sources"]) or "—"
    langs = data.get("langs", {})
    lines += [
        f"👥 Foydalanuvchilar: <b>{data['users_total']}</b> · 🇺🇿 {langs.get('uz', 0)} · 🇷🇺 {langs.get('ru', 0)}",
        f"🆕 Yangi foydalanuvchilar: <b>{data['new_users']}</b>",
        f"   {sources}",
        "",
    ]

    lines.append("🧭 <b>Voronka</b> <i>(odam soni)</i>")
    lines.append("<i>ochdi → boshladi → tugatdi → to‘lov oynasi → to‘ladi</i>")
    for key, f in data["funnel"].items():
        if not any((f["opened"], f["started"], f["completed"], f["paywall"], f["paid"])):
            continue
        lines.append("")
        lines.append(f"<b>{title(key)}</b>")
        lines.append(
            f"   {f['opened']} → {f['started']} ({_pct(f['started'], f['opened'])}) → "
            f"{f['completed']} ({_pct(f['completed'], f['started'])}) → "
            f"{f['paywall']} → {f['paid']} ({_pct(f['paid'], f['paywall'])})"
        )
        if f["milestones"]:
            steps = " · ".join(f"{m}% {f['milestones'].get(m, 0)}" for m in (25, 50, 75))
            lines.append(f"   test ichida: {steps} · tugatdi {f['completed']}")
    if all(not any(v for k, v in f.items() if k != "milestones") for f in data["funnel"].values()):
        lines.append("   Bu davrda hech kim test ochmadi.")

    lines += ["", "💰 <b>Tushum</b>"]
    cash_names = {"click": "Click", "manual_card": "karta"}
    total = sum(int(s) for _, _, s in data["cash"])
    parts = " · ".join(f"{cash_names.get(m, m)} {money(int(s))} ({n})" for m, n, s in data["cash"])
    lines.append(f"   Kirim: <b>{money(total)} so‘m</b>" + (f" — {parts}" if parts else ""))
    if data["sales"]:
        for product, n, s in data["sales"]:
            name = "📦 5 ta test (to‘plam)" if product in BUNDLES else title(product)
            lines.append(f"   {name}: {n} ta · {money(int(s))} so‘m")
    else:
        lines.append("   Sotuv yo‘q.")

    ev = data["events"]
    lines += ["", f"🎁 Taklif: qo‘shildi <b>{ev.get('referral_joined', 0)}</b> · "
              f"mukofot <b>{ev.get('referral_rewarded', 0)}</b> · "
              f"🏅 sertifikat <b>{ev.get('certificate_sent', 0)}</b>"]

    rate = _pct(data["blocked_total"], data["users_total"])
    lines += [f"🚫 Bloklagan: <b>{data['blocked_total']}</b> / {data['users_total']} ({rate})"
              f" · shu davrda +{data['blocked_new']}"]
    return "\n".join(lines)
