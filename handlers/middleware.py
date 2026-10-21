"""Fast per-update user context for Telegram handlers."""
from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message, TelegramObject

import database as db
import perf
from locales import DEFAULT_LANG, LANGS

#: Handler shuncha vaqtda tugma javobini o'zi bermasa, bo'sh javob yuboriladi —
#: tugmadagi "soat" belgisi uzoq turib qolmasin (masalan, sertifikat chizilayotganda).
ANSWER_FALLBACK_S = 0.3


async def _answer(callback: CallbackQuery) -> None:
    if perf.already_answered(callback.id):
        return
    try:
        await callback.answer()
    except Exception:  # noqa: BLE001 — eskirgan tugma: foydalanuvchi baribir natijani ko'radi
        pass


def _answer_later(callback: CallbackQuery) -> None:
    """Handler uzoq ishlasa (0.3 s dan ko'p) — bo'sh javob fonda ketadi."""
    if perf.already_answered(callback.id):
        return
    task = asyncio.ensure_future(_answer(callback))
    sample = perf.current()
    if sample is not None:
        sample.pending.append(task)


class UserContext(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        bot = data.get("bot")
        if bot is not None:
            perf.ensure_session(bot)
        handler_object = data.get("handler")
        if handler_object is not None:
            perf.set_handler(getattr(handler_object.callback, "__name__", "?"))

        user = data.get("event_from_user")
        if user is None:
            return await handler(event, data)

        # Tugma javobi oldindan KUTILMAYDI: handler o'z javobini (masalan,
        # "Balans yetarli emas" ogohlantirishini) bersin. Bermasa — 0.3 s dan
        # keyin yoki handler tugashi bilan bo'sh javob fonda ketadi.
        timer = token = None
        if isinstance(event, CallbackQuery):
            token = perf.begin_callback(event.id)
            timer = asyncio.get_running_loop().call_later(ANSWER_FALLBACK_S, _answer_later, event)

        try:
            data["is_new_user"] = False
            if isinstance(event, (Message, CallbackQuery)):
                force = isinstance(event, Message) and (event.text or "").startswith("/start")
                data["is_new_user"] = await db.upsert_user(
                    user.id, user.username, user.full_name, force=force
                )

            lang = await db.get_lang(user.id)
            if lang not in LANGS:
                # Birinchi marta: til Telegram sozlamasidan (ru → rus, qolgani → o'zbek).
                # "🌐 Til / Язык" tugmasi bilan har doim almashtirsa bo'ladi.
                lang = _guess(user.language_code)
                await db.set_lang(user.id, lang)
                import events
                events.track(user.id, "lang_set", lang=lang, auto=True)
            data["lang_known"] = True
            data["lang"] = lang
            return await handler(event, data)
        finally:
            if timer is not None:
                timer.cancel()
                # perf o'rnatilgan bo'lsa bu kutilmaydi — javob fonda ketadi.
                await _answer(event)
                perf.end_callback(token)


def _guess(code: str | None) -> str:
    """Telegram interfeys tili: "ru" → rus tili, qolgan hammasi → o'zbek tili."""
    if code and code.split("-")[0].lower() == "ru":
        return "ru"
    return DEFAULT_LANG
