from redis.asyncio import ConnectionPool, Redis
from src.core.config import settings
from src.core.logger import logger

redis_pool: ConnectionPool | None = None

async def init_redis():
    global redis_pool

    redis_pool = ConnectionPool.from_url(
        settings.REDIS_URL,
        decode_responses=True,
        max_connections=settings.REDIS_MAX_CONNECTIONS
    )
    client = Redis(connection_pool=redis_pool)
    await client.ping()
    await client.aclose()

async def close_redis():
    global redis_pool
    if redis_pool:
        await redis_pool.disconnect()
        logger.info("Redis connection pool closed")

def get_redis() -> Redis:
    return Redis(connection_pool=redis_pool)
