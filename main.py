import asyncio
import logging
import os
import sys

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from dotenv import load_dotenv

from handlers import admin, monitoring
from services.database import DatabaseService
from services.monitor import MonitorService
from services.neynar import NeynarService

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('bot.log', encoding='utf-8')
    ]
)

logger = logging.getLogger(__name__)


async def main():
    """Главная функция запуска бота"""
    logger.info("🚀 Starting Farcaster Monitor Bot...")
    
    bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
    neynar_api_key = os.getenv('NEYNAR_API_KEY')
    
    if not bot_token or not neynar_api_key:
        logger.error("❌ Missing tokens in .env file")
        return
    
    # Инициализация сервисов
    db = DatabaseService(db_path="farcaster_monitor.db")
    neynar = NeynarService(api_key=neynar_api_key)
    
    # Инициализация бота
    bot = Bot(token=bot_token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher()
    
    # Регистрация роутеров
    dp.include_router(admin.router)
    dp.include_router(monitoring.router)
    
    logger.info("✅ Bot initialized")
    
    # Запуск мониторинга
    monitor = MonitorService(db=db, neynar=neynar, bot=bot, check_interval=30)
    monitor_task = asyncio.create_task(monitor.start())
    
    try:
        logger.info("✅ Starting bot polling...")
        await dp.start_polling(bot, db=db, neynar=neynar)
    finally:
        await monitor.stop()
        await monitor_task
        await bot.session.close()


if __name__ == '__main__':
    asyncio.run(main())