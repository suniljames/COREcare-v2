"""Application configuration via environment variables."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Database
    database_url: str = "postgresql+asyncpg://corecare:corecare@localhost:5432/corecare"

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # Clerk
    clerk_secret_key: str = ""
    clerk_publishable_key: str = ""

    # Claude API
    claude_api_key: str = ""

    # App
    environment: str = "development"
    debug: bool = True
    secret_key: str = "dev-secret-change-in-production"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
