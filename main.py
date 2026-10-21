"""Kirish nuqtasi."""
import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import BotCommand, BotCommandScopeDefault

import content_cms as cms
import database as db
import events
import payments
import perf
import referrals
import wallet
from config import BOT_TOKEN, CLICK_ENABLED, LOG_LEVEL, PUBLIC_URL
from handlers import build_router
from handlers.autostart_runtime import notify_failed, notify_paid, set_runtime
from handlers.growth import set_bot_username
from handlers.lifecycle import record_blocked
from handlers.payment import set_bot

COMMANDS = {
    "uz": [
        ("start", "Testlar menyusi"), ("natijalar", "Natijalarim"),
        ("iq", "IQ testi (rasmli)"), ("til", "Tilni o‘zgartirish"),
        ("haqida", "Bot va manbalar haqida"), ("bekor", "Testni to‘xtatish"),
    ],
    "ru": [
        ("start", "Меню тестов"), ("natijalar", "Мои результаты"),
        ("iq", "IQ-тест (с картинками)"), ("til", "Сменить язык"),
        ("haqida", "О боте и источниках"), ("bekor", "Остановить тест"),
    ],
}

def _commands(lang: str) -> list[BotCommand]:
    return [BotCommand(command=c, description=d) for c, d in COMMANDS[lang]]

async def set_commands(bot: Bot) -> None:
    await bot.set_my_commands(_commands("uz"), scope=BotCommandScopeDefault())
    await bot.set_my_commands(_commands("ru"), scope=BotCommandScopeDefault(), language_code="ru")

async def main() -> None:
    logging.basicConfig(level=LOG_LEVEL, format="%(asctime)s %(levelname)-8s %(name)s: %(message)s")
    await db.init()
    await referrals.init()
    await wallet.init()
    await cms.init()
    await cms.apply_all()

    bot = Bot(BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    storage = MemoryStorage()
    dispatcher = Dispatcher(storage=storage)
    dispatcher.include_router(build_router())
    set_bot(bot)
    # Tezlik o'lchovi (har update uchun bitta "perf" qatori) va bloklaganlarni aniqlash.
    perf.install(dispatcher, bot, watch_loop=True)
    perf.on_blocked = record_blocked

    me = await bot.get_me()
    # Payment webhooks run in the same process, so give the autostart bridge
    # access to the exact FSM storage used by Dispatcher.
    set_runtime(me.id, storage)
    # Sertifikat va taklif havolalari botning haqiqiy nomi bilan yasaladi.
    set_bot_username(me.username)

    logging.info("Ishga tushdi: @%s (id=%s)", me.username, me.id)

    from psytests.iq import ANSWER_KEY_ENV, answer_key
    if answer_key() is None:
        logging.error("%s o‘rnatilmagan yoki noto‘g‘ri — IQ testi yopiq bo‘ladi.", ANSWER_KEY_ENV)

    runner = await payments.run_server(on_paid=notify_paid, on_failed=notify_failed)
    if CLICK_ENABLED:
        logging.info("Click prepare: %s/click/prepare", PUBLIC_URL)
        logging.info("Click complete: %s/click/complete", PUBLIC_URL)
    else:
        logging.warning("Click SOZLANMAGAN — CLICK_* kalitlari va PUBLIC_URL ni to‘ldiring.")

    await set_commands(bot)
    await bot.delete_webhook(drop_pending_updates=True)
    try:
        await dispatcher.start_polling(bot)
    finally:
        await events.flush()
        await runner.cleanup()
        await bot.session.close()
        await db.close()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.info("To‘xtatildi")
