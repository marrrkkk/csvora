from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "CSV Import Fixer API"
    app_env: str = "development"
    app_debug: bool = False
    log_level: str = "INFO"
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_prefix: str = "/api/v1"

    postgres_host: str = "postgres"
    postgres_port: int = 5432
    postgres_user: str = "csv_import_fixer"
    postgres_password: str = "csv_import_fixer"
    postgres_db: str = "csv_import_fixer"
    database_url: str | None = None

    redis_host: str = "redis"
    redis_port: int = 6379
    redis_db: int = 0
    redis_url: str = Field(default="redis://redis:6379/0")

    celery_broker_url: str = Field(default="redis://redis:6379/0")
    celery_result_backend: str = Field(default="redis://redis:6379/1")
    max_upload_size_bytes: int = 10 * 1024 * 1024

    storage_backend: str = "local"
    local_storage_root: str = "/data/storage"

    s3_endpoint_url: str | None = None
    s3_access_key_id: str | None = None
    s3_secret_access_key: str | None = None
    s3_region: str = "us-east-1"
    s3_bucket_name: str = "csv-import-fixer"
    s3_use_ssl: bool = False

    analysis_preview_rows: int = 10
    analysis_sample_lines: int = 50
    transform_phone_warning_is_error: bool = False
    import_requires_template: bool = False

    auth_enabled: bool = True
    rate_limit_enabled: bool = True
    rate_limit_per_minute: int = 120
    rate_limit_global_per_minute: int = 300
    rate_limit_window_seconds: int = 60
    rate_limit_fail_open: bool = True
    rate_limit_redis_timeout_ms: int = 250
    metrics_enabled: bool = True
    readiness_db_timeout_ms: int = 500
    readiness_redis_timeout_ms: int = 500
    readiness_storage_timeout_ms: int = 500

    openrouter_api_key: str | None = None
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    openrouter_model: str = "openai/gpt-4o-mini"
    openrouter_http_referer: str = "https://csvora.local"
    openrouter_app_title: str = "Csvora API"
    ai_mapping_enabled: bool = False
    ai_timeout_seconds: float = 20.0
    ai_max_retries: int = 1


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()


def build_database_url(settings: Settings) -> str:
    if settings.database_url:
        return settings.database_url
    return (
        f"postgresql+psycopg://{settings.postgres_user}:{settings.postgres_password}"
        f"@{settings.postgres_host}:{settings.postgres_port}/{settings.postgres_db}"
    )
