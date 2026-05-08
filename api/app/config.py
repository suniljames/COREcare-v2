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

    # Email — see ADR-011 / issue #120.
    email_transport: str = "console"  # "console" | "sendgrid"
    email_from_address: str = "noreply@corecare.local"
    sendgrid_api_key: str = ""

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}

    @property
    def is_dev_mode(self) -> bool:
        """Single source of truth for dev-mode behavior gates — see #241."""
        return self.environment == "development"


settings = Settings()
