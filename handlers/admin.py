"""Admin paneli: statistics, payments, broadcasts and product controls."""
from __future__ import annotations

import csv
import io
import logging

from aiogram import Bot, F, Router
from aiogram.filters import BaseFilter, Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import BufferedInputFile, CallbackQuery, Message

import database as db
import keyboards as kb
from config import (BUNDLE_KEY, BUNDLE_PRICE_DEFAULT, CLICK_ENABLED, DEFAULT_PRICE, IQ_EMOJI, IQ_KEY,
                    IQ_PRICE_DEFAULT, OPTIMISTIC_MAX, is_admin)
from locales import money, t, tr
from psytests import ORDER, REGISTRY

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
    await callback.answer()
    data = await db.stats()
    lines = ["📊 <b>Statistika</b>", "", f"👥 Foydalanuvchilar: <b>{data['users']:.0f}</b>", f"🆕 Bugun qo‘shilgan: <b>{data['new_today']:.0f}</b>", f"🚫 Bloklaganlar: <b>{data['blocked']:.0f}</b>", f"🌐 Til: 🇺🇿 <b>{data['uz']:.0f}</b> · 🇷🇺 <b>{data['ru']:.0f}</b>", "", f"📝 Jami testlar: <b>{data['tests']:.0f}</b>", f"📅 Bugun: <b>{data['tests_today']:.0f}</b>", f"🟢 Hozir test yechayotganlar: <b>{await db.active_now():.0f}</b>"]
    if data["per_test"]:
        lines += ["", "<b>Testlar bo‘yicha:</b>"]
        for row in data["per_test"]:
            test = REGISTRY.get(row["key"])
            title = tr(test.title, "uz") if test else row["key"]
            emoji = test.emoji if test else "•"
            line = f"{emoji} {title}: <b>{row['count']}</b> ta"
            if row["avg"] is not None: line += f" · o‘rtacha <b>{row['avg']:.1f}</b>"
            lines.append(line)
    await callback.message.edit_text("\n".join(lines), reply_markup=kb.admin_menu())


@router.callback_query(F.data == "adm:broadcast")
async def ask_target(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    await state.set_state(Broadcast.waiting_target)
    await callback.message.edit_text("📣 Kimga yuboramiz?", reply_markup=kb.broadcast_targets())


@router.callback_query(Broadcast.waiting_target, F.data.startswith("admto:"))
async def ask_message(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    target = callback.data.split(":", 1)[1]
    await state.update_data(target=target)
    await state.set_state(Broadcast.waiting_message)
    await callback.message.edit_text(f"📣 Yuboriladi: <b>{TARGET_LABELS.get(target, target)}</b>\n\nEndi xabaringizni yuboring — matn, rasm yoki video.\nBekor qilish: /bekor")


@router.message(Broadcast.waiting_message, Command("bekor"))
async def abort_waiting(message: Message, state: FSMContext) -> None:
    await state.clear(); await message.answer("❌ Bekor qilindi.", reply_markup=kb.admin_menu())


@router.message(Broadcast.waiting_message)
async def got_message(message: Message, state: FSMContext) -> None:
    data = await state.get_data(); target = data.get("target", "all")
    targets = await db.all_user_ids(lang=None if target == "all" else target)
    await state.update_data(from_chat_id=message.chat.id, message_id=message.message_id)
    await state.set_state(Broadcast.waiting_confirm)
    await message.answer(f"Yuqoridagi xabar <b>{len(targets)}</b> ta foydalanuvchiga ({TARGET_LABELS.get(target, target)}) yuboriladi.\n\nTasdiqlaysizmi?", reply_markup=kb.broadcast_confirm())


@router.callback_query(Broadcast.waiting_confirm, F.data == "adm:cancel")
async def cancel_broadcast(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer(); await state.clear(); await callback.message.edit_text("❌ Bekor qilindi.", reply_markup=kb.admin_menu())


@router.callback_query(Broadcast.waiting_confirm, F.data == "adm:send")
async def do_broadcast(callback: CallbackQuery, state: FSMContext, bot: Bot) -> None:
    await callback.answer(); data = await state.get_data(); await state.clear()
    from_chat_id, message_id, target = data.get("from_chat_id"), data.get("message_id"), data.get("target", "all")
    if not from_chat_id or not message_id:
        await callback.message.edit_text("Xabar topilmadi.", reply_markup=kb.admin_menu()); return
    await callback.message.edit_text("📤 Yuborilmoqda…")
    import broadcast

    async def send_one(user_id: int) -> None:
        await bot.copy_message(user_id, from_chat_id, message_id)

    # Bloklaganlar o'tkaziladi, Telegram cheklovi hisobga olinadi, natija log'ga va bazaga yoziladi.
    counts = await broadcast.send_all(await db.all_user_ids(lang=None if target == "all" else target), send_one,
                                      kind="admin", admin_id=callback.from_user.id, target=target)
    await callback.message.answer("✅ <b>Yuborish tugadi</b>\n\n" f"Yuborildi: <b>{counts['sent']}</b>\n" f"Bloklagan: <b>{counts['blocked']}</b>\n" f"Xatolik: <b>{counts['failed']}</b>", reply_markup=kb.admin_menu())


@router.callback_query(F.data == "adm:home")
async def admin_home(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer(); await state.clear(); await callback.message.edit_text("🛠 <b>Admin panel</b>", reply_markup=kb.admin_menu())


@router.callback_query(F.data == "adm:funnel")
async def show_funnel(callback: CallbackQuery) -> None:
    await callback.answer(); rows = await db.funnel()
    lines = ["📈 <b>Tugatish darajasi</b>", "", "<i>Boshlagan → tugatgan.</i>", ""]
    if not rows: lines.append("Hali ma’lumot yo‘q.")
    for row in rows:
        test = REGISTRY.get(row["key"]); title = tr(test.title, "uz") if test else row["key"]; emoji = test.emoji if test else "•"; rate = f"{row['rate']:.0f}%" if row["rate"] is not None else "—"
        lines.append(f"{emoji} <b>{title}</b>\n   {row['starts']} boshladi → {row['done']} tugatdi · <b>{rate}</b>")
    await callback.message.edit_text("\n".join(lines), reply_markup=kb.admin_back())


@router.callback_query(F.data == "adm:users")
async def show_users(callback: CallbackQuery) -> None:
    await callback.answer(); rows = await db.recent_users(); lines = ["👥 <b>Oxirgi qo‘shilganlar</b>", ""]
    if not rows: lines.append("Hali foydalanuvchi yo‘q.")
    for row in rows:
        name = (row["full_name"] or "?")[:24]; uname = f"@{row['username']}" if row["username"] else f"id{row['user_id']}"; flag = {"uz":"🇺🇿","ru":"🇷🇺"}.get(row["lang"] or "","❔")
        lines.append(f"{flag} <b>{name}</b> · {uname} · {row['tests']} test · <i>{(row['created_at'] or '')[:10]}</i>")
    await callback.message.edit_text("\n".join(lines), reply_markup=kb.admin_back())


@router.callback_query(F.data == "adm:tests")
async def list_tests(callback: CallbackQuery) -> None:
    await callback.answer(); off = await db.disabled_tests()
    await callback.message.edit_text("🧩 <b>Testlarni boshqarish</b>\n\n🟢 — foydalanuvchilarga ko‘rinadi\n🔴 — menyudan yashirilgan", reply_markup=kb.admin_tests(off))


@router.callback_query(F.data.startswith("admtest:"))
async def show_test(callback: CallbackQuery) -> None:
    await callback.answer(); key = callback.data.split(":", 1)[1]; test = REGISTRY.get(key)
    if not test: return
    off = await db.disabled_tests(); rows = await db.funnel(); stat = next((r for r in rows if r["key"] == key), None)
    lines = [f"{test.emoji} <b>{tr(test.title, 'uz')}</b>", "🔴 Hozir o‘chirilgan" if key in off else "🟢 Hozir yoqilgan", "", f"Savollar: <b>{test.size}</b> · yo‘nalishlar: <b>{len(test.scales)}</b>"]
    if stat:
        rate = f"{stat['rate']:.0f}%" if stat["rate"] is not None else "—"; lines.append(f"Boshlagan: <b>{stat['starts']}</b> · tugatgan: <b>{stat['done']}</b> ({rate})")
    await callback.message.edit_text("\n".join(lines), reply_markup=kb.admin_test_one(key, key in off))


@router.callback_query(F.data.startswith("admtoggle:"))
async def toggle(callback: CallbackQuery) -> None:
    await callback.answer(); key = callback.data.split(":", 1)[1]
    if key not in REGISTRY: return
    enabled = await db.toggle_test(key)
    await callback.message.edit_text("🛠 <b>Test holati yangilandi</b>", reply_markup=kb.admin_test_one(key, not enabled))


PER_PAGE = 8

@router.callback_query(F.data.startswith("admq:"))
async def show_questions(callback: CallbackQuery) -> None:
    await callback.answer(); _, key, raw_page = callback.data.split(":"); test = REGISTRY.get(key)
    if not test: return
    page = int(raw_page); pages = (test.size + PER_PAGE - 1) // PER_PAGE; chunk = test.items[page * PER_PAGE:(page + 1) * PER_PAGE]
    lines = [f"{test.emoji} <b>{tr(test.title, 'uz')}</b> — savollar {page * PER_PAGE + 1}–{page * PER_PAGE + len(chunk)} / {test.size}", ""]
    for i, item in enumerate(chunk, start=page * PER_PAGE + 1): lines += [f"<b>{i}. {tr(item.text, 'uz')}</b>{' <i>(teskari)</i>' if item.reverse else ''}", "   " + " · ".join(a.split(" ", 1)[1] for a in item.answers("uz")), ""]
    await callback.message.edit_text("\n".join(lines), reply_markup=kb.admin_questions(key, page, pages))


@router.callback_query(F.data == "adm:export")
async def export(callback: CallbackQuery) -> None:
    await callback.answer("Tayyorlanmoqda…"); rows = await db.export_results(); buf = io.StringIO(); writer = csv.writer(buf); writer.writerow(["sana","user_id","username","til","test","yosh_guruhi","umumiy_ball","shkalalar"])
    for row in rows: writer.writerow(row)
    await callback.message.answer_document(BufferedInputFile(buf.getvalue().encode("utf-8-sig"), filename="natijalar.csv"), caption=f"📥 {len(rows)} ta natija", reply_markup=kb.admin_back())


class Prices(StatesGroup):
    waiting_amount = State()


class Grant(StatesGroup):
    waiting_user = State()


def _product_title(key: str) -> str:
    if key == IQ_KEY: return f"{IQ_EMOJI} IQ testi"
    if key == BUNDLE_KEY: return "📦 5 ta testning to‘liq tahlili"
    test = REGISTRY.get(key); return f"{test.emoji} {tr(test.title, 'uz')}" if test else key


async def _optimistic() -> bool:
    return await db.get_setting("optimistic_unlock", "0") == "1"


@router.callback_query(F.data == "adm:pay")
async def payments_home(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer(); await state.clear(); await draw_payments(callback)


async def draw_payments(callback: CallbackQuery) -> None:
    data = await db.payment_stats(); free = await db.free_tests()
    optimistic = await _optimistic()
    lines = ["💳 <b>To‘lovlar</b>", "", f"✅ To‘langan: <b>{data['count']:.0f}</b> ta · <b>{money(int(data['sum']))}</b> so‘m", f"📅 Bugun: <b>{data['today']:.0f}</b> ta · <b>{money(int(data['today_sum']))}</b> so‘m", f"🧾 Boshlangan urinishlar: <b>{data['started']:.0f}</b>", f"🔓 Qo‘lda ochilgan: <b>{data['manual']:.0f}</b>", "", f"Click ulanishi: {'🟢 sozlangan' if CLICK_ENABLED else '🔴 sozlanmagan'}",
             "", "⚡️ <b>Chekdan oldin ochish</b> — karta orqali to‘lovda chek rasmi kelishi bilan to‘liq tahlil ochiladi, "
             f"siz keyin tekshirasiz ({money(OPTIMISTIC_MAX)} so‘mgacha, bitta odamda bir vaqtda bitta). Rad etsangiz, tahlil yopiladi "
             "va u odamga bu imkoniyat boshqa berilmaydi. " + ("Hozir: <b>YOQIQ</b>." if optimistic else "Hozir: <b>o‘chiq</b>.")]
    await callback.message.edit_text("\n".join(lines), reply_markup=kb.admin_payments(await db.admin_pays(), optimistic))


@router.callback_query(F.data == "adm:paylist")
async def payment_list(callback: CallbackQuery) -> None:
    await callback.answer(); rows = await db.recent_payments(); lines = ["🧾 <b>Oxirgi to‘lovlar</b>", ""]
    marks = {"paid":"✅","pending":"⏳","prepared":"🔄","cancelled":"❌","revoked":"🚫"}
    for row in rows:
        who = f"@{row['username']}" if row["username"] else f"id{row['user_id']}"; mark = marks.get(row["status"], "•")
        lines.append(f"{mark} <code>#{row['id']}</code> {who} · {_product_title(row['product'])} · <b>{money(row['amount'])}</b> so‘m")
    if not rows: lines.append("Hali to‘lov yo‘q.")
    await callback.message.edit_text("\n".join(lines), reply_markup=kb.admin_payments(await db.admin_pays(), await _optimistic()))


async def _price_rows() -> list[tuple[str, str, int]]:
    rows = [(IQ_KEY, f"{IQ_EMOJI} IQ testi", await db.price_of(IQ_KEY, IQ_PRICE_DEFAULT))]
    rows += [(key, f"{REGISTRY[key].emoji} {tr(REGISTRY[key].title, 'uz')}", await db.price_of(key, DEFAULT_PRICE)) for key in ORDER]
    rows.append((BUNDLE_KEY, "📦 5 ta test to‘plami", await db.price_of(BUNDLE_KEY, BUNDLE_PRICE_DEFAULT)))
    return rows


@router.callback_query(F.data == "adm:prices")
async def show_prices(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer(); await state.clear()
    await callback.message.edit_text("💰 <b>To‘liq tahlil narxlari</b>\n\nTestlarni topshirish bepul — narx faqat to‘liq tahlil uchun. "
                                     "To‘plam har bir to‘lov oynasida ikkinchi bo‘lib chiqadi.\n\nO‘zgartirish uchun tanlang.",
                                     reply_markup=kb.admin_prices(await _price_rows()))


@router.callback_query(F.data.startswith("admprice:"))
async def ask_price(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer(); key = callback.data.split(":",1)[1]
    if key not in ORDER and key not in (IQ_KEY, BUNDLE_KEY): return
    await state.set_state(Prices.waiting_amount); await state.update_data(product=key); await callback.message.edit_text(f"💰 <b>{_product_title(key)}</b>\n\nYangi narxni so‘mda yuboring — faqat raqam.")


@router.message(Prices.waiting_amount, Command("bekor"))
async def abort_price(message: Message, state: FSMContext) -> None:
    await state.clear(); await message.answer("❌ Bekor qilindi.", reply_markup=kb.admin_menu())


@router.message(Prices.waiting_amount)
async def save_price(message: Message, state: FSMContext) -> None:
    raw = "".join(c for c in (message.text or "") if c.isdigit())
    if not raw: await message.answer("Faqat raqam yuboring."); return
    data = await state.get_data(); await state.clear(); product = data.get("product", ""); await db.set_price(product, int(raw)); await message.answer(f"✅ <b>{_product_title(product)}</b> narxi endi <b>{money(int(raw))}</b> so‘m.", reply_markup=kb.admin_menu())


@router.callback_query(F.data.startswith("admfree:"))
async def toggle_free(callback: CallbackQuery) -> None:
    await callback.answer()
    key = callback.data.split(":", 1)[1]
    allowed = set(REGISTRY) | {IQ_KEY}
    if key not in allowed:
        return
    now_free = await db.toggle_free_test(key)
    free = await db.free_tests()
    await callback.message.edit_text(f"🎁 <b>To‘liq tahlil: pullik / bepul</b>\n\n{'🎁 Bepul' if now_free else '💳 Pullik'}: <b>{_product_title(key)}</b>\n\nHolatni boshqa test uchun ham o‘zgartirishingiz mumkin.", reply_markup=kb.admin_paid_tests(free))


@router.callback_query(F.data == "adm:grant")
async def ask_grant(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer(); await state.set_state(Grant.waiting_user); await callback.message.edit_text("🔓 <b>To‘liq tahlilni qo‘lda ochish</b>\n\nFoydalanuvchi ID va test kalitini yuboring (to‘plam uchun — <code>bundle</code>).\n<code>123456789 bigfive</code>\nKalitlar: iq, bigfive, career, future, child, bundle\nBekor qilish: /bekor")


@router.message(Grant.waiting_user, Command("bekor"))
async def abort_grant(message: Message, state: FSMContext) -> None:
    await state.clear(); await message.answer("❌ Bekor qilindi.", reply_markup=kb.admin_menu())


@router.message(Grant.waiting_user)
async def do_grant(message: Message, state: FSMContext, bot: Bot) -> None:
    parts = (message.text or "").split()
    if len(parts) != 2 or not parts[0].isdigit(): await message.answer("Format: <code>123456789 bigfive</code>"); return
    user_id, product = int(parts[0]), parts[1]
    if product not in REGISTRY and product not in (IQ_KEY, BUNDLE_KEY): await message.answer("Bunday test yo‘q."); return
    import access
    await state.clear(); await access.grant(user_id, access.products_for(product), "admin")
    await message.answer(f"✅ <code>{user_id}</code> uchun <b>{_product_title(product)}</b> to‘liq tahlili ochildi.", reply_markup=kb.admin_menu())
    try:
        from handlers.payment import product_title
        lang = await db.get_lang(user_id) or "uz"; await bot.send_message(user_id, t("pay_report_ok", lang, title=product_title(product, lang)), reply_markup=kb.back_to_menu(lang))
    except Exception: pass


@router.callback_query(F.data == "adm:testmode")
async def toggle_test_mode(callback: CallbackQuery) -> None:
    await callback.answer(); now_on = await db.toggle_admin_pays(); await callback.message.edit_reply_markup(reply_markup=kb.admin_payments(now_on))


@router.callback_query(F.data == "adm:freetests")
async def free_tests_screen(callback: CallbackQuery) -> None:
    await callback.answer()
    await callback.message.edit_text("🎁 <b>To‘liq tahlil: pullik / bepul</b>\n\nTestni topshirish har doim bepul. Bu yerda to‘liq tahlilni vaqtincha bepul qilish mumkin (masalan, aksiya uchun).\n\n💳 — to‘liq tahlil pullik\n🎁 — to‘liq tahlil bepul\n\nBosing va holatini darhol almashtiring.", reply_markup=kb.admin_paid_tests(await db.free_tests()))


@router.callback_query(F.data == "adm:optimistic")
async def toggle_optimistic(callback: CallbackQuery) -> None:
    """Chekdan oldin ochish (odatda o'chiq). Brief: yoqishdan oldin egasidan so'rang."""
    await callback.answer()
    now_on = not await _optimistic()
    await db.set_setting("optimistic_unlock", "1" if now_on else "0")
    await draw_payments(callback)


async def _uncredited_topups() -> list[dict]:
    """To'langan Click to'ldirishlari, lekin balansga tushmagan (eski xato)."""
    conn = await db.connect()
    cursor = await conn.execute(
        """
        SELECT p.id, p.user_id, p.amount, p.paid_at FROM payments p
        WHERE p.product = 'wallet_topup_click' AND p.status = 'paid'
          AND NOT EXISTS (SELECT 1 FROM wallet_transactions w WHERE w.reference = 'click_topup:' || p.id)
        ORDER BY p.id
        """
    )
    return [{"id": r[0], "user_id": r[1], "amount": r[2], "paid_at": r[3]} for r in await cursor.fetchall()]


@router.callback_query(F.data == "adm:reconcile")
async def reconcile(callback: CallbackQuery) -> None:
    await callback.answer()
    rows = await _uncredited_topups()
    from aiogram.utils.keyboard import InlineKeyboardBuilder
    b = InlineKeyboardBuilder()
    if not rows:
        text = "🔎 <b>Click to‘ldirishlari</b>\n\n✅ Hammasi balansga tushgan."
    else:
        total = sum(int(r["amount"]) for r in rows)
        lines = [f"🔎 <b>Click to‘ldirishlari</b>\n\n⚠️ {len(rows)} ta to‘lov Click’da o‘tgan, lekin balansga tushmagan "
                 f"(eski xato). Jami: <b>{money(total)} so‘m</b>.", ""]
        lines += [f"• #{r['id']} · <code>{r['user_id']}</code> · {money(int(r['amount']))} so‘m · {(r['paid_at'] or '')[:10]}"
                  for r in rows[:30]]
        lines += ["", "«Balansga tushirish» — har biri bir marta (qayta bossangiz ham ikki marta tushmaydi), "
                  "foydalanuvchiga xabar boradi."]
        text = "\n".join(lines)
        b.button(text=f"💰 Balansga tushirish ({len(rows)} ta)", callback_data="adm:reconcile:do")
    b.button(text="⬅️ To‘lovlar", callback_data="adm:pay")
    b.adjust(1)
    await callback.message.edit_text(text, reply_markup=b.as_markup())


@router.callback_query(F.data == "adm:reconcile:do")
async def reconcile_do(callback: CallbackQuery) -> None:
    await callback.answer("Tushirilmoqda…")
    from handlers import reports
    done = 0
    for row in await _uncredited_topups():
        await reports.after_payment(int(row["id"]), source="click")
        done += 1
    await callback.message.answer(f"✅ {done} ta to‘ldirish balansga tushirildi.", reply_markup=kb.admin_menu())

