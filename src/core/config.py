from pydantic_settings import SettingsConfigDict, BaseSettings

class Settings(BaseSettings):
    SHORT_URL_LENGTH: int
    CLICKS_FLUSH_INTERVAL: int
    BOT_TOKEN: str

    DB_HOST: str
    DB_USER: str
    DB_PASS: str
    DB_NAME: str
    DB_TYPE: str

    POSTGRES_POOL_SIZE: int
    POSTGRES_MAX_OVERFLOW: int

    MONGO_COLLECTION: str

    REDIS_HOST: str
    REDIS_MAX_CONNECTIONS: int
    REDIS_URL_TTL: int

    @property
    def DATABASE_URL_mongodb(self):
        return f"mongodb://{self.DB_USER}:{self.DB_PASS}@{self.DB_HOST}:27017"

    @property
    def DATABASE_URL_asyncpg(self):
        return f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASS}@{self.DB_HOST}:5432/{self.DB_NAME}"

    @property
    def REDIS_URL(self):
        return f"redis://{self.REDIS_HOST}:6379"

    model_config = SettingsConfigDict(env_file=".env")

settings = Settings()
