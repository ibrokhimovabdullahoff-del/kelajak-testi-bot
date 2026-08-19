"""Kirish nuqtasi."""
import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import BotCommand, BotCommandScopeDefault

import database as db
from config import BOT_TOKEN, LOG_LEVEL
from handlers import build_router

COMMANDS = {
    "uz": [
        ("start", "Testlar menyusi"),
        ("natijalar", "Mening natijalarim"),
        ("til", "Tilni o‘zgartirish"),
        ("haqida", "Bot va manbalar haqida"),
        ("bekor", "Testni bekor qilish"),
    ],
    "ru": [
        ("start", "Меню тестов"),
        ("natijalar", "Мои результаты"),
        ("til", "Сменить язык"),
        ("haqida", "О боте и источниках"),
        ("bekor", "Отменить тест"),
    ],
}


def _commands(lang: str) -> list[BotCommand]:
    return [BotCommand(command=c, description=d) for c, d in COMMANDS[lang]]


async def set_commands(bot: Bot) -> None:
    # O'zbekcha — standart ro'yxat (tili boshqa bo'lganlar ham shuni ko'radi),
    # ruscha — Telegram interfeysi rus tilida bo'lganlar uchun.
    await bot.set_my_commands(_commands("uz"), scope=BotCommandScopeDefault())
    await bot.set_my_commands(
        _commands("ru"), scope=BotCommandScopeDefault(), language_code="ru"
    )


async def main() -> None:
    logging.basicConfig(
        level=LOG_LEVEL,
        format="%(asctime)s %(levelname)-8s %(name)s: %(message)s",
    )

    await db.init()

    bot = Bot(BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dispatcher = Dispatcher(storage=MemoryStorage())
    dispatcher.include_router(build_router())

    me = await bot.get_me()
    logging.info("Ishga tushdi: @%s (id=%s)", me.username, me.id)

    await set_commands(bot)
    await bot.delete_webhook(drop_pending_updates=True)
    try:
        await dispatcher.start_polling(bot)
    finally:
        await bot.session.close()
        await db.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.info("To‘xtatildi")
