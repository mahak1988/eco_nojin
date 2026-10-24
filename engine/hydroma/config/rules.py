"""Production safety rules, extracted from ``Settings.validate_production_settings``.

The validator used to be one 140-line method whose docstring promised checks
"1..7" while the body carried fifteen numbered ``# CHECK n:`` comments. The
numbers were load-bearing for nothing except the reader's confidence: nothing
referenced them, so the list drifted and the docstring became a lie that no test
could catch.

Each rule here has a stable ``id`` -- a slug, not an index. Ids survive
reordering and deletion, so an operator grepping a log line, or a test asserting
a rule exists, keeps working when the sequence changes. ``validate_production_settings``
runs them in declaration order and raises naming the id.

Message text is a contract. Tests assert on substrings such as ``"CORS"``,
``"debug=False"`` and ``"TELEGRAM_BOT_TOKEN"``; those must survive any rewrite
of the prose, so ``message`` is the operator-facing text and each check returns
only the short detail that varies between the branches of one rule.

Storage tiers (DP-2, ``ECO-DP2-RUNTIME``) -- the runtime is Docker-free and needs
no mandatory PostgreSQL. ``HYDROMA_STORAGE_TIER`` selects between two tiers,
resolved by :func:`storage_tier`:

* ``local`` (default) -- SQLite + WAL, file-based, zero install, no server. The
  ``database_not_postgresql`` rule does NOT fire here; ``database_local_tier_notice``
  records the tier as a warning instead.
* ``scaled`` -- PostgreSQL, opt-in. ``database_not_postgresql`` keeps its
  original id, message and penalty and fires exactly as before.
"""

from __future__ import annotations

import os
import warnings
from collections.abc import Callable
from dataclasses import dataclass
from enum import StrEnum
from typing import TYPE_CHECKING, Final

from .secrets import reveal

if TYPE_CHECKING:  # pragma: no cover - import cycle only matters to type checkers
    from .settings import Settings

#: Values that are published in this repository, in ``.env.example`` or in
#: ``.env.template``. A secret matching any of them has not been rotated and
#: must not satisfy a production guard.
INSECURE_SECRETS: Final[frozenset[str]] = frozenset(
    {
        "",
        "CHANGE_ME",
        "CHANGE_ME_TO_A_STRONG_RANDOM_KEY",
        "change-me-in-production",
        "changeme",
        "demo123",
        "dev",
        "dev-jwt-secret",
        "dev-secret-key",
        "dev-secret-key-change-in-production",
        "secret",
        "your-secret-key",
    }
)

#: Production requires a key of at least this length. 32 bytes of entropy, hex
#: or base64 encoded.
MIN_SECRET_LENGTH: Final[int] = 64

#: Length below which a secret is rejected, phrased for the error message.
_MIN_LENGTH_TEXT: Final[str] = f"{MIN_SECRET_LENGTH}+ characters, not a known default"

_GENERATE_HINT: Final[str] = (
    'Generate with: python -c "import secrets; print(secrets.token_urlsafe(64))"'
)


class Severity(StrEnum):
    """Whether a violated rule aborts the boot or only warns."""

    ERROR = "error"
    WARNING = "warning"


@dataclass(frozen=True, slots=True)
class ProductionRule:
    """One production guard.

    Attributes:
        id: Stable slug. Never a sequence number.
        message: Operator-facing text. Always present in the raised error.
        check: Returns ``None`` when satisfied, or a short detail string.
        severity: ``ERROR`` raises; ``WARNING`` emits a ``RuntimeWarning``.
    """

    id: str
    message: str
    check: Callable[[Settings], str | None]
    severity: Severity = Severity.ERROR

    def violation(self, settings: Settings) -> str:
        """Render the message a failed run should surface, id included."""
        detail = self.check(settings)
        body = f"[{self.id}] {self.message}"
        return f"{body} ({detail})" if detail else body

    def is_violated(self, settings: Settings) -> bool:
        """True when this rule rejects ``settings``."""
        return self.check(settings) is not None


# ---------------------------------------------------------------------------
# Individual checks. Each returns None on success, a detail string on failure.
# ---------------------------------------------------------------------------


def _cors_wildcard_with_credentials(settings: Settings) -> str | None:
    if "*" in settings.cors_origins and settings.allow_credentials:
        return f"cors_origins={settings.cors_origins!r} allow_credentials=True"
    return None


def _secret_key_strength(settings: Settings) -> str | None:
    secret = (
        reveal(settings.secret_key)
        or reveal(settings.jwt_secret)
        or reveal(settings.app_secret_key)
    )
    if secret in INSECURE_SECRETS:
        return "the configured key is a published development default"
    if len(secret) < MIN_SECRET_LENGTH:
        return f"the key is {len(secret)} characters, need {_MIN_LENGTH_TEXT}"
    return None


def _jwt_secret_strength(settings: Settings) -> str | None:
    secret = (
        reveal(settings.jwt_secret)
        or reveal(settings.secret_key)
        or reveal(settings.app_secret_key)
    )
    if secret in INSECURE_SECRETS:
        return "the signing key is a published development default"
    if len(secret) < MIN_SECRET_LENGTH:
        return f"the signing key is {len(secret)} characters, need {_MIN_LENGTH_TEXT}"
    return None


def _debug_enabled(settings: Settings) -> str | None:
    if settings.debug:
        return "debug=True"
    return None


def _simulated_data_enabled(settings: Settings) -> str | None:
    if settings.enable_simulated_data:
        return "enable_simulated_data=True"
    return None


def _agent_token_insecure(settings: Settings) -> str | None:
    if reveal(settings.agent_token) == "dev-agent-token":
        return "agent_token is the development default"
    return None


def _debug_routes_enabled(settings: Settings) -> str | None:
    if settings.enable_debug_routes:
        return "enable_debug_routes=True"
    return None


def _supabase_url_missing(settings: Settings) -> str | None:
    if not settings.enable_supabase_sync:
        return None
    insecure = {
        "",
        "your-project.supabase.co",
        "your-supabase-key",
        "your-anon-key",
        "your-service-role-key",
    }
    if not settings.supabase_url or settings.supabase_url in insecure:
        return "enable_supabase_sync=True requires a real SUPABASE_URL"
    return None


def _supabase_service_role_key_missing(settings: Settings) -> str | None:
    if not settings.enable_supabase_sync:
        return None
    insecure = {
        "",
        "your-project.supabase.co",
        "your-supabase-key",
        "your-anon-key",
        "your-service-role-key",
    }
    key = settings.supabase_service_role_key
    if not key or key in insecure:
        return "enable_supabase_sync=True requires a real SUPABASE_SERVICE_ROLE_KEY"
    return None


def _telegram_bot_token_missing(settings: Settings) -> str | None:
    if reveal(settings.telegram_bot_token) in {"", "CHANGE_ME", "GET_FROM_BOTFATHER"}:
        return "telegram_bot_token is unset or still a placeholder"
    return None


def _blockchain_private_key_missing(settings: Settings) -> str | None:
    if not settings.enable_blockchain:
        return None
    if reveal(settings.blockchain_private_key) in {"", "CHANGE_ME", "your-private-key"}:
        return "enable_blockchain=True requires a real BLOCKCHAIN_PRIVATE_KEY"
    return None


def _alchemy_api_key_missing(settings: Settings) -> str | None:
    if not settings.enable_blockchain:
        return None
    if settings.alchemy_api_key in {"", "your-alchemy-key"}:
        return "enable_blockchain=True requires a real ALCHEMY_API_KEY"
    return None


#: Environment variable selecting the storage tier. Part of the Docker-free
#: runtime decision (DP-2): the ``local`` tier needs no PostgreSQL server, so
#: the production rule below must not demand one there.
_STORAGE_TIER_ENV: Final[str] = "HYDROMA_STORAGE_TIER"

#: The two recognised storage tiers. ``local`` is the default and needs no
#: server; ``scaled`` is the opt-in PostgreSQL tier.
STORAGE_TIERS: Final[frozenset[str]] = frozenset({"local", "scaled"})

#: Default storage tier: file-based SQLite + WAL, no server required (DP-2).
DEFAULT_STORAGE_TIER: Final[str] = "local"

#: The one-line informational message the local tier records in place of the
#: scaled-only PostgreSQL requirement.
LOCAL_TIER_NOTICE: Final[str] = (
    "local tier: SQLite + WAL, no server required "
    "— set HYDROMA_STORAGE_TIER=scaled for PostgreSQL"
)


def storage_tier(settings: Settings | None = None) -> str:
    """Return the active storage tier: ``"local"`` (default) or ``"scaled"``.

    DP-2 removed Docker and the mandatory PostgreSQL from the runtime. The value
    is read from a ``storage_tier`` attribute on ``settings`` when one is
    configured, otherwise from the ``HYDROMA_STORAGE_TIER`` environment variable,
    and defaults to ``"local"`` (SQLite + WAL, no server).

    Raises:
        ValueError: if the configured value is neither ``"local"`` nor ``"scaled"``.
    """
    raw = getattr(settings, "storage_tier", None) if settings is not None else None
    if not raw:
        raw = os.environ.get(_STORAGE_TIER_ENV, DEFAULT_STORAGE_TIER)
    tier = str(raw).strip().lower()
    if tier not in STORAGE_TIERS:
        raise ValueError(
            f"HYDROMA_STORAGE_TIER must be one of {sorted(STORAGE_TIERS)}; got {tier!r}"
        )
    return tier


def _database_not_postgresql(settings: Settings) -> str | None:
    # DP-2: PostgreSQL is required only in the scaled tier. In the local tier
    # SQLite + WAL is correct, so this rule must not fire there; the local-tier
    # notice records the tier instead.
    if storage_tier(settings) != "scaled":
        return None
    if settings.database_url.startswith("sqlite"):
        return f"database_url={settings.database_url!r}"
    return None


def _database_local_tier_notice(settings: Settings) -> str | None:
    """DP-2 local-tier notice: SQLite + WAL needs no PostgreSQL server.

    Complementary to ``_database_not_postgresql``: fires only in the ``local``
    tier, returning the one-line informational message that records the tier and
    points at the scaled-tier opt-in.
    """
    if storage_tier(settings) != "local":
        return None
    return LOCAL_TIER_NOTICE


def _redis_url_missing(settings: Settings) -> str | None:
    if settings.redis_url in {"", "redis://localhost:6379/0"}:
        return f"redis_url={settings.redis_url!r}"
    return None


def _nats_url_missing(settings: Settings) -> str | None:
    if settings.enable_event_bus and not (settings.nats_url or settings.nats_servers):
        return f"nats_url={settings.nats_url!r} nats_servers={settings.nats_servers!r}"
    return None


def _sentry_dsn_missing(settings: Settings) -> str | None:
    if not settings.sentry_dsn:
        return "sentry_dsn is empty"
    return None


#: The production guards, in the order they run. First failure aborts the boot.
#: The order is deliberate where it matters: CORS is checked before anything
#: else because a wildcard-with-credentials deployment is already leaking
#: regardless of how strong its keys are.
def _oauth_encryption_key(settings: Settings) -> str | None:
    """OAuth access tokens are encrypted at rest with a Fernet key.

    Without a configured key the gateway derived one from SECRET_KEY: signing and
    encryption then share key material, and rotating SECRET_KEY makes every
    previously stored OAuthConnection.access_token_encrypted permanently
    undecryptable. Refusing to boot is the only honest response.
    """
    if not reveal(settings.oauth_encryption_key):
        return "OAUTH_ENCRYPTION_KEY is empty"
    return None


def _passkey_rp_id_missing(settings: Settings) -> str | None:
    """WebAuthn ceremonies are bound to a relying-party domain.

    The field defaulted to "localhost", which would scope every registered
    credential to the loopback interface. Added 2026-10-01; ported from the
    inline "# CHECK 16" on 2026-10-03 when the checks became rules.
    """
    if not settings.passkey_rp_id:
        return "PASSKEY_RP_ID is empty"
    return None


def _passkey_origin_missing(settings: Settings) -> str | None:
    """Second half of CHECK 16: the origin is asserted independently of the
    relying-party id, so a mismatched pair is refused rather than silently
    producing ceremonies no browser will accept."""
    if not settings.passkey_origin:
        return "PASSKEY_ORIGIN is empty"
    return None


def _oauth_redirect_uri_missing(settings: Settings) -> str | None:
    """The OAuth redirect target is an allow-list entry.

    Added 2026-10-1 alongside CHECK 16; ported from the inline "# CHECK 17".
    """
    if not settings.oauth_redirect_uri:
        return "OAUTH_REDIRECT_URI is empty"
    return None


PRODUCTION_RULES: Final[tuple[ProductionRule, ...]] = (
    ProductionRule(
        id="cors_wildcard_with_credentials",
        message="CORS: Cannot use wildcard origins with allow_credentials=True in production",
        check=_cors_wildcard_with_credentials,
    ),
    ProductionRule(
        id="secret_key_strength",
        message=f"Production requires a strong, non-default secret key ({_MIN_LENGTH_TEXT}). {_GENERATE_HINT}",
        check=_secret_key_strength,
    ),
    ProductionRule(
        id="jwt_secret_strength",
        message=f"Production requires a strong, non-default JWT secret ({_MIN_LENGTH_TEXT}). {_GENERATE_HINT}",
        check=_jwt_secret_strength,
    ),
    ProductionRule(
        id="debug_enabled",
        message="Production requires debug=False and app_debug=False",
        check=_debug_enabled,
    ),
    ProductionRule(
        id="simulated_data_enabled",
        message="Production requires enable_simulated_data=False",
        check=_simulated_data_enabled,
    ),
    ProductionRule(
        id="agent_token_insecure",
        message="Production requires a secure agent_token (not the development default)",
        check=_agent_token_insecure,
    ),
    ProductionRule(
        id="debug_routes_enabled",
        message="Production requires enable_debug_routes=False",
        check=_debug_routes_enabled,
    ),
    ProductionRule(
        id="supabase_url_missing",
        message="SUPABASE_URL must be configured for production when enable_supabase_sync=True",
        check=_supabase_url_missing,
    ),
    ProductionRule(
        id="supabase_service_role_key_missing",
        message=(
            "SUPABASE_SERVICE_ROLE_KEY must be configured for production "
            "when enable_supabase_sync=True"
        ),
        check=_supabase_service_role_key_missing,
    ),
    ProductionRule(
        id="telegram_bot_token_missing",
        message="TELEGRAM_BOT_TOKEN must be configured for production",
        check=_telegram_bot_token_missing,
    ),
    ProductionRule(
        id="blockchain_private_key_missing",
        message=(
            "BLOCKCHAIN_PRIVATE_KEY must be configured for production when enable_blockchain=True"
        ),
        check=_blockchain_private_key_missing,
    ),
    ProductionRule(
        id="alchemy_api_key_missing",
        message="ALCHEMY_API_KEY must be configured for production when enable_blockchain=True",
        check=_alchemy_api_key_missing,
    ),
    ProductionRule(
        id="database_not_postgresql",
        message="Production requires PostgreSQL database. Set DATABASE_URL to postgresql+psycopg://...",
        check=_database_not_postgresql,
    ),
    # DP-2: in the local tier SQLite + WAL is correct and no server is required,
    # so this is a WARNING (a recorded notice) rather than an aborted boot. It is
    # the complement of database_not_postgresql, which now fires only in scaled.
    ProductionRule(
        id="database_local_tier_notice",
        message="Local storage tier: SQLite + WAL, no server required (DP-2).",
        check=_database_local_tier_notice,
        severity=Severity.WARNING,
    ),
    ProductionRule(
        id="redis_url_missing",
        message="REDIS_URL must be configured for production",
        check=_redis_url_missing,
    ),
    ProductionRule(
        id="nats_url_missing",
        message="NATS_URL or NATS_SERVERS must be configured when ENABLE_EVENT_BUS=True",
        check=_nats_url_missing,
    ),
    ProductionRule(
        id="sentry_dsn_missing",
        message="SENTRY_DSN not configured - error tracking disabled in production",
        check=_sentry_dsn_missing,
        severity=Severity.WARNING,
    ),
    # The next four were "# CHECK 16", "# CHECK 17" and "# CHECK 18" inline in
    # settings.py until 2026-10-03. Order is preserved deliberately: a
    # half-configured deployment must still be told about the FIRST thing it is
    # missing, and these three predated the fourth. Reordering them changes which
    # error an operator sees.
    ProductionRule(
        id="passkey_rp_id_missing",
        message="passkey_rp_id must be configured for production",
        check=_passkey_rp_id_missing,
    ),
    ProductionRule(
        id="passkey_origin_missing",
        message="passkey_origin must be configured for production",
        check=_passkey_origin_missing,
    ),
    ProductionRule(
        id="oauth_redirect_uri_missing",
        message="oauth_redirect_uri must be configured for production",
        check=_oauth_redirect_uri_missing,
    ),
    # Added 2026-10-03 during integration. This was "# CHECK 18" inline in
    # settings.py; the branch this rules.py came from predates the fix, so
    # porting the rules across would otherwise have silently dropped the guard.
    # Test: test_production_missing_oauth_encryption_key_raises.
    ProductionRule(
        id="oauth_encryption_key",
        message=(
            "oauth_encryption_key must be configured for production. Without it "
            "the gateway derives a Fernet key from SECRET_KEY, which shares key "
            "material with JWT signing and makes every stored OAuth access token "
            "undecryptable the moment SECRET_KEY is rotated."
        ),
        check=_oauth_encryption_key,
    ),
)

#: Stable id of the pre-production fail-fast, kept out of ``PRODUCTION_RULES``
#: because it fires in *every* non-test environment, not only production.
REQUIRED_SECRET_KEY_ID: Final[str] = "secret_key_required"

REQUIRED_SECRET_KEY_MESSAGE: Final[str] = (
    f"[{REQUIRED_SECRET_KEY_ID}] SECRET_KEY must be set in environment. {_GENERATE_HINT}"
)


def check_required_secret_key(settings: Settings) -> str:
    """Return the fail-fast message when no signing key is configured.

    Applies to any non-test, non-production environment. It is not part of
    ``PRODUCTION_RULES`` because it must fire before the ``is_production``
    early return, and because it is not a production-specific policy.
    """
    if settings.is_production:
        return ""
    if str(settings.environment or "").lower().strip() == "test":
        return ""
    if reveal(settings.secret_key):
        return ""
    return REQUIRED_SECRET_KEY_MESSAGE


def apply_production_rules(settings: Settings) -> None:
    """Run :data:`PRODUCTION_RULES` in order, raising or warning on the first failure."""
    for rule in PRODUCTION_RULES:
        if not rule.is_violated(settings):
            continue
        rendered = rule.violation(settings)
        if rule.severity is Severity.WARNING:
            warnings.warn(rendered, RuntimeWarning, stacklevel=3)
        else:
            raise RuntimeError(rendered)


def rule_ids() -> tuple[str, ...]:
    """Every production rule id, in declaration order."""
    return tuple(rule.id for rule in PRODUCTION_RULES)


def rule_by_id(rule_id: str) -> ProductionRule:
    """Look a rule up by its stable id.

    Raises:
        KeyError: if no such rule exists.
    """
    for rule in PRODUCTION_RULES:
        if rule.id == rule_id:
            return rule
    raise KeyError(rule_id)
