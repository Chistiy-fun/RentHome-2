"""
Bot entry point. Registers all routers and starts polling.
Also launches the reminder background task via on_startup hook.

aiogram 3.7 compatible:
- DefaultBotProperties для parse_mode (Bot(parse_mode=...) устарело)
- dp.startup.register() для фоновой задачи вместо asyncio.create_task до polling
"""

import asyncio
import logging
import os

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from handlers import start, houses, bookings, support
from services.notifications import run_reminder_loop
from services.api import close_session

from dotenv import load_dotenv
load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.environ.get('BOT_TOKEN', '')


async def on_startup(bot: Bot) -> None:
    """Запускается сразу после старта polling — безопасное место для фоновых задач."""
    logger.info('Bot started, launching reminder loop...')
    asyncio.create_task(run_reminder_loop(bot))


async def on_shutdown(bot: Bot) -> None:
    """Корректно закрывает HTTP-сессию при остановке бота."""
    logger.info('Bot stopping, closing HTTP session...')
    await close_session()


async def main() -> None:
    if not BOT_TOKEN:
        raise RuntimeError('BOT_TOKEN environment variable is not set!')

    # aiogram 3.7: parse_mode задаётся через DefaultBotProperties, НЕ в конструкторе Bot
    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )

    dp = Dispatcher(storage=MemoryStorage())

    # Lifecycle hooks
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)

    # Регистрируем роутеры (порядок важен — более специфичные первыми)
    dp.include_router(start.router)
    dp.include_router(houses.router)
    dp.include_router(bookings.router)
    dp.include_router(support.router)

    logger.info('Starting polling...')
    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())


if __name__ == '__main__':
    asyncio.run(main())
