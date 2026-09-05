from datetime import datetime
from random import choice
from string import ascii_letters, digits
from urllib.parse import urlparse
from uuid import uuid4, UUID

from pydantic import HttpUrl
from redis.asyncio import Redis, RedisError

from src.core.config import settings
from src.core.logger import logger
from src.models.schemas import ShortUrlDTO
from src.repositories.base import BaseRepository


SHORT_URL_LENGTH = settings.SHORT_URL_LENGTH
ALPHABET = ascii_letters + digits

def generate_random_id() -> str:
    url_id = str()
    for _ in range(SHORT_URL_LENGTH):
        url_id += choice(ALPHABET)
    return url_id


def get_id_from_url(url: str) -> str:
    path = urlparse(url).path.rstrip('/')
    return path.split('/')[-1] if path else url


class URLService:
    def __init__(self, repository: BaseRepository, redis: Redis):
        self.repository = repository
        self.redis = redis

    async def get_original_url(self, url_id: str) -> str | None:
        cache_key = f"url_id:{url_id}"
        try:
            cached_url = await self.redis.get(cache_key)
            if cached_url:
                await self.redis.hincrby("url_clicks", url_id, 1)
                return cached_url
        except RedisError as e:
            logger.warning(f"Redis is down! Fallback to DB for url_id={url_id}. Error: {e}")

        short_url = await self.repository.get_data_by_url_id(url_id)
        if short_url is None:
            return None

        original_url = str(short_url.original_url)

        try:
            await self.redis.set(cache_key, original_url, ex=settings.REDIS_URL_TTL)
            await self.redis.hincrby("url_clicks", url_id, 1)
        except RedisError as e:
            logger.warning(f"Failed to cache url_id={url_id} to Redis: {e}")

            await self.repository.update_clicks_by_id(url_id)

        return original_url
    
    async def get_short_url_data(self, status_token: UUID) -> ShortUrlDTO | None:
        logger.info(f"Stats requested for token={status_token}")
        short_url = await self.repository.get_data_by_token(status_token)

        return short_url if short_url else None

    async def create_short_url(self, original_url: HttpUrl) -> ShortUrlDTO:
        url_id = generate_random_id()
        while await self.repository.get_data_by_url_id(url_id):
            logger.warning("url_id collision: the generated random ID already exists in the database; the service generates a new one (retry)")
            url_id = generate_random_id()

        logger.info(f"Short URL created: url_id='{url_id}' -> original_url='{str(original_url)}'")
            
        status_token = uuid4()
        created_at = datetime.now().replace(microsecond=0)

        short_url = ShortUrlDTO(
            url_id=url_id,
            original_url=original_url,
            clicks=0,
            created_at=created_at,
            status_token=status_token
        )

        await self.repository.insert_data(short_url)

        return short_url
