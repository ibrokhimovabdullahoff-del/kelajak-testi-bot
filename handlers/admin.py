"""Admin paneli: statistika, to'lovlar va ommaviy xabar.

Interfeys faqat o'zbekcha — uni faqat egasi ko'radi.
"""
from __future__ import annotations

import asyncio
import csv
import io
import logging

from aiogram import Bot, F, Router
from aiogram.exceptions import TelegramForbiddenError, TelegramRetryAfter
from aiogram.filters import BaseFilter, Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import BufferedInputFile, CallbackQuery, Message

import database as db
import keyboards as kb
from config import CLICK_ENABLED, DEFAULT_PRICE, DEFAULT_PRICE_ALL, is_admin
from locales import money, t, tr
from psytests import ORDER, REGISTRY

from . import payment

log = logging.getLogger(__name__)

TARGET_LABELS = {"all": "hamma", "uz": "o‘zbekcha", "ru": "ruscha"}


class IsAdmin(BaseFilter):
    async def __call__(self, event: Message | CallbackQuery) -> bool:
        return bool(event.from_user) and is_admin(event.from_user.id)


router = Router()
router.message.filter(IsAdmin())
router.callback_query.filter(IsAdmin())


class Broadcast(StatesGroup):
    waiting_target = State()
    waiting_message = State()
    waiting_confirm = State()


@router.message(Command("admin"))
async def cmd_admin(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer("🛠 <b>Admin panel</b>", reply_markup=kb.admin_menu())


@router.callback_query(F.data == "adm:stats")
async def show_stats(callback: CallbackQuery) -> None:
    data = await db.stats()

    lines = [
        "📊 <b>Statistika</b>",
        "",
        f"👥 Foydalanuvchilar: <b>{data['users']:.0f}</b>",
        f"🆕 Bugun qo‘shilgan: <b>{data['new_today']:.0f}</b>",
        f"🚫 Bloklaganlar: <b>{data['blocked']:.0f}</b>",
        f"🌐 Til: 🇺🇿 <b>{data['uz']:.0f}</b> · 🇷🇺 <b>{data['ru']:.0f}</b>",
        "",
        f"📝 Jami testlar: <b>{data['tests']:.0f}</b>",
        f"📅 Bugun: <b>{data['tests_today']:.0f}</b>",
        f"🟢 Hozir test yechayotganlar: <b>{await db.active_now():.0f}</b>",
    ]

    if data["per_test"]:
        lines += ["", "<b>Testlar bo‘yicha:</b>"]
        for row in data["per_test"]:
            test = REGISTRY.get(row["key"])
            title = tr(test.title, "uz") if test else row["key"]
            emoji = test.emoji if test else "•"
            line = f"{emoji} {title}: <b>{row['count']}</b> ta"
            if row["avg"] is not None:
                line += f" · o‘rtacha <b>{row['avg']:.1f}</b>"
            lines.append(line)

    daily = await db.daily(7)
    if daily:
        lines += ["", "<b>Oxirgi kunlar</b> (yangi / test):"]
        for day, users, results in daily:
            lines.append(f"<code>{day}</code>  {users} / {results}")

    await callback.message.edit_text("\n".join(lines), reply_markup=kb.admin_menu())
    await callback.answer()


# --- Ommaviy xabar ----------------------------------------------------------


@router.callback_query(F.data == "adm:broadcast")
async def ask_target(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(Broadcast.waiting_target)
    await callback.message.edit_text(
        "📣 Kimga yuboramiz?", reply_markup=kb.broadcast_targets()
    )
    await callback.answer()


@router.callback_query(Broadcast.waiting_target, F.data.startswith("admto:"))
async def ask_message(callback: CallbackQuery, state: FSMContext) -> None:
    target = callback.data.split(":", 1)[1]
    await state.update_data(target=target)
    await state.set_state(Broadcast.waiting_message)
    await callback.message.edit_text(
        f"📣 Yuboriladi: <b>{TARGET_LABELS.get(target, target)}</b>\n\n"
        "Endi xabaringizni yuboring — matn, rasm yoki video.\n"
        "Bekor qilish: /bekor"
    )
    await callback.answer()


@router.message(Broadcast.waiting_message, Command("bekor"))
async def abort_waiting(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer("❌ Bekor qilindi.", reply_markup=kb.admin_menu())


@router.message(Broadcast.waiting_message)
async def got_message(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    target = data.get("target", "all")
    targets = await db.all_user_ids(lang=None if target == "all" else target)

    await state.update_data(
        from_chat_id=message.chat.id, message_id=message.message_id
    )
    await state.set_state(Broadcast.waiting_confirm)
    await message.answer(
        f"Yuqoridagi xabar <b>{len(targets)}</b> ta foydalanuvchiga "
        f"({TARGET_LABELS.get(target, target)}) yuboriladi.\n\nTasdiqlaysizmi?",
        reply_markup=kb.broadcast_confirm(),
    )


@router.callback_query(Broadcast.waiting_confirm, F.data == "adm:cancel")
async def cancel_broadcast(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await callback.message.edit_text("❌ Bekor qilindi.", reply_markup=kb.admin_menu())
    await callback.answer()


@router.callback_query(Broadcast.waiting_confirm, F.data == "adm:send")
async def do_broadcast(callback: CallbackQuery, state: FSMContext, bot: Bot) -> None:
    data = await state.get_data()
    await state.clear()

    from_chat_id = data.get("from_chat_id")
    message_id = data.get("message_id")
    target = data.get("target", "all")
    if not from_chat_id or not message_id:
        await callback.answer("Xabar topilmadi.", show_alert=True)
        return

    await callback.message.edit_text("📤 Yuborilmoqda…")
    await callback.answer()

    sent = failed = blocked = 0
    for user_id in await db.all_user_ids(lang=None if target == "all" else target):
        try:
            await bot.copy_message(user_id, from_chat_id, message_id)
            sent += 1
        except TelegramRetryAfter as exc:
            await asyncio.sleep(exc.retry_after)
            try:
                await bot.copy_message(user_id, from_chat_id, message_id)
                sent += 1
            except Exception:
                failed += 1
        except TelegramForbiddenError:
            await db.mark_blocked(user_id)
            blocked += 1
        except Exception as exc:  # bitta odam butun jarayonni to'xtatmasin
            log.warning("broadcast %s ga yuborilmadi: %s", user_id, exc)
            failed += 1
        await asyncio.sleep(0.05)  # Telegram limiti ~30 xabar/sekund

    await callback.message.answer(
        "✅ <b>Yuborish tugadi</b>\n\n"
        f"Yuborildi: <b>{sent}</b>\n"
        f"Bloklagan: <b>{blocked}</b>\n"
        f"Xatolik: <b>{failed}</b>",
        reply_markup=kb.admin_menu(),
    )


# --- Bosh sahifa ------------------------------------------------------------


@router.callback_query(F.data == "adm:home")
async def admin_home(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await callback.message.edit_text("🛠 <b>Admin panel</b>", reply_markup=kb.admin_menu())
    await callback.answer()


# --- Tugatish darajasi ------------------------------------------------------


@router.callback_query(F.data == "adm:funnel")
async def show_funnel(callback: CallbackQuery) -> None:
    rows = await db.funnel()
    lines = ["📈 <b>Tugatish darajasi</b>", "",
             "<i>Boshlagan → tugatgan. Past foiz = test uzun yoki zerikarli.</i>", ""]
    if not rows:
        lines.append("Hali ma’lumot yo‘q.")
    for row in rows:
        test = REGISTRY.get(row["key"])
        title = tr(test.title, "uz") if test else row["key"]
        emoji = test.emoji if test else "•"
        rate = f"{row['rate']:.0f}%" if row["rate"] is not None else "—"
        line = f"{emoji} <b>{title}</b>\n   {row['starts']} boshladi → {row['done']} tugatdi · <b>{rate}</b>"
        if row["avg"] is not None:
            line += f" · o‘rtacha ball {row['avg']:.1f}"
        lines.append(line)
    await callback.message.edit_text("\n".join(lines), reply_markup=kb.admin_back())
    await callback.answer()


# --- Foydalanuvchilar -------------------------------------------------------


@router.callback_query(F.data == "adm:users")
async def show_users(callback: CallbackQuery) -> None:
    rows = await db.recent_users()
    lines = ["👥 <b>Oxirgi qo‘shilganlar</b>", ""]
    if not rows:
        lines.append("Hali foydalanuvchi yo‘q.")
    for row in rows:
        name = (row["full_name"] or "?")[:24]
        uname = f"@{row['username']}" if row["username"] else f"id{row['user_id']}"
        flag = {"uz": "🇺🇿", "ru": "🇷🇺"}.get(row["lang"] or "", "❔")
        lines.append(
            f"{flag} <b>{name}</b> · {uname} · {row['tests']} test "
            f"· <i>{(row['created_at'] or '')[:10]}</i>"
        )
    await callback.message.edit_text("\n".join(lines), reply_markup=kb.admin_back())
    await callback.answer()


# --- Testlarni boshqarish ---------------------------------------------------


@router.callback_query(F.data == "adm:tests")
async def list_tests(callback: CallbackQuery) -> None:
    off = await db.disabled_tests()
    text = (
        "🧩 <b>Testlarni boshqarish</b>\n\n"
        "🟢 — foydalanuvchilarga ko‘rinadi\n"
        "🔴 — menyudan yashirilgan\n\n"
        "Testni tanlab, savollarini ko‘rishingiz yoki vaqtincha "
        "o‘chirib qo‘yishingiz mumkin."
    )
    await callback.message.edit_text(text, reply_markup=kb.admin_tests(off))
    await callback.answer()


@router.callback_query(F.data.startswith("admtest:"))
async def show_test(callback: CallbackQuery) -> None:
    key = callback.data.split(":", 1)[1]
    test = REGISTRY.get(key)
    if not test:
        await callback.answer()
        return
    off = await db.disabled_tests()
    rows = await db.funnel()
    stat = next((r for r in rows if r["key"] == key), None)

    lines = [
        f"{test.emoji} <b>{tr(test.title, 'uz')}</b>",
        "🔴 Hozir o‘chirilgan" if key in off else "🟢 Hozir yoqilgan",
        "",
        f"Savollar: <b>{test.size}</b> · yo‘nalishlar: <b>{len(test.scales)}</b>",
        f"Teskari savollar: <b>{sum(1 for i in test.items if i.reverse)}</b>",
    ]
    if stat:
        rate = f"{stat['rate']:.0f}%" if stat["rate"] is not None else "—"
        lines.append(f"Boshlagan: <b>{stat['starts']}</b> · tugatgan: "
                     f"<b>{stat['done']}</b> ({rate})")
    await callback.message.edit_text(
        "\n".join(lines), reply_markup=kb.admin_test_one(key, key in off))
    await callback.answer()


@router.callback_query(F.data.startswith("admtoggle:"))
async def toggle(callback: CallbackQuery) -> None:
    key = callback.data.split(":", 1)[1]
    if key not in REGISTRY:
        await callback.answer()
        return
    enabled = await db.toggle_test(key)
    await callback.answer("🟢 Yoqildi" if enabled else "🔴 O‘chirildi", show_alert=True)
    await show_test(callback)


PER_PAGE = 8


@router.callback_query(F.data.startswith("admq:"))
async def show_questions(callback: CallbackQuery) -> None:
    _, key, raw_page = callback.data.split(":")
    test = REGISTRY.get(key)
    if not test:
        await callback.answer()
        return
    page = int(raw_page)
    pages = (test.size + PER_PAGE - 1) // PER_PAGE
    chunk = test.items[page * PER_PAGE:(page + 1) * PER_PAGE]

    lines = [f"{test.emoji} <b>{tr(test.title, 'uz')}</b> — "
             f"savollar {page * PER_PAGE + 1}–{page * PER_PAGE + len(chunk)} "
             f"/ {test.size}", ""]
    for i, item in enumerate(chunk, start=page * PER_PAGE + 1):
        mark = " <i>(teskari)</i>" if item.reverse else ""
        lines.append(f"<b>{i}. {tr(item.text, 'uz')}</b>{mark}")
        lines.append("   " + " · ".join(
            a.split(" ", 1)[1] for a in item.answers("uz")))
        lines.append("")
    await callback.message.edit_text(
        "\n".join(lines), reply_markup=kb.admin_questions(key, page, pages))
    await callback.answer()


# --- Eksport ----------------------------------------------------------------


@router.callback_query(F.data == "adm:export")
async def export(callback: CallbackQuery) -> None:
    await callback.answer("Tayyorlanmoqda…")
    rows = await db.export_results()
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["sana", "user_id", "username", "til", "test",
                     "yosh_guruhi", "umumiy_ball", "shkalalar"])
    for row in rows:
        writer.writerow(row)
    data = buf.getvalue().encode("utf-8-sig")  # Excel uchun BOM
    await callback.message.answer_document(
        BufferedInputFile(data, filename="natijalar.csv"),
        caption=f"📥 {len(rows)} ta natija",
        reply_markup=kb.admin_back(),
    )


# --- To'lovlar --------------------------------------------------------------


class Prices(StatesGroup):
    waiting_amount = State()


class Grant(StatesGroup):
    waiting_user = State()


def _product_title(key: str) -> str:
    if key == db.ALL_PRODUCTS:
        return "🎁 Barcha testlar"
    test = REGISTRY.get(key)
    return f"{test.emoji} {tr(test.title, 'uz')}" if test else key


@router.callback_query(F.data == "adm:pay")
async def payments_home(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    data = await db.payment_stats()
    free = await db.free_tests()

    lines = [
        "💳 <b>To‘lovlar</b>",
        "",
        f"✅ To‘langan: <b>{data['count']:.0f}</b> ta · "
        f"<b>{money(int(data['sum']))}</b> so‘m",
        f"📅 Bugun: <b>{data['today']:.0f}</b> ta · "
        f"<b>{money(int(data['today_sum']))}</b> so‘m",
        f"🧾 Boshlangan urinishlar: <b>{data['started']:.0f}</b>",
        f"🔓 Qo‘lda ochilgan: <b>{data['manual']:.0f}</b>",
        "",
        f"Click ulanishi: {'🟢 sozlangan' if CLICK_ENABLED else '🔴 sozlanmagan'}",
    ]
    if not CLICK_ENABLED:
        lines.append(
            "<i>CLICK_* kalitlari va PUBLIC_URL to‘ldirilmagan — hech kim "
            "to‘lov qila olmaydi.</i>"
        )
    lines += [
        "",
        "<b>Testlar:</b> 💳 pullik · 🎁 bepul",
        " ".join(
            ("🎁" if key in free else "💳") + REGISTRY[key].emoji for key in ORDER
        ),
    ]
    await callback.message.edit_text("\n".join(lines), reply_markup=kb.admin_payments())
    await callback.answer()


@router.callback_query(F.data == "adm:paylist")
async def payment_list(callback: CallbackQuery) -> None:
    rows = await db.recent_payments()
    marks = {
        "paid": "✅", "pending": "⏳", "prepared": "🔄",
        "cancelled": "❌", "revoked": "🚫",
    }
    lines = ["🧾 <b>Oxirgi to‘lovlar</b>", ""]
    if not rows:
        lines.append("Hali to‘lov yo‘q.")
    for row in rows:
        who = f"@{row['username']}" if row["username"] else f"id{row['user_id']}"
        mark = marks.get(row["status"], "•")
        lines.append(
            f"{mark} <code>#{row['id']}</code> {who} · "
            f"{_product_title(row['product'])} · <b>{money(row['amount'])}</b> so‘m"
        )
        lines.append(f"   <i>{(row['paid_at'] or row['created_at'] or '')[:16]}"
                     f" · {row['method']}</i>")
    await callback.message.edit_text("\n".join(lines), reply_markup=kb.admin_payments())
    await callback.answer()


# --- Narxlar ----------------------------------------------------------------


async def _price_rows() -> list[tuple[str, str, int]]:
    rows = [(db.ALL_PRODUCTS, "🎁 Barcha testlar",
             await db.price_of(db.ALL_PRODUCTS, DEFAULT_PRICE_ALL))]
    for key in ORDER:
        rows.append((key, f"{REGISTRY[key].emoji} {tr(REGISTRY[key].title, 'uz')}",
                     await db.price_of(key, DEFAULT_PRICE)))
    return rows


@router.callback_query(F.data == "adm:prices")
async def show_prices(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await callback.message.edit_text(
        "💰 <b>Narxlar</b>\n\n"
        "O‘zgartirish uchun mahsulotni tanlang.\n"
        "<i>Narxni 0 qilsangiz, «Barcha testlar» paketi taklif qilinmaydi.</i>",
        reply_markup=kb.admin_prices(await _price_rows()),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("admprice:"))
async def ask_price(callback: CallbackQuery, state: FSMContext) -> None:
    key = callback.data.split(":", 1)[1]
    if key != db.ALL_PRODUCTS and key not in REGISTRY:
        await callback.answer()
        return
    await state.set_state(Prices.waiting_amount)
    await state.update_data(product=key)
    await callback.message.edit_text(
        f"💰 <b>{_product_title(key)}</b>\n\n"
        "Yangi narxni so‘mda yuboring — faqat raqam, masalan <code>12000</code>.\n"
        "Bekor qilish: /bekor"
    )
    await callback.answer()


@router.message(Prices.waiting_amount, Command("bekor"))
async def abort_price(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer("❌ Bekor qilindi.", reply_markup=kb.admin_payments())


@router.message(Prices.waiting_amount)
async def save_price(message: Message, state: FSMContext) -> None:
    raw = "".join(c for c in (message.text or "") if c.isdigit())
    if not raw:
        await message.answer("Faqat raqam yuboring, masalan <code>12000</code>.")
        return

    data = await state.get_data()
    await state.clear()
    product = data.get("product", "")
    await db.set_price(product, int(raw))
    await message.answer(
        f"✅ <b>{_product_title(product)}</b> narxi endi "
        f"<b>{money(int(raw))}</b> so‘m.",
        reply_markup=kb.admin_prices(await _price_rows()),
    )


# --- Pullik / bepul ---------------------------------------------------------


@router.callback_query(F.data.startswith("admfree:"))
async def toggle_free(callback: CallbackQuery) -> None:
    key = callback.data.split(":", 1)[1]
    if key not in REGISTRY:
        await callback.answer()
        return
    now_free = await db.toggle_free_test(key)
    await callback.answer(
        "🎁 Endi bepul" if now_free else "💳 Endi pullik", show_alert=True
    )
    await callback.message.edit_reply_markup(
        reply_markup=kb.admin_paid_tests(await db.free_tests())
    )


# --- Qo'lda ochish ----------------------------------------------------------


@router.callback_query(F.data == "adm:grant")
async def ask_grant(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(Grant.waiting_user)
    await callback.message.edit_text(
        "🔓 <b>Qo‘lda ochish</b>\n\n"
        "Foydalanuvchi ID sini va mahsulotni yuboring:\n"
        "<code>123456789 all</code> — barcha testlar\n"
        "<code>123456789 bigfive</code> — bitta test\n\n"
        f"Mavjud kalitlar: <code>{'</code>, <code>'.join(ORDER)}</code>\n"
        "Bekor qilish: /bekor"
    )
    await callback.answer()


@router.message(Grant.waiting_user, Command("bekor"))
async def abort_grant(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer("❌ Bekor qilindi.", reply_markup=kb.admin_payments())


@router.message(Grant.waiting_user)
async def do_grant(message: Message, state: FSMContext, bot: Bot) -> None:
    parts = (message.text or "").split()
    if len(parts) != 2 or not parts[0].isdigit():
        await message.answer("Format: <code>123456789 all</code>")
        return
    user_id, product = int(parts[0]), parts[1]
    if product != db.ALL_PRODUCTS and product not in REGISTRY:
        await message.answer(f"<code>{product}</code> — bunday test yo‘q.")
        return

    await state.clear()
    await db.grant_access(user_id, product, message.from_user.id)
    await message.answer(
        f"✅ <code>{user_id}</code> uchun <b>{_product_title(product)}</b> ochildi.",
        reply_markup=kb.admin_payments(),
    )
    # Odamning o'zini ham xabardor qilamiz — aks holda u ochilganini bilmaydi.
    try:
        lang = await db.get_lang(user_id) or "uz"
        await bot.send_message(
            user_id,
            t("pay_success", lang, product=payment.product_title(product, lang)),
            reply_markup=kb.unlocked(
                "" if product == db.ALL_PRODUCTS else product, lang
            ),
        )
    except Exception as exc:  # noqa: BLE001
        log.warning("Qo‘lda ochish haqida xabar ketmadi (%s): %s", user_id, exc)


@router.callback_query(F.data == "adm:freetests")
async def free_tests_screen(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await callback.message.edit_text(
        "🎁 <b>Pullik / bepul testlar</b>\n\n"
        "💳 — test pullik, ochish uchun to‘lov kerak\n"
        "🎁 — test bepul, hamma ochaveradi\n\n"
        "Holatini almashtirish uchun testni bosing.",
        reply_markup=kb.admin_paid_tests(await db.free_tests()),
    )
    await callback.answer()
