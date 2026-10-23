"""Rasmli IQ testini uchidan-uchiga tekshirish (haqiqiy Telegram'siz).

Tekshiriladi: rasmlar va javoblar kaliti, to'lov to'sig'i, yosh tanlash, rasm
Telegram'ga bir marta yuklanishi, javob berish/orqaga/ikki marta bosish,
taxminiy IQ bilan natija va uni saqlash, to'g'ri javoblar hech qayerda
ko'rinmasligi, foiz ko'rsatish, to'xtatish, tarix va rus tili.

Ishlatish:  ./venv/bin/python iqtest.py
"""
import asyncio
import json
import os
import sys
import tempfile
from datetime import datetime

os.environ["BOT_TOKEN"] = "0:test"
os.environ["ADMIN_ID"] = "1000001"
os.environ["DB_PATH"] = tempfile.mktemp(suffix=".db")
os.environ["BOT_USERNAME"] = "kelajak_test_bot"
# SOXTA kalit. Haqiqiy kalit hech qachon kodga (va ochiq repoga) yozilmaydi —
# u faqat serverdagi IQ_ANSWERS o'zgaruvchisida turadi.
KEY = list("ABCD" * 5)
os.environ["IQ_ANSWERS"] = "".join(KEY)
os.environ.update(CLICK_SERVICE_ID="1", CLICK_MERCHANT_ID="1",
                  CLICK_SECRET_KEY="x", PUBLIC_URL="https://example.test")

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.client.session.base import BaseSession
from aiogram.enums import ParseMode
from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import (CallbackQuery, Chat, FSInputFile, Message, PhotoSize,
                           Update, User)

import database as db
from psytests.iq import (AGE_GROUPS, IQ_MARGIN, IQ_MAX, IQ_MIN, KINDS, LETTERS, MIN_PEERS,
                         PUZZLES, TOTAL, answer_key, estimate_iq, grade, level_for, percentile)

CALLS: list = []
FAILURES: list[str] = []
STATE = {"user": None, "chat": None}
BROKEN_FILE_IDS: set[str] = set()
_n = [5000]


def check(label: str, ok: bool, detail: str = "") -> None:
    print(("  ✅ " if ok else "  ❌ ") + label + ("" if ok else f"  — {detail}"))
    if not ok:
        FAILURES.append(label)


def as_user(uid: int, lang: str = "uz") -> None:
    STATE["user"] = User(id=uid, is_bot=False, first_name="T", language_code=lang)
    STATE["chat"] = Chat(id=uid, type="private")


def _message(text=None, caption=None, photo=False) -> Message:
    _n[0] += 1
    sizes = [PhotoSize(file_id=f"fid_{_n[0]}", file_unique_id=f"u{_n[0]}", width=1147, height=1108)] if photo else None
    return Message(message_id=_n[0], date=datetime.now(), chat=STATE["chat"],
                   from_user=STATE["user"], text=text, caption=caption, photo=sizes)


class FakeSession(BaseSession):
    async def make_request(self, bot, method, timeout=None):
        name = type(method).__name__
        CALLS.append((name, method))
        if name in ("SendPhoto", "EditMessageMedia"):
            media = method.photo if name == "SendPhoto" else method.media.media
            if isinstance(media, str) and media in BROKEN_FILE_IDS:
                BROKEN_FILE_IDS.discard(media)
                raise TelegramBadRequest(method=method, message="Bad Request: wrong file identifier/HTTP URL specified")
            caption = method.caption if name == "SendPhoto" else method.media.caption
            return _message(caption=caption, photo=True).as_(bot)
        if name in ("SendMessage", "EditMessageText", "CopyMessage"):
            # Haqiqiy Telegram javobi botga bog'langan bo'ladi — xabar ustida
            # keyin .edit_text() chaqirilsa ishlashi uchun shunday qaytaramiz.
            return _message(text=getattr(method, "text", "") or "").as_(bot)
        if name == "GetMe":
            return User(id=1, is_bot=True, first_name="Bot", username="kelajak_test_bot")
        return True

    async def stream_content(self, *a, **k):
        yield b""

    async def close(self):
        pass


def calls(name: str) -> list:
    return [m for n, m in CALLS if n == name]


def last_photo():
    for name, m in reversed(CALLS):
        if name == "SendPhoto":
            return m.caption or "", m.reply_markup, m.photo
        if name == "EditMessageMedia":
            return m.media.caption or "", m.reply_markup, m.media.media
    return "", None, None


def last_text() -> str:
    for name, m in reversed(CALLS):
        if name in ("SendMessage", "EditMessageText"):
            return m.text or ""
    return ""


def all_texts() -> str:
    return "\n".join(m.text or "" for name, m in CALLS if name in ("SendMessage", "EditMessageText"))


def text_buttons() -> list:
    for name, m in reversed(CALLS):
        if name in ("SendMessage", "EditMessageText") and m.reply_markup:
            return [b for row in m.reply_markup.inline_keyboard for b in row]
    return []


def alert() -> str:
    got = calls("AnswerCallbackQuery")
    return (got[-1].text or "") if got else ""


async def press(dp, bot, data: str, on_photo: bool = False) -> None:
    msg = _message(caption="rasm", photo=True) if on_photo else _message(text="oldingi")
    cb = CallbackQuery(id=str(len(CALLS)), from_user=STATE["user"], chat_instance="ci",
                       data=data, message=msg)
    await dp.feed_update(bot, Update(update_id=len(CALLS) + 1, callback_query=cb))


async def send(dp, bot, text: str) -> None:
    await dp.feed_update(bot, Update(update_id=len(CALLS) + 1, message=_message(text=text)))


async def begin(dp, bot, age: str = "i_18_29") -> None:
    """Kartochkadan «Boshlash» → yosh tanlash → birinchi rasm."""
    await press(dp, bot, "iq:start")
    await press(dp, bot, f"iqage:{age}")


async def solve(dp, bot, answers: list[str]) -> None:
    for i, letter in enumerate(answers):
        await press(dp, bot, f"iq:a:{i}:{letter}", on_photo=True)


def data_checks() -> None:
    print("1. Rasmlar va javoblar kaliti")
    check(f"{TOTAL} ta topshiriq", TOTAL == 20, str(TOTAL))
    check("fayllar takrorlanmaydi", len({p.file for p in PUZZLES}) == TOTAL)
    missing = [p.file for p in PUZZLES if not p.path.exists()]
    check("hamma rasm joyida", not missing, str(missing))
    not_png = [p.file for p in PUZZLES if p.path.exists() and p.path.read_bytes()[:8] != b"\x89PNG\r\n\x1a\n"]
    check("hamma rasm PNG", not not_png, str(not_png))
    big = [p.file for p in PUZZLES if p.path.exists() and p.path.stat().st_size > 5_000_000]
    check("rasmlar Telegram cheklovidan kichik", not big, str(big))
    check("kalit muhitdan o‘qildi", answer_key() == KEY)
    for bad in ("", "ABCD", "ABCDE" * 4, "ABCD" * 4 + "ABCX"):
        os.environ["IQ_ANSWERS"] = bad
        check(f"noto‘g‘ri kalit rad etildi: {bad[:8]!r}…", answer_key() is None)
    os.environ["IQ_ANSWERS"] = " ".join("abcd" * 5)
    check("kichik harf va probel bilan ham o‘qiladi", answer_key() == KEY)
    os.environ["IQ_ANSWERS"] = "".join(KEY)
    source = "".join(open(f, encoding="utf-8").read() for f in ("psytests/iq.py", "handlers/iq.py"))
    check("kodda javoblar kaliti yo‘q", "answer=" not in source and '"D", "' not in source)
    check("har bir topshiriq turi mavjud", all(p.kind in KINDS for p in PUZZLES))
    check("hammasini topish = 20", grade(list(KEY), KEY)["correct"] == 20)
    check("hammasiga A = 5", grade(["A"] * TOTAL, KEY)["correct"] == 5)
    check(f"foiz: {MIN_PEERS} dan kam ishtirokchida ko‘rsatilmaydi", percentile(10, [5.0] * (MIN_PEERS - 1)) is None)
    check("foiz: hammadan yuqori = 100", percentile(20, [5.0] * MIN_PEERS) == 100)

    print("1b. Taxminiy IQ")
    ages = [code for code, _ in AGE_GROUPS]
    for age in ages:
        row = [estimate_iq(c, age, [])["iq"] for c in range(TOTAL + 1)]
        check(f"{age}: ko‘p to‘g‘ri javob → IQ kamaymaydi", row == sorted(row), str(row))
        check(f"{age}: IQ {IQ_MIN}–{IQ_MAX} ichida", IQ_MIN <= min(row) and max(row) <= IQ_MAX, str(row))
    adult = {c: estimate_iq(c, "i_18_29", [])["iq"] for c in (0, 12, 20)}
    check("kattalar: 0 → 70, 12–13 → ~100, 20 → 125+",
          adult[0] == 70 and 95 <= adult[12] <= 102 and adult[20] >= 125, str(adult))
    check("bir xil natijada bolaning IQ si kattanikidan yuqori",
          estimate_iq(12, "i_10_13", [])["iq"] > estimate_iq(12, "i_18_29", [])["iq"])
    est = estimate_iq(16, "i_18_29", [])
    check(f"oraliq ±{IQ_MARGIN}", est["high"] - est["iq"] == IQ_MARGIN == est["iq"] - est["low"], str(est))
    check("kam ishtirokchida boshlang‘ich me’yor", est["source"] == "prior")
    peers = [float(x % 21) for x in range(MIN_PEERS * 2)]
    top, mid = estimate_iq(20, "i_18_29", peers), estimate_iq(10, "i_18_29", peers)
    check("ko‘p ishtirokchida me’yor ulardan olinadi", top["source"] == "peers" and top["iq"] > mid["iq"] and 95 <= mid["iq"] <= 105,
          f"{top} {mid}")
    check("daraja nomlari IQ bo‘yicha", level_for(131).name["uz"] == "Juda yuqori" and level_for(100).name["uz"] == "O‘rtacha")


async def main() -> int:
    data_checks()
    from handlers import build_router
    import content_cms as cms
    from handlers import autostart_runtime

    await db.init()
    import referrals  # main.py dagi ishga tushish tartibi bilan bir xil
    await referrals.init()
    await cms.init()
    await cms.apply_all()
    bot = Bot("0:test", session=FakeSession(), default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)
    dp.include_router(build_router())
    autostart_runtime.set_runtime(1, storage)
    from handlers.payment import set_bot
    set_bot(bot)

    user = 777
    as_user(user)
    await db.set_lang(user, "uz")

    print("2. Test oldidan ekran (test bepul)")
    CALLS.clear()
    await send(dp, bot, "/iq")
    card = last_text()
    check("kartochka: 20 ta rasmli topshiriq", "20 ta rasmli topshiriq" in card, card[:80])
    check("nima bepul, nima pullik — boshlashdan oldin", "Bepul:" in card and "To‘liq tahlil — 5 000 so‘m" in card,
          card[-200:])
    check("«Boshlash» tugmasi, to‘lov tugmasi yo‘q",
          any(b.callback_data == "iq:start" for b in text_buttons())
          and not any((b.callback_data or "").startswith("pay:") for b in text_buttons()),
          str([b.callback_data for b in text_buttons()]))
    CALLS.clear()
    await press(dp, bot, "iq:a:0:A", on_photo=True)
    check("boshlanmagan testga javob qabul qilinmadi", "tugagan" in alert(), alert())

    print("3. Test boshlanishi va rasm yuklash")
    CALLS.clear()
    await press(dp, bot, "iq:start")
    check("avval yosh so‘raldi (rasm hali yo‘q)", "Yoshingizni tanlang" in last_text() and not calls("SendPhoto"),
          last_text()[:60])
    ages = [b.callback_data for b in text_buttons() if (b.callback_data or "").startswith("iqage:")]
    check("4 ta yosh tugmasi", len(ages) == 4, str(ages))
    await press(dp, bot, "iqage:i_18_29")
    caption, markup, media = last_photo()
    check("birinchi rasm yuborildi", "1 / 20" in caption, caption)
    check("birinchi marta fayl yuklandi", isinstance(media, FSInputFile), type(media).__name__)
    labels = [b.text for row in markup.inline_keyboard for b in row]
    check("A B C D + To‘xtatish", labels[:4] == list(LETTERS) and "To‘xtatish" in labels[-1], str(labels))
    cached = await db.get_setting([k for k in (await _settings()) if k.startswith("iq_photo:01.png") or k.startswith(f"iq_photo:{PUZZLES[0].file}")][0])
    check("file_id bazaga saqlandi", bool(cached), str(cached))

    print("4. Javob berish, ikki marta bosish, orqaga")
    CALLS.clear()
    await press(dp, bot, "iq:a:0:D", on_photo=True)
    caption, _, _ = last_photo()
    check("2-savolga o‘tdi (o‘sha xabar tahrirlandi)", "2 / 20" in caption and calls("EditMessageMedia"), caption)
    CALLS.clear()
    await press(dp, bot, "iq:a:0:A", on_photo=True)
    check("ikki marta bosish e’tiborsiz", "qabul qilingan" in alert() and not calls("EditMessageMedia"), alert())
    await press(dp, bot, "iq:back", on_photo=True)
    caption, markup, _ = last_photo()
    check("orqaga → 1-savol", "1 / 20" in caption, caption)
    await send(dp, bot, "javob A")
    check("matn yozilsa tugma bosish so‘raladi", "A, B, C yoki D" in last_text(), last_text()[:60])

    print("5. Natija")
    answers = list(KEY)
    answers[3] = "A" if answers[3] != "A" else "B"
    answers[17] = "A" if answers[17] != "A" else "B"
    CALLS.clear()
    await solve(dp, bot, answers)
    result = last_text()
    check("bepul natijada to‘g‘ri javoblar soni yo‘q (18 / 20 faqat to‘liq tahlilda)",
          "18 / 20" not in result and "18/20" not in result, result[:200])
    expected = estimate_iq(18, "i_18_29", [])
    print("5a. Bepul natija va to‘lov")
    check("bepul natija: to‘g‘ri javoblar va eng kuchli tur", "Test yakunlandi" in result
          and "Eng kuchli tomoningiz" in result, result[:300])
    check("taxminiy IQ qulflangan: «hisoblandi», raqam yo‘q", "Taxminiy IQ’ingiz hisoblandi — ░░░░░ 🔒" in result
          and f"≈ {expected['iq']}" not in result, result)
    cert_photo = next(m for n, m in CALLS if n == "SendPhoto" and "sertifikat" in (m.caption or ""))
    cert_buttons = [b.callback_data or "" for row in cert_photo.reply_markup.inline_keyboard for b in row]
    check("bepul sertifikatda «Ballni yashirish» yo‘q (yashiradigan raqam yo‘q)",
          not any(c.startswith("cardsc:") for c in cert_buttons), str(cert_buttons))
    free_part = list(CALLS)
    CALLS.clear()
    await press(dp, bot, "nav:history")
    check("Natijalarim: to‘lamaguncha IQ raqami yo‘q", "IQ — to‘liq tahlilda 🔒" in last_text()
          and f"≈{expected['iq']}" not in last_text() and "18/20" not in last_text(), last_text())
    CALLS[:] = free_part  # quyidagi tekshiruvlar bepul natija xabari bo'yicha davom etadi
    share = [b.url for row in cert_photo.reply_markup.inline_keyboard for b in row if b.url]
    check("sertifikat ostida ulashish: shaxsiy taklif havolasi bilan",
          bool(share) and "start%3Dref_" in share[0], str(share))
    unlock = next((b.callback_data for b in text_buttons() if (b.callback_data or "").startswith("rep:buy:")), "")
    check("«To‘liq tahlilni ochish — 5 000 so‘m»", bool(unlock) and "5 000" in text_buttons()[0].text,
          str([b.text for b in text_buttons()]))
    free_calls = list(CALLS)
    CALLS.clear()
    await press(dp, bot, unlock)
    pay_row = (await db.recent_payments(1))[0]
    check("Click to‘lovi aynan IQ tahlili narxiga", pay_row["product"] == "iq" and pay_row["amount"] == 5000,
          str(pay_row))
    await db.mark_paid(pay_row["id"])
    CALLS.clear()
    await autostart_runtime.notify_paid(pay_row["id"])
    result = last_text()
    check("to‘lovdan keyin to‘liq tahlil shu chatda", "To‘lov qabul qilindi" in "\n".join(
        m.text or "" for n, m in CALLS if n == "SendMessage"), str([n for n, _ in CALLS]))
    paid_cert = [m for n, m in CALLS if n == "SendPhoto" and "IQ bilan" in (m.caption or "")]
    check("to‘lovdan keyin IQ yozilgan sertifikat o‘zi keldi (IQ ≥ 100)",
          expected["iq"] < 100 or (len(paid_cert) == 1 and any(
              (b.callback_data or "").startswith("cardsc:") for r in paid_cert[0].reply_markup.inline_keyboard for b in r)),
          f"iq={expected['iq']} {[n for n, _ in CALLS]}")
    order_paid = [n for n, m in CALLS if n in ("SendMessage", "SendPhoto")]
    check("tartib: tasdiq → to‘liq tahlil → sertifikat", expected["iq"] < 100 or order_paid[-1] == "SendPhoto",
          str(order_paid))
    await autostart_runtime.notify_paid(pay_row["id"])
    check("Click ikkinchi marta xabar bersa — sertifikat takrorlanmaydi",
          len([m for n, m in CALLS if n == "SendPhoto" and "IQ bilan" in (m.caption or "")]) == len(paid_cert))
    CALLS[:0] = free_calls  # tartib tekshiruvi uchun bepul qism ham ro'yxatda qolsin
    check(f"taxminiy IQ ≈ {expected['iq']} ko‘rsatildi", f"Taxminiy IQ: <b>≈ {expected['iq']}</b>" in result, result[:200])
    check("IQ oralig‘i ko‘rsatildi", f"{expected['low']}–{expected['high']}" in result, result[:260])
    check("IQ shkalasi ko‘rsatildi", "🔵" in result and f"{IQ_MIN} " in result)
    check(f"daraja: {level_for(expected['iq']).name['uz']}",
          f"Daraja: <b>{level_for(expected['iq']).name['uz']}</b>" in result, result[:300])
    check("to‘liq tahlilda 4 ta fikrlash turi va mashq", all(k.name["uz"] in result for k in KINDS.values())
          and "Mashq:" in result, result[-600:])
    check("vaqt ko‘rsatildi", "Sarflangan vaqt" in result)
    check("tez yechilgani haqida ogohlantirish", "Juda tez" in result)
    check("«rasmiy IQ emas» izohi yo‘q", "IQ taxminiy" not in result and "rasmiy" not in result, result[-200:])
    check("oxirida keyingi qadam", "KEYINGI QADAM" in result and result.rstrip().endswith("oching."), result[-200:])
    check("HTML teglar yopilgan", result.count("<b>") == result.count("</b>") and result.count("<i>") == result.count("</i>"))
    check("natija 4096 belgidan qisqa", len(result) < 4096, str(len(result)))
    order = [(n, getattr(m, "caption", None) or getattr(m, "text", "") or "") for n, m in free_calls
             if n in ("SendPhoto", "SendMessage")]
    cert = next((i for i, (n, text) in enumerate(order) if n == "SendPhoto" and "sertifikat" in text), None)
    check("tartib: sertifikat → bepul natija (xatolar tahlili taklifi yo‘q)",
          cert is not None and cert == len(order) - 2 and "Test yakunlandi" in order[-1][1]
          and not any("start=ref_777" in text for _, text in order[:-1]),
          str([(n, t[:30]) for n, t in order]))
    cert_markup = next(m.reply_markup for n, m in CALLS if n == "SendPhoto" and "sertifikat" in (m.caption or ""))
    check("sertifikat ostida «yuklab olish» tugmasi",
          any((b.callback_data or "").startswith("card:") for row in cert_markup.inline_keyboard for b in row))
    rbuttons = [b for b in text_buttons()]
    check("ulashish — shaxsiy taklif havolasi bilan",
          any(b.url and "start%3Dref_777" in b.url for b in rbuttons), str([b.url for b in rbuttons]))
    check("keyingi test tugmasi (Kasb yo‘nalishi)", any(b.callback_data == "test:career" for b in rbuttons))
    check("ulashish tugmasi", any(b.url and "t.me/share" in b.url for b in rbuttons))
    check("savol rasmi o‘chirildi", bool(calls("DeleteMessage")))
    history = await db.user_history(user)
    check("natija saqlandi (18)", history and history[0]["test_key"] == "iq" and history[0]["total"] == 18.0, str(history[:1]))
    saved = json.loads(history[0]["scales"])
    check("yosh va IQ saqlandi", history[0]["age_group"] == "i_18_29" and saved["iq"] == expected["iq"], str(saved)[:120])
    import access
    check("to‘liq tahlil ochiq qoldi (keyingi urinishlarda ham)", await access.has(user, "iq"))

    print("6. To‘g‘ri javoblar hech qayerda ko‘rinmaydi")
    everything = "\n".join(
        (getattr(m, "text", None) or getattr(m, "caption", None)
         or getattr(getattr(m, "media", None), "caption", None) or "")
        for _, m in CALLS
    )
    check("har bir javobdan keyin to‘g‘ri/noto‘g‘ri aytilmaydi",
          not any(w in everything for w in ("Noto‘g‘ri", "To‘g‘ri!", "✅ To‘g‘ri", "Неверно", "Верно!")))
    check("«To‘g‘ri javob» degan matn yo‘q", "To‘g‘ri javob:" not in everything)
    CALLS.clear()
    result_id = (await db.latest_result(user, "iq"))["id"]
    await press(dp, bot, f"iqrev:{result_id}:0")
    check("eski «xatolarni ko‘rish» tugmasi: faqat izoh, rasm va javob yo‘q",
          not calls("SendPhoto") and "mavjud emas" in alert() and "To‘g‘ri javob" not in alert(), alert())

    print("7. Tugagandan keyin")
    CALLS.clear()
    await press(dp, bot, "iq:a:5:A", on_photo=True)
    check("eski tugma: ogohlantirish", "tugagan" in alert(), alert())
    CALLS.clear()
    await press(dp, bot, "iq:card")
    check("kartochka: to‘liq tahlil sizda ochiq", "sizda ochiq" in last_text(), last_text()[-120:])
    CALLS.clear()
    await press(dp, bot, "nav:history")
    check(f"tarixda «Premium IQ testi · IQ ≈{expected['iq']} (18/20)»",
          "Premium IQ testi" in last_text() and f"IQ ≈{expected['iq']} (18/20)" in last_text(), last_text())
    CALLS.clear()
    await press(dp, bot, "iqage:i_18_29")
    caption, _, _ = last_photo()
    check("eski yosh tugmasi — test yana bepul boshlanadi", "1 / 20" in caption, caption)

    print("8. Rasm keshidan foydalanish va buzilgan file_id")
    other = 999
    as_user(other)
    await db.set_lang(other, "uz")
    CALLS.clear()
    await begin(dp, bot)
    _, _, media = last_photo()
    check("ikkinchi odamga file_id yuborildi (qayta yuklanmadi)", isinstance(media, str), type(media).__name__)
    key = next(k for k in await _settings() if k.startswith(f"iq_photo:{PUZZLES[1].file}"))
    BROKEN_FILE_IDS.add(await db.get_setting(key))
    CALLS.clear()
    await press(dp, bot, f"iq:a:0:{KEY[0]}", on_photo=True)
    caption, _, media = last_photo()
    check("buzilgan file_id → fayl qayta yuklandi", "2 / 20" in caption and isinstance(media, FSInputFile),
          f"{caption[:30]} {type(media).__name__}")

    print("9. To‘xtatish (javoblar saqlanadi)")
    CALLS.clear()
    await press(dp, bot, "iq:stop", on_photo=True)
    check("avval so‘raldi: javoblar saqlanishi aytildi", "to‘xtatasizmi" in last_text() and "saqlanadi" in last_text(),
          last_text()[:80])
    yes = next(b.callback_data for b in text_buttons() if b.callback_data.startswith("iqquit:yes"))
    CALLS.clear()
    await press(dp, bot, yes)
    check("to‘xtatildi va menyu chiqdi", "to‘xtatildi" in all_texts() and "Kelajak Testi" in last_text(),
          all_texts()[:200])
    check("menyuda «Testni davom ettirish (1/20)»",
          any(b.callback_data == "resume:iq" and "1/20" in b.text for b in text_buttons()),
          str([b.text for b in text_buttons()]))
    CALLS.clear()
    await press(dp, bot, "resume:iq")
    caption, _, _ = last_photo()
    check("davom ettirish — 2-savoldan", "2 / 20" in caption, caption)
    CALLS.clear()
    await press(dp, bot, "iq:a:1:A", on_photo=True)
    caption, _, _ = last_photo()
    check("javob qabul qilindi va 3-savol", "3 / 20" in caption, caption)

    print("10. Ishtirokchilar orasidagi o‘rin (rus tili)")
    conn = await db.connect()
    for uid in range(20000, 20000 + MIN_PEERS + 10):
        await conn.execute(
            "INSERT INTO results (user_id, test_key, lang, age_group, total, scales, created_at) VALUES (?,?,?,?,?,?,?)",
            (uid, "iq", "ru", "i_18_29", float(uid % 20), json.dumps({"version": 2}), "2026-09-17T00:00:00"))
    for uid in range(30000, 30000 + MIN_PEERS + 10):  # boshqa yosh — hisobga olinmasligi kerak
        await conn.execute(
            "INSERT INTO results (user_id, test_key, lang, age_group, total, scales, created_at) VALUES (?,?,?,?,?,?,?)",
            (uid, "iq", "ru", "i_10_13", 20.0, json.dumps({"version": 2}), "2026-09-17T00:00:00"))
    await conn.commit()
    as_user(other, "ru")
    await db.set_lang(other, "ru")
    await access.grant(other, ["iq"], "admin")  # to'liq tahlil (foiz bilan) ko'rinsin
    CALLS.clear()
    await begin(dp, bot)
    caption, _, _ = last_photo()
    check("rus tilida savol", "IQ-тест" in caption, caption)
    await solve(dp, bot, list(KEY))
    result = last_text()
    check("rus tilida natija", "Правильных ответов" in result and "20 / 20" in result, result[:120])
    # Hamma ishtirokchi bilan solishtiriladi (yoshidan qat'i nazar), har kimdan birinchi
    # urinish: 60 ta (0–19), 60 ta (20) va 777 (18). 20 dan qat'iy past: 61 / 121 = 50%.
    check("hamma ishtirokchi bilan solishtirish (tenglar «yaxshiroq» emas)",
          "Вы ответили лучше, чем <b>50%</b> людей, прошедших этот тест (121 чел.)" in result,
          result[:400])
    check("rus tilida taxminiy IQ", "Примерный IQ" in result, result[:200])
    saved = json.loads((await db.user_history(other))[0]["scales"])
    check("me’yor tengdoshlardan olindi", saved["iq_source"] == "peers", str(saved)[:120])

    print("10b. Serverda kalit o‘rnatilmagan")
    as_user(4242)
    await db.set_lang(4242, "uz")
    os.environ["IQ_ANSWERS"] = ""
    CALLS.clear()
    await press(dp, bot, "iq:card")
    check("kartochka: test vaqtincha yopiq", "vaqtincha yopiq" in last_text(), last_text()[-80:])
    check("to‘lov tugmasi chiqmadi", not any((b.callback_data or "").startswith("pay:") for b in text_buttons()))
    CALLS.clear()
    await press(dp, bot, "iq:start")
    check("test boshlanmadi", not calls("SendPhoto") and "vaqtincha yopiq" in last_text(), last_text()[:60])
    os.environ["IQ_ANSWERS"] = "".join(KEY)

    print("11. Testni topshirmay turib to‘lov")
    auto = 555
    as_user(auto)
    await db.set_lang(auto, "uz")
    pid = await db.create_payment(auto, "iq", 5000, "click")
    await db.mark_paid(pid)
    CALLS.clear()
    await autostart_runtime.notify_paid(pid)
    check("huquq berildi", await access.has(auto, "iq"))
    check("«testni topshiring — tahlil darhol ochiladi»", "hali topshirmagansiz" in last_text()
          and any(b.callback_data == "iq:card" for b in text_buttons()), last_text()[:80])

    print("12. Do‘st taklifi")
    import referrals
    friend = 4444
    as_user(friend)
    CALLS.clear()
    await send(dp, bot, "/start ref_777")
    check("yangi do‘st hisoblandi", await referrals.invited_count(777) == 1)
    check("taklif qilganga to‘g‘ri javob yoki tahlil yuborilmadi",
          not [m for n, m in CALLS if n in ("SendMessage", "SendPhoto") and getattr(m, "chat_id", None) == 777])
    await send(dp, bot, "/start ref_777")
    check("o‘sha do‘st qayta bossa — ikki marta hisoblanmaydi", await referrals.invited_count(777) == 1)
    as_user(other)  # botni avval ishlatgan
    await send(dp, bot, "/start ref_777")
    check("eski foydalanuvchi hisoblanmaydi", await referrals.invited_count(777) == 1)
    as_user(777)
    await send(dp, bot, "/start ref_777")
    check("o‘zini taklif qilish hisoblanmaydi", await referrals.invited_count(777) == 1)

    print("13. Sertifikatni yuklab olish")
    as_user(777)
    CALLS.clear()
    await press(dp, bot, f"card:{result_id}")
    docs = calls("SendDocument")
    check("to‘liq sifatli PNG hujjat yuborildi",
          docs and docs[0].document.filename.endswith(".png") and "sifatda" in (docs[0].caption or ""),
          str(docs[:1]))
    as_user(friend)
    CALLS.clear()
    await press(dp, bot, f"card:{result_id}")
    check("birovning sertifikati yuklab olinmaydi", not calls("SendDocument"))

    await bot.session.close()
    await db.close()
    print()
    if FAILURES:
        print(f"❌ {len(FAILURES)} ta muammo: {FAILURES}")
        return 1
    print("✅ IQ testi to‘liq ishlaydi.")
    return 0


async def _settings() -> list[str]:
    conn = await db.connect()
    cursor = await conn.execute("SELECT key FROM settings")
    return [row[0] for row in await cursor.fetchall()]


async def _guarded() -> int:
    # Tekshiruv xato bilan to'xtasa ham baza ulanishi yopilsin — aks holda
    # aiosqlite oqimi jarayonni tugatmay, skript (va CI) osilib qoladi.
    try:
        return await main()
    finally:
        await db.close()


sys.exit(asyncio.run(_guarded()))
