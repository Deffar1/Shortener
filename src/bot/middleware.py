from typing import Callable, Awaitable, Dict, Any

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject

from src.core.database import get_mongo_db, get_postgres_session
from src.core.config import settings
from src.core.redis import get_redis
from src.repositories.mongo import MongoRepository
from src.repositories.postgres import PostgresRepository
from src.services.url_service import URLService

class DatabaseMiddleware(BaseMiddleware):
    async def __call__(
            self,
            handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
            event: TelegramObject,
            data: Dict[str, Any]
    ) -> Any:
        redis = get_redis()
        try:
            if settings.DB_TYPE == "postgres":
                async with get_postgres_session() as session:
                    repository = PostgresRepository(session)
                    service = URLService(repository, redis)
                    data["service"] = service

                    return await handler(event, data)

            elif settings.DB_TYPE == "mongo":
                db = get_mongo_db()
                repository = MongoRepository(db)
                service = URLService(repository, redis)
                data["service"] = service

                return await handler(event, data)
        finally:
            await redis.aclose()
