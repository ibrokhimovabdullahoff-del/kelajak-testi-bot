"""Admin: 🚀 O'sish — do'st mukofoti, eslatmalar, promo kodlar, bir martalik e'lon.

Hamma sozlama bazada (settings) — kodga tegmasdan admin paneldan o'zgaradi:
  ref_reward_on / ref_reward_cap — do'st mukofoti va oylik chegara;
  reminders_on                   — avtomatik eslatmalar;
  announce_v1                    — yangilik e'loni yuborilgan broadcast raqami.
"""
from __future__ import annotations

import asyncio
import html
import logging
from datetime import timedelta

from aiogram import Bot, F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, LinkPreviewOptions, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder

import access
import broadcast
import clock
import database as db
import promo
import referral_rewards
import reminders
from locales import t

from .admin import IsAdmin
from .growth import bot_username
from .reports import test_title

log = logging.getLogger(__name__)
router = Router()
router.message.filter(IsAdmin())
router.callback_query.filter(IsAdmin())

ANNOUNCE_KEY = "announce_v1"
_announce_lock = asyncio.Lock()


def _on(flag: bool) -> str:
    return "<b>YOQIQ</b>" if flag else "<b>o‘chiq</b>"


async def _count(query: str, args: tuple = ()) -> int:
    conn = await db.connect()
    cursor = await conn.execute(query, args)
    row = await cursor.fetchone()
    return int(row[0] or 0) if row else 0


async def _home_text() -> str:
    ref_on, cap = await referral_rewards.enabled(), await referral_rewards.cap()
    month = await _count("SELECT COUNT(*) FROM referral_rewards WHERE month = ? AND status = 'rewarded'",
                         (clock.month_key(),))
    week = await _count("SELECT COUNT(*) FROM auto_messages WHERE kind != 'optout' AND ok = 1 AND sent_at >= ?",
                        (clock.iso(clock.utc_now() - timedelta(days=7)),))
    codes = await _count("SELECT COUNT(*) FROM promo_codes WHERE active = 1")
    sent = await db.get_setting(ANNOUNCE_KEY)
    if sent and sent.isdigit() and (row := await broadcast.get(int(sent))):
        ann = f"✅ yuborilgan ({(row['started_at'] or '')[:10]}) — yetdi {row['sent']}, bloklagan {row['blocked']}"
    else:
        ann = "hali yuborilmagan"
    return "\n".join([
        "🚀 <b>O‘sish</b>", "",
        f"🎁 Do‘st mukofoti: {_on(ref_on)} · oyiga {cap} tagacha",
        f"   Do‘sti testni tugatsa — taklif qilganga 1 ta bepul to‘liq tahlil. Shu oy berildi: <b>{month}</b>",
        "",
        f"🔔 Eslatmalar: {_on(await reminders.enabled())}",
        "   Tashlab ketilgan test — 3 soatdan keyin, ochilmagan to‘liq tahlil — 24 soatdan keyin. "
        "7 kunda 2 tadan ko‘p emas, 23:00–08:00 da yuborilmaydi.",
        f"   Oxirgi 7 kunda: <b>{week}</b>",
        "",
        f"🎟 Faol promo kodlar: <b>{codes}</b>",
        f"📣 Yangilik e’loni: {ann}",
    ])


async def _home_markup():
    b = InlineKeyboardBuilder()
    b.button(text=("🎁 Do‘st mukofoti: YOQIQ" if await referral_rewards.enabled() else "🎁 Do‘st mukofoti: o‘chiq"),
             callback_data="grow:ref")
    b.button(text=f"🔢 Oylik chegara: {await referral_rewards.cap()}", callback_data="grow:cap")
    b.button(text=("🔔 Eslatmalar: YOQIQ" if await reminders.enabled() else "🔔 Eslatmalar: o‘chiq"),
             callback_data="grow:rem")
    b.button(text="🎟 Promo kodlar", callback_data="promo:list")
    b.button(text="📣 Yangilik e’loni (bir martalik)", callback_data="grow:ann")
    b.button(text="⬅️ Admin panel", callback_data="adm:home")
    b.adjust(1)
    return b.as_markup()


async def _draw(callback: CallbackQuery) -> None:
    await callback.message.edit_text(await _home_text(), reply_markup=await _home_markup())


@router.callback_query(F.data == "grow:home")
async def home(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await _draw(callback)


@router.callback_query(F.data == "grow:ref")
async def toggle_ref(callback: CallbackQuery) -> None:
    await db.set_setting("ref_reward_on", "0" if await referral_rewards.enabled() else "1")
    await _draw(callback)


@router.callback_query(F.data == "grow:rem")
async def toggle_rem(callback: CallbackQuery) -> None:
    await db.set_setting("reminders_on", "0" if await reminders.enabled() else "1")
    await _draw(callback)


class Cap(StatesGroup):
    waiting = State()


@router.callback_query(F.data == "grow:cap")
async def ask_cap(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(Cap.waiting)
    await callback.message.edit_text("🔢 Bitta odam oyiga nechta do‘st mukofoti olishi mumkin? Raqam yuboring "
                                     "(masalan, 10).\nBekor qilish: /bekor")


@router.message(Cap.waiting, Command("bekor"))
async def cancel_cap(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer(await _home_text(), reply_markup=await _home_markup())


@router.message(Cap.waiting)
async def save_cap(message: Message, state: FSMContext) -> None:
    raw = (message.text or "").strip()
    if not raw.isdigit() or not 0 < int(raw) <= 1000:
        await message.answer("1 dan 1000 gacha raqam yuboring.")
        return
    await state.clear()
    await db.set_setting("ref_reward_cap", str(int(raw)))
    await message.answer(await _home_text(), reply_markup=await _home_markup())


# --- Promo kodlar -------------------------------------------------------------


def _describe(row: dict) -> str:
    if row["kind"] == promo.DISCOUNT:
        what = f"{row['percent']}% chegirma"
    else:
        what = "bepul: " + ", ".join(test_title(k, "uz") for k in promo.tests_of(row))
    limit = f"{row['uses']}/{row['max_uses']}" if row["max_uses"] else f"{row['uses']}/∞"
    until = f" · {row['expires_at'][:10]} gacha" if row.get("expires_at") else ""
    label = f" · {html.escape(row['label'])}" if row.get("label") else ""
    mark = "🟢" if row["active"] else "🔴"
    return f"{mark} <code>{row['code'].upper()}</code> — {what} · {limit}{until}{label}"


@router.callback_query(F.data == "promo:list")
async def promo_list(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    rows = await promo.all_codes()
    lines = ["🎟 <b>Promo kodlar</b>", "",
             "Odam kodni havola orqali yoki /promo KOD bilan kiritadi. Bitta odam bitta kodni bir marta ishlatadi.",
             ""]
    lines += [_describe(r) for r in rows] or ["Hali kod yo‘q."]
    b = InlineKeyboardBuilder()
    b.button(text="➕ Yangi promo kod", callback_data="promo:new")
    for row in rows[:20]:
        b.button(text=row["code"].upper(), callback_data=f"promo:view:{row['code']}")
    b.button(text="⬅️ O‘sish", callback_data="grow:home")
    b.adjust(1)
    await callback.message.edit_text("\n".join(lines), reply_markup=b.as_markup())


async def _view(message: Message, code: str, edit: bool = True) -> None:
    row = await promo.get(code)
    if row is None:
        return
    link = f"https://t.me/{bot_username()}?start=promo_{code}" if bot_username() else "—"
    text = "\n".join([_describe(row), "", f"Havola: {link}",
                      f"Yoki botda: <code>/promo {code.upper()}</code>"])
    b = InlineKeyboardBuilder()
    b.button(text="🔴 O‘chirish" if row["active"] else "🟢 Yoqish", callback_data=f"promo:toggle:{code}")
    b.button(text="⬅️ Promo kodlar", callback_data="promo:list")
    b.adjust(1)
    preview = LinkPreviewOptions(is_disabled=True)
    if edit:
        await message.edit_text(text, reply_markup=b.as_markup(), link_preview_options=preview)
    else:
        await message.answer(text, reply_markup=b.as_markup(), link_preview_options=preview)


@router.callback_query(F.data.startswith("promo:view:"))
async def promo_view(callback: CallbackQuery) -> None:
    await _view(callback.message, callback.data.split(":", 2)[2])


@router.callback_query(F.data.startswith("promo:toggle:"))
async def promo_toggle(callback: CallbackQuery) -> None:
    code = callback.data.split(":", 2)[2]
    row = await promo.get(code)
    if row:
        await promo.set_active(code, not row["active"])
        await _view(callback.message, code)


class NewPromo(StatesGroup):
    code = State()
    kind = State()
    value = State()
    tests = State()
    uses = State()
    days = State()
    label = State()


def _tests_markup(chosen: list[str]):
    b = InlineKeyboardBuilder()
    for key in access.TESTS:
        b.button(text=("✅ " if key in chosen else "▫️ ") + test_title(key, "uz"), callback_data=f"pnew:t:{key}")
    b.button(text="Hammasi", callback_data="pnew:t:all")
    b.button(text="➡️ Tayyor", callback_data="pnew:t:done")
    b.adjust(1)
    return b.as_markup()


@router.callback_query(F.data == "promo:new")
async def new_code(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await state.set_state(NewPromo.code)
    await callback.message.edit_text("🎟 <b>Yangi promo kod</b> (1/6)\n\nKod nomini yuboring: lotin harflari va "
                                     "raqamlar, 3–24 belgi. Masalan: <code>MAKTAB5</code>\nBekor qilish: /bekor")


@router.message(NewPromo.code, Command("bekor"))
@router.message(NewPromo.value, Command("bekor"))
@router.message(NewPromo.uses, Command("bekor"))
@router.message(NewPromo.days, Command("bekor"))
@router.message(NewPromo.label, Command("bekor"))
async def cancel_new(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer("❌ Bekor qilindi.", reply_markup=await _home_markup())


@router.message(NewPromo.code)
async def got_code(message: Message, state: FSMContext) -> None:
    code = promo.normalize(message.text)
    if code is None:
        await message.answer("Faqat lotin harflari va raqamlar, 3–24 belgi. Qayta yuboring.")
        return
    if await promo.get(code):
        await message.answer("Bunday kod allaqachon bor. Boshqa nom yuboring.")
        return
    await state.update_data(code=code)
    await state.set_state(NewPromo.kind)
    b = InlineKeyboardBuilder()
    b.button(text="💸 Chegirma (%)", callback_data="pnew:k:discount")
    b.button(text="🎁 Bepul to‘liq tahlil", callback_data="pnew:k:free")
    b.adjust(1)
    await message.answer(f"🎟 <code>{code.upper()}</code> (2/6)\n\nTuri qanday?", reply_markup=b.as_markup())


@router.callback_query(NewPromo.kind, F.data.startswith("pnew:k:"))
async def got_kind(callback: CallbackQuery, state: FSMContext) -> None:
    kind = callback.data.rsplit(":", 1)[1]
    await state.update_data(kind=kind, tests=[])
    if kind == promo.DISCOUNT:
        await state.set_state(NewPromo.value)
        await callback.message.edit_text(f"💸 (3/6) Necha foiz chegirma? 1 dan {promo.MAX_PERCENT} gacha raqam yuboring.\n"
                                         "Chegirma odamning keyingi bitta to‘loviga ishlaydi.")
        return
    await state.set_state(NewPromo.tests)
    await callback.message.edit_text("🎁 (3/6) Qaysi testlarning to‘liq tahlili ochilsin? Tanlang va «Tayyor» ni bosing.",
                                     reply_markup=_tests_markup([]))


@router.message(NewPromo.value)
async def got_percent(message: Message, state: FSMContext) -> None:
    raw = (message.text or "").strip().rstrip("%")
    if not raw.isdigit() or not 1 <= int(raw) <= promo.MAX_PERCENT:
        await message.answer(f"1 dan {promo.MAX_PERCENT} gacha raqam yuboring.")
        return
    await state.update_data(percent=int(raw))
    await _ask_uses(message, state)


@router.callback_query(NewPromo.tests, F.data.startswith("pnew:t:"))
async def pick_tests(callback: CallbackQuery, state: FSMContext) -> None:
    choice = callback.data.rsplit(":", 1)[1]
    chosen = list((await state.get_data()).get("tests") or [])
    if choice == "done":
        if not chosen:
            await callback.answer("Kamida bitta testni tanlang.", show_alert=True)
            return
        await _ask_uses(callback.message, state)
        return
    if choice == "all":
        chosen = list(access.TESTS)
    elif choice in access.TESTS:
        chosen = [k for k in chosen if k != choice] if choice in chosen else [*chosen, choice]
    await state.update_data(tests=chosen)
    await callback.message.edit_reply_markup(reply_markup=_tests_markup(chosen))


async def _ask_uses(message: Message, state: FSMContext) -> None:
    await state.set_state(NewPromo.uses)
    await message.answer("👥 (4/6) Nechta odam ishlata oladi? Raqam yuboring (0 — cheksiz).")


@router.message(NewPromo.uses)
async def got_uses(message: Message, state: FSMContext) -> None:
    raw = (message.text or "").strip()
    if not raw.isdigit():
        await message.answer("Raqam yuboring (0 — cheksiz).")
        return
    await state.update_data(max_uses=int(raw))
    await state.set_state(NewPromo.days)
    await message.answer("📅 (5/6) Necha kun amal qiladi? Raqam yuboring (0 — muddatsiz).")


@router.message(NewPromo.days)
async def got_days(message: Message, state: FSMContext) -> None:
    raw = (message.text or "").strip()
    if not raw.isdigit():
        await message.answer("Raqam yuboring (0 — muddatsiz).")
        return
    await state.update_data(days=int(raw))
    await state.set_state(NewPromo.label)
    await message.answer("🏷 (6/6) Izoh — kim uchun? Masalan: <i>Najot ta’lim o‘quv markazi</i>. "
                         "Kerak bo‘lmasa, «-» yuboring.")


@router.message(NewPromo.label)
async def got_label(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    await state.clear()
    label = (message.text or "").strip()
    label = "" if label == "-" else label[:60]
    created = await promo.create(
        data["code"], data["kind"], percent=int(data.get("percent") or 0), tests=data.get("tests") or [],
        max_uses=int(data.get("max_uses") or 0), days=int(data.get("days") or 0), label=label,
        admin_id=message.from_user.id)
    if not created:
        await message.answer("Bunday kod allaqachon bor — yaratilmadi.", reply_markup=await _home_markup())
        return
    log.info("Promo kod yaratildi: %s (%s) — admin %s", data["code"], data["kind"], message.from_user.id)
    await message.answer("✅ Promo kod yaratildi.")
    await _view(message, data["code"], edit=False)


# --- Bir martalik yangilik e'loni ------------------------------------------------


def _announce_markup(lang: str):
    b = InlineKeyboardBuilder()
    b.button(text=t("btn_start_test", lang), callback_data="iq:card")
    return b.as_markup()


async def _recipients() -> list[int]:
    return await db.all_user_ids()


@router.callback_query(F.data == "grow:ann")
async def announce_preview(callback: CallbackQuery) -> None:
    b = InlineKeyboardBuilder()
    sent = await db.get_setting(ANNOUNCE_KEY)
    if sent:
        row = await broadcast.get(int(sent)) if sent.isdigit() else None
        text = ("📣 <b>Yangilik e’loni</b>\n\n✅ Allaqachon yuborilgan — bu e’lon bir martalik.\n\n"
                + (f"Sana: {(row['started_at'] or '')[:16]}\nJami: {row['total']} · yetdi: <b>{row['sent']}</b> · "
                   f"bloklagan: {row['blocked']} · xato: {row['failed']}" if row else
                   "Hozir yuborilmoqda (yoki bot yuborish paytida qayta ishga tushgan)."))
    else:
        users = await _recipients()
        text = ("📣 <b>Yangilik e’loni (bir martalik)</b>\n\n"
                "Har kim o‘z tilida oladi, ostida «▶️ Boshlash» tugmasi (IQ testi). Bloklaganlarga yuborilmaydi.\n\n"
                f"<b>O‘zbekcha:</b>\n<blockquote>{t('announce_text', 'uz')}</blockquote>\n"
                f"<b>Ruscha:</b>\n<blockquote>{t('announce_text', 'ru')}</blockquote>\n"
                f"Oluvchilar: <b>{len(users)}</b> ta")
        b.button(text=f"✅ Yuborish ({len(users)} ta)", callback_data="grow:ann:go")
    b.button(text="⬅️ O‘sish", callback_data="grow:home")
    b.adjust(1)
    await callback.message.edit_text(text, reply_markup=b.as_markup())


@router.callback_query(F.data == "grow:ann:go")
async def announce_send(callback: CallbackQuery, bot: Bot) -> None:
    if _announce_lock.locked() or await db.get_setting(ANNOUNCE_KEY):
        await callback.answer("E’lon allaqachon yuborilgan yoki yuborilmoqda.", show_alert=True)
        return
    await callback.message.edit_text("📤 E’lon yuborilmoqda… Tugagach, natijani shu yerga yozaman.")
    asyncio.get_running_loop().create_task(_announce(bot, callback.from_user.id, callback.message.chat.id))


async def _announce(bot: Bot, admin_id: int, chat_id: int) -> None:
    async with _announce_lock:
        if await db.get_setting(ANNOUNCE_KEY):
            return
        # Ikki marta yuborilmasin: boshlanishidan oldin belgi qo'yiladi.
        await db.set_setting(ANNOUNCE_KEY, "sending")

        async def send_one(user_id: int) -> None:
            lang = await db.get_lang(user_id) or "uz"
            await bot.send_message(user_id, t("announce_text", lang), reply_markup=_announce_markup(lang))

        counts = await broadcast.send_all(await _recipients(), send_one, kind="announce_v1",
                                          admin_id=admin_id, target="all")
        await db.set_setting(ANNOUNCE_KEY, str(counts["id"]))
    try:
        await bot.send_message(chat_id, "✅ <b>E’lon yuborildi</b>\n\n"
                               f"Jami: {counts['total']}\nYetdi: <b>{counts['sent']}</b>\n"
                               f"Bloklagan: <b>{counts['blocked']}</b>\nXato: <b>{counts['failed']}</b>",
                               reply_markup=await _home_markup())
    except Exception as exc:  # noqa: BLE001
        log.warning("E’lon natijasi adminga yetmadi: %s", exc)
