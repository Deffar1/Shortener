import asyncio
from src.core.logger import logger
from src.core.config import settings
from redis.asyncio import Redis
from src.core.database import get_postgres_session, get_mongo_db
from src.repositories.postgres import PostgresRepository
from src.repositories.mongo import MongoRepository
from src.models.schemas import ClicksBatchDTO
from typing import List
from src.core.redis import get_redis

RENAME_LUA_SCRIPT = """
if redis.call('EXISTS', KEYS[1]) == 1 then
    redis.call('RENAME', KEYS[1], KEYS[2])
    return 1
end
return 0
"""

RESTORE_LUA_SCRIPT = """
local temp_data = redis.call('HGETALL', KEYS[2])
for i = 1, #temp_data, 2 do
    redis.call('HINCRBY', KEYS[1], temp_data[i], tonumber(temp_data[i+1]))
end
redis.call('DEL', KEYS[2])
"""

async def flush_clicks_to_db(redis: Redis) -> None:
    main_key = "url_clicks"
    temp_key = "url_clicks:temp"

    try:
        has_data = await redis.eval(RENAME_LUA_SCRIPT, 2, main_key, temp_key)
        if not has_data:
            return

        raw_data = await redis.hgetall(temp_key)
        if not raw_data:
            await redis.delete(temp_key)
            return

        clicks_batch: List[ClicksBatchDTO] = [
            ClicksBatchDTO(url_id=url_id, clicks=int(clicks))
            for url_id, clicks in raw_data.items()
        ]

        logger.info(f"Flushing clicks data to the database for {len(clicks_batch)} links...")

        if settings.DB_TYPE == "postgres":
            async with get_postgres_session() as session:
                repository = PostgresRepository(session)
                await repository.batch_increment_clicks(clicks_batch)
        elif settings.DB_TYPE == "mongo":
            db = get_mongo_db()
            repository = MongoRepository(db)
            await repository.batch_increment_clicks(clicks_batch)

        await redis.delete(temp_key)
        logger.info("Click flush completed successfully")

    except Exception as e:
        logger.error(f"Error flushing clicks from Redis to the database: {e}")
        try:
            if await redis.exists(temp_key):
                await redis.eval(RESTORE_LUA_SCRIPT, 2, main_key, temp_key)
                logger.warning("Restored un-flushed clicks back to Redis main key due to DB error")
        except Exception as restore_err:
            logger.critical(f"Failed to restore clicks in Redis: {restore_err}")

async def periodic_click_flusher():
    while True:
        try:
            await asyncio.sleep(settings.CLICKS_FLUSH_INTERVAL)

            redis = get_redis()
            try:
                await flush_clicks_to_db(redis)
            finally:
                await redis.aclose()
            
        except asyncio.CancelledError:
            logger.info("Shutting down: final flush of clicks to the database...")

            redis = get_redis()
            try:
                await flush_clicks_to_db(redis)

                logger.info("Click flush completed successfully")
            finally:
                await redis.aclose()
            break
        except Exception as e:
            logger.error(f"Click flusher error: {e}")
