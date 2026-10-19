from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+asyncpg://theater:theater@localhost:5432/theater"
    redis_url: str = "redis://localhost:6379/0"

    # Исходящий трафик к Telegram и LLM идёт через контейнер vpn (Xray).
    # Пустое значение — ходить напрямую (локальная разработка).
    tg_proxy_url: str | None = None
    llm_proxy_url: str | None = None

    llm_base_url: str = "https://opencode.ai/zen/go/v1"
    llm_api_key: str | None = None

    log_level: str = "INFO"


@lru_cache
def get_settings() -> Settings:
    return Settings()
