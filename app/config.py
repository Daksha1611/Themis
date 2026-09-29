"""Application configuration. Every setting comes from an environment variable."""

from functools import lru_cache

from pydantic import SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    github_app_id: str
    github_private_key: SecretStr
    github_webhook_secret: SecretStr
    redis_url: str = "redis://localhost:6379"
    langfuse_public_key: str
    langfuse_secret_key: SecretStr
    langfuse_host: str = "https://cloud.langfuse.com"
    database_url: str
    log_level: str = "INFO"

    @field_validator("github_private_key", mode="before")
    @classmethod
    def _unescape_newlines(cls, value: str) -> str:
        # .env files cannot hold multi-line values reliably, so accept "\n"-escaped PEM keys.
        return value.replace("\\n", "\n")


@lru_cache
def get_settings() -> Settings:
    return Settings()
