"""Secret field handling for :mod:`engine.hydroma.config.settings`.

A ``SecretStr`` keeps its value out of ``repr()``, ``model_dump()`` and any
f-string that happens to interpolate the model. That is the point: the previous
plain ``str`` fields meant ``logger.info(f"settings loaded: {settings}")`` wrote
every signing key to the log.

Reading one back requires an explicit act. :func:`reveal` is that act, and
:data:`SECRET_FIELDS` is the allowlist of names that may pass through it, so a
new secret cannot be revealed by accident and a non-secret cannot be treated as
one.
"""

from __future__ import annotations

from typing import Any, Final

from pydantic import SecretStr

#: Field names typed as ``SecretStr``. Every one of these is redacted in
#: ``repr()``/``model_dump()`` and must be unwrapped with :func:`reveal`.
SECRET_FIELDS: Final[frozenset[str]] = frozenset(
    {
        "secret_key",
        "app_secret_key",
        "jwt_secret",
        "agent_token",
        "nats_password",
        "nats_token",
        "telegram_bot_token",
        "telco_webhook_key",
        "blockchain_private_key",
        # Added 2026-10-03. The Fernet key for OAuth access tokens at rest.
        # Previously absent from the allowlist, which would have left it as the
        # one credential still printed by repr().
        "oauth_encryption_key",
        # Ingestion credential for the MRV write path. It was retyped as
        # SecretStr but missing from this allowlist, so `reveal` would have
        # refused it while `repr()` redacted it -- caught by
        # test_every_secret_field_is_wrapped.
        "mrv_ingest_key",
    }
)


def reveal(value: Any) -> str:
    """Return the plaintext behind a secret, or ``""`` for an absent one.

    ``SecretStr("")`` is truthy as an object, so ``settings.secret_key or
    settings.jwt_secret`` no longer selects the first *configured* key once
    these fields are wrapped -- it always selected the first *declared* one.
    Every truthiness test on a secret has to go through here instead.
    """
    if value is None:
        return ""
    if isinstance(value, SecretStr):
        return value.get_secret_value()
    return str(value)
