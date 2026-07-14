from __future__ import annotations

"""Centralised configuration for FulfillCrew backend.

Uses the 12-Factor App methodology: configuration is stored in environment
variables, not code. This makes the app portable across dev/staging/prod
environments without code changes.

Design Pattern: Singleton + Immutable Dataclass
    - @dataclass(frozen=True): Settings cannot be modified after creation
    - Module-level `settings` instance: Global singleton accessible anywhere
    - os.getenv() with defaults: Works out of the box in development

Environment Variables:
    DATABASE_URL      → PostgreSQL async connection string
    REDIS_URL         → Redis pub/sub connection (optional)
    BACKEND_LOG_LEVEL → structlog filter level
    BACKEND_PORT      → HTTP server port
    CORS_ORIGINS      → Comma-separated allowed origins

Engineering Note:
    Q: Why frozen dataclass instead of a dict or global variables?
    A: Immutable dataclasses prevent accidental mutation at runtime.
       Type checkers (mypy, pyright) can verify usage. The property
       accessor (cors_origins_list) provides derived values without
       storing duplicate state.
       
    Q: How would you handle secrets like DB passwords?
    A: Use Docker secrets, AWS Secrets Manager, or HashiCorp Vault.
       Never commit secrets to Git. The .env.example file shows the
       expected keys without real values.
"""
import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    """Immutable settings loaded from environment variables with sensible defaults."""

    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost:5432/fulfillcrew"
    )
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    BACKEND_LOG_LEVEL: str = os.getenv("BACKEND_LOG_LEVEL", "info")
    BACKEND_PORT: int = int(os.getenv("BACKEND_PORT", "8000"))
    CORS_ORIGINS: str = os.getenv("CORS_ORIGINS", "http://localhost:5173,http://localhost:8080")

    @property
    def cors_origins_list(self) -> list[str]:
        """Return CORS origins as a list of strings."""
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]


settings = Settings()
