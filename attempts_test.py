"""Regression test for one paid purchase = one completed test attempt."""
from __future__ import annotations

import asyncio
import os
import tempfile

DB_FILE = tempfile.mktemp(suffix=".db")
os.environ.update(
    BOT_TOKEN="0:test",
    ADMIN_ID="999999001",
    DB_PATH=DB_FILE,
    CLICK_SERVICE_ID="test",
    CLICK_MERCHANT_ID="test",
    CLICK_SECRET_KEY="test",
    PUBLIC_URL="https://example.test",
)

import database as db
import database_attempts_patch  # noqa: F401 - installs behavior


async def main() -> int:
    user_id = 123456789
    await db.init()

    payment_id = await db.create_payment(user_id, "bigfive", 9900, "click")
    await db.mark_paid(payment_id)
    assert await db.has_access(user_id, "bigfive")

    await db.save_result(user_id, "bigfive", "uz", None, None, {})
    assert not await db.has_access(user_id, "bigfive"), "completed purchase must be consumed"

    payment_id_2 = await db.create_payment(user_id, "bigfive", 9900, "click")
    await db.mark_paid(payment_id_2)
    assert await db.has_access(user_id, "bigfive")
    await db.save_result(user_id, "bigfive", "uz", None, None, {})
    assert not await db.has_access(user_id, "bigfive")

    rows = await db.recent_payments(10)
    assert sum(1 for row in rows if row["status"] == "paid") == 2
    await db.close()
    print("PASS: each paid test purchase unlocks exactly one completed attempt")
    return 0


raise SystemExit(asyncio.run(main()))
