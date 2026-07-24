from __future__ import annotations

from functools import lru_cache

from pydantic import Field, RedisDsn
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Typed runtime settings loaded from the environment or a local `.env` file."""

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore", populate_by_name=True
    )

    app_env: str = Field(default="development", validation_alias="APP_ENV")
    database_url: str = Field(
        default="postgresql+asyncpg://ai_course:ai_course@localhost:5432/ai_course",
        validation_alias="DATABASE_URL",
    )
    redis_url: RedisDsn = Field(
        default=RedisDsn("redis://localhost:6379/0"), validation_alias="REDIS_URL"
    )
    celery_result_backend_url: RedisDsn = Field(
        default=RedisDsn("redis://localhost:6379/1"), validation_alias="CELERY_RESULT_BACKEND_URL"
    )
    log_level: str = Field(default="INFO", validation_alias="LOG_LEVEL")
    minio_endpoint: str = Field(default="localhost:9000", validation_alias="MINIO_ENDPOINT")
    minio_access_key: str = Field(default="minio", validation_alias="MINIO_ACCESS_KEY")
    minio_secret_key: str = Field(default="minio12345", validation_alias="MINIO_SECRET_KEY")
    minio_bucket: str = Field(default="ai-course", validation_alias="MINIO_BUCKET")
    searxng_url: str = Field(default="http://localhost:8080", validation_alias="SEARXNG_URL")
    llm_provider: str = Field(default="", validation_alias="LLM_PROVIDER")
    llm_api_key: str = Field(default="", validation_alias="LLM_API_KEY")
    service_name: str = Field(default="ai-course-api", validation_alias="SERVICE_NAME")
    otel_exporter_otlp_endpoint: str = Field(
        default="", validation_alias="OTEL_EXPORTER_OTLP_ENDPOINT"
    )
    sentry_dsn: str = Field(default="", validation_alias="SENTRY_DSN")
    rate_limit_requests: int = Field(default=120, ge=1, validation_alias="RATE_LIMIT_REQUESTS")
    rate_limit_window_seconds: int = Field(
        default=60, ge=1, validation_alias="RATE_LIMIT_WINDOW_SECONDS"
    )
    metrics_token: str = Field(default="", validation_alias="METRICS_TOKEN")

    def production_errors(self) -> tuple[str, ...]:
        """Report required production integration configuration without exposing values."""

        if self.app_env != "production":
            return ()
        missing = []
        if not self.metrics_token:
            missing.append("METRICS_TOKEN")
        if not self.otel_exporter_otlp_endpoint:
            missing.append("OTEL_EXPORTER_OTLP_ENDPOINT")
        return tuple(missing)


@lru_cache
def get_settings() -> Settings:
    """Return the process-wide immutable settings instance."""

    return Settings()
