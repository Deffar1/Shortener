from datetime import datetime
from uuid import UUID

from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    def __repr__(self):
        cols = []
        for col in self.__table__.columns.keys():
            cols.append(f"{col}={getattr(self, col)}")

        return f"<{self.__class__.__name__} {', '.join(cols)}>"

class ShortUrlsOrm(Base):
    __tablename__ = "shorturls"

    id: Mapped[int] = mapped_column(primary_key=True)
    url_id: Mapped[str] = mapped_column(index=True, unique=True)
    original_url: Mapped[str]
    clicks: Mapped[int]
    created_at: Mapped[datetime]
    status_token: Mapped[UUID] = mapped_column(index=True, unique=True)

    