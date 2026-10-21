"""1-bosqich tekshiruvi: test bepul, to'liq tahlil pullik.

Tekshiriladi: eski xaridorlar huquqi (migratsiya), bepul natija va qulflangan
qatorlar, to'liq tahlil, to'plam, karta cheki (admin tasdiqlaydi/rad etadi),
chekdan oldin ochish qoidalari, balans, Click bekor qilinishi, balans
to'ldirish xatosining tuzatilishi, davom ettirish (bot qayta ishga tushsa
ham), bosqich qatorlari, avtomatik til, halol arxetiplar.

Haqiqiy Telegram'siz: soxta sessiya, vaqtinchalik baza.

Ishlatish:  ./venv/bin/python phase1test.py
"""
import asyncio
import json
import os
import sys
import tempfile
from datetime import datetime

DB_FILE = tempfile.mktemp(suffix=".db")
os.environ.update(BOT_TOKEN="0:test", ADMIN_ID="1000001", DB_PATH=DB_FILE,
                  BOT_USERNAME="kelajak_test_bot", IQ_ANSWERS="ABCD" * 5,
                  CLICK_SERVICE_ID="1", CLICK_MERCHANT_ID="1", CLICK_SECRET_KEY="x",
                  PUBLIC_URL="https://example.test", MANUAL_RECEIPT_CHAT="@someone")

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.client.session.base import BaseSession
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import CallbackQuery, Chat, Message, PhotoSize, Update, User

import access
import database as db
import migrations
import profiles
import progress
import result_image as ri
import wallet
from handlers import build_router
from handlers import payment as payment_handlers
from handlers.growth import set_bot_username
from psytests import REGISTRY

ADMIN = 1000001
CALLS: list = []
FAILURES: list[str] = []
_ids = [100]


def check(label: str, ok: bool, detail: str = "") -> None:
    print(("  ✅ " if ok else "  ❌ ") + label + ("" if ok else f"  — {detail}"))
    if not ok:
        FAILURES.append(label)


def user(uid: int, lang: str = "uz") -> User:
    return User(id=uid, is_bot=False, first_name=f"U{uid}", language_code=lang)


def msg(uid: int, text: str | None = "x", photo: bool = False, lang: str = "uz") -> Message:
    _ids[0] += 1
    extra = {"photo": [PhotoSize(file_id=f"ph{_ids[0]}", file_unique_id="u", width=1, height=1)]} if photo else {}
    return Message(message_id=_ids[0], date=datetime.now(), chat=Chat(id=uid, type="private"),
                   from_user=user(uid, lang), text=None if photo else text, **extra)


class FakeSession(BaseSession):
    async def make_request(self, bot, method, timeout=None):
        name = type(method).__name__
        if name == "GetMe":
            return User(id=1, is_bot=True, first_name="Bot", username="kelajak_test_bot")
        CALLS.append((name, method))
        chat = getattr(method, "chat_id", None)
        if name in ("SendPhoto", "EditMessageMedia"):
            return msg(int(chat) if isinstance(chat, int) else 1, photo=True).as_(bot)
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


def last_markup():
    for n, m in reversed(CALLS):
        if n in ("SendMessage", "EditMessageText") and m.reply_markup:
            return [b for row in m.reply_markup.inline_keyboard for b in row]
    return []


def answers_for(key: str, level: int) -> list[int]:
    return [level] * REGISTRY[key].size


async def main() -> int:
    print("1. Eski xaridorlar (migratsiya 5)")
    await db.init()
    conn = await db.connect()
    await conn.execute("DELETE FROM schema_migrations WHERE version = 5")
    rows = [
        (10, "bigfive", "click", "paid"), (10, "iq", "wallet", "paid"), (11, "all", "click", "paid"),
        (12, "career", "click", "pending"), (13, "future", "click", "cancelled"),
        (14, "child", "manual", "paid"), (15, "wallet_topup", "manual_card", "paid"),
    ]
    for uid, product, method, status in rows:
        await conn.execute(
            "INSERT INTO payments (user_id, product, amount, method, status, created_at) VALUES (?, ?, 1000, ?, ?, 'x')",
            (uid, product, method, status))
    await conn.commit()
    before = await (await conn.execute("SELECT * FROM payments ORDER BY id")).fetchall()
    done = await migrations.run()
    check("migratsiya 5 bajarildi", done == [5], str(done))
    got = {(u, k) for u, k in await (await conn.execute("SELECT user_id, test_key FROM report_access")).fetchall()}
    check("sotib olgan test — to‘liq tahlil ochiq", {(10, "bigfive"), (10, "iq"), (14, "child")} <= got, str(got))
    check("«hamma test» paketi — 5 ta test", {(11, k) for k in access.TESTS} <= got, str(got))
    check("to‘lanmagan / bekor qilingan — huquq yo‘q", not {(12, "career"), (13, "future")} & got, str(got))
    check("balans to‘ldirish — test huquqi emas", not any(u == 15 for u, _ in got), str(got))
    check("to‘lovlar o‘zgarmadi", before == await (await conn.execute("SELECT * FROM payments ORDER BY id")).fetchall())
    check("qayta ishga tushganda takrorlanmaydi", await migrations.run() == [])

    bot = Bot("0:test", session=FakeSession(), default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)
    dp.include_router(build_router())
    set_bot_username("kelajak_test_bot")
    payment_handlers.set_bot(bot)
    upd = [0]

    async def send(uid: int, text: str, lang: str = "uz", dispatcher=None) -> None:
        upd[0] += 1
        await (dispatcher or dp).feed_update(bot, Update(update_id=upd[0], message=msg(uid, text, lang=lang)))

    async def photo(uid: int) -> None:
        upd[0] += 1
        await dp.feed_update(bot, Update(update_id=upd[0], message=msg(uid, photo=True)))

    async def press(uid: int, data: str, on_photo: bool = False, dispatcher=None, lang: str = "uz") -> None:
        upd[0] += 1
        cb = CallbackQuery(id=f"q{upd[0]}", from_user=user(uid, lang), chat_instance="ci", data=data,
                           message=msg(uid, "prev", photo=on_photo))
        await (dispatcher or dp).feed_update(bot, Update(update_id=upd[0], callback_query=cb))

    async def take(uid: int, key: str, level: int = 4) -> dict:
        await press(uid, f"go:{key}")
        test = REGISTRY[key]
        if test.ask_age:
            await press(uid, "age:" + ("k_7_10" if test.subject == "child" else "a_19_25"))
        for i, value in enumerate(answers_for(key, level)):
            await press(uid, f"ans:{key}:{i}:{value}")
        return await db.latest_result(uid, key)

    print("2. Avtomatik til va menyu")
    CALLS.clear()
    await send(20, "/start", lang="ru")
    check("ruscha Telegram → menyu ruscha, til so‘ralmadi", "Тесты мировой психологии" in texts(), texts()[:120])
    check("til bazaga yozildi (ru)", await db.get_lang(20) == "ru")
    CALLS.clear()
    await send(21, "/start", lang="en")
    check("boshqa til → o‘zbekcha", await db.get_lang(21) == "uz" and "Testni topshirish — bepul" in texts())
    labels = [b.text for b in last_markup()]
    check("tugmalar brief bo‘yicha: IQ birinchi, 5 test, Natijalarim, Do‘st", labels[0].startswith("🧩 IQ’ingiz qancha?")
          and "📈 Natijalarim" in labels and "🎁 Do‘stni taklif qilish" in labels and len(labels) == 9, str(labels))

    print("3. Bepul natija → to‘liq tahlil (Big Five)")
    u = 30
    await send(u, "/start")
    CALLS.clear()
    await press(u, "test:bigfive")
    card = texts()
    check("test oldidan: bepul va pullik qism, narx", "Bepul:" in card and "To‘liq tahlil — 9 900 so‘m" in card
          and "Validatsiyadan o‘tgan" in card, card)
    CALLS.clear()
    row = await take(u, "bigfive", level=3)
    free = sent("SendMessage", u)[-1].text
    check("bepul natija: arxetip, eng kuchli tomon, 4 ta qulf", "Shaxsiyat turingiz" in free and free.count("░░░░░ 🔒") == 4,
          free[-900:])
    check("bepul natijada to‘liq qism yo‘q", "XAVF ZONALARI" not in free and "█" not in free)
    buttons = last_markup()
    check("to‘lov tugmalari: tahlil, to‘plam, boshqa testlar",
          buttons[0].callback_data == f"rep:buy:{row['id']}" and buttons[1].callback_data == f"rep:bundle:{row['id']}"
          and buttons[-1].callback_data == "nav:menu", str([b.callback_data for b in buttons]))
    check("sertifikat bepul yuborildi", bool(sent("SendPhoto", u)))

    print("4. To‘plam (bundle)")
    CALLS.clear()
    await press(u, f"rep:bundle:{row['id']}")
    screen = texts()
    check("to‘plam narxi va alohida narx", "7 990" in screen and "alohida olinsa" in screen, screen)
    pay = (await db.recent_payments(1))[0]
    check("Click buyurtmasi to‘plamga", pay["product"] == "bundle" and pay["amount"] == 7990, str(pay))
    await db.mark_paid(pay["id"])
    CALLS.clear()
    await payment_handlers.notify_paid(pay["id"])
    check("to‘plam: 5 ta testning hammasi ochildi", await access.missing(u) == [], str(await access.missing(u)))
    check("to‘lovdan keyin Big Five to‘liq tahlili keldi", "XAVF ZONALARI" in texts() and "5 ta testning" in texts(),
          texts()[:300])
    CALLS.clear()
    await press(u, "test:career")
    check("boshqa test: «to‘liq tahlil sizda ochiq»", "sizda ochiq" in texts(), texts()[-150:])
    CALLS.clear()
    row2 = await take(u, "career")
    check("huquqi bor odam — darhol to‘liq tahlil", "MOS KASBLAR" in texts() and "QAYERDA O‘QISH" in texts(),
          texts()[-400:])

    print("5. Karta orqali: chek → admin tasdiqlaydi")
    v = 40
    await send(v, "/start")
    row = await take(v, "future")
    CALLS.clear()
    await press(v, f"rep:buy:{row['id']}")
    check("to‘lov ekrani: avval Click, keyin karta", [b.text for b in last_markup()][0].startswith("💳 Click")
          and "Karta" in [b.text for b in last_markup()][1], str([b.text for b in last_markup()]))
    CALLS.clear()
    await press(v, f"rep:card:future:{row['id']}")
    card_screen = texts()
    check("karta ekrani: summa, karta raqami (nusxa olinadi), chek so‘raladi",
          "9 900 so‘m o‘tkazing" in card_screen and "<code>" in card_screen and "chek" in card_screen, card_screen)
    check("summani yozish so‘ralmaydi", "raqamda yuboring" not in card_screen)
    CALLS.clear()
    await send(v, "to'ladim")
    check("matn yozsa — chekni rasm qilib yuborish so‘raladi", "rasm" in texts(), texts())
    CALLS.clear()
    await photo(v)
    check("foydalanuvchiga: qabul qilindi, 15 daqiqa, boshqa test taklifi",
          "15 daqiqa" in texts() and "bepul" in texts(), texts())
    admin_photo = sent("SendPhoto", ADMIN)
    check("chek adminga ID bo‘yicha yetdi (bir bosishda tasdiqlash tugmalari bilan)",
          admin_photo and "9 900" in admin_photo[0].caption
          and [b.callback_data for b in admin_photo[0].reply_markup.inline_keyboard[0]][0].startswith("rcpt:ok:"),
          str(admin_photo[:1]))
    check("hali ochilmadi (admin kutilmoqda)", not await access.has(v, "future"))
    pid = int(admin_photo[0].reply_markup.inline_keyboard[0][0].callback_data.split(":")[2])
    CALLS.clear()
    await press(ADMIN, f"rcpt:ok:{pid}", on_photo=True)
    check("tasdiqlandi → huquq", await access.has(v, "future"))
    check("foydalanuvchiga darhol xabar va to‘liq tahlil", "tasdiqlandi" in texts(v) and "USTIDA ISHLASH" in texts(v),
          texts(v)[:300])
    check("admin xabari yangilandi (tugmalar olindi)", sent("EditMessageCaption"))
    CALLS.clear()
    await press(ADMIN, f"rcpt:ok:{pid}", on_photo=True)
    check("ikkinchi marta tasdiqlab bo‘lmaydi", not sent("SendMessage", v))

    print("6. Chek rad etildi")
    w = 41
    await send(w, "/start")
    row = await take(w, "child")
    await press(w, f"rep:card:child:{row['id']}")
    await photo(w)
    pid = (await db.recent_payments(1))[0]["id"]
    CALLS.clear()
    await press(ADMIN, f"rcpt:no:{pid}", on_photo=True)
    rejected = sent("SendMessage", w)
    check("rad etildi: xabar va «qayta urinish» tugmasi",
          rejected and "tasdiqlanmadi" in rejected[-1].text
          and any((b.callback_data or "").startswith("rep:buy:") for r in rejected[-1].reply_markup.inline_keyboard for b in r),
          str(rejected[-1:]))
    check("huquq yo‘q", not await access.has(w, "child"))

    print("7. Chekdan oldin ochish (admin yoqsa)")
    await db.set_setting("optimistic_unlock", "1")
    x = 42
    await send(x, "/start")
    row = await take(x, "bigfive")
    await press(x, f"rep:card:bigfive:{row['id']}")
    CALLS.clear()
    await photo(x)
    check("≤ 5 000 so‘m bo‘lmasa — kutadi (Big Five 9 900)", not await access.has(x, "bigfive"))
    await db.set_price("bigfive", 2490)
    await press(x, f"rep:card:bigfive:{row['id']}")
    CALLS.clear()
    await photo(x)
    check("≤ 5 000 so‘m — chek kelishi bilan ochildi", await access.has(x, "bigfive"))
    check("foydalanuvchi to‘liq tahlilni ko‘rdi", "XAVF ZONALARI" in texts(x), texts(x)[:200])
    optimistic_pid = (await db.recent_payments(1))[0]["id"]
    row_iq = await db.latest_result(x, "bigfive")
    await db.set_price("career", 1990)
    crow = await take(x, "career")
    await press(x, f"rep:card:career:{crow['id']}")
    await photo(x)
    check("bir vaqtda faqat bitta tasdiqlanmagan ochilish", not await access.has(x, "career"))
    CALLS.clear()
    await press(ADMIN, f"rcpt:no:{optimistic_pid}", on_photo=True)
    check("rad etildi → yopildi", not await access.has(x, "bigfive"))
    check("foydalanuvchiga «tahlil yopildi»", "yopildi" in texts(x), texts(x))
    y_pid = None
    frow = await take(x, "future")
    await db.set_price("future", 1990)
    await press(x, f"rep:card:future:{frow['id']}")
    await photo(x)
    check("rad etilgandan keyin bu odamga chekdan oldin ochish yo‘q", not await access.has(x, "future"))
    await db.set_setting("optimistic_unlock", "0")
    del y_pid, row_iq

    print("8. Balansdan")
    z = 43
    await send(z, "/start")
    row = await take(z, "career")
    CALLS.clear()
    await press(z, f"rep:buy:{row['id']}")
    check("balans yo‘q — balans tugmasi yo‘q", not any("Balans" in b.text for b in last_markup()))
    await wallet.credit(z, 5000, "test", "t:1")
    CALLS.clear()
    await press(z, f"rep:buy:{row['id']}")
    wallet_button = next((b.callback_data for b in last_markup() if "Balans" in b.text), "")
    check("balans yetarli — «Balansdan to‘lash» tugmasi", wallet_button.startswith("rep:wallet:career:"), wallet_button)
    CALLS.clear()
    await press(z, wallet_button)
    check("balansdan ochildi va tahlil keldi", await access.has(z, "career") and "MOS KASBLAR" in texts(z))
    check("balans kamaydi", await wallet.balance(z) == 5000 - 1990, str(await wallet.balance(z)))

    print("9. Click bekor qilindi")
    pid = await db.create_payment(z, "iq", 4990, "click")
    await db.set_payment_note(pid, "ctx=0")
    CALLS.clear()
    await payment_handlers.notify_failed(pid)
    check("bitta aniq «qayta urinish» xabari", sent("SendMessage", z) and "o‘tmadi" in sent("SendMessage", z)[-1].text)

    print("10. Click orqali balans to‘ldirish (tuzatilgan xato)")
    pid = await db.create_payment(z, "wallet_topup_click", 10000, "click")
    await db.mark_paid(pid)
    before = await wallet.balance(z)
    await payment_handlers.notify_paid(pid)
    await payment_handlers.notify_paid(pid)  # Click takrorlasa ham bir marta
    check("webhook'dan keyin balansga tushdi (bir marta)", await wallet.balance(z) == before + 10000,
          str(await wallet.balance(z)))
    old = await db.create_payment(44, "wallet_topup_click", 15000, "click")
    await db.mark_paid(old)  # eski xato: to'langan, lekin balansga tushmagan
    CALLS.clear()
    await press(ADMIN, "adm:reconcile")
    check("admin: tushmagan to‘ldirish ko‘rindi", "15 000" in texts() and "1 ta" in texts(), texts())
    await press(ADMIN, "adm:reconcile:do")
    check("tushirildi", await wallet.balance(44) == 15000)
    await press(ADMIN, "adm:reconcile:do")
    check("qayta bosilsa ikki marta tushmaydi", await wallet.balance(44) == 15000)

    print("11. Davom ettirish (bot qayta ishga tushsa ham)")
    r = 50
    await send(r, "/start")
    await press(r, "go:bigfive")
    for i in range(12):
        await press(r, f"ans:bigfive:{i}:2")
    CALLS.clear()
    await press(r, "nav:cancel:bigfive")
    check("bekor qilish avval so‘raydi va saqlanishini aytadi", "saqlanadi" in texts(), texts())
    await press(r, "quit:yes:bigfive")
    resume = [b for b in last_markup() if (b.callback_data or "").startswith("resume:")]
    check("menyu tepasida «Testni davom ettirish (12/50)»", resume and "12/50" in resume[0].text
          and last_markup()[0].callback_data == "resume:bigfive", str([b.text for b in last_markup()]))
    storage.storage.clear()  # bot qayta ishga tushdi: FSM xotirasi bo'sh
    fresh = dp
    CALLS.clear()
    await press(r, "ans:bigfive:12:3", dispatcher=fresh)
    check("eski savol tugmasi ishladi — 14-savol", "Savol 14 / 50" in texts(), texts()[:120])
    saved = await progress.load(r, "bigfive")
    check("javoblar bazada", saved and len(saved["answers"]) == 13, str(saved)[:100])
    CALLS.clear()
    await press(r, "resume:bigfive", dispatcher=fresh)
    check("«davom ettirish» — 14-savol", "Savol 14 / 50" in texts(), texts()[:80])
    CALLS.clear()
    await press(r, "go:bigfive", dispatcher=fresh)
    check("«yangidan boshlash» — 1-savol, eski javoblar o‘chdi",
          "Savol 1 / 50" in texts() and (await progress.load(r, "bigfive"))["answers"] == [], texts()[:80])

    print("12. Bosqich qatorlari (25/50/75 %)")
    from handlers.user import question_text
    check("boshida qator yo‘q", "🔥" not in question_text("bigfive", 5, "uz") and "🏁" not in question_text("bigfive", 5, "uz"))
    check("25 %", "Chorak" in question_text("bigfive", 13, "uz"))
    check("50 %", "Yarmidan o‘tdingiz" in question_text("bigfive", 25, "uz"))
    check("75 %", "Oz qoldi" in question_text("bigfive", 40, "uz"))
    check("ruscha", "половину" in question_text("bigfive", 25, "ru"))

    print("13. Halol arxetiplar")
    low = {k: 30 for k in REGISTRY["bigfive"].scales}
    check("Big Five: hamma past → «Muvozanatli shaxs»",
          profiles.archetype("bigfive", low).name["uz"] == "Muvozanatli shaxs")
    pair = {"E": 80, "A": 40, "C": 70, "S": 50, "O": 45}
    check("Big Five: ikkita yuqori → juftlik nomi", profiles.archetype("bigfive", pair).name["uz"] == "Tashabbuskor yetakchi")
    check("Kelajak: past → «Yo‘l boshida»",
          profiles.archetype("future", {k: 40 for k in REGISTRY["future"].scales}).name["uz"] == "Yo‘l boshida")
    check("IQ: tur yarmidan kam → kuchli nom yo‘q",
          profiles.archetype("iq", {"kinds": {"change": [1, 5], "rows": [2, 5], "spatial": [1, 5], "combine": [0, 5]}}).name["uz"]
          == "Yo‘l boshida")

    print("14. Natijalarim")
    CALLS.clear()
    await press(w, "nav:history")
    opens = [b.callback_data for b in last_markup() if (b.callback_data or "").startswith("rep:open:")]
    check("natijalar tugma bo‘lib chiqdi", bool(opens), str([b.text for b in last_markup()]))
    CALLS.clear()
    await press(w, opens[0])
    check("yopiq natija → bepul natija va to‘lov", "░░░░░" in texts() or "🔒" in texts(), texts()[:200])
    CALLS.clear()
    await press(v, "nav:history")
    vopen = next(b.callback_data for b in last_markup() if (b.callback_data or "").startswith("rep:open:"))
    CALLS.clear()
    await press(v, vopen)
    check("ochiq natija → to‘liq tahlil", "█" in texts(), texts()[:120])
    CALLS.clear()
    await press(w, vopen)
    check("birovning natijasini ochib bo‘lmaydi", "█" not in texts() and not sent("SendMessage", w))

    print("15. Farzand testi: sertifikatda bola ma’lumoti yo‘q")
    card = ri.build_card("child", 90, {k: 95 for k in REGISTRY["child"].scales}, "uz")
    check("neytral ota-ona kartasi", card.headline == "G‘amxo‘r ota-ona" and card.pill is None and card.stat is None,
          str(card))

    print("16. Admin: narxlar va to‘plam")
    CALLS.clear()
    await press(ADMIN, "adm:prices")
    labels = [b.text for b in last_markup()]
    check("narxlar ekranida to‘plam ham bor", any("to‘plami" in x for x in labels), str(labels))
    await press(ADMIN, "admprice:bundle")
    await send(ADMIN, "6990")
    check("to‘plam narxi o‘zgardi", await payment_handlers.price_for("bundle") == 6990)
    CALLS.clear()
    await press(ADMIN, "adm:pay")
    check("«Chekdan oldin ochish» odatda o‘chiq", any("Chekdan oldin ochish: o‘chiq" in b.text for b in last_markup()),
          str([b.text for b in last_markup()]))

    await bot.session.close()
    print()
    if FAILURES:
        print(f"❌ {len(FAILURES)} ta muammo: {FAILURES}")
        return 1
    print("✅ 1-bosqich joyida.")
    return 0


async def _guarded() -> int:
    try:
        return await main()
    finally:
        import events
        await events.flush()
        await db.close()


sys.exit(asyncio.run(_guarded()))
