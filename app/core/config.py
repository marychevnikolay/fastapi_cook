from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    DB_HOST: str
    DB_PORT: int
    DB_USER: str
    DB_PASS: str
    DB_NAME: str

    app_name: str = "Демо авторизации: session и JWT"
    # database_url: str = Field(default="postgresql+asyncpg://postgres:1234567@localhost:5432/cook", alias="DATABASE_URL")
    # jwt_secret_key: str = Field(default="change-me", alias="JWT_SECRET_KEY")
    # jwt_algorithm: str = "HS256"
    # access_token_expires_minutes: int = 15
    # refresh_token_expires_minutes: int = 60 * 24 * 30
    # session_ttl_minutes: int = 60 * 24
    # session_extend_minutes: int = 60 * 24 * 7
    # session_rolling_interval_minutes: int = 10
    # session_absolute_timeout_days: int = 30
    # session_cookie_name: str = "session_id"
    # session_cookie_secure: bool = False
    # session_cookie_domain: str | None = None
    # access_cookie_name: str = "access_token"
    # refresh_cookie_name: str = "refresh_token"

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
