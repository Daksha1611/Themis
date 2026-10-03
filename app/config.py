"""Application configuration. Every setting comes from an environment variable."""

import os
from functools import lru_cache

from pydantic import Field, SecretStr, field_validator
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
    langfuse_environment: str = "development"
    database_url: str
    log_level: str = "INFO"

    # LLM providers (ADR-021): free tiers only. An empty key means "skip this provider".
    groq_api_key: SecretStr = SecretStr("")
    gemini_api_key: SecretStr = SecretStr("")
    mistral_api_key: SecretStr = SecretStr("")
    openrouter_api_key: SecretStr = SecretStr("")
    # Providers to try, in order. Each name is a LiteLLM provider prefix. JSON list in the env.
    llm_provider_cascade: list[str] = Field(
        default_factory=lambda: ["groq", "gemini", "mistral", "openrouter"]
    )
    # Model ID per provider; LiteLLM is called with "<provider>/<model>". JSON object in the env.
    llm_models: dict[str, str] = Field(
        default_factory=lambda: {
            "groq": "openai/gpt-oss-120b",
            "gemini": "gemini-3.5-flash",
            "mistral": "codestral-2508",
            "openrouter": "qwen/qwen3.8-27b:free",
        }
    )
    llm_max_tokens: int = 2048
    llm_temperature: float = 0.0
    # Eval runs pin one provider and model, cascade disabled (ADR-024). Default: the production
    # primary, so the baseline measures what production actually runs.
    eval_provider: str = "groq"
    eval_model: str = "openai/gpt-oss-120b"

    @field_validator("github_private_key", mode="before")
    @classmethod
    def _unescape_newlines(cls, value: str) -> str:
        # .env files cannot hold multi-line values reliably, so accept "\n"-escaped PEM keys.
        return value.replace("\\n", "\n")

    def api_key_for(self, provider: str) -> str:
        """A provider's API key: the `<provider>_api_key` setting, else `<PROVIDER>_API_KEY`.

        The environment fallback lets a provider be added by configuration alone.
        """
        configured = getattr(self, f"{provider}_api_key", None)
        if isinstance(configured, SecretStr):
            return configured.get_secret_value()
        return os.environ.get(f"{provider.upper()}_API_KEY", "")


@lru_cache
def get_settings() -> Settings:
    return Settings()
