"""Kirish nuqtasi."""
import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import BotCommand, BotCommandScopeDefault

import database as db
import payments
import wallet
from config import BOT_TOKEN, CLICK_ENABLED, LOG_LEVEL, PUBLIC_URL
from handlers import build_router
from handlers.payment import notify_paid, set_bot

COMMANDS = {
    "uz": [
        ("start", "Testlar menyusi"),
        ("natijalar", "Mening natijalarim"),
        ("balans", "Mening balansim"),
        ("shop", "Balansdan test sotib olish"),
        ("iq", "Premium IQ testi — 5 000 so‘m"),
        ("til", "Tilni o‘zgartirish"),
        ("haqida", "Bot va manbalar haqida"),
        ("bekor", "Testni bekor qilish"),
    ],
    "ru": [
        ("start", "Меню тестов"),
        ("natijalar", "Мои результаты"),
        ("balans", "Мой баланс"),
        ("shop", "Покупка тестов с баланса"),
        ("iq", "Премиум IQ-тест — 5 000 сум"),
        ("til", "Сменить язык"),
        ("haqida", "О боте и источниках"),
        ("bekor", "Отменить тест"),
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
    await wallet.init()

    bot = Bot(BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dispatcher = Dispatcher(storage=MemoryStorage())
    dispatcher.include_router(build_router())
    set_bot(bot)

    me = await bot.get_me()
    logging.info("Ishga tushdi: @%s (id=%s)", me.username, me.id)

    runner = await payments.run_server(on_paid=notify_paid)
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
        await runner.cleanup()
        await bot.session.close()
        await db.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.info("To‘xtatildi")
