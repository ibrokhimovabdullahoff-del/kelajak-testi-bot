"""Admin paneli: statistika va ommaviy xabar. Interfeys faqat o'zbekcha."""
from __future__ import annotations

import asyncio
import logging

from aiogram import Bot, F, Router
from aiogram.exceptions import TelegramForbiddenError, TelegramRetryAfter
from aiogram.filters import BaseFilter, Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message

import database as db
import keyboards as kb
from config import is_admin
from locales import tr
from psytests import REGISTRY

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
