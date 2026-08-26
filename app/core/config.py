from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    MODE: Literal['TEST', 'DEV','LOCAL','PROD'] = "LOCAL"

    DB_HOST: str
    DB_PORT: int
    DB_USER: str
    DB_PASS: str
    DB_NAME: str

    app_name: str = "Демо авторизации: session и JWT"
    
    REDIS_HOST: str
    REDIS_PORT: int

    @property
    def REDIS_URL(self):
        
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}"

    @property
    def DB_URL(self):
        return f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASS}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int
    REFRESH_TOKEN_EXPIRE_MINUTES: int
    SESSION_TTL_MINUTES: int
    SESSION_ABSOLUTE_TIMEOUT_DAYS: int
    SESSION_COOKIE_NAME: str
    SESSION_COOKIE_SECURE: bool
    SESSION_COOKIE_DOMAIN: str

    ACCESS_COOKIE_NAME: str
    REFRESH_COOKIE_NAME: str

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=False, extra="ignore"
    )


settings = Settings()
