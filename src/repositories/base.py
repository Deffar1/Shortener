from abc import abstractmethod, ABC
from uuid import UUID
from typing import List

from src.models.schemas import ShortUrlDTO, ClicksBatchDTO


class BaseRepository(ABC):

    @abstractmethod
    async def insert_data(self, data: ShortUrlDTO) -> None:
        pass

    @abstractmethod
    async def update_clicks_by_id(
        self, 
        id: str
    ) -> ShortUrlDTO | None:
        pass

    @abstractmethod
    async def get_data_by_token(self, token: UUID) -> ShortUrlDTO | None:
        pass

    @abstractmethod
    async def get_data_by_url_id(self, url_id: str) -> ShortUrlDTO | None:
        pass

    @abstractmethod
    async def batch_increment_clicks(self, clicks_batch: List[ClicksBatchDTO]) -> None:
        pass
