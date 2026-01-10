from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    secret_key: str
    tmdb_key: str
    proxy_url: str | None = None
    addon_path: str | None = None
    enable_https: bool | None = False
    port: int | None = 8000
    model_config = SettingsConfigDict(env_file=".env")


@lru_cache
def get_settings() -> Settings:
    return Settings()
