from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "NotesNest API"
    app_env: str = "development"
    database_url: str = "sqlite:///./notesnest.db"
    secret_key: str = "change-me"
    cors_origins: str = "http://localhost:3000"
    storage_dir: str = "./storage"

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
