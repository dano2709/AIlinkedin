from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "AIlinkedin"
    app_env: str = "development"
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    database_url: str = "postgresql+psycopg://aiuser:aipassword@localhost:5432/ailinkedin"
    redis_url: str = "redis://localhost:6379/0"

    apify_api_token: str = ""
    apify_actor_id: str = Field(default="bebity/linkedin-jobs-scraper")
    apify_base_url: str = "https://api.apify.com/v2"
    apify_timeout_seconds: float = 180.0
    apify_default_rows: int = Field(default=25, ge=1, le=1000)

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
