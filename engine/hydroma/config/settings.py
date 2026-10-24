"""
Eco Nojin - Application Settings
Safe, robust configuration using pydantic-settings.
"""

from typing import Annotated, Any, Literal

from pydantic import (
    AliasChoices,
    BeforeValidator,
    Field,
    SecretStr,
    field_validator,
    model_validator,
)
from pydantic_settings import BaseSettings, SettingsConfigDict

from engine.hydroma.config.rules import apply_production_rules
from engine.hydroma.config.secrets import reveal


def _coerce_secret(value: Any) -> SecretStr:
    """Wrap a secret value exactly once.

    Idempotent on purpose. ``SecretStr``'s constructor does not type-check its
    argument, so a ``BeforeValidator(SecretStr)`` on a field that is *already*
    holding a ``SecretStr`` builds ``SecretStr(SecretStr('x'))``: an outer
    wrapper whose ``get_secret_value()`` returns a ``SecretStr`` rather than the
    plaintext. ``reveal`` then returns that inner wrapper instead of the string
    it promises, so ``reveal(settings.secret_key) == 'x'`` is False and
    ``is_secure_secret`` silently reports on the wrapper.

    That is reachable today by passing a ``SecretStr`` as an init kwarg, and it
    becomes reachable from the defaults the moment they are written as
    ``SecretStr(...)`` so that they type-check. Returning an existing wrapper
    unchanged makes both paths safe and keeps ``-> str`` honest.
    """
    if isinstance(value, SecretStr):
        return value
    return SecretStr(value)


#: A secret that still accepts a plain ``str``.
#:
#: Pydantic coerces ``str -> SecretStr`` on its own, so this looks
#: redundant. It is kept explicit because the alternative is that the
#: acceptance of a bare string is an incidental property of pydantic's
#: coercion table rather than something this package states. A secret is
#: the one field type where silently becoming stricter would break a
#: deployment, so the leniency is declared, not inherited.
#:
#: Every field below carries ``# type: ignore[assignment]`` on its
#: ``""`` default, and the ignore is load-bearing rather than lazy. Three
#: enforced rules in this repository cannot be satisfied at once:
#:
#: 1. ``tests/unit/test_settings_env_resolution.py::test_field_defaults_are_literals``
#:    walks the class body with ``ast`` and rejects any default that is a
#:    call other than ``Field(...)`` carrying a literal. So the default
#:    cannot be ``SecretStr("")``.
#: 2. ``tests/unit/test_jwt_signing_key.py`` asserts
#:    ``TestSettings.model_fields[...].default == "dev-secret-key"`` -- a
#:    plain ``str``. ``FieldInfo.default`` is the value *before*
#:    validation, so a ``SecretStr`` default fails here too.
#: 3. ``mypy --strict`` rejects assigning a ``str`` to a ``SecretStr``.
#:    ``Field(default="")`` does not help: with ``plugins = ["pydantic.mypy"]``
#:    the plugin types the ``Field(...)`` call as the type of its ``default``
#:    argument, i.e. ``str``, so the error is identical.
#:
#: The runtime is not in doubt. ``BaseSettings`` sets ``validate_default``,
#: so every one of these literals is passed through ``_coerce_secret`` at
#: construction: ``Settings().secret_key`` is a ``SecretStr`` and
#: ``repr()`` redacts it. Measured, not assumed -- see
#: ``test_every_secret_field_is_wrapped`` and the repr test in
#: ``tests/unit/test_settings_env_resolution.py``.
#:
#: The alternative that needs no ignore is annotating the fields
#: ``SecretStr | str``, which types ``settings.secret_key + "x"`` as valid.
#: Trading a real type error for fourteen comment lines is the worse deal.
SecretValue = Annotated[SecretStr, BeforeValidator(_coerce_secret)]


class Settings(BaseSettings):
    """Application settings - loaded from .env and environment."""

    # =====================================================================
    # APPLICATION
    # =====================================================================
    app_name: str = "Eco Nojin"
    app_host: str = "127.0.0.1"
    app_port: int = 8000
    app_log_level: str = "INFO"
    app_secret_key: SecretValue = "change-me-in-production"  # type: ignore[assignment]
    api_version: str = "0.1.0"
    project_name: str = "Eco Nojin"

    # `environment` and `app_env` were two separate fields holding the same
    # concept, so `is_production` had to read both and could be contradicted by a
    # half-set pair. 12-Factor III is explicit that config values must be
    # orthogonal and must not be grouped into "environments" that a deployment
    # switches between wholesale; two names for one value is that grouping by
    # another name.
    #
    # One field, several accepted environment variables. No existing `.env` has
    # to change: APP_ENV still works, ENVIRONMENT still works, and passing
    # `environment=` as an init kwarg still works because `populate_by_name` is
    # on. `app_env` survives below as a read-only property for the code that
    # still uses the old name.
    environment: Literal["development", "production", "staging", "test"] = Field(
        default="development",
        validation_alias=AliasChoices("ENVIRONMENT", "APP_ENV"),
    )
    debug: bool = Field(
        default=False,
        validation_alias=AliasChoices("DEBUG", "APP_DEBUG"),
    )

    @property
    def app_env(self) -> str:
        """Deprecated alias of :attr:`environment`.

        Kept because `services/api_gateway/main.py` reads it five times. Reads
        only; assigning to it would now raise, which is the intended direction --
        a write that appears to set the app environment but does not is exactly
        the bug the collapse removes.
        """
        return self.environment

    @property
    def app_debug(self) -> bool:
        """Deprecated alias of :attr:`debug`. Reads only; see :attr:`app_env`."""
        return self.debug

    # =====================================================================
    # DEBUG & DEVELOPMENT
    # =====================================================================
    enable_debug_routes: bool = False

    # Gates the EcoCrop crop recommender (`engine/hydroma/decision_support/recommender.py`).
    # Declared here 2026-10-03. The recommender read
    # `os.environ.get("ENABLE_CROP_RECOMMENDER", "true").lower() == "true"`
    # directly, which meant `=1`, `=on` and `=yes` all disabled it -- the inverse
    # of every similarly named flag in this tree. pydantic's boolean parser
    # accepts all of them.
    enable_crop_recommender: bool = True

    # Offline OAuth fallback (auth_supabase._local_oauth_callback) fabricates a
    # local account from a caller-supplied `code_verifier` and mints a real
    # signed session for it. That is a development affordance only: with it on,
    # anyone who can reach the callback can create an account without proving
    # anything. Default off, and refused outright in production.
    enable_local_oauth_fallback: bool = False

    # =====================================================================
    # DATABASE
    # =====================================================================
    database_url: str = "sqlite:///./data/econojin.db"
    engine_name: str = "hydroma"

    # =====================================================================
    # JWT / AUTH
    # =====================================================================
    secret_key: SecretValue = ""  # type: ignore[assignment]
    jwt_secret: SecretValue = ""  # type: ignore[assignment]
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_minutes: int = 43200
    jwt_expiration_minutes: int = 30
    jwt_refresh_expiration_days: int = 30

    # =====================================================================
    # RBAC
    # =====================================================================
    default_user_role: str = "farmer"
    # Canonical allowed roles from unified permission matrix (services.auth.permissions.sync_settings_allowed_roles)
    # farmer,advisor,admin,researcher,organization,tourist
    allowed_roles: str = "farmer,advisor,admin,researcher,organization,tourist"

    # =====================================================================
    # CORS
    # =====================================================================
    # No development port is listed by default. The 3000/3001 origins that used
    # to be here belonged to the deleted Next.js app, and `allow_credentials` is
    # True below, so an allowlisted dev port is a credentialed cross-origin hole
    # for any process on the operator's own machine. Set CORS_ORIGINS explicitly.
    # pydantic-settings parses a JSON array here, which is why the value in
    # .env / .env.example is written as `CORS_ORIGINS=["http://..."]` and not
    # comma-separated. The previous default split a comma-joined string by hand,
    # so the two formats disagreed and a JSON value produced a single element
    # containing brackets and quotes.
    cors_origins: list[str] = ["http://localhost:8000"]
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
    nats_url: str = "nats://localhost:4222"
    nats_servers: str = ""
    nats_user: str = ""
    nats_password: SecretValue = ""  # type: ignore[assignment]
    nats_token: SecretValue = ""  # type: ignore[assignment]
    nats_stream: str = "ECONOJIN"
    nats_subject_prefix: str = "econojin.events"
    nats_durable_consumer: str = "econojin-workers"
    nats_consumer_queue: str = ""
    nats_max_retries: int = 5
    nats_retry_base_delay: float = 1.0
    nats_retry_max_delay: float = 60.0
    # Retry attempts before a message is dead-lettered. Separate from
    # nats_max_retries: retries govern our own backoff, this governs the
    # JetStream consumer's own delivery cap. Conflating the two meant a
    # settings key was read that did not exist, so the getattr always fell
    # back and there was no way to configure the cap.
    nats_max_deliver: int = 5
    # The hand-rolled parser this replaced accepted {"1","true","yes"} while
    # `security.py`'s `_flag` accepted {"1","true","yes","on"} and pydantic's own
    # boolean parser accepts more again, so one variable meant different things in
    # different places. pydantic-settings parses this field now.
    nats_retry_jitter: bool = True
    nats_connect_timeout: float = 2.0
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
    telegram_bot_token: SecretValue = ""  # type: ignore[assignment]
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
    # bank_transfer_* and intl_payment_checkout_url also appeared here once.
    # They are declared once, further down, with the other integration settings;
    # see the note there.

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
    # hydroma_core_dll is declared once, with the other integration settings.
    host: str = "127.0.0.1"

    # =====================================================================
    # MANUAL DATA
    # =====================================================================
    manual_data_db: str = "./data/manual/eco_manual_v1.sqlite"

    # =====================================================================
    # PUBLIC URLS
    # =====================================================================
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
    blockchain_private_key: SecretValue = ""  # type: ignore[assignment]
    eco_token_contract_address: str = ""
    enable_blockchain: bool = False
    blockchain_wallet_address: str = ""
    alchemy_api_key: str = ""
    polygonscan_api_key: str = ""
    mumbai_rpc_url: str = "https://rpc-mumbai.maticvigil.com"
    # local_rpc_url is declared once, with the other integration settings.
    # A bare `private_key` used to sit here as well. It had no consumer
    # anywhere in the tree, no production validator, and sat eight lines below
    # `blockchain_private_key`, which has one — so it was an unvalidated escape
    # hatch for the same secret. Removed 2026-10-03.

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
    # SEC-24: seeding used to be allowed by default. It creates demo accounts
    # (and, with ECO_NOJIN_DEMO_ADMIN=1, an admin one), so it is opt-in per
    # environment now: 1 only where demo accounts are actually wanted.
    eco_nojin_allow_seed: int = 0
    default_latitude: float = 35.6892
    default_longitude: float = 51.3890
    trusted_domains: str = "econojin.ir,econojin.com,econojin.land"
    admin_temp: str = ""
    agent_token: SecretValue = ""  # type: ignore[assignment]
    hashed_password: str = ""
    password: str = ""
    client_secret: str = ""
    access_token: str = ""
    api_key: str = ""
    # These six were each declared twice in this class body — once under their
    # topical group (PAYMENT, HYDROMA C++ ENGINE, INTEGRATION) and once here.
    # A re-annotated name in a class body silently replaces the earlier one, so
    # this set was the live value and the other set was dead text that read as
    # a real setting. Identical defaults, so nothing changed behaviourally.
    # Only one declaration now, and it is here.
    bank_transfer_card_number: str = ""
    bank_transfer_holder: str = ""
    bank_transfer_sheba: str = ""
    hydroma_core_dll: str = ""
    intl_payment_checkout_url: str = ""
    local_rpc_url: str = ""
    # Removed here, each with zero consumers anywhere outside this file:
    #   frontend_url       — pointed at the deleted SPA (frontend/ tree);
    #                        public_base_url is the backend-only replacement
    #   frond_end_url      — a typo of FRONTEND_URL, kept with a comment
    #                        admitting the typo rather than fixing it
    #   ocelo_model_name   — a typo of COQUI_MODEL_NAME, same
    # If either is ever needed, add it under its correct name.

    # =====================================================================
    # FEATURE FLAGS
    # =====================================================================
    enable_satellite_real: bool = True
    enable_ai_assistant: bool = True
    enable_marketplace: bool = True
    enable_simulated_data: bool = False  # W-001: disable in production
    enable_realtime_sse: bool = True  # Feature flag for SSE realtime sync
    enable_supabase_sync: bool = False  # Feature flag for Supabase sync
    enable_event_bus: bool = False

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
    # NOT a duplicate of `cds_timeout: int = 300` (declared near the CDSE
    # credentials, and the one CDSE callers actually read — services/*/cds.py).
    # Two similarly named settings with 10x different values invited an earlier
    # misreading that treated this as a redefinition of the other. This field has
    # no consumer anywhere in the tree as of 2026-09-30.
    cdse_timeout: float = 30.0
    nasa_power_timeout: float = 30.0
    supabase_timeout: float = 30.0
    blockchain_timeout: float = 60.0

    # =====================================================================
    # SECURITY
    # =====================================================================
    api_key_header: str = "X-API-Key"
    telco_webhook_key: SecretValue = ""  # type: ignore[assignment]
    # B3: shared ingest key for device-submitted MRV observations
    # (POST /api/v1/mrv/iot-reading, header X-Source-Key). Separate from
    # telco_webhook_key because they are different sources with different
    # rotation: a LoRaWAN network operator's webhook and this platform's own
    # field devices are not the same trust relationship, and rotating one must
    # not invalidate the other. Empty means "ingestion unavailable" — the
    # endpoint answers 503 rather than accepting unauthenticated readings.
    mrv_ingest_key: SecretValue = ""  # type: ignore[assignment]
    # B8: WebAuthn relying-party identity. WebAuthn cannot work outside the
    # browser's declared origin, so these two are deployment values and not
    # preferences. They used to be hardcoded to RP_ID="localhost" and
    # ORIGIN="http://localhost:3000" in the router, with a comment two lines
    # above saying they "must be the real deployment values" — so the comment
    # was the only thing enforcing it, and it was wrong in every deployment.
    # Empty means "passkeys are not available here"; CHECK 16 refuses to start
    # in production with either unset, rather than silently serving ceremonies
    # scoped to localhost that no real browser would honour.
    passkey_rp_id: str = ""
    passkey_origin: str = ""
    # B8: OAuth post-login landing page. It was defaulting to a Vite dev server
    # on :5173, a port that belonged to the deleted frontend and that no
    # deployment runs. A GET that issues a redirect must not send an
    # authorization response to a host the operator never chose.
    oauth_redirect_uri: str = ""
    # Symmetric key for OAuth access-token encryption at rest (Fernet).
    #
    # This field did not exist. `routers/auth.py` read it with
    # `getattr(settings, "oauth_encryption_key", None)`, which therefore always
    # returned None, and the fallback branch derived a Fernet key from the first
    # 32 bytes of SECRET_KEY. Three defects followed from that:
    #   1. Key reuse — the same material that signs JWTs also encrypted tokens.
    #   2. Truncation — `secret.encode()[:32]` keeps only the first 32 bytes and
    #      `ljust(32, b"0")` pads with the ASCII byte 0x30, so a short SECRET_KEY
    #      produced a low-entropy key.
    #   3. Unrecoverable rotation — changing SECRET_KEY made every previously
    #      stored OAuthConnection.access_token_encrypted permanently
    #      undecryptable, with no way to migrate them.
    # Rotation now affects one value only, and it is not shared with signing.
    oauth_encryption_key: SecretValue = ""  # type: ignore[assignment]
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
        return [lang.strip() for lang in str(self.supported_languages).split(",") if lang.strip()]

    @property
    def rtl_languages_list(self) -> list[str]:
        """Get RTL languages as list."""
        if not self.rtl_languages:
            return []
        return [lang.strip() for lang in str(self.rtl_languages).split(",") if lang.strip()]

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
        return app_env_val in ("production", "prod")

    @field_validator("cors_origins", mode="after")
    @classmethod
    def validate_cors_origins(cls, v: list[str]) -> list[str]:
        """Reject empty CORS origins list."""
        if isinstance(v, list) and len(v) == 0:
            raise ValueError("cors_origins cannot be empty")
        return v

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
        # Required for the AliasChoices collapse: without it a field carrying a
        # validation_alias can only be populated through the alias, so every
        # `Settings(environment=...)` and `Settings(debug=...)` in the test suite
        # and in TestSettings would stop working.
        populate_by_name=True,
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

        # Same reason as `jwt_signing_key`: unwrapping each candidate keeps the
        # `or` chain meaningful, because `SecretStr("")` is truthy.
        secret = (
            reveal(self.secret_key)
            or reveal(self.jwt_secret)
            or reveal(self.app_secret_key)
        )

        # Empty or default = not secure
        if not secret or secret in insecure_defaults:
            return False

        # Must be 64+ chars
        return not len(secret) < 64

    # C4 FIX: Validate JWT secret is not default
    @property
    def jwt_signing_key(self) -> str:
        """The single key used to sign and verify JWTs.

        ``jwt_secret`` is the canonical source and is what
        ``validate_production_settings`` CHECK 3 audits. The previous code signed
        with ``secret_key`` instead, which left ``jwt_secret`` inert: an operator
        who set a strong ``JWT_SECRET`` while leaving ``SECRET_KEY`` at a shared
        value got a forgeable token, and the guard reported the wrong key as
        healthy.

        Resolution order is ``jwt_secret`` -> ``secret_key`` -> ``app_secret_key``
        so existing development setups keep working. In production the guards have
        already rejected a short or default value, so the fallback chain can only
        ever resolve to a validated key.
        """
        # `reveal` on each side of the `or` chain is load-bearing, not stylistic.
        # `SecretStr("")` is truthy as an object, so the unwrapped form
        # `self.jwt_secret or self.secret_key` returns the first *declared* key
        # even when it is empty, and a deployment with no JWT_SECRET at all would
        # silently sign with the empty string instead of falling through.
        return (
            reveal(self.jwt_secret)
            or reveal(self.secret_key)
            or reveal(self.app_secret_key)
        )

    @property
    def jwt_secret_secure(self) -> bool:
        """Check if JWT secret is secure (not default)."""
        jwt_secret = self.jwt_signing_key
        insecure = {
            "dev-jwt-secret",
            "CHANGE_ME",
            "CHANGE_ME_TO_A_STRONG_RANDOM_KEY",
            "",
            "dev",
            "secret",
            "demo123",
        }
        return not (not jwt_secret or jwt_secret in insecure or len(jwt_secret) < 64)

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
        """Enforce the production configuration rules.

        The checks themselves are not here. They live in
        ``engine/hydroma/config/rules.py`` as ``ProductionRule`` records with
        stable ids, so a test can assert on the id of the rule that fired rather
        than on a substring of its message, and so the rule set is data rather
        than a 200-line method.

        This used to carry ``# CHECK n:`` markers inline, and its docstring
        promised seven checks while the body ran to eighteen. Both the count and
        the numbering had drifted; the count is now ``len(rule_ids())``.

        Two things deliberately stay inline because they are not production-only:

        * a fail-fast that a secret exists at all in a non-test environment;
        * the early return for non-production, so the rules never run against a
          development machine.
        """
        # Fail-fast: secret_key must be set (non-empty) in any non-test
        # environment, including development.
        if (
            not self.is_production
            and str(self.environment or "").lower().strip() not in ("test",)
            and not reveal(self.secret_key)
        ):
            raise RuntimeError(
                "SECRET_KEY must be set in environment. "
                'Generate with: python -c "import secrets; print(secrets.token_urlsafe(64))"'
            )

        if not self.is_production:
            return self

        apply_production_rules(self)
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


class TestSettings(Settings):
    """Settings with the fail-closed development defaults, declared.

    This replaces an ``__init__`` override on ``Settings`` that injected
    insecure defaults whenever the caller passed ``_env_file=None``. That
    overloading was the root cause of a recorded production incident:

    * ``_env_file=None`` means two different things. "Load no dotenv file" and
      "I am a test and want insecure defaults" are not the same request, and
      the override answered both.
    * The values were injected as init kwargs. pydantic-settings ranks
      ``init_settings`` above ``env_settings`` and ``dotenv_settings``, so an
      ambient ``ENVIRONMENT=production`` and a real ``SECRET_KEY`` were silently
      discarded, the process booted with ``debug=True`` and the public literal
      ``"dev-secret-key"`` as its signing key, and
      ``validate_production_settings`` returned early on every boot.

    A subclass makes the intent explicit at the call site and removes the
    ambient-environment read that the old guard needed to avoid a downgrade.
    Reading ``.env`` is suppressed here because a test must not pick up a
    developer's local secrets.
    """

    model_config = SettingsConfigDict(
        env_file=None,
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
        protected_namespaces=(),
    )

    #: pytest collects any class whose name starts with ``Test``. Without this it
    #: emits a collection warning and tries to treat this production class as a
    #: test case. ``__test__ = False`` is pytest's documented opt-out.
    __test__ = False

    app_name: str = "Eco Nojin"
    # `app_env` and `app_debug` are NOT redeclared here. They are read-only
    # properties on `Settings` after the AliasChoices collapse, and redeclaring
    # them as fields would shadow those properties -- pydantic warns about it,
    # and a field of that name would once again be a second source of truth for
    # the same concept, which is what the collapse exists to remove.
    #
    # The two redeclared fields MUST repeat the parent's `Field(...)` wrapper and
    # not just the default. A bare `environment: ... = "development"` in a
    # subclass replaces the field definition outright and silently drops
    # `validation_alias`, after which APP_ENV stops being read -- verified, and it
    # fails as a wrong default rather than as an error.
    debug: bool = Field(
        default=True,
        validation_alias=AliasChoices("DEBUG", "APP_DEBUG"),
    )
    environment: Literal["development", "production", "staging", "test"] = Field(
        default="development",
        validation_alias=AliasChoices("ENVIRONMENT", "APP_ENV"),
    )

    app_secret_key: SecretValue = "change-me-in-production"  # type: ignore[assignment]
    secret_key: SecretValue = "dev-secret-key"  # type: ignore[assignment]
    # `jwt_secret` is deliberately NOT overridden. Leaving it at the parent's
    # empty default is what lets `jwt_signing_key` fall through to `secret_key`,
    # which is the behaviour a development setup with no JWT_SECRET depends on.
    # The old override instead did `setdefault("jwt_secret", values["secret_key"])`,
    # coupling the two fields so that this fallback could not be observed.
    agent_token: SecretValue = "dev-agent-token"  # type: ignore[assignment]
    cors_origins: list[str] = ["http://localhost:3000", "http://localhost:8000"]
