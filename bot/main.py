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


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv('BOT_TOKEN')


async def on_startup(bot: Bot) -> None:
    """Запуск бота и запуск цикла с напоминаниями"""
    logger.info('Бот запущен, запуск напоминаний...')
    asyncio.create_task(run_reminder_loop(bot))


async def on_shutdown(bot: Bot) -> None:
    """Остановка бота с закрытием HTTP сессии"""
    logger.info('Бот остановлен, закрытие HTTP сессии...')
    await close_session()


async def main() -> None:
    if not BOT_TOKEN:
        raise RuntimeError('BOT_TOKEN не задан!')

    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )

    dp = Dispatcher(storage=MemoryStorage())

    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)

    # Регистрируем роутеры
    dp.include_router(start.router)
    dp.include_router(houses.router)
    dp.include_router(bookings.router)
    dp.include_router(support.router)

    logger.info('Starting polling...')
    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())


if __name__ == '__main__':
    asyncio.run(main())
