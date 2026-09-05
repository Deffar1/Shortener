import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI

from src.api.middleware import log_middleware
from src.api.router import router as api_router
from src.core.config import settings
from src.core.database import init_db, close_db
from src.core.logger import logger
from src.core.redis import init_redis, close_redis
from src.services.click_flush import periodic_click_flusher
from src.bot.bot import start_bot, stop_bot, bot

@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        logger.info(f"Connecting to database (type={settings.DB_TYPE})")
        await init_db()
        logger.info(f"Database connected!")

        logger.info("Connecting to Redis...")
        await init_redis()
        logger.info("Redis connected!")
    except Exception as e:
        logger.critical(f"Failed to connect to database (type={settings.DB_TYPE}): {e}")
        raise e

    flush_task = asyncio.create_task(
        periodic_click_flusher(),
        name="click-flusher"
    )
    logger.info("Click flusher started!")

    bot_task = asyncio.create_task(
        start_bot(),
        name="telegram-bot"
    )
    logger.info("Telegram bot task started")

    try:
        yield
    finally:
        logger.warning("Graceful shutdown initiated...")

        try:
            await stop_bot()
        except Exception as e:
            logger.exception(f"Error while stopping Telegram bot: {e}")

        try:
            if not bot_task.done():
                bot_task.cancel()
            await bot_task
        except asyncio.CancelledError:
            logger.info("Bot task cancelled")
        except Exception as e:
            logger.exception(f"Bot task finished with error: {e}")

        try:
            await bot.session.close()
        except Exception:
            logger.exception("Error while closing bot session")

        try:
            if not flush_task.done():
                flush_task.cancel()
            await flush_task
        except asyncio.CancelledError:
            logger.info("Click flusher stopped")

        logger.info("Closing Redis connection...")
        await close_redis()

        logger.info("Closing database connection...")
        await close_db()
    
app = FastAPI(lifespan=lifespan, title="Shortener")

app.include_router(api_router)
app.middleware("http")(log_middleware)
