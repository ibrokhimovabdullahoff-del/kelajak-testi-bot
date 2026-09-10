"""Persistent internal wallet + manual UZCARD/HUMO top-up ledger.

The wallet is an application balance, not a bank account. Every balance change
is represented by an immutable transaction row. Debits are atomic and can never
make the balance negative.
"""
from __future__ import annotations

import asyncio
from datetime import datetime, timezone

import database as db

SCHEMA = """
CREATE TABLE IF NOT EXISTS wallets (
    user_id INTEGER PRIMARY KEY,
    balance INTEGER NOT NULL DEFAULT 0 CHECK(balance >= 0),
    updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS wallet_transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    amount INTEGER NOT NULL,
    kind TEXT NOT NULL,
    reference TEXT,
    note TEXT,
    created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_wallet_tx_user ON wallet_transactions(user_id, id DESC);
CREATE UNIQUE INDEX IF NOT EXISTS idx_wallet_tx_ref
    ON wallet_transactions(reference) WHERE reference IS NOT NULL;
"""

_lock = asyncio.Lock()


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


async def init() -> None:
    conn = await db.connect()
    await conn.executescript(SCHEMA)
    await conn.commit()


async def balance(user_id: int) -> int:
    conn = await db.connect()
    cur = await conn.execute("SELECT balance FROM wallets WHERE user_id=?", (user_id,))
    row = await cur.fetchone()
    return int(row[0]) if row else 0


async def history(user_id: int, limit: int = 20) -> list[dict]:
    conn = await db.connect()
    cur = await conn.execute(
        "SELECT id, amount, kind, reference, note, created_at "
        "FROM wallet_transactions WHERE user_id=? ORDER BY id DESC LIMIT ?",
        (user_id, limit),
    )
    rows = await cur.fetchall()
    return [
        {"id": r[0], "amount": r[1], "kind": r[2], "reference": r[3],
         "note": r[4], "created_at": r[5]}
        for r in rows
    ]


async def credit(user_id: int, amount: int, kind: str, reference: str | None = None,
                note: str | None = None) -> bool:
    """Atomically credit once. Returns False for a duplicate reference."""
    if amount <= 0:
        raise ValueError("amount must be positive")
    async with _lock:
        conn = await db.connect()
        try:
            await conn.execute("BEGIN IMMEDIATE")
            if reference:
                cur = await conn.execute(
                    "SELECT 1 FROM wallet_transactions WHERE reference=?", (reference,)
                )
                if await cur.fetchone():
                    await conn.rollback()
                    return False
            now = _now()
            await conn.execute(
                "INSERT INTO wallets(user_id,balance,updated_at) VALUES(?,?,?) "
                "ON CONFLICT(user_id) DO UPDATE SET balance=balance+excluded.balance, "
                "updated_at=excluded.updated_at",
                (user_id, amount, now),
            )
            await conn.execute(
                "INSERT INTO wallet_transactions(user_id,amount,kind,reference,note,created_at) "
                "VALUES(?,?,?,?,?,?)",
                (user_id, amount, kind, reference, note, now),
            )
            await conn.commit()
            return True
        except Exception:
            await conn.rollback()
            raise


async def debit(user_id: int, amount: int, kind: str, reference: str | None = None,
               note: str | None = None) -> bool:
    """Atomically debit only if enough balance exists; never goes negative."""
    if amount <= 0:
        raise ValueError("amount must be positive")
    async with _lock:
        conn = await db.connect()
        try:
            await conn.execute("BEGIN IMMEDIATE")
            cur = await conn.execute(
                "UPDATE wallets SET balance=balance-?, updated_at=? "
                "WHERE user_id=? AND balance>=?",
                (amount, _now(), user_id, amount),
            )
            if cur.rowcount != 1:
                await conn.rollback()
                return False
            await conn.execute(
                "INSERT INTO wallet_transactions(user_id,amount,kind,reference,note,created_at) "
                "VALUES(?,?,?,?,?,?)",
                (user_id, -amount, kind, reference, note, _now()),
            )
            await conn.commit()
            return True
        except Exception:
            await conn.rollback()
            raise


async def purchase(user_id: int, product: str, amount: int) -> bool:
    """Debit wallet and create a paid access payment in one SQLite transaction."""
    if amount <= 0:
        return False
    async with _lock:
        conn = await db.connect()
        try:
            await conn.execute("BEGIN IMMEDIATE")
            cur = await conn.execute(
                "SELECT balance FROM wallets WHERE user_id=?", (user_id,)
            )
            row = await cur.fetchone()
            if not row or row[0] < amount:
                await conn.rollback()
                return False
            now = _now()
            await conn.execute(
                "UPDATE wallets SET balance=balance-?, updated_at=? WHERE user_id=?",
                (amount, now, user_id),
            )
            cur = await conn.execute(
                "INSERT INTO payments(user_id,product,amount,method,status,note,created_at,paid_at) "
                "VALUES(?,?,?,?,?,?,?,?)",
                (user_id, product, amount, "wallet", "paid", "Wallet purchase", now, now),
            )
            payment_id = cur.lastrowid
            await conn.execute(
                "INSERT INTO wallet_transactions(user_id,amount,kind,reference,note,created_at) "
                "VALUES(?,?,?,?,?,?)",
                (user_id, -amount, "purchase", f"payment:{payment_id}",
                 f"Purchase: {product}", now),
            )
            await conn.commit()
            return True
        except Exception:
            await conn.rollback()
            raise


async def manual_create(user_id: int, amount: int, receipt_file_id: str, caption: str = "") -> int:
    """Create a pending manual top-up; it does not credit the wallet."""
    if amount <= 0:
        raise ValueError("amount must be positive")
    conn = await db.connect()
    now = _now()
    note = f"receipt_file_id={receipt_file_id}\n{caption[:500]}"
    cur = await conn.execute(
        "INSERT INTO payments(user_id,product,amount,method,status,note,created_at) "
        "VALUES(?,?,?,?,?,?,?)",
        (user_id, "wallet_topup", amount, "manual_card", "pending", note, now),
    )
    await conn.commit()
    return int(cur.lastrowid)


async def manual_review(payment_id: int, admin_id: int, approve: bool) -> bool:
    """Approve/reject exactly once. Approval credits wallet idempotently."""
    async with _lock:
        conn = await db.connect()
        try:
            await conn.execute("BEGIN IMMEDIATE")
            cur = await conn.execute(
                "SELECT user_id, amount, status, method FROM payments WHERE id=?",
                (payment_id,),
            )
            row = await cur.fetchone()
            if not row or row[2] != "pending" or row[3] != "manual_card":
                await conn.rollback()
                return False
            user_id, amount = int(row[0]), int(row[1])
            now = _now()
            new_status = "paid" if approve else "cancelled"
            await conn.execute(
                "UPDATE payments SET status=?, reviewed_by=?, paid_at=? WHERE id=? AND status='pending'",
                (new_status, admin_id, now if approve else None, payment_id),
            )
            if approve:
                await conn.execute(
                    "INSERT INTO wallets(user_id,balance,updated_at) VALUES(?,?,?) "
                    "ON CONFLICT(user_id) DO UPDATE SET balance=balance+excluded.balance, updated_at=excluded.updated_at",
                    (user_id, amount, now),
                )
                await conn.execute(
                    "INSERT INTO wallet_transactions(user_id,amount,kind,reference,note,created_at) "
                    "VALUES(?,?,?,?,?,?)",
                    (user_id, amount, "manual_topup", f"manual:{payment_id}",
                     f"Approved by admin {admin_id}", now),
                )
            await conn.commit()
            return True
        except Exception:
            await conn.rollback()
            raise


async def adjust(user_id: int, amount: int, admin_id: int, note: str = "") -> bool:
    """Admin balance adjustment; negative values are still protected by the same floor."""
    if amount == 0:
        return False
    if amount > 0:
        return await credit(user_id, amount, "admin_adjustment", f"admin:{admin_id}:{_now()}", note)
    return await debit(user_id, -amount, "admin_adjustment", f"admin:{admin_id}:{_now()}", note)


async def pending_manual(limit: int = 20) -> list[dict]:
    conn = await db.connect()
    cur = await conn.execute(
        "SELECT p.id,p.user_id,p.amount,p.status,p.note,p.created_at,u.username,u.full_name "
        "FROM payments p LEFT JOIN users u ON u.user_id=p.user_id "
        "WHERE p.method='manual_card' ORDER BY p.id DESC LIMIT ?", (limit,)
    )
    rows = await cur.fetchall()
    return [
        {"id": r[0], "user_id": r[1], "amount": r[2], "status": r[3],
         "note": r[4] or "", "created_at": r[5], "username": r[6], "full_name": r[7]}
        for r in rows
    ]
