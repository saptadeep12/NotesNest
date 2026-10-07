from functools import lru_cache
from typing import Literal

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "NotesNest API"
    app_env: str = "development"
    database_url: str = "sqlite:///./notesnest.db"
    secret_key: str = "change-me"
    cors_origins: str = "http://localhost:3000"
    storage_dir: str = "./storage"
    storage_backend: Literal["local", "s3"] = "local"
    s3_bucket: str | None = None
    s3_endpoint_url: str | None = None
    s3_access_key_id: str | None = None
    s3_secret_access_key: str | None = None
    s3_region: str = "auto"
    s3_presign_seconds: int = 300

    @model_validator(mode="before")
    @classmethod
    def normalize_database_url(cls, values: object) -> object:
        if isinstance(values, dict):
            url = values.get("database_url")
            if isinstance(url, str):
                if url.startswith("postgres://"):
                    values["database_url"] = "postgresql+psycopg://" + url.removeprefix(
                        "postgres://"
                    )
                elif url.startswith("postgresql://"):
                    values["database_url"] = "postgresql+psycopg://" + url.removeprefix(
                        "postgresql://"
                    )
        return values

    @model_validator(mode="after")
    def validate_storage(self) -> "Settings":
        if self.storage_backend == "s3":
            missing = [
                name
                for name, value in (
                    ("S3_BUCKET", self.s3_bucket),
                    ("S3_ENDPOINT_URL", self.s3_endpoint_url),
                    ("S3_ACCESS_KEY_ID", self.s3_access_key_id),
                    ("S3_SECRET_ACCESS_KEY", self.s3_secret_access_key),
                )
                if not value
            ]
            if missing:
                raise ValueError(
                    "STORAGE_BACKEND=s3 requires: " + ", ".join(missing)
                )
        return self

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
