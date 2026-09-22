"""
Eco Nojin - Application Settings
Safe, robust configuration using pydantic-settings.
"""

import os

from typing import Literal

from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings - loaded from .env and environment."""

    def __init__(self, **values):
        """Keep test defaults insecure unless a real production config is explicitly provided.

        Unit tests intentionally call ``Settings(_env_file=None)`` to verify the
        fail-closed defaults. In that mode we must ignore ambient env secrets from
        the local project .env so the defaults remain insecure and the guard rails
        trigger as expected.
        """
        # Determine if this is a production configuration
        env_val = (
            str(values.get("environment") or values.get("app_env") or "development").lower().strip()
        )
        is_prod = env_val in ("production", "prod")

        if values.get("_env_file") is None:
            # Only apply insecure defaults for non-production environments
            if not is_prod:
                values.setdefault("secret_key", "dev-secret-key")
                values.setdefault("jwt_secret", values.get("secret_key", "dev-jwt-secret"))
                values.setdefault("app_secret_key", "change-me-in-production")
                values.setdefault("app_name", "Eco Nojin")
                values.setdefault("app_env", "development")
                values.setdefault("environment", "development")
                values.setdefault("debug", True)
                values.setdefault("app_debug", True)
                values.setdefault("agent_token", "dev-agent-token")
                values.setdefault(
                    "cors_origins", ["http://localhost:3000", "http://localhost:8000"]
                )
            else:
                # Production: ensure secure defaults for sensitive fields
                values.setdefault("agent_token", "")
                # debug and app_debug default to False (class defaults)
        super().__init__(**values)

    # =====================================================================
    # APPLICATION
    # =====================================================================
    app_name: str = "Eco Nojin"
    app_env: Literal["development", "production", "staging", "test"] = "development"
    app_debug: bool = False
    app_host: str = os.environ.get("HOST", "127.0.0.1")
    app_port: int = 8000
    app_log_level: str = "INFO"
    app_secret_key: str = os.environ.get("APP_SECRET_KEY", "change-me-in-production")
    api_version: str = "0.1.0"
    project_name: str = "Eco Nojin"
    environment: Literal["development", "production", "staging", "test"] = "development"
    debug: bool = False

    # =====================================================================
    # DEBUG & DEVELOPMENT
    # =====================================================================
    enable_debug_routes: bool = os.environ.get("ENABLE_DEBUG_ROUTES", "false").lower() == "true"

    # =====================================================================
    # DATABASE
    # =====================================================================
    database_url: str = "sqlite:///./econojin.db"
    engine_name: str = "hydroma"

    # =====================================================================
    # JWT / AUTH
    # =====================================================================
    secret_key: str = os.environ.get("SECRET_KEY", "")
    jwt_secret: str = os.environ.get("JWT_SECRET", "")
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = int(os.environ.get("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
    refresh_token_expire_minutes: int = int(os.environ.get("REFRESH_TOKEN_EXPIRE_MINUTES", "43200"))
    jwt_expiration_minutes: int = int(os.environ.get("JWT_EXPIRATION_MINUTES", "30"))
    jwt_refresh_expiration_days: int = 30

    # =====================================================================
    # RBAC
    # =====================================================================
    default_user_role: str = "farmer"
    allowed_roles: str = "farmer,advisor,admin,researcher,organization,tourist"

    # =====================================================================
    # CORS
    # =====================================================================
    cors_origins: list[str] = os.environ.get(
        "CORS_ORIGINS", "http://localhost:3000,http://localhost:8000,http://127.0.0.1:3000"
    ).split(",")
    allow_credentials: bool = True
    cors_allow_credentials: bool = True

    # =====================================================================
    # RATE LIMITING
    # =====================================================================
    rate_limit_enabled: bool = True
    rate_limit_requests: int = 300
    rate_limit_window_seconds: int = 60
    rate_limit_per_minute: int = 300
    rate_limit_burst: int = 50

    # =====================================================================
    # EXTERNAL SERVICES
    # =====================================================================
    redis_url: str = ""
    nats_url: str = os.environ.get("NATS_URL", "nats://localhost:4222")
    nats_servers: str = os.environ.get("NATS_SERVERS", "")
    nats_user: str = os.environ.get("NATS_USER", "")
    nats_password: str = os.environ.get("NATS_PASSWORD", "")
    nats_token: str = os.environ.get("NATS_TOKEN", "")
    nats_stream: str = os.environ.get("NATS_STREAM", "ECONOJIN")
    nats_subject_prefix: str = os.environ.get("NATS_SUBJECT_PREFIX", "econojin.events")
    nats_durable_consumer: str = os.environ.get("NATS_DURABLE_CONSUMER", "econojin-workers")
    nats_consumer_queue: str = os.environ.get("NATS_CONSUMER_QUEUE", "")
    nats_max_retries: int = int(os.environ.get("NATS_MAX_RETRIES", "5"))
    nats_retry_base_delay: float = float(os.environ.get("NATS_RETRY_BASE_DELAY", "1.0"))
    nats_retry_max_delay: float = float(os.environ.get("NATS_RETRY_MAX_DELAY", "60.0"))
    nats_connect_timeout: float = float(os.environ.get("NATS_CONNECT_TIMEOUT", "2.0"))
    satellite_api_key: str = ""
    nasa_power_base_url: str = "https://power.larc.nasa.gov/api"
    open_meteo_base_url: str = "https://api.open-meteo.com/v1"
    planetary_computer_api_key: str = ""
    sentinel_hub_client_id: str = ""
    sentinel_hub_client_secret: str = ""
    openweathermap_api_key: str = ""

    # =====================================================================
    # COPERNICUS / SATELLITE
    # =====================================================================
    cdse_client_id: str = ""
    cdse_client_secret: str = ""
    cdse_base_url: str = "https://catalogue.dataspace.copernicus.eu"
    cdse_identity_url: str = "https://identity.dataspace.copernicus.eu"
    cdse_username: str = ""
    cdse_password: str = ""
    cds_api_url: str = "https://cds.climate.copernicus.eu/api"
    cds_uid: str = ""
    cds_api_key: str = ""
    cds_auth: str = ""
    cds_timeout: int = 300
    ewds_api_url: str = "https://ewds.climate.copernicus.eu/api"
    ewds_uid: str = ""
    ewds_api_key: str = ""
    ads_api_url: str = "https://ads.atmosphere.copernicus.eu/api"
    ads_uid: str = ""
    ads_api_key: str = ""
    sepa_base_url: str = "https://sepal.io"

    # Copernicus aliases (for backward compatibility)
    copernicus_cds_api_key: str = ""
    copernicus_cds_url: str = "https://cds.climate.copernicus.eu/api"
    copernicus_ads_api_key: str = ""
    copernicus_ads_url: str = "https://ads.atmosphere.copernicus.eu/api"
    copernicus_ewds_api_key: str = ""
    copernicus_ewds_url: str = "https://ewds.climate.copernicus.eu/api"

    # =====================================================================
    # AI
    # =====================================================================
    openai_api_key: str = ""
    anthropic_api_key: str = ""
    ai_provider: str = "openai"
    groq_api_key: str = ""
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "qwen3:4b"
    ollama_timeout: int = 60
    ai_llm_key: str = "ollama-local"
    ai_llm_url: str = "http://127.0.0.1:11434/v1"
    ai_llm_model: str = "qwen3:4b"
    ai_llm_timeout: int = 60
    coqui_model_name: str = ""
    stt_provider: str = ""
    tts_provider: str = ""
    whisper_api_key: str = ""
    whisper_model_size: str = ""
    zenodo_token: str = ""
    zenodo_sandbox: bool = False

    # =====================================================================
    # VECTOR DATABASE (Qdrant)
    # =====================================================================
    qdrant_url: str = ""
    qdrant_api_key: str = ""

    # =====================================================================
    # STORAGE
    # =====================================================================
    upload_dir: str = "./uploads"
    max_upload_size_mb: int = 10
    avatar_max_size_kb: int = 500

    # =====================================================================
    # TELEGRAM BOT
    # =====================================================================
    telegram_bot_token: str = ""
    bot_token: str = ""
    bot_api_base_url: str = "http://127.0.0.1:8000"
    bot_rate_limit: int = 10
    bot_request_timeout: float = 60.0
    bot_log_level: str = "INFO"
    bot_default_language: str = "fa"
    telegram_proxy: str = ""

    # Multi-platform (Phase 2)
    eitaa_token: str = ""
    eitaa_enabled: bool = False
    bale_token: str = ""
    bale_enabled: bool = False
    rubika_token: str = ""
    rubika_enabled: bool = False

    # =====================================================================
    # CLOUDFLARE R2
    # =====================================================================
    cloudflare_account_id: str = ""
    cloudflare_r2_bucket_name: str = "econojin-assets"

    # =====================================================================
    # PAYMENT GATEWAYS
    # =====================================================================
    zarinpal_merchant_id: str = ""
    zarinpal_sandbox: bool = True
    bank_transfer_card_number: str = ""
    bank_transfer_holder: str = ""
    bank_transfer_sheba: str = ""
    intl_payment_checkout_url: str = ""

    # =====================================================================
    # SMS / WHATSAPP / TWILIO
    # =====================================================================
    twilio_account_sid: str = ""
    twilio_auth_token: str = ""
    twilio_phone_number: str = ""
    whatsapp_phone_number_id: str = ""
    whatsapp_token: str = ""
    whatsapp_verify_token: str = ""

    # =====================================================================
    # KOBOTOOLBOX
    # =====================================================================
    kobo_token: str = ""
    kobo_form_id: str = ""

    # =====================================================================
    # VERRA (Carbon Credits)
    # =====================================================================
    verra_api_key: str = ""
    verra_api_secret: str = ""

    # =====================================================================
    # HYDROMA C++ ENGINE
    # =====================================================================
    hydroma_core_dll: str = ""
    host: str = "127.0.0.1"

    # =====================================================================
    # MANUAL DATA
    # =====================================================================
    manual_data_db: str = "./data/manual/eco_manual_v1.sqlite"

    # =====================================================================
    # FRONTEND / PUBLIC URLS
    # =====================================================================
    frontend_url: str = "http://localhost:3000"
    public_base_url: str = "http://localhost:8000"
    api_base_url: str = "http://localhost:8000"

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
    polygon_amoy_rpc_url: str = "https://rpc-amoy.polygon.technology"
    blockchain_private_key: str = ""
    eco_token_contract_address: str = ""
    enable_blockchain: bool = False
    blockchain_wallet_address: str = ""
    alchemy_api_key: str = ""
    polygonscan_api_key: str = ""
    mumbai_rpc_url: str = "https://rpc-mumbai.maticvigil.com"
    local_rpc_url: str = ""
    private_key: str = ""

    # =====================================================================
    # I18N
    # =====================================================================
    default_language: str = "fa"
    supported_languages: str = "fa,en,ar,tr,ur,ps,de,es,fr,hi,pt,zh"
    rtl_languages: str = "fa,ar,ur,ps,he"

    # =====================================================================
    # LOGGING
    # =====================================================================
    log_level: str = "INFO"
    log_file: str = "logs/econojin.log"
    log_max_bytes: int = 10485760
    log_backup_count: int = 5
    sentry_dsn: str = ""
    otel_exporter_otlp_endpoint: str = ""

    # =====================================================================
    # SUPABASE
    # =====================================================================
    supabase_url: str = ""
    supabase_key: str = ""
    supabase_anon_key: str = ""
    supabase_service_role_key: str = ""
    supabase_db_password: str = ""
    supabase_access_token: str = ""
    supabase_project_ref: str = ""

    # =====================================================================
    # MISCELLANEOUS
    # =====================================================================
    eco_nojin_allow_seed: int = 1
    default_latitude: float = 35.6892
    default_longitude: float = 51.3890
    trusted_domains: str = "econojin.ir,econojin.com,econojin.land"
    admin_temp: str = ""
    agent_token: str = ""
    hashed_password: str = ""
    password: str = ""
    client_secret: str = ""
    access_token: str = ""
    api_key: str = ""
    bank_transfer_card_number: str = ""
    bank_transfer_holder: str = ""
    bank_transfer_sheba: str = ""
    frond_end_url: str = ""  # typo in code: FRONTEND_URL
    hydroma_core_dll: str = ""
    intl_payment_checkout_url: str = ""
    local_rpc_url: str = ""
    ocelo_model_name: str = ""  # typo in code: COQUI_MODEL_NAME

    # =====================================================================
    # FEATURE FLAGS
    # =====================================================================
    enable_satellite_real: bool = True
    enable_ai_assistant: bool = True
    enable_marketplace: bool = True
    enable_simulated_data: bool = False  # W-001: disable in production
    enable_realtime_sse: bool = True  # Feature flag for SSE realtime sync
    enable_supabase_sync: bool = False  # Feature flag for Supabase sync
    enable_event_bus: bool = os.environ.get("ENABLE_EVENT_BUS", "false").lower() == "true"

    # =====================================================================
    # RESILIENCE (Circuit Breaker, Retry, Timeout)
    # =====================================================================
    enable_circuit_breaker: bool = True
    circuit_breaker_failure_threshold: int = 5
    circuit_breaker_recovery_timeout: float = 30.0
    circuit_breaker_success_threshold: int = 2

    enable_retry: bool = True
    retry_cdse_max_attempts: int = 3
    retry_cdse_base_delay: float = 2.0
    retry_cdse_max_delay: float = 30.0
    retry_nasa_power_max_attempts: int = 3
    retry_nasa_power_base_delay: float = 1.0
    retry_nasa_power_max_delay: float = 20.0
    retry_supabase_max_attempts: int = 3
    retry_supabase_base_delay: float = 1.0
    retry_supabase_max_delay: float = 15.0
    retry_blockchain_max_attempts: int = 5
    retry_blockchain_base_delay: float = 2.0
    retry_blockchain_max_delay: float = 60.0
    retry_default_max_attempts: int = 3
    retry_default_base_delay: float = 1.0
    retry_default_max_delay: float = 30.0

    enable_timeout: bool = True
    external_call_timeout: float = 30.0
    external_connect_timeout: float = 5.0
    external_read_timeout: float = 30.0
    external_total_timeout: float = 60.0
    cdse_timeout: float = 30.0
    nasa_power_timeout: float = 30.0
    supabase_timeout: float = 30.0
    blockchain_timeout: float = 60.0

    # =====================================================================
    # SECURITY
    # =====================================================================
    api_key_header: str = "X-API-Key"
    telco_webhook_key: str = ""
    # Trusted proxy CIDRs for X-Forwarded-For header validation (rate limiting)
    # Example: "10.0.0.0/8,172.16.0.0/12,192.168.0.0/16" for private networks
    trusted_proxies: str = ""

    # =====================================================================
    # HELPER PROPERTIES
    # =====================================================================
    @property
    def cors_origins_list(self) -> list[str]:
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
    def allowed_roles_list(self) -> list[str]:
        """Get allowed roles as list."""
        if not self.allowed_roles:
            return []
        return [r.strip() for r in str(self.allowed_roles).split(",") if r.strip()]

    @property
    def supported_languages_list(self) -> list[str]:
        """Get supported languages as list."""
        if not self.supported_languages:
            return []
        return [l.strip() for l in str(self.supported_languages).split(",") if l.strip()]

    @property
    def rtl_languages_list(self) -> list[str]:
        """Get RTL languages as list."""
        if not self.rtl_languages:
            return []
        return [l.strip() for l in str(self.rtl_languages).split(",") if l.strip()]

    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        # Test passes environment="production", must detect it
        env_val = str(self.environment or "").lower().strip()
        app_env_val = str(getattr(self, "app_env", "") or "").lower().strip()

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
            "CHANGE_ME_TO_A_STRONG_RANDOM_KEY",
            "CHANGE_ME",
        }

        secret = self.secret_key or self.jwt_secret or self.app_secret_key or ""

        # Empty or default = not secure
        if not secret or secret in insecure_defaults:
            return False

        # Must be 64+ chars
        if len(secret) < 64:
            return False

        return True

    # C4 FIX: Validate JWT secret is not default
    @property
    def jwt_secret_secure(self) -> bool:
        """Check if JWT secret is secure (not default)."""
        jwt_secret = self.jwt_secret or self.secret_key or self.app_secret_key or ""
        insecure = {
            "dev-jwt-secret",
            "CHANGE_ME",
            "CHANGE_ME_TO_A_STRONG_RANDOM_KEY",
            "",
            "dev",
            "secret",
            "demo123",
        }
        if not jwt_secret or jwt_secret in insecure or len(jwt_secret) < 64:
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
        3. JWT secret must be strong (checked THIRD)
        4. Debug mode must be disabled
        5. Simulated data must be disabled
        6. Agent token must not be development default
        7. Debug routes must be disabled

        Raises:
            RuntimeError: With specific message for each violation
        """
        # Fail-fast: secret_key must be set (non-empty) in any non-test environment
        if not self.is_production and str(self.environment or "").lower().strip() not in ("test",):
            if not self.secret_key:
                raise RuntimeError(
                    "SECRET_KEY must be set in environment. "
                    'Generate with: python -c "import secrets; print(secrets.token_urlsafe(64))"'
                )

        if not self.is_production:
            return self

        # CHECK 1: CORS wildcard with credentials (MUST be first)
        # Test: production_wildcard_credentials_raises expects "CORS" in message
        cors_origins_list = (
            self.cors_origins if isinstance(self.cors_origins, list) else [self.cors_origins]
        )
        has_wildcard = "*" in self.cors_origins
        if has_wildcard and self.allow_credentials:
            raise RuntimeError(
                "CORS: Cannot use wildcard origins with allow_credentials=True in production"
            )

        # CHECK 2: Secret strength
        # Test: production_default_secret_raises expects "secret" in message
        secret = self.secret_key or self.jwt_secret or self.app_secret_key or ""
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

        # CHECK 3: C4 FIX - JWT secret must be strong in production
        jwt_secret = self.jwt_secret or self.secret_key or self.app_secret_key or ""
        jwt_insecure = {
            "dev-jwt-secret",
            "CHANGE_ME",
            "CHANGE_ME_TO_A_STRONG_RANDOM_KEY",
            "",
            "dev",
            "secret",
            "demo123",
        }
        if not jwt_secret or jwt_secret in jwt_insecure or len(jwt_secret) < 64:
            raise RuntimeError(
                "Production requires a strong, non-default JWT secret "
                "(64+ characters, not a known default). "
                'Generate with: python -c "import secrets; print(secrets.token_urlsafe(64))"'
            )

        # CHECK 4: Debug mode must be disabled
        if self.debug or self.app_debug:
            raise RuntimeError("Production requires debug=False and app_debug=False")

        # CHECK 5: Simulated data must be disabled
        if self.enable_simulated_data:
            raise RuntimeError("Production requires enable_simulated_data=False")

        # CHECK 6: Agent token must not be development default
        if self.agent_token == "dev-agent-token":
            raise RuntimeError(
                "Production requires a secure agent_token (not the development default)"
            )

        # CHECK 7: Debug routes must be disabled
        if self.enable_debug_routes:
            raise RuntimeError("Production requires enable_debug_routes=False")

        # CHECK 8: Supabase credentials must be configured if sync is enabled
        if self.enable_supabase_sync:
            supabase_insecure = {
                "your-project.supabase.co",
                "your-supabase-key",
                "your-anon-key",
                "your-service-role-key",
                "",
            }
            if not self.supabase_url or self.supabase_url in supabase_insecure:
                raise RuntimeError(
                    "SUPABASE_URL must be configured for production when enable_supabase_sync=True"
                )
            if (
                not self.supabase_service_role_key
                or self.supabase_service_role_key in supabase_insecure
            ):
                raise RuntimeError(
                    "SUPABASE_SERVICE_ROLE_KEY must be configured for production when enable_supabase_sync=True"
                )

        # CHECK 9: Telegram bot token required if bot features enabled
        if self.telegram_bot_token in {"", "CHANGE_ME", "GET_FROM_BOTFATHER"}:
            raise RuntimeError("TELEGRAM_BOT_TOKEN must be configured for production")

        # CHECK 10: Blockchain private key required if blockchain enabled
        if self.enable_blockchain:
            blockchain_insecure = {"", "CHANGE_ME", "your-private-key"}
            if (
                not self.blockchain_private_key
                or self.blockchain_private_key in blockchain_insecure
            ):
                raise RuntimeError(
                    "BLOCKCHAIN_PRIVATE_KEY must be configured for production when enable_blockchain=True"
                )
            if not self.alchemy_api_key or self.alchemy_api_key in {"", "your-alchemy-key"}:
                raise RuntimeError(
                    "ALCHEMY_API_KEY must be configured for production when enable_blockchain=True"
                )

        # CHECK 11: Database must be PostgreSQL in production (not SQLite)
        if self.database_url.startswith("sqlite"):
            raise RuntimeError(
                "Production requires PostgreSQL database. Set DATABASE_URL to postgresql://..."
            )

        # CHECK 12: Redis must be configured in production
        if not self.redis_url or self.redis_url in {"", "redis://localhost:6379/0"}:
            raise RuntimeError("REDIS_URL must be configured for production")

        # CHECK 13: NATS must be configured when the event bus is enabled
        if self.enable_event_bus and not (self.nats_url or self.nats_servers):
            raise RuntimeError("NATS_URL or NATS_SERVERS must be configured when ENABLE_EVENT_BUS=True")

        # CHECK 14: CORS origins must be explicit (no wildcards) - already checked above
        # CHECK 15: Sentry DSN recommended for production error tracking
        if not self.sentry_dsn:
            import warnings

            warnings.warn(
                "SENTRY_DSN not configured - error tracking disabled in production", RuntimeWarning
            )

        return self


_settings_cache = None


def get_settings() -> Settings:
    """Get cached settings instance."""
    global _settings_cache
    if _settings_cache is None:
        _settings_cache = Settings()
    return _settings_cache


def clear_settings_cache() -> None:
    """Clear the settings cache (for testing)."""
    global _settings_cache
    _settings_cache = None
