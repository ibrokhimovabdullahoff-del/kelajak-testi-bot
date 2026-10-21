"""Foydalanuvchi botni bloklashi/qaytishi va zararsiz xatolar.

  * my_chat_member — Telegram foydalanuvchi botni bloklaganda (yoki blokdan
    chiqarganda) shu updateni yuboradi. Bloklaganlar xabar tarqatishda
    o'tkazib yuboriladi; qaytib /start bossa, blok olib tashlanadi.
  * "message is not modified" — tugma ikki marta bosilib, xabar o'zgarmasa
    Telegram shu xatoni beradi. Bu xato emas, log'ni ifloslantirmasin.
"""
from __future__ import annotations

import logging

from aiogram import Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import (KICKED, MEMBER, ChatMemberUpdatedFilter, ExceptionMessageFilter,
                             ExceptionTypeFilter)
from aiogram.types import ChatMemberUpdated, ErrorEvent

import database as db
import events

log = logging.getLogger(__name__)
router = Router()


async def record_blocked(user_id: int) -> None:
    """Bloklaganini yozadi — hodisa faqat holat o'zgarganda bir marta."""
    if await db.mark_blocked(user_id):
        events.track(user_id, "blocked")


@router.my_chat_member(ChatMemberUpdatedFilter(member_status_changed=KICKED))
async def bot_blocked(update: ChatMemberUpdated) -> None:
    if update.chat.type == "private":
        await record_blocked(update.from_user.id)


@router.my_chat_member(ChatMemberUpdatedFilter(member_status_changed=MEMBER))
async def bot_unblocked(update: ChatMemberUpdated) -> None:
    if update.chat.type == "private":
        await db.mark_unblocked(update.from_user.id)


@router.errors(ExceptionTypeFilter(TelegramBadRequest), ExceptionMessageFilter(r".*message is not modified"))
async def not_modified(event: ErrorEvent) -> bool:
    return True
