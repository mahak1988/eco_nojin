"""KN-02 — EcoCoin writes stay frozen until D-04 is decided.

P1 of `docs/project/PHASE_PLAN.md`. `services/blockchain/service.py` persists
EcoCoin balances through raw SQL against tables that are in neither the
`database/models.py` registry nor any Alembic revision, while the D-04 decision
(internal points, transferable, or removed?) is still open. The P1 freeze
gates every state-changing method on `HYDROMA_ECOCOIN_WRITES_ENABLED`, read
from the environment at call time.

The tests drive no database: a sentinel session proves *whether execution
reached* the DB layer, which is exactly the property the freeze must have —
frozen calls never reach it, enabled calls do, and read paths never freeze.
"""

from __future__ import annotations

from decimal import Decimal
from types import SimpleNamespace

import pytest

from services.blockchain.service import (
    ECOCOIN_WRITES_ENV,
    EcocoinLedgerService,
    EcoCoinWritesFrozen,
    _writes_enabled,
)


class _SentinelReachedDB(Exception):
    """Raised by the fake session: proof a call got past the freeze guard."""


def _sentinel_session():
    """A session whose first DB touch is observable and harmless."""

    async def execute(*args, **kwargs):
        raise _SentinelReachedDB

    async def commit():
        raise _SentinelReachedDB

    return SimpleNamespace(execute=execute, commit=commit)


def _write_calls(service: EcocoinLedgerService):
    """(name, coroutine-factory) for every state-changing method."""
    return (
        ("ensure_balance", lambda: service.ensure_balance("u1")),
        ("earn_ecocoin", lambda: service.earn_ecocoin("u1", "tree_planting", Decimal("1"))),
        ("redeem_ecocoin", lambda: service.redeem_ecocoin("u1", "tree_planting", Decimal("1"))),
        ("transfer_ecocoin", lambda: service.transfer_ecocoin("a", "b", Decimal("1"))),
        (
            "create_impact_certificate",
            lambda: service.create_impact_certificate("act1", "u1", 90, "hash"),
        ),
        ("activate_phase", lambda: service.activate_phase(1)),
        (
            "submit_attestation",
            lambda: service.submit_attestation("act1", "type", 90, "commit", "sig"),
        ),
        (
            "submit_impact_report",
            lambda: service.submit_impact_report("act1", "type", 90, "hash", "commit"),
        ),
        (
            "create_treasury_proposal",
            lambda: service.create_treasury_proposal("to", 1.0, "purpose"),
        ),
        (
            "create_grant",
            lambda: service.create_grant("rec", 1.0, "type", "desc", "region", "2026-01-01", 1),
        ),
    )


@pytest.fixture(autouse=True)
def _unfrozen_env_guard(monkeypatch):
    """Every test starts from the deployed default: writes frozen."""
    monkeypatch.delenv(ECOCOIN_WRITES_ENV, raising=False)


async def test_the_deployed_default_frozen(monkeypatch):
    assert _writes_enabled() is False


@pytest.mark.parametrize("value", ["true", "TRUE", "1", "yes", "on"])
async def test_explicit_override_values(monkeypatch, value):
    monkeypatch.setenv(ECOCOIN_WRITES_ENV, value)
    assert _writes_enabled() is True


@pytest.mark.parametrize("value", ["", "false", "0", "no", "off", "banana"])
async def test_non_override_values_stay_frozen(monkeypatch, value):
    monkeypatch.setenv(ECOCOIN_WRITES_ENV, value)
    assert _writes_enabled() is False


_ALL_WRITE_NAMES = [name for name, _ in _write_calls(EcocoinLedgerService(None))]


@pytest.mark.parametrize("method_name", _ALL_WRITE_NAMES)
async def test_every_write_is_frozen_by_default(monkeypatch, method_name):
    factory = dict(_write_calls(EcocoinLedgerService(None)))[method_name]
    with pytest.raises(EcoCoinWritesFrozen):
        await factory()


async def test_frozen_writes_never_reach_the_database(monkeypatch):
    calls = {"execute": 0, "commit": 0}

    async def execute(*args, **kwargs):
        calls["execute"] += 1
        raise _SentinelReachedDB

    async def commit():
        calls["commit"] += 1
        raise _SentinelReachedDB

    session = SimpleNamespace(execute=execute, commit=commit)
    service = EcocoinLedgerService(session)
    for _, factory in _write_calls(service):
        with pytest.raises(EcoCoinWritesFrozen):
            await factory()
    assert calls == {"execute": 0, "commit": 0}


async def test_enabled_writes_pass_the_guard_and_reach_the_database(monkeypatch):
    monkeypatch.setenv(ECOCOIN_WRITES_ENV, "true")
    service = EcocoinLedgerService(_sentinel_session())
    for _, factory in _write_calls(service):
        with pytest.raises(_SentinelReachedDB):
            await factory()


async def test_reads_stay_free_while_frozen(monkeypatch):
    service = EcocoinLedgerService(_sentinel_session())
    with pytest.raises(_SentinelReachedDB):
        await service.get_balance("u1")


async def test_the_freeze_error_type_survives_legacy_handling():
    """P1 note: ``except RuntimeError`` arms still catch the freeze."""

    class _Legacy:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            assert isinstance(exc, EcoCoinWritesFrozen)
            return True

    with _Legacy():
        raise EcoCoinWritesFrozen("frozen for tests")


def test_freeze_message_is_actionable():
    from services.blockchain.service import _FREEZE_MESSAGE

    assert "D-04" in _FREEZE_MESSAGE
    assert ECOCOIN_WRITES_ENV in _FREEZE_MESSAGE
    assert "docs/project/OPEN_DECISIONS.md" in _FREEZE_MESSAGE


def test_freeze_error_is_a_runtime_error():
    assert issubclass(EcoCoinWritesFrozen, RuntimeError)
