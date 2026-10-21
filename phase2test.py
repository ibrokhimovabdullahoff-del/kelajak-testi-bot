"""2-bosqich tekshiruvi: o'sish halqalari.

Tekshiriladi: do'st mukofoti (faqat yangi odam, bir marta, oylik chegara,
o'chirsa bo'ladi) va bepul tahlilni ishlatish; do'st bilan solishtirish
(faqat havolani bosganga, foizlarsiz); promo kodlar (admin yaratadi, bepul
va chegirma, limit, muddat); sertifikat ostidagi ulashish matni; bir
martalik e'lon (bloklaganlar o'tkaziladi, natija yoziladi, ikki marta
ketmaydi); eslatmalar (3 soat / 24 soat, 7 kunda 2 ta, tungi soatlar,
"kerak emas"); /stats.

Haqiqiy Telegram'siz: soxta sessiya, vaqtinchalik baza.

Ishlatish:  ./venv/bin/python phase2test.py
"""
import asyncio
import os
import re
import sys
import tempfile
from datetime import datetime, timedelta, timezone

DB_FILE = tempfile.mktemp(suffix=".db")
os.environ.update(BOT_TOKEN="0:test", ADMIN_ID="1000001", DB_PATH=DB_FILE,
                  BOT_USERNAME="kelajak_test_bot", IQ_ANSWERS="ABCD" * 5,
                  CLICK_SERVICE_ID="1", CLICK_MERCHANT_ID="1", CLICK_SECRET_KEY="x",
                  PUBLIC_URL="https://example.test")

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.client.session.base import BaseSession
from aiogram.enums import ParseMode
from aiogram.exceptions import TelegramForbiddenError
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import CallbackQuery, Chat, Message, Update, User

import access
import broadcast
import clock
import compare
import credits
import database as db
import events
import promo
import reminders
import stats
from handlers import build_router
from handlers import payment as payment_handlers
from handlers import reports
from handlers.growth import set_bot_username
from psytests import REGISTRY

ADMIN = 1000001
CALLS: list = []
#: Hamma yuborilgan matn (DUMP=fayl berilsa, oxirida o'sha faylga yoziladi — ko'z bilan tekshirish uchun).
LOG: list[str] = []
BLOCKED: set[int] = set()
FAILURES: list[str] = []
_ids = [100]


def check(label: str, ok: bool, detail: str = "") -> None:
    print(("  ✅ " if ok else "  ❌ ") + label + ("" if ok else f"  — {detail}"))
    if not ok:
        FAILURES.append(label)


def user(uid: int, lang: str = "uz") -> User:
    return User(id=uid, is_bot=False, first_name=f"U{uid}", language_code=lang)


def msg(uid: int, text: str | None = "x", lang: str = "uz") -> Message:
    _ids[0] += 1
    return Message(message_id=_ids[0], date=datetime.now(), chat=Chat(id=uid, type="private"),
                   from_user=user(uid, lang), text=text)


class FakeSession(BaseSession):
    async def make_request(self, bot, method, timeout=None):
        name = type(method).__name__
        if name == "GetMe":
            return User(id=1, is_bot=True, first_name="Bot", username="kelajak_test_bot")
        chat = getattr(method, "chat_id", None)
        if chat in BLOCKED and name in ("SendMessage", "CopyMessage", "SendPhoto"):
            raise TelegramForbiddenError(method=method, message="Forbidden: bot was blocked by the user")
        CALLS.append((name, method))
        body = getattr(method, "text", None) or getattr(method, "caption", None)
        if body:
            markup = getattr(method, "reply_markup", None)
            keys = [f"[{b.text}]" for row in (markup.inline_keyboard if markup else []) for b in row]
            LOG.append(f"--- {name} → {chat}\n{body}\n{' '.join(keys)}")
        if name in ("SendPhoto", "EditMessageMedia"):
            m = msg(int(chat) if isinstance(chat, int) else 1)
            return m.as_(bot)
        if name in ("SendMessage", "EditMessageText", "SendDocument", "EditMessageCaption"):
            return msg(int(chat) if isinstance(chat, int) else 1, getattr(method, "text", "") or "x").as_(bot)
        return True

    async def stream_content(self, *a, **k):
        yield b""

    async def close(self):
        pass


def sent(name: str, chat: int | None = None) -> list:
    return [m for n, m in CALLS if n == name and (chat is None or getattr(m, "chat_id", None) == chat)]


def texts(chat: int | None = None) -> str:
    return "\n".join(m.text or "" for n, m in CALLS if n in ("SendMessage", "EditMessageText")
                     and (chat is None or getattr(m, "chat_id", None) in (chat, None)))


def buttons(chat: int | None = None) -> list:
    for n, m in reversed(CALLS):
        if n in ("SendMessage", "EditMessageText") and m.reply_markup and \
                (chat is None or getattr(m, "chat_id", None) in (chat, None)):
            return [b for row in m.reply_markup.inline_keyboard for b in row]
    return []


async def main() -> int:
    await db.init()
    bot = Bot("0:test", session=FakeSession(), default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher(storage=MemoryStorage())
    dp.include_router(build_router())
    set_bot_username("kelajak_test_bot")
    payment_handlers.set_bot(bot)
    broadcast.PAUSE = 0
    upd = [0]

    async def send(uid: int, text: str, lang: str = "uz") -> None:
        upd[0] += 1
        await dp.feed_update(bot, Update(update_id=upd[0], message=msg(uid, text, lang=lang)))

    async def press(uid: int, data: str, lang: str = "uz") -> None:
        upd[0] += 1
        cb = CallbackQuery(id=f"q{upd[0]}", from_user=user(uid, lang), chat_instance="ci", data=data,
                           message=msg(uid, "prev"))
        await dp.feed_update(bot, Update(update_id=upd[0], callback_query=cb))

    async def take(uid: int, key: str, level: int = 4, stop_at: int | None = None) -> dict | None:
        await press(uid, f"go:{key}")
        test = REGISTRY[key]
        if test.ask_age:
            await press(uid, "age:" + ("k_7_10" if test.subject == "child" else "a_19_25"))
        for i in range(test.size if stop_at is None else stop_at):
            await press(uid, f"ans:{key}:{i}:{level}")
        return await db.latest_result(uid, key)

    print("0. Migratsiya 6")
    conn = await db.connect()
    tables = {r[0] for r in await (await conn.execute("SELECT name FROM sqlite_master WHERE type='table'")).fetchall()}
    need = {"unlock_credits", "referral_rewards", "promo_codes", "promo_redemptions", "compare_invites",
            "auto_messages", "broadcasts"}
    check("yangi jadvallar bor", need <= tables, str(need - tables))

    print("1. Do‘st mukofoti")
    a = 200
    await send(a, "/start")
    b = 201
    CALLS.clear()
    await send(b, "/start ref_200")
    await take(b, "future")
    reward_msgs = [m for m in sent("SendMessage", a) if "Do‘stingiz testni tugatdi" in (m.text or "")]
    check("yangi do‘st testni tugatdi → taklif qilganga 1 ta xabar", len(reward_msgs) == 1, texts(a)[-200:])
    check("…va tugmasi «Tahlilni tanlash»", reward_msgs and
          reward_msgs[0].reply_markup.inline_keyboard[0][0].callback_data == "cred:menu")
    check("bepul tahlil: 1 ta", await credits.available(a) == 1, str(await credits.available(a)))
    CALLS.clear()
    await take(b, "career")
    check("o‘sha do‘st yana test tugatsa — mukofot yo‘q", await credits.available(a) == 1
          and not sent("SendMessage", a))
    c = 202
    await send(c, "/start")
    await send(c, "/start ref_200")
    await take(c, "future")
    check("eski foydalanuvchi havolani bossa — hisoblanmaydi", await credits.available(a) == 1)
    await send(a, "/start ref_200")
    await take(a, "future")
    check("o‘zini taklif qilish — hisoblanmaydi", await credits.available(a) == 1)

    await db.set_setting("ref_reward_cap", "2")
    for friend in (203, 204):
        await send(friend, "/start ref_200")
        await take(friend, "future")
    status = dict(await (await conn.execute("SELECT referred_id, status FROM referral_rewards")).fetchall())
    check("oylik chegara: 2 ta mukofot, keyingisi «capped»", await credits.available(a) == 2
          and status.get(203) == "rewarded" and status.get(204) == "capped", str(status))
    await db.set_setting("ref_reward_on", "0")
    await send(205, "/start ref_200")
    await take(205, "future")
    check("o‘chirilgan — mukofot ham, yozuv ham yo‘q", await credits.available(a) == 2 and 205 not in dict(
        await (await conn.execute("SELECT referred_id, status FROM referral_rewards")).fetchall()))
    CALLS.clear()
    await press(a, "ref:menu")
    check("o‘chirilganda taklif oynasi oddiy (mukofot va'dasi yo‘q)", "bepul" not in texts(a).split("havola")[0].lower()
          or "1 ta to‘liq tahlil" not in texts(a), texts(a))
    await db.set_setting("ref_reward_on", "1")
    await db.set_setting("ref_reward_cap", "10")
    CALLS.clear()
    await press(a, "ref:menu")
    menu = texts(a)
    check("taklif oynasi: qoida, havola, hisob", "1 ta to‘liq tahlil bepul" in menu and "start=ref_200" in menu
          and "Taklif qilganlaringiz: <b>5</b>" in menu and "Bepul tahlil: <b>2 ta</b>" in menu, menu)

    CALLS.clear()
    row = await take(a, "bigfive")
    paywall = buttons(a)
    use = next((x for x in paywall if (x.callback_data or "").startswith("cred:use:bigfive:")), None)
    check("to‘lov oynasida «Bepul ochish (sizda 2 ta)»", use is not None and "2 ta" in use.text,
          str([x.text for x in paywall]))
    check("…va «Do‘stingiz bilan solishtiring»", any(x.callback_data == "cmp:share:bigfive" for x in paywall))
    CALLS.clear()
    await press(a, use.callback_data)
    check("bepul tahlil ishlatildi → Big Five to‘liq ochildi", await access.has(a, "bigfive")
          and await credits.available(a) == 1 and "XAVF ZONALARI" in texts(a), texts(a)[:200])
    CALLS.clear()
    await press(a, "cred:use:bigfive:0")
    check("ochiq testga ikkinchi marta sarflanmaydi", await credits.available(a) == 1)
    CALLS.clear()
    await press(a, "cred:menu")
    labels = [x.callback_data for x in buttons(a)]
    check("bepul tahlil menyusi: faqat ochilmagan testlar", "cred:use:bigfive:0" not in labels
          and "cred:use:child:0" in labels, str(labels))
    CALLS.clear()
    await press(a, "cred:use:child:0")
    check("natijasi yo‘q test: ochildi va «testni topshiring»", await access.has(a, "child")
          and "Testni topshiring" in texts(a) and await credits.available(a) == 0, texts(a))

    print("2. Do‘st bilan solishtirish")
    CALLS.clear()
    await press(a, "cmp:share:bigfive")
    share = [x.url for x in buttons(a) if x.url]
    check("ulashish havolasi cmp_bigfive_<id>", share and "cmp_bigfive_200" in share[0], str(share))
    g = 206
    CALLS.clear()
    await send(g, "/start cmp_bigfive_200")
    check("do‘stga taklif: kim taklif qildi, foizlarsiz", "U200 sizni solishtirishga taklif qildi" in texts(g),
          texts(g))
    check("…va menyu o‘rniga «Boshlash» (test:bigfive)", any(x.callback_data == "test:bigfive" for x in buttons(g)))
    check("solishtirish havolasi ham taklif sifatida yozildi",
          (await (await conn.execute("SELECT referrer_id FROM referrals WHERE referred_id = ?", (g,))).fetchone())
          == (a,))
    CALLS.clear()
    await take(g, "bigfive", level=1)
    comparison = [m.text for m in sent("SendMessage", g) if "Siz va U200" in (m.text or "")]
    check("do‘st testni tugatdi → solishtirish faqat unga", len(comparison) == 1, texts(g)[-300:])
    body = comparison[0] if comparison else ""
    check("solishtirishda foiz va ball yo‘q", "%" not in body and not re.search(r"\d+ ?/ ?\d+", body), body)
    check("5 ta xususiyat va «eng o‘xshash»", body.count(" — ") >= 5 and "Eng o‘xshash" in body, body)
    check("taklif qilgan odamga solishtirish yuborilmadi", not any("Siz va" in (m.text or "") for m in sent("SendMessage", a)))
    check("do‘st yangi bo‘lgani uchun taklif qilganga mukofot", await credits.available(a) == 1)
    h = 207
    await send(h, "/start")
    await take(h, "bigfive", level=2)
    CALLS.clear()
    await send(h, "/start cmp_bigfive_200")
    check("testni avval topshirgan bo‘lsa — solishtirish darhol", "Siz va U200" in texts(h), texts(h))
    CALLS.clear()
    await send(a, "/start cmp_bigfive_200")
    check("o‘z havolasi — solishtirish yo‘q, oddiy menyu", "Siz va" not in texts(a) and "Kelajak Testi" in texts(a))
    mine = {"test_key": "iq", "scales": {"correct": 12, "kinds": {"change": [4, 5], "spatial": [3, 5],
                                                                   "rows": [3, 5], "combine": [2, 5]}}}
    theirs = {"test_key": "iq", "scales": {"correct": 8, "kinds": {"change": [2, 5], "spatial": [3, 5],
                                                                    "rows": [2, 5], "combine": [1, 5]}}}
    iq_text = await compare.text_for(mine, theirs, "Ali", "uz")
    check("IQ solishtirish: umumiy va turlar, raqamsiz", "Umumiy natija: siz ko‘proq" in iq_text
          and "12" not in iq_text and "8" not in iq_text.replace("👥", ""), iq_text)
    iq_ru = await compare.text_for(mine, theirs, "Ali", "ru")
    check("IQ solishtirish ruscha", "Вы и Ali" in iq_ru and "у вас выше" in iq_ru, iq_ru)

    print("3. Promo kodlar")
    CALLS.clear()
    await press(ADMIN, "grow:home")
    check("admin: 🚀 O‘sish oynasi", "Do‘st mukofoti" in texts(ADMIN) and "Eslatmalar" in texts(ADMIN), texts(ADMIN))
    await press(ADMIN, "promo:new")
    await send(ADMIN, "Maktab-5")
    await press(ADMIN, "pnew:k:free")
    await press(ADMIN, "pnew:t:career")
    await press(ADMIN, "pnew:t:done")
    await send(ADMIN, "2")
    await send(ADMIN, "30")
    CALLS.clear()
    await send(ADMIN, "Maktab 5")
    code = await promo.get("maktab5")
    check("admin bepul kod yaratdi (Kasb, 2 ta, 30 kun, izoh)", code and code["kind"] == "free"
          and code["tests"] == "career" and code["max_uses"] == 2 and code["expires_at"] and code["label"] == "Maktab 5",
          str(code))
    check("admin kod havolasini ko‘rdi", "start=promo_maktab5" in texts(ADMIN), texts(ADMIN))
    p1, p2, p3 = 300, 301, 302
    CALLS.clear()
    await send(p1, "/start promo_MAKTAB5")
    check("havola orqali: Kasb to‘liq tahlili ochildi", await access.has(p1, "career") and "qabul qilindi" in texts(p1),
          texts(p1))
    src = (await (await conn.execute("SELECT source FROM users WHERE user_id = ?", (p1,))).fetchone())[0]
    check("manba kod nomi bilan: promo_maktab5", src == "promo_maktab5", src)
    await send(p2, "/start")
    await send(p2, "/promo maktab5")
    check("/promo KOD bilan ham ishlaydi", await access.has(p2, "career"))
    await send(p3, "/start")
    CALLS.clear()
    await send(p3, "/promo")
    await send(p3, "MAKTAB5")
    check("limit tugadi (2 ta)", "limiti tugagan" in texts(p3) and not await access.has(p3, "career"), texts(p3))
    CALLS.clear()
    await send(p1, "/promo maktab5")
    check("bitta odam bir marta", "allaqachon" in texts(p1), texts(p1))
    CALLS.clear()
    await send(p3, "/promo yoqkod")
    check("yo‘q kod", "topilmadi" in texts(p3), texts(p3))
    await promo.create("eski", promo.DISCOUNT, percent=10, days=1)
    await conn.execute("UPDATE promo_codes SET expires_at = '2020-01-01T00:00:00+00:00' WHERE code = 'eski'")
    await conn.commit()
    CALLS.clear()
    await send(p3, "/promo eski")
    check("muddati o‘tgan kod", "muddati tugagan" in texts(p3), texts(p3))
    await promo.create("najot", promo.DISCOUNT, percent=50)
    await promo.set_active("najot", False)
    CALLS.clear()
    await send(p3, "/promo najot")
    check("o‘chirilgan kod ishlamaydi", "ishlamaydi" in texts(p3), texts(p3))
    await promo.set_active("najot", True)
    CALLS.clear()
    await send(p3, "/promo najot")
    check("chegirma kodi qabul qilindi", "50% chegirma" in texts(p3), texts(p3))
    full = await payment_handlers.price_for("bigfive")
    row = await take(p3, "bigfive")
    unlock = next((x.text for x in buttons(p3) if (x.callback_data or "").startswith("rep:buy:")), "")
    check("to‘lov tugmasida chegirmali narx", f"{full // 2:,}".replace(",", " ") in unlock, f"{unlock} / {full}")
    CALLS.clear()
    await press(p3, f"rep:buy:{row['id']}")
    check("to‘lov oynasida promo qatori", "NAJOT" in texts(p3) and "−50%" in texts(p3), texts(p3))
    pay = (await db.recent_payments(1))[0]
    check("Click buyurtmasi chegirmali summaga", pay["amount"] == promo.apply(full, 50), str(pay))
    await db.mark_paid(pay["id"])
    await reports.after_payment(pay["id"])
    check("to‘lov o‘tdi → tahlil ochildi, chegirma ishlatildi", await access.has(p3, "bigfive")
          and await promo.active_discount(p3) is None)
    row2 = await take(p3, "future")
    unlock2 = next((x.text for x in buttons(p3) if (x.callback_data or "").startswith("rep:buy:")), "")
    future_price = await payment_handlers.price_for("future")
    check("keyingi to‘lov — to‘liq narx", f"{future_price:,}".replace(",", " ") in unlock2, unlock2)
    del row2

    print("4. Sertifikat ostidagi ulashish")
    cert = sent("SendPhoto", p3)
    share = [x.url for r in cert[-1].reply_markup.inline_keyboard for x in r if x.url] if cert else []
    check("sertifikatda ulashish: shaxsiy havola + natija nomi", share and "start%3Dref_302" in share[0]
          and ("chiqdim" in share[0] or "sinab" in share[0]), str(share))
    k = 310
    await send(k, "/start")
    CALLS.clear()
    await take(k, "child")
    cert = sent("SendPhoto", k)
    child_share = [x.url for r in cert[-1].reply_markup.inline_keyboard for x in r if x.url] if cert else []
    from urllib.parse import unquote
    check("Farzand: ulashish matnida bolaning natijasi yo‘q", child_share and "ota-onalar" in unquote(child_share[0])
          and "chiqdim" not in unquote(child_share[0]), str(child_share))

    print("5. Bir martalik e’lon")
    await send(400, "/start")
    await send(401, "/start", lang="ru")
    await send(402, "/start")
    await db.mark_blocked(402)
    BLOCKED.add(401)
    CALLS.clear()
    await press(ADMIN, "grow:ann")
    check("e’lon oldidan ko‘rinishi va oluvchilar soni", "Oluvchilar" in texts(ADMIN) and "IQ’ingiz qancha" in texts(ADMIN),
          texts(ADMIN))
    CALLS.clear()
    await press(ADMIN, "grow:ann:go")
    for _ in range(200):
        value = await db.get_setting("announce_v1")
        if value and value.isdigit():
            break
        await asyncio.sleep(0.02)
    await asyncio.sleep(0.05)
    to_400 = [m for m in sent("SendMessage", 400) if "Assalomu alaykum" in (m.text or "")]
    check("e’lon yetdi (o‘zbekcha, «Boshlash» → IQ)", to_400 and
          to_400[0].reply_markup.inline_keyboard[0][0].callback_data == "iq:card", texts(400))
    check("bloklagan odamga yuborilmadi", not sent("SendMessage", 402))
    flag = (await (await conn.execute("SELECT is_blocked FROM users WHERE user_id = 401")).fetchone())[0]
    check("yuborishda bloklagani aniqlandi va belgilandi", flag == 1)
    row = await broadcast.get(int(await db.get_setting("announce_v1")))
    check("natija bazaga yozildi", row and row["blocked"] == 1 and row["sent"] >= 1 and row["finished_at"], str(row))
    check("adminga natija yuborildi", "E’lon yuborildi" in texts(ADMIN), texts(ADMIN))
    CALLS.clear()
    await press(ADMIN, "grow:ann:go")
    check("ikkinchi marta yuborilmaydi", not sent("SendMessage", 400))
    BLOCKED.discard(401)

    print("6. Eslatmalar")
    day = datetime(2026, 10, 22, 7, 0, tzinfo=timezone.utc)  # Toshkent 12:00
    r1 = 500
    await send(r1, "/start")
    await take(r1, "future", stop_at=7)
    await events.flush()

    async def age(uid: int, hours: float, *, progress_h: float | None = None, paywall_h: float | None = None):
        await conn.execute("UPDATE users SET last_seen = ? WHERE user_id = ?", (clock.iso(day - timedelta(hours=hours)), uid))
        if progress_h is not None:
            await conn.execute("UPDATE progress SET updated_at = ? WHERE user_id = ?",
                               (clock.iso(day - timedelta(hours=progress_h)), uid))
        if paywall_h is not None:
            await conn.execute("UPDATE events SET created_at = ? WHERE user_id = ? AND event = 'paywall_shown'",
                               (clock.iso(day - timedelta(hours=paywall_h)), uid))
        await conn.commit()

    await age(r1, 2, progress_h=2)
    check("2 soat — hali erta", await reminders.tick(bot, day) == 0)
    await age(r1, 4, progress_h=4)
    CALLS.clear()
    check("3 soatdan keyin — bitta eslatma", await reminders.tick(bot, day) == 1)
    rem = sent("SendMessage", r1)
    check("matn: «7-savolda to‘xtatdingiz», tugma resume:future",
          rem and "7-savolda to‘xtatdingiz" in rem[0].text
          and rem[0].reply_markup.inline_keyboard[0][0].callback_data == "resume:future", texts(r1))
    check("ikkinchi aylanishda takrorlanmaydi", await reminders.tick(bot, day) == 0)
    night = datetime(2026, 10, 22, 18, 30, tzinfo=timezone.utc)  # Toshkent 23:30
    r2 = 501
    await send(r2, "/start")
    await take(r2, "career", stop_at=3)
    await age(r2, 4, progress_h=4)
    check("23:00–08:00 — hech narsa yuborilmaydi", await reminders.tick(bot, night - timedelta(hours=0)) == 0
          and reminders.quiet(night))
    await conn.execute("UPDATE progress SET updated_at = ? WHERE user_id = ?", (clock.iso(day - timedelta(hours=50)), r2))
    await conn.commit()
    check("48 soatdan eski — yozilmaydi", await reminders.tick(bot, day) == 0)

    r3 = 502
    await send(r3, "/start")
    await take(r3, "career")
    await events.flush()
    await age(r3, 13, paywall_h=25)
    CALLS.clear()
    check("to‘liq tahlil oynasidan 24 soat o‘tib — bitta eslatma", await reminders.tick(bot, day) == 1)
    rem = sent("SendMessage", r3)
    check("bosimsiz matn va «Natijani ko‘rish» tugmasi", rem and "tayyor" in rem[0].text
          and rem[0].reply_markup.inline_keyboard[0][0].callback_data.startswith("rep:open:"), texts(r3))
    r4 = 503
    await send(r4, "/start")
    await take(r4, "career")
    await events.flush()
    await access.grant(r4, ["career"], "admin")
    await age(r4, 13, paywall_h=25)
    check("tahlil ochilgan bo‘lsa — eslatma yo‘q", await reminders.tick(bot, day) == 0)

    r5 = 504
    await send(r5, "/start")
    await take(r5, "future", stop_at=5)
    for i in range(2):
        await conn.execute("INSERT INTO auto_messages (user_id, kind, ref, sent_at) VALUES (?, 'paywall', ?, ?)",
                           (r5, f"x{i}", clock.iso(day - timedelta(days=2))))
    await conn.commit()
    await age(r5, 4, progress_h=4)
    check("7 kunda 2 tadan ortiq emas", await reminders.tick(bot, day) == 0)
    r6 = 505
    await send(r6, "/start")
    await take(r6, "future", stop_at=5)
    await press(r6, "rem:off")
    await age(r6, 4, progress_h=4)
    check("«Eslatma kerak emas» — yuborilmaydi", await reminders.tick(bot, day) == 0)
    r7 = 506
    await send(r7, "/start")
    await take(r7, "future", stop_at=5)
    await age(r7, 4, progress_h=4)
    await db.set_setting("reminders_on", "0")
    check("admin o‘chirsa — yuborilmaydi", await reminders.tick(bot, day) == 0)
    await db.set_setting("reminders_on", "1")
    BLOCKED.add(r7)
    await reminders.tick(bot, day)
    flag = (await (await conn.execute("SELECT is_blocked FROM users WHERE user_id = ?", (r7,))).fetchone())[0]
    check("bloklagan bo‘lsa — belgilanadi", flag == 1)
    BLOCKED.discard(r7)

    print("7. /stats")
    await events.flush()
    stats.drop_cache()
    text = stats.render(await stats.get("7d"))
    check("/stats: promo kodlar, solishtirish, eslatma, bepul ochilgan", "MAKTAB5 2 (Maktab 5)" in text
          and "Solishtirish: <b>2</b>" in text and "eslatma: <b>2</b>" in text and "bepul ochildi <b>2</b>" in text,
          text[-500:])
    check("/stats: yangi foydalanuvchi manbalari ichida promo_maktab5", "promo_maktab5" in text, text[:400])

    print()
    await db.close()
    if os.environ.get("DUMP"):
        with open(os.environ["DUMP"], "w", encoding="utf-8") as fh:
            fh.write("\n".join(LOG))
    if FAILURES:
        print(f"❌ {len(FAILURES)} ta muammo: {FAILURES}")
        return 1
    print("✅ 2-bosqich: hammasi ishlayapti.")
    return 0


sys.exit(asyncio.run(main()))
