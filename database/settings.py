"""Database-layer settings that the services may read directly.

The engine already owns the application-wide configuration
(``engine.hydroma.config.settings.Settings``), and the import guard sanctions
``engine.hydroma.config.settings`` as a service-facing module. What this file
adds is the *narrow* subset that lives under ``database/`` and that a service
currently reads straight out of ``os.environ``.

``BANK_WEBHOOK_SECRET`` is that case. ``POST
/api/v1/finance/payments/webhook/{provider}`` verifies an HMAC-SHA256 signature
over the raw request body with this shared secret (fail-closed: 503 when it is
unset, so the callback is refused rather than served unverified). It was
previously only an environment variable name embedded in two call sites, which
meant it had no declaration, no repr redaction and no way to be listed by any
settings inventory tool.

The field is typed ``SecretStr`` for the same reason the engine's secret fields
are: a plain ``str`` would be printed verbatim by ``repr()`` and by
``model_dump()``, which is how a signing key ends up in a log. Reading it back
requires the explicit ``reveal`` act.

Reading the environment at request time is deliberate and is *not* a caching
bug. ``_LazyBankTransferProvider`` binds its database session per call, and the
signature is verified on each incoming webhook against the value that is
configured then. A process-wide cached instance would freeze the value at
import time, so a rotation applied by restarting the process with a new
environment would be invisible to the already-imported router.
"""

from __future__ import annotations

from typing import Annotated, Any

from pydantic import BeforeValidator, Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

from engine.hydroma.config.secrets import reveal


def _coerce_secret(value: Any) -> SecretStr:
    """Wrap a secret value exactly once (see ``engine`` for the rationale)."""
    if isinstance(value, SecretStr):
        return value
    return SecretStr(value)


#: A bank-webhook secret that still accepts a plain ``str``. Same alias as the
#: engine's ``SecretValue``, restated here so this module does not have to
#: import a symbol whose name carries no meaning on its own.
SecretValue = Annotated[SecretStr, BeforeValidator(_coerce_secret)]

#: The environment variable ``POST /finance/payments/webhook`` verifies against.
#: Declared once so the router, this settings class and any operational
#: documentation all name the same string.
BANK_WEBHOOK_SECRET_ENV = "BANK_WEBHOOK_SECRET"


class DatabaseSettings(BaseSettings):
    """Settings owned by the ``database`` layer.

    Deliberately minimal: only the values whose canonical home is the
    persistence surface rather than the scientific engine. Everything else
    continues to live in ``engine.hydroma.config.settings.Settings``.
    """

    # Shared secret for the bank-transfer callback signature.
    #
    # Empty means "verification unavailable": the endpoint answers 503 rather
    # than accepting an unverified callback, so an unset value cannot silently
    # disable authentication the way a permissive fallback would.
    bank_webhook_secret: SecretValue = Field(
        default="",
        validation_alias=BANK_WEBHOOK_SECRET_ENV,
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
        populate_by_name=True,
        protected_namespaces=(),
    )

    def bank_webhook_secret_plain(self) -> str:
        """Return the plaintext webhook secret, or ``""`` when unset.

        ``SecretStr("")`` is truthy as an object, so any caller deciding
        whether verification is enabled has to go through this (or ``reveal``)
        rather than testing the field directly.
        """
        return reveal(self.bank_webhook_secret)


def get_database_settings() -> DatabaseSettings:
    """Build a fresh settings instance reading the *current* environment.

    Not cached, on purpose. The SMTP/telegram-integration style of reading
    settings once at import time is the wrong shape for a credential that a
    deployment rotates by changing the environment and restarting: a cached
    instance would keep serving the pre-rotation value to a router that is
    expected to see the new one on the very next request. Constructing an
    instance is cheap and the webhook path is not hot enough to care.
    """
    return DatabaseSettings()
