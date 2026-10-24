"""Storage-tier contract tests (R-B, DP-2, ``ECO-DP2-RUNTIME``).

The DP-2 decision removes Docker and the mandatory PostgreSQL from the runtime.
These tests pin the two storage tiers that replace the unconditional PostgreSQL
mandate:

* the tier-aware database rule and the :func:`storage_tier` helper in
  ``engine.hydroma.config.rules`` -- the ``local`` tier (default) no longer fires
  ``database_not_postgresql`` and instead records a one-line notice; the
  ``scaled`` tier keeps the original rule, message and penalty intact; an unknown
  tier value is rejected.
* the Docker-free runtime descriptor in
  ``engine.hydroma.production.runtime_deployment`` -- no docker, no orchestrator,
  no Kubernetes/Helm/image key in the local tier; the PostgreSQL escape hatch
  appears only in the scaled tier.
"""

from __future__ import annotations

from typing import Any, cast

import pytest

from engine.hydroma.config.rules import rule_by_id, storage_tier
from engine.hydroma.config.settings import TestSettings
from engine.hydroma.production.runtime_deployment import runtime_descriptor

_LOCAL_TIER_NOTICE = (
    "local tier: SQLite + WAL, no server required "
    "— set HYDROMA_STORAGE_TIER=scaled for PostgreSQL"
)
_SCALED_SQLITE_MESSAGE = (
    "Production requires PostgreSQL database. Set DATABASE_URL to postgresql+psycopg://..."
)


def _sqlite_settings(**kwargs: object) -> TestSettings:
    """A settings object holding a SQLite DATABASE_URL, isolated from any .env.

    ``environment="test"`` short-circuits ``validate_production_settings`` so the
    construction never runs the production rule set (which would depend on the
    ambient environment); the tier is supplied by the env var under monkeypatch.
    """
    return TestSettings(
        environment="test",
        database_url="sqlite:///./data/econojin.db",
        # the **kwargs: object splat widens every pydantic field to ``object``;
        # the helper's contract is "settings fields only", which the cast states.
        **cast("dict[str, Any]", kwargs),
    )


class TestLocalTier:
    def test_local_tier_defaults_and_skips_the_postgres_rule(self, monkeypatch) -> None:
        monkeypatch.delenv("HYDROMA_STORAGE_TIER", raising=False)
        settings = _sqlite_settings()
        assert storage_tier(settings) == "local"
        assert rule_by_id("database_not_postgresql").check(settings) is None
        assert rule_by_id("database_local_tier_notice").check(settings) == _LOCAL_TIER_NOTICE


class TestScaledTier:
    def test_scaled_tier_still_requires_postgres(self, monkeypatch) -> None:
        monkeypatch.setenv("HYDROMA_STORAGE_TIER", "scaled")
        settings = _sqlite_settings()
        assert storage_tier(settings) == "scaled"
        rule = rule_by_id("database_not_postgresql")
        # Original id, message text and detail are preserved for the scaled tier.
        assert rule.message == _SCALED_SQLITE_MESSAGE
        assert rule.is_violated(settings)
        assert rule.check(settings) == f"database_url={settings.database_url!r}"
        rendered = rule.violation(settings)
        assert rendered.startswith(f"[database_not_postgresql] {_SCALED_SQLITE_MESSAGE}")
        # The local notice is silent in the scaled tier.
        assert rule_by_id("database_local_tier_notice").check(settings) is None

    def test_invalid_tier_is_rejected(self, monkeypatch) -> None:
        monkeypatch.setenv("HYDROMA_STORAGE_TIER", "banana")
        settings = _sqlite_settings()
        with pytest.raises(ValueError):
            storage_tier(settings)

    def test_runtime_descriptor_is_docker_free(self, monkeypatch) -> None:
        monkeypatch.delenv("HYDROMA_STORAGE_TIER", raising=False)
        descriptor = runtime_descriptor()
        assert descriptor["docker"] is False
        assert descriptor["orchestrator"] is None
        assert descriptor["storage_tier"] == "local"
        assert descriptor == {
            "runtime": "hydroma-runtime",
            "docker": False,
            "orchestrator": None,
            "storage_tier": "local",
            "services_source": "runtime/services.yaml",
            "logs_dir": "data/logs",
            "backup": "runtime.backup",
            "secrets": ["env"],
        }
        for key in descriptor:
            lowered = key.lower()
            assert "kubernetes" not in lowered
            assert "helm" not in lowered
            assert "image" not in lowered

    def test_scaled_tier_descriptor_keeps_the_escape_hatch(self, monkeypatch) -> None:
        monkeypatch.setenv("HYDROMA_STORAGE_TIER", "scaled")
        descriptor = runtime_descriptor()
        assert descriptor["storage_tier"] == "scaled"
        assert "postgresql" in descriptor
        assert descriptor["postgresql"]["enabled"] is True
        assert descriptor["postgresql"]["host"] == "postgresql"
