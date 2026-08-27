"""Uchidan-uchiga tekshiruv: butun bot oqimi haqiqiy Telegram'siz sinaladi.

Telegram API o'rniga soxta sessiya qo'yiladi, baza vaqtinchalik faylga
yoziladi — skript hech kimga xabar yubormaydi va haqiqiy bazaga tegmaydi.

Ishlatish:  ./venv/bin/python flowtest.py
"""
import asyncio
import os
import sys
import tempfile

os.environ["BOT_TOKEN"] = "0:test"
os.environ["ADMIN_ID"] = "1000001"
os.environ["DB_PATH"] = tempfile.mktemp(suffix=".db")

# To'lov oqimini ham sinash uchun Click sozlangandek ko'rsatamiz. Haqiqiy
# Click serveriga murojaat qilinmaydi — protokolning o'zi clicktest.py da
# tekshiriladi, bu yerda faqat botning xatti-harakati muhim.
os.environ.update(
    CLICK_SERVICE_ID="110965",
    CLICK_MERCHANT_ID="64192",
    CLICK_SECRET_KEY="test-secret",
    PUBLIC_URL="https://example.test",
)

#: Sinov uchun soxta foydalanuvchi — haqiqiy Telegram ID emas.
TEST_USER = 1000001

from datetime import datetime

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.client.session.base import BaseSession
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import CallbackQuery, Chat, Message, Update, User

import database as db
from config import ADMIN_ID
from psytests import REGISTRY

CALLS: list = []
STATE = {"user": None, "chat": None}
_counter = [1000]
FAILURES: list[str] = []


def as_user(uid: int, name: str = "Test") -> None:
    STATE["user"] = User(id=uid, is_bot=False, first_name=name, language_code="uz")
    STATE["chat"] = Chat(id=uid, type="private")


def _msg(text: str = "x") -> Message:
    _counter[0] += 1
    return Message(
        message_id=_counter[0], date=datetime.now(),
        chat=STATE["chat"], from_user=STATE["user"], text=text,
    )


class FakeSession(BaseSession):
    async def make_request(self, bot, method, timeout=None):
        name = type(method).__name__
        CALLS.append((name, method))
        if name in ("SendMessage", "EditMessageText", "CopyMessage"):
            return _msg(getattr(method, "text", "") or "")
        if name == "GetMe":
            return User(id=1, is_bot=True, first_name="Bot", username="test_bot")
        return True

    async def stream_content(self, *a, **k):
        yield b""

    async def close(self):
        pass


def last(name: str):
    for call_name, method in reversed(CALLS):
        if call_name == name:
            return method
    return None


def last_text() -> str:
    for call_name, method in reversed(CALLS):
        if call_name in ("SendMessage", "EditMessageText"):
            return method.text or ""
    return ""


def all_text() -> str:
    return "\n".join(
        m.text or "" for n, m in CALLS if n in ("SendMessage", "EditMessageText")
    )


def buttons() -> list:
    for call_name, method in reversed(CALLS):
        if call_name in ("SendMessage", "EditMessageText") and method.reply_markup:
            return [b for row in method.reply_markup.inline_keyboard for b in row]
    return []


def check(label: str, ok: bool, detail: str = "") -> None:
    print(("  ✅ " if ok else "  ❌ ") + label + ("" if ok else f"  — {detail}"))
    if not ok:
        FAILURES.append(label)


async def send(dp, bot, text: str) -> None:
    await dp.feed_update(bot, Update(update_id=len(CALLS) + 1, message=_msg(text)))


async def press(dp, bot, data: str) -> None:
    cb = CallbackQuery(
        id=str(len(CALLS)), from_user=STATE["user"], chat_instance="ci",
        data=data, message=_msg("oldingi"),
    )
    await dp.feed_update(bot, Update(update_id=len(CALLS) + 1, callback_query=cb))


async def take_test(dp, bot, key: str, perfect: bool = True) -> None:
    """Testni to'liq topshiradi. perfect=True — teskari savollarni hisobga olib."""
    test = REGISTRY[key]
    for i, item in enumerate(test.items):
        value = (0 if item.reverse else test.max_answer) if perfect else 2
        await press(dp, bot, f"ans:{i}:{value}")


async def main() -> int:
    from handlers import build_router  # config o'qilgandan keyin

    await db.init()
    bot = Bot("0:test", session=FakeSession(),
              default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher(storage=MemoryStorage())
    dp.include_router(build_router())

    as_user(TEST_USER)

    # --- 1. Birinchi kirish: til so'raladi ---------------------------------
    print("1. Til tanlash")
    await send(dp, bot, "/start")
    check("til so‘raldi", "Tilni tanlang" in last_text(), last_text()[:60])
    check("ikkita til tugmasi", len(buttons()) == 2, str(len(buttons())))
    await press(dp, bot, "lang:uz")
    check("menyu o‘zbekcha", "Psixologik testlar" in last_text(), last_text()[:60])
    check("menyuda 4 test + 3 tugma", len(buttons()) == 7, str(len(buttons())))
    check("til bazaga yozildi", await db.get_lang(TEST_USER) == "uz")

    # --- 2. Big Five: kartochka, manba, to'liq test ------------------------
    print("2. Big Five (50 savol, validatsiyalangan)")
    await press(dp, bot, "test:bigfive")
    check("kartochka ochildi", "50 ta savol" in last_text(), last_text()[-80:])
    check("validatsiya belgisi bor", "Validatsiyadan o‘tgan" in last_text())
    await press(dp, bot, "src:bigfive")
    check("manba ko‘rsatildi", "IPIP" in last_text() and "Goldberg" in last_text())
    check("public domain aytilgan", "ochiq mulk" in last_text())
    await press(dp, bot, "go:bigfive")
    check("yosh so‘ralmadi, savol boshlandi", "Savol 1 / 50" in last_text(),
          last_text()[:60])
    await take_test(dp, bot, "bigfive")
    result = all_text()
    check("profil chiqdi (daraja so‘zlari bilan)",
          "yuqori" in result and "█" in result, result[:120])
    check("umumiy ball yo‘q", "/ 100" not in result, result[:120])
    check("beshta shkala bor", all(
        n in result for n in ("Ekstraversiya", "Kelishuvchanlik", "Vijdonlilik",
                              "Hissiy barqarorlik", "Ochiqlik")))
    check("ogohlantirish bor", "tashxis emas" in result)
    history = await db.user_history(TEST_USER)
    check("natija saqlandi", len(history) == 1 and history[0]["test_key"] == "bigfive")
    check("Big Five uchun umumiy ball saqlanmadi", history[0]["total"] is None)

    # --- 3. Kelajak salohiyati: yosh + indeks ------------------------------
    print("3. Kelajak salohiyati (28 savol, indeks)")
    CALLS.clear()
    await press(dp, bot, "test:future")
    check("mualliflik belgisi bor", "Mualliflik so‘rovnomasi" in last_text())
    await press(dp, bot, "go:future")
    check("yosh so‘raldi", "Yoshingizni" in last_text(), last_text()[:50])
    await press(dp, bot, "age:a_19_25")
    check("savol boshlandi", "Savol 1 / 28" in last_text())
    check("javob tugmalari 6 ta", len(buttons()) == 6, str(len(buttons())))
    await take_test(dp, bot, "future")
    result = all_text()
    check("umumiy ball chiqdi", "100 / 100" in result, result[-200:])
    check("yosh maslahati bor", "Yoshingizga mos" in result)
    check("kuchli tomonlar bor", "KUCHLI TOMONLAR" in result)
    saved = (await db.user_history(TEST_USER))[0]
    check("ball saqlandi", saved["total"] == 100.0, str(saved["total"]))
    check("yosh guruhi saqlandi", saved["age_group"] == "a_19_25")

    # --- 4. Orqaga va ikki marta bosish ------------------------------------
    print("4. Orqaga va ikki marta bosish")
    CALLS.clear()
    await press(dp, bot, "go:career")
    await press(dp, bot, "ans:0:4")
    await press(dp, bot, "ans:1:4")
    check("3-savolda", "Savol 3 / 30" in last_text(), last_text()[:40])
    await press(dp, bot, "back")
    check("orqaga → 2-savol", "Savol 2 / 30" in last_text(), last_text()[:40])
    CALLS.clear()
    await press(dp, bot, "ans:0:4")
    check("eski tugma e’tiborsiz qoldirildi",
          last("AnswerCallbackQuery") is not None
          and "javob berilgan" in (last("AnswerCallbackQuery").text or ""),
          str(last("AnswerCallbackQuery")))

    # --- 5. Kasb yo'nalishi to'liq -----------------------------------------
    print("5. Kasb yo‘nalishi (RIASEC)")
    CALLS.clear()
    await press(dp, bot, "nav:cancel")
    await press(dp, bot, "go:career")
    test = REGISTRY["career"]
    for i, item in enumerate(test.items):
        # Faqat "S" (ijtimoiy) yo'nalishga yuqori baho beramiz.
        await press(dp, bot, f"ans:{i}:{4 if item.scale == 'S' else 0}")
    result = all_text()
    check("Holland kodi chiqdi", "SIZNING KODINGIZ" in result)
    check("S birinchi o‘rinda", "KODINGIZ: S" in result, result[:200])
    check("kasblar ro‘yxati bor", "o‘qituvchi" in result or "psixolog" in result)

    # --- 6. Farzand testi ---------------------------------------------------
    print("6. Farzand salohiyati")
    CALLS.clear()
    await press(dp, bot, "go:child")
    check("bola yoshi so‘raldi", "Farzandingiz nechchi yoshda" in last_text())
    await press(dp, bot, "age:k_7_10")
    await take_test(dp, bot, "child")
    check("farzand maslahati bor", "Farzandingiz yoshiga mos" in all_text())

    # --- 7. Tarix -----------------------------------------------------------
    print("7. Tarix")
    CALLS.clear()
    await press(dp, bot, "nav:history")
    text = last_text()
    check("4 ta natija ko‘rinadi", text.count("<b>") >= 5, text[:200])
    check("Big Five ballsiz ko‘rsatilgan", "ball" in text)

    # --- 8. Rus tili --------------------------------------------------------
    print("8. Rus tiliga o‘tish")
    CALLS.clear()
    await send(dp, bot, "/til")
    await press(dp, bot, "lang:ru")
    check("menyu ruscha", "Психологические тесты" in last_text(), last_text()[:60])
    check("til yangilandi", await db.get_lang(TEST_USER) == "ru")
    await press(dp, bot, "test:future")
    check("kartochka ruscha", "Авторский опросник" in last_text(), last_text()[-100:])
    await press(dp, bot, "src:future")
    check("manba ruscha", "Duckworth" in last_text() and "опросник" in last_text())
    await press(dp, bot, "go:future")
    check("yosh ruscha so‘raldi", "Выберите свой возраст" in last_text())
    await press(dp, bot, "age:a_26_35")
    check("savol ruscha", "Вопрос 1 / 28" in last_text(), last_text()[:50])
    CALLS.clear()
    await take_test(dp, bot, "future")
    result = all_text()
    check("natija ruscha", "100 / 100" in result and "Очень высокий" in result,
          result[:120])
    check("ruscha maslahat", "Совет по вашему возрасту" in result)
    check("ruscha ogohlantirish", "не предсказание" in result, result[-200:])
    await press(dp, bot, "nav:about")
    check("«bot haqida» ruscha", "О боте" in last_text())

    # --- 9. Test paytida matn yozish ---------------------------------------
    print("9. Test paytida matn yuborish")
    CALLS.clear()
    await press(dp, bot, "go:career")
    await send(dp, bot, "salom")
    check("tugma bosish so‘raldi (ruscha)", "выберите один из вариантов" in
          last_text().lower(), last_text()[:60])
    await send(dp, bot, "/bekor")
    check("/bekor ishladi", "отменён" in last_text().lower(), last_text()[:60])

    # --- 10. Tugagan testdagi eski tugma -----------------------------------
    print("10. Eski tugma")
    CALLS.clear()
    await press(dp, bot, "ans:5:4")
    alert = last("AnswerCallbackQuery")
    check("ogohlantirish chiqdi",
          alert is not None and "уже завершён" in (alert.text or ""), str(alert))

    # --- 11. Admin ----------------------------------------------------------
    print("11. Admin panel")
    check("ADMIN_ID muhitdan olindi", ADMIN_ID == TEST_USER, str(ADMIN_ID))
    CALLS.clear()
    await send(dp, bot, "/admin")
    check("panel ochildi", "Admin panel" in last_text())
    await press(dp, bot, "adm:stats")
    stats = last_text()
    check("statistika chiqdi", "Foydalanuvchilar" in stats, stats[:60])
    check("til bo‘yicha bo‘lingan", "🇺🇿" in stats and "🇷🇺" in stats)
    check("testlar bo‘yicha bo‘lingan", "Big Five" in stats, stats[-200:])
    await press(dp, bot, "adm:broadcast")
    check("kimga yuborish so‘raldi", "Kimga yuboramiz" in last_text())
    await press(dp, bot, "admto:ru")
    check("ruscha tanlandi", "ruscha" in last_text())
    await send(dp, bot, "Salom!")
    check("tasdiq so‘raldi", "Tasdiqlaysizmi" in last_text(), last_text()[:80])
    CALLS.clear()
    await press(dp, bot, "adm:send")
    check("copy_message chaqirildi", last("CopyMessage") is not None)
    check("hisobot chiqdi", "Yuborish tugadi" in last_text(), last_text()[:60])

    # --- 12. Oddiy foydalanuvchi -------------------------------------------
    print("12. Oddiy foydalanuvchi")
    as_user(999, "Oddiy")
    CALLS.clear()
    await send(dp, bot, "/admin")
    check("admin panel ochilmadi", "Admin panel" not in last_text(), last_text()[:60])
    check("yangi foydalanuvchidan til so‘raldi", "Tilni tanlang" in last_text())
    await press(dp, bot, "lang:ru")
    await press(dp, bot, "test:bigfive")
    check("yangi foydalanuvchi ruscha ko‘rdi", "50 вопросов" in last_text(),
          last_text()[-80:])

    # --- 13. To'lov to'sig'i ------------------------------------------------
    # Eng muhim qism: pul to'lanmaguncha test ochilmasligi kerak.
    print("13. To‘lov to‘sig‘i")
    as_user(999, "Oddiy")
    CALLS.clear()
    await press(dp, bot, "lang:uz")
    await press(dp, bot, "test:bigfive")
    card = last_text()
    check("kartochkada narx bor", "Narxi" in card, card[-120:])
    labels = [b.text for b in buttons()]
    check("«To‘lash» tugmasi chiqdi",
          any("to‘lash" in x.lower() for x in labels), str(labels))
    check("«Boshlash» tugmasi yo‘q",
          not any("Boshlash" in x for x in labels), str(labels))

    CALLS.clear()
    await press(dp, bot, "go:bigfive")
    wall = last_text()
    check("test o‘rniga paywall chiqdi", "Bu test pullik" in wall, wall[:80])
    check("savol berilmadi", "Savol 1" not in all_text())

    CALLS.clear()
    await press(dp, bot, "pay:bigfive")
    pay_text = last_text()
    check("to‘lov ekrani ochildi", "Buyurtma" in pay_text, pay_text[:80])
    urls = [b.url for b in buttons() if b.url]
    check("my.click.uz havolasi berildi",
          any("my.click.uz" in (u or "") for u in urls), str(urls))

    payment = (await db.recent_payments(1))[0]
    check("to‘lov bazaga yozildi",
          payment["user_id"] == 999 and payment["status"] == "pending", str(payment))

    CALLS.clear()
    await press(dp, bot, "ans:0:4")
    check("to‘lovsiz savolga javob berib bo‘lmadi", "Savol 2" not in all_text())

    # Click "to'landi" dedi — endi ochilishi kerak.
    await db.mark_paid(payment["id"])
    check("huquq berildi", await db.has_access(999, "bigfive"))

    CALLS.clear()
    await press(dp, bot, "go:bigfive")
    # Big Five yosh so'ramaydi — to'lovdan keyin darrov savolga o'tadi.
    check("test ochildi va savol berildi", "Savol 1" in last_text(), last_text()[:60])
    await press(dp, bot, "ans:0:4")
    check("javob qabul qilindi", "Savol 2" in last_text(), last_text()[:60])

    CALLS.clear()
    await press(dp, bot, "pay:bigfive")
    alert = last("AnswerCallbackQuery")
    check("ikkinchi marta pul so‘ralmadi",
          alert is not None and "allaqachon ochiq" in (alert.text or ""), str(alert))
    check("yangi buyurtma ochilmadi",
          len(await db.recent_payments(10)) == 1, str(await db.recent_payments(10)))

    CALLS.clear()
    await press(dp, bot, "test:career")
    check("boshqa test hamon yopiq", "Narxi" in last_text(), last_text()[-80:])

    # --- 14. Sinov rejimi ---------------------------------------------------
    # Admin odatda to'siqni ko'rmaydi — bu tugma uni ham to'siq ortiga qo'yadi,
    # aks holda to'lov oqimini o'z akkauntida sinab bo'lmaydi.
    print("14. Admin sinov rejimi")
    as_user(TEST_USER)
    # Bu foydalanuvchi 9-bo'limda ruschaga o'tgan edi — tekshiruvlar
    # o'zbekcha matnga tayanadi, shuning uchun tilni qaytaramiz.
    await press(dp, bot, "lang:uz")
    CALLS.clear()
    await press(dp, bot, "test:career")
    check("admin to‘siqni ko‘rmaydi", "Narxi" not in last_text(), last_text()[-60:])

    await press(dp, bot, "adm:testmode")
    check("sinov rejimi yoqildi", await db.admin_pays())
    CALLS.clear()
    await press(dp, bot, "test:career")
    check("endi admin ham narxni ko‘radi", "Narxi" in last_text(), last_text()[-60:])
    CALLS.clear()
    await press(dp, bot, "go:career")
    check("admin ham to‘siqqa uchradi", "Bu test pullik" in last_text(),
          last_text()[:60])

    await press(dp, bot, "adm:testmode")
    check("sinov rejimi o‘chirildi", not await db.admin_pays())
    CALLS.clear()
    await press(dp, bot, "go:career")
    check("admin uchun yana ochiq", "Savol 1" in last_text(), last_text()[:60])

    await bot.session.close()
    await db.close()

    print()
    if FAILURES:
        print(f"❌ {len(FAILURES)} ta muammo: {FAILURES}")
        return 1
    print("✅ Hammasi ishladi.")
    return 0


sys.exit(asyncio.run(main()))
