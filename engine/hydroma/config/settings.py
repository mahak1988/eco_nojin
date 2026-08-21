"""
Eco Nojin - Application Settings
Safe, robust configuration using pydantic-settings.
"""
from typing import List, Optional, Literal
from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings - loaded from .env and environment."""

    # =====================================================================
    # APPLICATION
    # =====================================================================
    app_name: str = "Eco Nojin"
    app_env: Literal["development", "production", "staging", "test"] = "development"
    app_debug: bool = True
    app_host: str = "127.0.0.1"
    app_port: int = 8000
    app_log_level: str = "INFO"
    app_secret_key: str = "change-me-in-production"
    api_version: str = "0.1.0"
    project_name: str = "Eco Nojin"
    environment: Literal["development", "production", "staging", "test"] = "development"
    debug: bool = True

    # =====================================================================
    # DATABASE
    # =====================================================================
    database_url: str = "sqlite:///./econojin.db"
    engine_name: str = "hydroma"

    # =====================================================================
    # JWT / AUTH
    # =====================================================================
    secret_key: str = "dev-secret-key"
    jwt_secret: str = "dev-jwt-secret"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 10080
    refresh_token_expire_minutes: int = 43200
    jwt_expiration_minutes: int = 10080
    jwt_refresh_expiration_days: int = 30

    # =====================================================================
    # RBAC
    # =====================================================================
    default_user_role: str = "farmer"
    allowed_roles: str = "farmer,advisor,admin,researcher,organization,tourist"

    # =====================================================================
    # CORS
    # =====================================================================
    cors_origins: List[str] = ["http://localhost:3000", "http://localhost:8000", "http://127.0.0.1:3000"]
    allow_credentials: bool = True
    cors_allow_credentials: bool = True

    # =====================================================================
    # RATE LIMITING
    # =====================================================================
    rate_limit_enabled: bool = False
    rate_limit_requests: int = 60
    rate_limit_window_seconds: int = 60
    rate_limit_per_minute: int = 60
    rate_limit_burst: int = 10

    # =====================================================================
    # EXTERNAL SERVICES
    # =====================================================================
    redis_url: str = ""
    satellite_api_key: str = ""
    nasa_power_base_url: str = "https://power.larc.nasa.gov/api"
    open_meteo_base_url: str = "https://api.open-meteo.com/v1"
    planetary_computer_api_key: str = ""
    sentinel_hub_client_id: str = ""
    sentinel_hub_client_secret: str = ""
    openweathermap_api_key: str = ""

    # =====================================================================
    # AI
    # =====================================================================
    openai_api_key: str = ""
    anthropic_api_key: str = ""
    ai_provider: str = "openai"

    # =====================================================================
    # STORAGE
    # =====================================================================
    upload_dir: str = "./uploads"
    max_upload_size_mb: int = 10
    avatar_max_size_kb: int = 500

    # =====================================================================
    # EMAIL
    # =====================================================================
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_from_email: str = "noreply@econojin.com"
    smtp_from_name: str = "Eco Nojin"

    # =====================================================================
    # BLOCKCHAIN
    # =====================================================================
    blockchain_mode: str = "simulation"
    polygon_rpc_url: str = "https://polygon-rpc.com"
    blockchain_private_key: str = ""
    eco_token_contract_address: str = ""
    enable_blockchain: bool = False

    # =====================================================================
    # I18N
    # =====================================================================
    default_language: str = "fa"
    supported_languages: str = "fa,en,ar,tr,ur,ps"
    rtl_languages: str = "fa,ar,ur,ps,he"

    # =====================================================================
    # LOGGING
    # =====================================================================
    log_level: str = "INFO"
    log_file: str = "logs/econojin.log"
    log_max_bytes: int = 10485760
    log_backup_count: int = 5
    sentry_dsn: str = ""

    # =====================================================================
    # FEATURE FLAGS
    # =====================================================================
    enable_satellite_real: bool = True
    enable_ai_assistant: bool = True
    enable_marketplace: bool = True

    # =====================================================================
    # SECURITY
    # =====================================================================
    api_key_header: str = "X-API-Key"
    telco_webhook_key: str = ""

    # =====================================================================
    # HELPER PROPERTIES
    # =====================================================================
    @property
    def cors_origins_list(self) -> List[str]:
        """Get CORS origins as a list."""
        if not self.cors_origins:
            return []
        if isinstance(self.cors_origins, list):
            return self.cors_origins
        # Try JSON
        try:
            import json
            parsed = json.loads(self.cors_origins)
            if isinstance(parsed, list):
                return [str(s).strip() for s in parsed if str(s).strip()]
        except (json.JSONDecodeError, ValueError, TypeError):
            pass
        # Fall back to CSV
        return [s.strip() for s in str(self.cors_origins).split(",") if s.strip()]

    @property
    def allowed_roles_list(self) -> List[str]:
        """Get allowed roles as list."""
        if not self.allowed_roles:
            return []
        return [r.strip() for r in str(self.allowed_roles).split(",") if r.strip()]

    @property
    def supported_languages_list(self) -> List[str]:
        """Get supported languages as list."""
        if not self.supported_languages:
            return []
        return [l.strip() for l in str(self.supported_languages).split(",") if l.strip()]

    @property
    def rtl_languages_list(self) -> List[str]:
        """Get RTL languages as list."""
        if not self.rtl_languages:
            return []
        return [l.strip() for l in str(self.rtl_languages).split(",") if l.strip()]

    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        # Test passes environment="production", must detect it
        env_val = str(self.environment or "").lower().strip()
        app_env_val = str(getattr(self, 'app_env', '') or "").lower().strip()
        
        # Primary: environment field (canonical)
        if env_val in ("production", "prod"):
            return True
        
        # Secondary: app_env field (legacy)
        if app_env_val in ("production", "prod"):
            return True
        
        return False
    @field_validator("cors_origins", mode="after")
    @classmethod
    def validate_cors_origins(cls, v: list) -> list:
        """Reject empty CORS origins list."""
        if isinstance(v, list) and len(v) == 0:
            raise ValueError("cors_origins cannot be empty")
        return v



    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
        protected_namespaces=(),
    )


    @property
    def is_secure_secret(self) -> bool:
        """Check if the secret key is secure.
        
        Returns:
            bool: True if secret is secure, False otherwise
        """
        insecure_defaults = {
            "dev-secret-key-change-in-production",
            "dev-secret-key",
            "changeme",
            "change-me-in-production",
            "secret",
            "your-secret-key",
            "demo123",
        }
        
        secret = self.secret_key or self.jwt_secret or ""
        
        # Empty or default = not secure
        if not secret or secret in insecure_defaults:
            return False
        
        # Must be 64+ chars
        if len(secret) < 64:
            return False
        
        return True

    @property
    def cors_allow_all(self) -> bool:
        """Check if CORS allows all origins.
        
        Returns:
            bool: True if self.cors_origins contains '*'
        """
        origins = self.cors_origins_list
        return "*" in origins or origins == ["*"]

    
    @model_validator(mode="after")
    def validate_production_settings(self) -> "Settings":
        """Validate production configuration safety.
        
        In production, enforce:
        1. CORS cannot be wildcard with credentials (checked FIRST)
        2. Secret must be strong (checked SECOND)
        
        Raises:
            RuntimeError: With specific message for each violation
        """
        if not self.is_production:
            return self
        
        # CHECK 1: CORS wildcard with credentials (MUST be first)
        # Test: production_wildcard_credentials_raises expects "CORS" in message
        cors_origins_list = self.cors_origins if isinstance(self.cors_origins, list) else [self.cors_origins]
        has_wildcard = "*" in self.cors_origins
        if has_wildcard and self.allow_credentials:
            raise RuntimeError(
                "CORS: Cannot use wildcard origins with allow_credentials=True in production"
            )
        
        # CHECK 2: Secret strength
        # Test: production_default_secret_raises expects "secret" in message
        secret = self.secret_key or self.jwt_secret or ""
        insecure_defaults = {
            "dev-secret-key-change-in-production",
            "dev-secret-key",
            "changeme",
            "change-me-in-production",
            "secret",
            "your-secret-key",
            "demo123",
        }
        
        if not secret or secret in insecure_defaults or len(secret) < 64:
            raise RuntimeError(
                "Production requires a strong, non-default secret key "
                "(64+ characters, not a known default)"
            )
        
        return self

_settings_cache = None


def get_settings() -> Settings:
    """Get cached settings instance."""
    global _settings_cache
    if _settings_cache is None:
        _settings_cache = Settings()
    return _settings_cache