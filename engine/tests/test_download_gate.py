"""Tests for the ZED §2.2ج download gate (``download_gate``).

No network access is performed or needed: every test drives ``note_download``
with a monkeypatched environment and counts emissions through caplog (which
captures the ``logging.WARNING`` records the gate emits) plus the gate's own
one-time-warning registry.
"""

from __future__ import annotations

import pytest

from engine.hydroma.data_pipeline import download_gate as gate

_COUNT_TARGET = "x"


@pytest.fixture
def clean_gate(monkeypatch):
    """Fresh gate state and an environment whose flag controls the test alone."""
    monkeypatch.delenv(gate.ENV_VAR, raising=False)
    gate.reset_seen()
    yield gate
    gate.reset_seen()


def _warning_count(caplog) -> int:
    return sum(1 for r in caplog.records if r.levelno >= 30)


def test_default_permits_and_warns_once(clean_gate, caplog):
    """Unset flag: permitted (default behaviour) and warned once per target."""
    caplog.set_level("WARNING")

    clean_gate.note_download(_COUNT_TARGET)
    clean_gate.note_download(_COUNT_TARGET)
    count = _warning_count(caplog)

    assert count == 1
    assert _COUNT_TARGET in caplog.text
    assert "ZED §2.2ج" in caplog.text


def test_strict_mode_blocks(clean_gate, monkeypatch, caplog):
    """``HYDROMA_ALLOW_DOWNLOAD=0`` refuses the download, naming the target."""
    monkeypatch.setenv(gate.ENV_VAR, "0")
    caplog.set_level("WARNING")

    with pytest.raises(PermissionError) as excinfo:
        clean_gate.note_download(_COUNT_TARGET)

    assert _COUNT_TARGET in str(excinfo.value)


def test_strict_mode_explicit_allow(clean_gate, monkeypatch, caplog):
    """``HYDROMA_ALLOW_DOWNLOAD=1`` is an explicit allow: no error."""
    monkeypatch.setenv(gate.ENV_VAR, "1")
    caplog.set_level("WARNING")

    assert clean_gate.is_strict() is False
    clean_gate.note_download(_COUNT_TARGET)


def test_garbage_env_value_defaults_to_permit(clean_gate, monkeypatch, caplog):
    """An unrecognised value keeps the default (permit) and warns about it."""
    monkeypatch.setenv(gate.ENV_VAR, "banana")
    caplog.set_level("WARNING")

    clean_gate.note_download(_COUNT_TARGET)  # must not raise
    count = _warning_count(caplog)

    assert count == 1  # only the bad-value warning; permit is already default
    assert "not a recognised gate value" in caplog.text
    assert clean_gate.is_strict() is False


def test_strict_flag_maps_every_documented_value(clean_gate, monkeypatch):
    """Every documented flag value round-trips to the right mode."""
    for raw in ("0", "false", "no", "off", "OFF"):
        monkeypatch.setenv(gate.ENV_VAR, raw)
        assert clean_gate.is_strict() is True
    for raw in ("1", "true", "yes", "on", "YES"):
        monkeypatch.setenv(gate.ENV_VAR, raw)
        assert clean_gate.is_strict() is False


def test_seen_registry_records_target_and_resets(clean_gate):
    """``reset_seen`` clears the registry a fresh test relies on."""
    clean_gate.note_download(_COUNT_TARGET)
    assert _COUNT_TARGET in clean_gate._SEEN

    clean_gate.reset_seen()
    assert clean_gate._SEEN == set()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
