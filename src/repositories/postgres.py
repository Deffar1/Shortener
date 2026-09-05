from typing import List, Dict
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, bindparam, case

from src.models.models import ShortUrlsOrm
from src.models.schemas import ShortUrlDTO, ClicksBatchDTO
from src.repositories.base import BaseRepository


class PostgresRepository(BaseRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def insert_data(self, data: ShortUrlDTO) -> None:
        data_dict = data.model_dump()
        data_dict["original_url"] = str(data_dict["original_url"])
        short_url = ShortUrlsOrm(**data_dict)
        self.session.add(short_url)
        await self.session.flush()

    async def update_clicks_by_id(self, id: str) -> ShortUrlDTO | None:
        stmt = (
            update(ShortUrlsOrm)
            .where(ShortUrlsOrm.url_id == id)
            .values(clicks=ShortUrlsOrm.clicks + 1)
            .returning(ShortUrlsOrm)
        )
        result = await self.session.execute(stmt)
        short_url = result.scalar_one_or_none()
        return ShortUrlDTO.model_validate(short_url, from_attributes=True) if short_url else None

    async def get_data_by_token(self, token: UUID) -> ShortUrlDTO | None:
        query = select(ShortUrlsOrm).where(ShortUrlsOrm.status_token == token)
        result = await self.session.execute(query)
        short_url = result.scalar_one_or_none()
        return ShortUrlDTO.model_validate(short_url, from_attributes=True) if short_url else None

    async def get_data_by_url_id(self, url_id: str) -> ShortUrlDTO | None:
        query = select(ShortUrlsOrm).where(ShortUrlsOrm.url_id == url_id)
        result = await self.session.execute(query)
        short_url = result.scalar_one_or_none()
        return ShortUrlDTO.model_validate(short_url, from_attributes=True) if short_url else None

    async def batch_increment_clicks(self, clicks_batch: List[ClicksBatchDTO]) -> None:
        clicks_map: Dict[str, int] = {
            item.url_id: item.clicks for item in clicks_batch
        }
        stmt = (
            update(ShortUrlsOrm)
            .where(ShortUrlsOrm.url_id.in_(list(clicks_map.keys())))
            .values(
                clicks=ShortUrlsOrm.clicks + case(
                    clicks_map, 
                    value=ShortUrlsOrm.url_id
                )
            )
            .execution_options(synchronize_session=None)
        )
        await self.session.execute(stmt)
