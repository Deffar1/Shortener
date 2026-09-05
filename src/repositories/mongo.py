from typing import List
from uuid import UUID

from motor.motor_asyncio import AsyncIOMotorDatabase, AsyncIOMotorCollection
from pymongo import UpdateOne

from src.core.config import settings
from src.models.schemas import ShortUrlDTO, ClicksBatchDTO
from src.repositories.base import BaseRepository


class MongoRepository(BaseRepository):
    def __init__(self, db: AsyncIOMotorDatabase):
        self.collection: AsyncIOMotorCollection = db[settings.MONGO_COLLECTION]

    async def insert_data(self, data: ShortUrlDTO) -> None:
        await self.collection.insert_one(data.model_dump(mode="json"))

    async def update_clicks_by_id(self, id: str) -> ShortUrlDTO | None:
        data = await self.collection.find_one_and_update(
            filter={"url_id": id},
            update={"$inc": {"clicks": 1}},
            return_document=True
        )
        return ShortUrlDTO.model_validate(data) if data else None

    async def get_data_by_token(self, token: UUID) -> ShortUrlDTO | None:
        filter = {"status_token": str(token)}
        data = await self.collection.find_one(filter)
        return ShortUrlDTO.model_validate(data) if data else None

    async def get_data_by_url_id(self, url_id: str) -> ShortUrlDTO | None:
        filter = {"url_id": url_id}
        data = await self.collection.find_one(filter)
        return ShortUrlDTO.model_validate(data) if data else None

    async def batch_increment_clicks(self, clicks_batch: List[ClicksBatchDTO]) -> None:
        operations = [
            UpdateOne(
                {"url_id": item.url_id}, 
                {"$inc": {"clicks": item.clicks}}
            )
            for item in clicks_batch
        ]

        if operations:
            await self.collection.bulk_write(operations)
