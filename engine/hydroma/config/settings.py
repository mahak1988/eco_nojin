"""HyDroMa engine configuration — single source of truth (Phase 0).

Uses pydantic-settings so every runtime value can be overridden via
environment variables or a `.env` file. Never hard-code secrets.

References:
- 12-factor app configuration (https://12factor.net/config)
"""

from functools import lru_cache

from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Default development secret — MUST be overridden in production.
# `is_secure_secret` and the production guard enforce this.
_DEV_SECRET = "dev-in…e-me"


class Settings(BaseSettings):
    """Runtime configuration for EcoNojin / HyDroMa.

    Environment variables take precedence over `.env` file values,
    which take precedence over these defaults.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # --- Platform ---
    project_name: str = "Eco Nojin"
    engine_name: str = "HyDroMa"
    environment: str = "development"  # development | testing | production
    api_version: str = "1.5.0"
    debug: bool = False
    log_level: str = "INFO"

    # --- Security ---
    secret_key: str = _DEV_SECRET
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24 * 7      # 7 days
    refresh_token_expire_minutes: int = 60 * 24 * 30    # 30 days
    api_key_header: str = "X-API-Key"
    # Shared secret for telco webhooks (USSD/SMS/Voice). Empty = disabled.
    telco_webhook_key: str = ""

    # --- CORS (Phase 0 fix for W-003) ---
    cors_origins: list[str] = [
        "http://127.0.0.1:3000",
        "http://localhost:3000",
    ]
    allow_credentials: bool = True

    # --- Rate limiting (Phase 0) ---
    rate_limit_enabled: bool = True
    rate_limit_requests: int = 100      # requests per window per client
    rate_limit_window_seconds: int = 60

    # --- Database ---
    # Default: SQLite next to the repo (research mode).
    # Production: postgresql+psycopg://user:pass@host:5432/eco_nojin
    database_url: str = "sqlite:///./data/econojin.db"
    redis_url: str = "redis://localhost:6379/0"

    # --- External integrations ---
    # Sentinel-2 / Planetary Computer (empty = simulated data, W-001 staged)
    satellite_api_key: str = ""
    # NASA POWER (no key required, but endpoint overridable)
    nasa_power_base_url: str = "https://power.larc.nasa.gov/api"

    @field_validator("environment")
    @classmethod
    def _validate_environment(cls, v: str) -> str:
        v = v.strip().lower()
        if v not in {"development", "testing", "production"}:
            raise ValueError(f"Invalid environment: {v!r}")
        return v

    @field_validator("cors_origins")
    @classmethod
    def _validate_cors(cls, v: list[str]) -> list[str]:
        cleaned = [o.rstrip("/") for o in v if o.strip()]
        if not cleaned:
            raise ValueError("cors_origins must not be empty")
        return cleaned

    @model_validator(mode="after")
    def _production_guards(self) -> "Settings":
        """Hard security guards, enforced at construction time."""
        if self.environment == "production":
            if not self.is_secure_secret:
                raise RuntimeError(
                    "Refusing to start in production with the default dev secret. "
                    "Set SECRET_KEY in .env."
                )
            if self.cors_allow_all and self.allow_credentials:
                raise RuntimeError(
                    "Refusing to start in production with allow_origins=['*'] and "
                    "allow_credentials=True (CORS W-003). Set CORS_ORIGINS explicitly."
                )
        return self

    @property
    def is_production(self) -> bool:
        return self.environment == "production"

    @property
    def is_secure_secret(self) -> bool:
        """True when secret_key is not the known dev placeholder."""
        return self.secret_key != _DEV_SECRET

    @property
    def cors_allow_all(self) -> bool:
        return "*" in self.cors_origins


@lru_cache
def get_settings() -> Settings:
    """Return cached settings (fast, env-read once per process)."""
    return Settings()
