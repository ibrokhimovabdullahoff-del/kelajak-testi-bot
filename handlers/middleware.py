"""Har bir yangilanish uchun foydalanuvchini yozib qo'yadi va tilni aniqlaydi.

Natijada handlerlar `lang` ni tayyor holda oladi va hech biri bazaga
alohida murojaat qilmaydi.
"""
from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message, TelegramObject

import database as db
from locales import DEFAULT_LANG, LANGS


class UserContext(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        user = data.get("event_from_user")
        if user is None:
            return await handler(event, data)

        if isinstance(event, (Message, CallbackQuery)):
            await db.upsert_user(user.id, user.username, user.full_name)

        lang = await db.get_lang(user.id)
        data["lang_known"] = lang in LANGS
        data["lang"] = lang if lang in LANGS else _guess(user.language_code)
        return await handler(event, data)


def _guess(code: str | None) -> str:
    """Telegram interfeys tili bo'yicha taxmin — foydalanuvchi tanlagunicha."""
    if code and code.split("-")[0].lower() in ("ru", "be", "kk", "ky"):
        return "ru"
    return DEFAULT_LANG
