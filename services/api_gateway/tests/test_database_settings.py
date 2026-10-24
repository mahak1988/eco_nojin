"""Tests for the ``database``-layer settings surface.

``BANK_WEBHOOK_SECRET`` was an environment variable name embedded in two call
sites under ``services/finance``, so it had no declaration, no repr redaction
and no way to be inventoried. ``database/settings.py`` gives it a field.

What is pinned:

* the field reads the correct environment variable name, so an operator who
  sets ``BANK_WEBHOOK_SECRET`` gets a configured secret and one who does not
  gets an empty one;
* the empty case is observable, because ``SecretStr("")`` is truthy as an
  object and a caller testing the field directly would conclude the webhook
  is configured when it is not;
* the value never appears in ``repr()``/``model_dump()`` -- the reason the
  field is a ``SecretStr`` at all;
* the plaintext read is an explicit act, not a property access;
* a fresh instance is built per call, so the value a deployment rotates by
  changing the environment is visible on the very next request rather than
  frozen at import time.
"""

from __future__ import annotations

import pytest
from pydantic import SecretStr

from database.settings import (
    BANK_WEBHOOK_SECRET_ENV,
    DatabaseSettings,
    get_database_settings,
)


@pytest.fixture(autouse=True)
def _clean_env(monkeypatch):
    """Every case starts with the variable absent, then sets it if it wants to."""
    monkeypatch.delenv(BANK_WEBHOOK_SECRET_ENV, raising=False)
    yield
    monkeypatch.delenv(BANK_WEBHOOK_SECRET_ENV, raising=False)


class TestBankWebhookSecretResolution:
    def test_unset_environment_yields_an_empty_secret(self):
        assert get_database_settings().bank_webhook_secret_plain() == ""

    def test_environment_variable_is_read(self, monkeypatch):
        monkeypatch.setenv(BANK_WEBHOOK_SECRET_ENV, "s3kret")

        assert get_database_settings().bank_webhook_secret_plain() == "s3kret"

    def test_the_wire_name_matches_the_variable_the_router_reads(self):
        assert BANK_WEBHOOK_SECRET_ENV == "BANK_WEBHOOK_SECRET"

    def test_the_field_is_a_secret_str(self):
        assert isinstance(get_database_settings().bank_webhook_secret, SecretStr)

    def test_a_plain_string_default_still_validates_to_a_secret(self):
        # The default has to stay a bare literal for the field to be
        # constructible without arguments; validate_default does the wrapping.
        settings = DatabaseSettings()
        assert settings.bank_webhook_secret_plain() == ""


class TestBankWebhookSecretIsRedacted:
    def test_repr_does_not_leak_the_plaintext(self, monkeypatch):
        monkeypatch.setenv(BANK_WEBHOOK_SECRET_ENV, "do-not-print-me")

        assert "do-not-print-me" not in repr(get_database_settings())

    def test_model_dump_does_not_leak_the_plaintext(self, monkeypatch):
        monkeypatch.setenv(BANK_WEBHOOK_SECRET_ENV, "do-not-print-me")

        assert "do-not-print-me" not in str(get_database_settings().model_dump())

    def test_the_empty_default_is_not_truthy(self):
        # If this ever becomes True, a caller can no longer distinguish
        # "verification disabled" from "verification configured" by testing
        # the field, and the fail-closed 503 path stops being reachable.
        assert not get_database_settings().bank_webhook_secret_plain()


class TestRequestTimeResolution:
    def test_each_call_sees_the_current_environment(self, monkeypatch):
        """A per-call read, so an env rotation is not frozen into a singleton."""
        first = get_database_settings()
        assert first.bank_webhook_secret_plain() == ""

        monkeypatch.setenv(BANK_WEBHOOK_SECRET_ENV, "rotated")

        second = get_database_settings()
        assert second.bank_webhook_secret_plain() == "rotated"
        # The object built before the rotation is untouched, but the accessor
        # now yields the new value -- nothing was cached.
        assert first is not second

    def test_values_are_not_shared_between_instances(self, monkeypatch):
        monkeypatch.setenv(BANK_WEBHOOK_SECRET_ENV, "first")
        a = DatabaseSettings()
        monkeypatch.setenv(BANK_WEBHOOK_SECRET_ENV, "second")
        b = DatabaseSettings()

        assert a.bank_webhook_secret_plain() == "first"
        assert b.bank_webhook_secret_plain() == "second"
