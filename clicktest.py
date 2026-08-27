"""Click integratsiyasini tekshirish.

    ./venv/bin/python clicktest.py

Haqiqiy Click serveriga ulanmaydi — uning o'rniga o'zimiz Click bo'lib,
hujjatdagi qoida bo'yicha imzo yasab, o'z serverimizga so'rov yuboramiz.
Shu sababli internetsiz ham ishlaydi va har deploy oldidan chopiladi.

Tekshiriladi:
  * imzo hujjatdagi formula bo'yicha hisoblanadi
  * soxta imzo rad etiladi (-1), noto'g'ri summa rad etiladi (-2)
  * mavjud bo'lmagan buyurtma rad etiladi (-5 / -6)
  * to'g'ri Prepare + Complete testni ochadi
  * Complete takror kelsa, huquq ikki marta berilmaydi
  * to'lanmagan test yopiq turadi
  * bekor qilingan to'lov huquq bermaydi
"""
import asyncio
import hashlib
import os
import sys
import tempfile
import time

# config .env ni o'qiydi, lekin allaqachon o'rnatilgan qiymatlarni bosmaydi —
# shuning uchun sinov qiymatlarini IMPORTDAN OLDIN qo'yamiz.
SERVICE_ID = "110965"
SECRET = "test-secret-key"
os.environ.update(
    CLICK_SERVICE_ID=SERVICE_ID,
    CLICK_MERCHANT_ID="64192",
    CLICK_SECRET_KEY=SECRET,
    CLICK_MERCHANT_USER_ID="90473",
    PUBLIC_URL="https://example.test",
    DB_PATH=os.path.join(tempfile.mkdtemp(), "clicktest.db"),
)

from aiohttp.test_utils import TestClient, TestServer  # noqa: E402

import database as db  # noqa: E402
from payments import click, webapp  # noqa: E402

FAILURES: list[str] = []
USER = 424242


def check(label: str, ok: bool, detail: str = "") -> None:
    print(("  ✅ " if ok else "  ❌ ") + label + ("" if ok else f"  — {detail}"))
    if not ok:
        FAILURES.append(label)


def sign(fields: list[str]) -> str:
    return hashlib.md5("".join(fields).encode()).hexdigest()


def prepare_body(payment_id: int, amount: str, trans_id: str = "9001") -> dict:
    """Click yuboradigan Prepare so'rovi."""
    stamp = time.strftime("%Y-%m-%d %H:%M:%S")
    return {
        "click_trans_id": trans_id,
        "service_id": SERVICE_ID,
        "click_paydoc_id": "777",
        "merchant_trans_id": str(payment_id),
        "amount": amount,
        "action": "0",
        "error": "0",
        "error_note": "Success",
        "sign_time": stamp,
        "sign_string": sign(
            [trans_id, SERVICE_ID, SECRET, str(payment_id), amount, "0", stamp]
        ),
    }


def complete_body(
    payment_id: int, amount: str, trans_id: str = "9001", error: str = "0"
) -> dict:
    """Click yuboradigan Complete so'rovi."""
    stamp = time.strftime("%Y-%m-%d %H:%M:%S")
    prepare_id = str(payment_id)
    return {
        "click_trans_id": trans_id,
        "service_id": SERVICE_ID,
        "click_paydoc_id": "777",
        "merchant_trans_id": str(payment_id),
        "merchant_prepare_id": prepare_id,
        "amount": amount,
        "action": "1",
        "error": error,
        "error_note": "Success",
        "sign_time": stamp,
        "sign_string": sign(
            [trans_id, SERVICE_ID, SECRET, str(payment_id), prepare_id,
             amount, "1", stamp]
        ),
    }


async def main() -> None:
    await db.init()
    notified: list[int] = []

    async def on_paid(payment_id: int) -> None:
        notified.append(payment_id)

    webapp._on_paid = on_paid
    server = TestServer(webapp.build_app())
    async with TestClient(server) as http:

        # --- Imzo ----------------------------------------------------------
        print("Imzo:")
        body = prepare_body(1, "9900.00")
        check("hujjatdagi formula bilan bir xil",
              click.sign_string(body, click.PREPARE) == body["sign_string"])
        check("soxta imzo o'tmaydi",
              not click.verify({**body, "sign_string": "0" * 32}, click.PREPARE))

        # --- To'lov havolasi ------------------------------------------------
        print("To'lov havolasi:")
        url = click.payment_url(42, 9900)
        check("my.click.uz manzili", url.startswith("https://my.click.uz/services/pay?"))
        for part in (f"service_id={SERVICE_ID}", "amount=9900", "transaction_param=42"):
            check(f"havolada {part}", part in url, url)

        # --- Boshlang'ich holat --------------------------------------------
        print("To'lovsiz holat:")
        check("test yopiq", not await db.has_access(USER, "bigfive"))

        # --- Prepare --------------------------------------------------------
        print("Prepare:")
        payment_id = await db.create_payment(USER, "bigfive", 9900, "click")

        got = await (await http.post("/click/prepare", data=prepare_body(payment_id, "9900.00"))).json()
        check("to'g'ri so'rov qabul qilindi", got["error"] == click.SUCCESS, str(got))
        check("merchant_prepare_id qaytdi",
              got.get("merchant_prepare_id") == payment_id, str(got))

        bad = prepare_body(payment_id, "9900.00")
        bad["sign_string"] = "f" * 32
        got = await (await http.post("/click/prepare", data=bad)).json()
        check("soxta imzo rad etildi", got["error"] == click.SIGN_FAILED, str(got))

        got = await (await http.post("/click/prepare", data=prepare_body(payment_id, "100.00"))).json()
        check("noto'g'ri summa rad etildi", got["error"] == click.BAD_AMOUNT, str(got))

        got = await (await http.post("/click/prepare", data=prepare_body(999999, "9900.00"))).json()
        check("yo'q buyurtma rad etildi", got["error"] == click.USER_NOT_FOUND, str(got))

        check("Prepare hali huquq bermaydi", not await db.has_access(USER, "bigfive"))

        # --- Complete -------------------------------------------------------
        print("Complete:")
        got = await (await http.post("/click/complete", data=complete_body(payment_id, "9900.00"))).json()
        check("to'lov tasdiqlandi", got["error"] == click.SUCCESS, str(got))
        check("merchant_confirm_id qaytdi",
              got.get("merchant_confirm_id") == payment_id, str(got))
        check("test ochildi", await db.has_access(USER, "bigfive"))
        check("foydalanuvchiga xabar berildi", notified == [payment_id], str(notified))

        got = await (await http.post("/click/complete", data=complete_body(payment_id, "9900.00"))).json()
        check("takroriy Complete xato bermaydi", got["error"] == click.SUCCESS, str(got))
        check("xabar ikki marta ketmadi", notified == [payment_id], str(notified))

        bad = complete_body(payment_id, "9900.00")
        bad["sign_string"] = "f" * 32
        got = await (await http.post("/click/complete", data=bad)).json()
        check("soxta imzo rad etildi", got["error"] == click.SIGN_FAILED, str(got))

        # --- Bekor qilingan to'lov ------------------------------------------
        print("Bekor qilingan to'lov:")
        other = await db.create_payment(USER, "career", 9900, "click")
        await http.post("/click/prepare", data=prepare_body(other, "9900.00", "9002"))
        got = await (await http.post(
            "/click/complete",
            data=complete_body(other, "9900.00", "9002", error="-5001"),
        )).json()
        check("bekor qilish qayd etildi", got["error"] == click.CANCELLED, str(got))
        check("huquq berilmadi", not await db.has_access(USER, "career"))

        # --- Boshqa xizmat --------------------------------------------------
        print("Begona so'rov:")
        alien = prepare_body(payment_id, "9900.00")
        alien["service_id"] = "1"
        got = await (await http.post("/click/prepare", data=alien)).json()
        check("boshqa service_id rad etildi", got["error"] == click.BAD_REQUEST, str(got))

        # --- Yordamchi sahifalar ---------------------------------------------
        print("Sahifalar:")
        check("/health ishlaydi", (await http.get("/health")).status == 200)
        check("/click/return ishlaydi", (await http.get("/click/return")).status == 200)

        # --- Telefon raqami ---------------------------------------------------
        print("Telefon raqami:")
        for raw in ("+998 90 123 45 67", "998901234567", "901234567"):
            check(f"{raw!r} tanildi", click.normalize_phone(raw) == "998901234567")
        for raw in ("12345", "", "7 900 123 45 67"):
            check(f"{raw!r} rad etildi", click.normalize_phone(raw) is None)

    await db.close()


if __name__ == "__main__":
    asyncio.run(main())
    print()
    if FAILURES:
        print(f"❌ {len(FAILURES)} ta muammo")
        sys.exit(1)
    print("✅ Click integratsiyasi joyida.")
