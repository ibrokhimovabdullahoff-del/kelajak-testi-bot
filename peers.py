"""Foydalanuvchini shu testni topshirgan boshqa odamlar bilan solishtirish.

Foiz faqat bazadagi haqiqiy natijalardan hisoblanadi — hech qachon
o'ylab topilmaydi. Qoidalar:

  * har bir odamdan faqat BIRINCHI urinishi olinadi: qayta topshirganlar
    solishtirishni o'z tomoniga og'dirmasin (IQ da esa javoblar eslab
    qolinadi);
  * foydalanuvchining o'zi va adminlarning sinov natijalari hisoblanmaydi;
  * MIN_SAMPLE tadan kam odam bo'lsa, foiz umuman ko'rsatilmaydi: 5 kishi
    orasidagi "80 foiz" tasodifiy raqam, u odamni chalg'itadi.

Faqat "yaxshiroq-yomonroq" degan tushuncha bor testlar solishtiriladi
(SCORED): IQ va 0–100 indeksli testlar. Big Five va kasb testida
"yaxshiroq javob" bo'lmaydi — ular xususiyat va qiziqishni o'lchaydi.
"""
from __future__ import annotations

import database as db
from config import IQ_KEY, is_admin

#: Shundan kam boshqa odam bo'lsa, foiz ko'rsatilmaydi.
MIN_SAMPLE = 20
#: Foiz shundan past bo'lsa, raqam o'rniga yumshoq jumla ko'rsatiladi —
#: "3 foizdan yaxshiroq" to'g'ri, lekin odamni hech narsaga undamaydi.
LOW_PERCENT = 10
#: Solishtiriladigan testlar. IQ da `total` — to'g'ri javoblar soni.
SCORED = {"future", "child", IQ_KEY}
#: Rasmli IQ natijalari shu versiya bilan saqlanadi (handlers/iq.py).
#: Eski matnli IQ natijalarida `total` boshqa narsa edi — ular aralashmasin.
IQ_RESULT_VERSION = 2


async def others(test_key: str, user_id: int) -> list[float]:
    """Boshqa odamlarning shu testdagi birinchi natijasi."""
    is_iq = test_key == IQ_KEY
    conn = await db.connect()
    cursor = await conn.execute(
        """
        SELECT r.user_id, r.total FROM results r
        JOIN (
            SELECT MIN(id) AS first_id FROM results
            WHERE test_key = ? AND total IS NOT NULL
              AND (? = 0 OR json_extract(scales, '$.version') = ?)
            GROUP BY user_id
        ) f ON f.first_id = r.id
        WHERE r.user_id != ?
        """,
        (test_key, int(is_iq), IQ_RESULT_VERSION, user_id),
    )
    return [float(total) for uid, total in await cursor.fetchall() if not is_admin(uid)]


def better_than(value: float, other_values: list[float]) -> dict | None:
    """Necha foiz odamdan qat'iy yaxshiroq. Odam kam bo'lsa — None."""
    n = len(other_values)
    if n < MIN_SAMPLE:
        return None
    below = sum(1 for other in other_values if other < value)
    percent = below * 100 // n
    return {"percent": percent, "n": n, "low": percent < LOW_PERCENT}


async def compare(test_key: str, user_id: int, value: float | None) -> dict | None:
    """Hisobot uchun tayyor solishtirish yoki None (ko'rsatilmaydi)."""
    if test_key not in SCORED or value is None:
        return None
    return better_than(float(value), await others(test_key, user_id))
