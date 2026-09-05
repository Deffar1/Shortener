from aiogram import Bot, Dispatcher
from aiogram.methods import DeleteWebhook
from aiogram.types import ErrorEvent
from src.bot.middleware import DatabaseMiddleware
from src.bot.messages import ERROR_OCCURED
from src.bot.handlers import router as bot_router
from src.core.config import settings
from src.core.logger import logger

bot = Bot(token=settings.BOT_TOKEN)

dp = Dispatcher()

bot_router.message.middleware(DatabaseMiddleware())
dp.include_router(bot_router)

@dp.error()
async def global_error_handler(event: ErrorEvent):
    logger.exception(f"Unhandled error in Telegram Bot: {event.exception}")
    if event.update.message:
        await event.update.message.answer(ERROR_OCCURED)

async def start_bot() -> None:
    logger.info("Starting Telegram bot...")

    await bot(DeleteWebhook(drop_pending_updates=True))
    await dp.start_polling(bot, handle_signals=False)

    logger.info("Telegram bot polling stopped")

async def stop_bot() -> None:
    logger.info("Stopping Telegram bot...")

    await dp.stop_polling()

    logger.info("Telegram bot stopped")
