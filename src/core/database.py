from contextlib import asynccontextmanager
from typing import AsyncGenerator

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker, AsyncEngine

from src.core.config import settings
from src.core.logger import logger
from src.models.models import Base

pg_engine: AsyncEngine | None = None
pg_session_factory: async_sessionmaker[AsyncSession] | None = None
mongo_client: AsyncIOMotorClient | None = None

async def init_db():
    global pg_engine, pg_session_factory, mongo_client
    if settings.DB_TYPE == "postgres":
        pg_engine = create_async_engine(
            settings.DATABASE_URL_asyncpg,
            pool_size=settings.POSTGRES_POOL_SIZE,
            max_overflow=settings.POSTGRES_MAX_OVERFLOW,
            pool_pre_ping=True
        )
        pg_session_factory = async_sessionmaker(
            pg_engine, expire_on_commit=False
        )
        async with pg_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    elif settings.DB_TYPE == "mongo":
        mongo_client = AsyncIOMotorClient(
            settings.DATABASE_URL_mongodb,
            serverSelectionTimeoutMS=3000
        )

        await mongo_client[settings.DB_NAME][settings.MONGO_COLLECTION].create_index("url_id", unique=True)
        await mongo_client[settings.DB_NAME][settings.MONGO_COLLECTION].create_index("status_token", unique=True)
    else:
        raise RuntimeError("Wrong Database type")

async def close_db():
    global pg_engine, mongo_client
    if pg_engine:
        await pg_engine.dispose()
        logger.info("PostgreSQL connection pool closed")
    elif mongo_client:
        mongo_client.close()
        logger.info("MongoDB connection closed")

@asynccontextmanager
async def get_postgres_session() -> AsyncGenerator[AsyncSession, None]:
    async with pg_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception as e:
            await session.rollback()
            raise e

def get_mongo_db() -> AsyncIOMotorDatabase:
    return mongo_client[settings.DB_NAME]
