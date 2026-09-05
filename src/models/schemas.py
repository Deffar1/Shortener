from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, HttpUrl


class ShortUrlDTO(BaseModel):
    url_id: str
    original_url: HttpUrl
    clicks: int
    created_at: datetime
    status_token: UUID


class ClicksBatchDTO(BaseModel):
    url_id: str
    clicks: int

    def __repr__(self):
        return f"URL id: {self.url_id}; Clicks: {self.clicks}"
