from typing import AsyncGenerator

from fastapi import Depends
from redis.asyncio import Redis

from src.core.config import settings
from src.core.database import get_postgres_session, get_mongo_db
from src.core.redis import get_redis
from src.repositories.base import BaseRepository
from src.repositories.mongo import MongoRepository
from src.repositories.postgres import PostgresRepository
from src.services.url_service import URLService

async def get_repository() -> AsyncGenerator[BaseRepository, None]:
    if settings.DB_TYPE == "postgres":
        async with get_postgres_session() as session:
            yield PostgresRepository(session)
    
    elif settings.DB_TYPE == "mongo":
        db = get_mongo_db()
        yield MongoRepository(db)
        
    else:
        raise ValueError(f"Unknown DB_TYPE: {settings.DB_TYPE}")

async def get_redis_dependency() -> AsyncGenerator[Redis, None]:
    redis = get_redis()
    try:
        yield redis
    finally:
        await redis.aclose()

def get_url_service(
        repository: BaseRepository = Depends(get_repository),
        redis: Redis = Depends(get_redis_dependency)
) -> URLService:
    return URLService(repository, redis)

