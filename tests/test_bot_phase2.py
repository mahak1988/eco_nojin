"""Phase 2 tests: multi-platform registry, Eitaa adapter, Bale/Rubika gates,
and the smart-alert engine. All offline and deterministic."""

from __future__ import annotations

import os

import pytest

from services.bots.config import BotConfig
from services.bots.core.alerts import AlertRule, evaluate_rules, format_alert
from services.bots.platforms import EITAA_API_BASE, PLATFORM_SPECS, enabled_platforms, token_for


# ---------------------------------------------------------------------------
# Platform registry
# ---------------------------------------------------------------------------
def test_platform_specs_complete():
    assert set(PLATFORM_SPECS) == {"telegram", "eitaa", "bale", "rubika"}
    assert PLATFORM_SPECS["telegram"].verified is True
    # everything else is explicitly unverified (honest status)
    assert all(not s.verified for k, s in PLATFORM_SPECS.items() if k != "telegram")


def test_enabled_platforms_telegram_only_by_default(monkeypatch):
    monkeypatch.delenv("BOT_TOKEN", raising=False)
    monkeypatch.delenv("EITAA_ENABLED", raising=False)
    monkeypatch.delenv("EITAA_TOKEN", raising=False)
    monkeypatch.delenv("BALE_ENABLED", raising=False)
    monkeypatch.delenv("RUBIKA_ENABLED", raising=False)
    config = BotConfig()  # no token
    assert enabled_platforms(config) == []

    config_tok = BotConfig(bot_token="123:abc")
    keys = [s.key for s in enabled_platforms(config_tok)]
    assert keys == ["telegram"]


def test_enabled_platforms_eitaa_requires_flag_and_token(monkeypatch):
    monkeypatch.setenv("EITAA_ENABLED", "true")
    monkeypatch.setenv("EITAA_TOKEN", "eit-123")
    config = BotConfig(bot_token="123:abc")
    keys = [s.key for s in enabled_platforms(config)]
    assert "eitaa" in keys

    monkeypatch.setenv("EITAA_ENABLED", "false")  # flag off -> excluded
    assert "eitaa" not in [s.key for s in enabled_platforms(config)]

    monkeypatch.setenv("EITAA_ENABLED", "true")
    monkeypatch.setenv("EITAA_TOKEN", "")  # no token -> excluded
    assert "eitaa" not in [s.key for s in enabled_platforms(config)]


def test_token_for_reads_env(monkeypatch):
    monkeypatch.setenv("EITAA_TOKEN", "eit-secret")
    config = BotConfig()
    assert token_for(PLATFORM_SPECS["eitaa"], config) == "eit-secret"


# ---------------------------------------------------------------------------
# Eitaa adapter (Telegram-compatible API base)
# ---------------------------------------------------------------------------
def test_eitaa_api_base_url_is_telegram_compatible():
    assert EITAA_API_BASE == "https://eitaayar.ir/api"


def test_create_bot_with_custom_api_base():
    from services.bots.adapters.telegram import create_bot

    bot = create_bot("123:fake", api_base=EITAA_API_BASE)
    api = bot.session.api
    # Telegram-shaped URL patterns with the Eitaa base
    assert "eitaayar.ir/api/bot{token}/{method}" in api.base
    bot.session.close()


def test_create_bot_defaults_to_official_api():
    from services.bots.adapters.telegram import create_bot

    bot = create_bot("123:fake")
    assert "api.telegram.org" in bot.session.api.base
    bot.session.close()


# ---------------------------------------------------------------------------
# Bale / Rubika gates fail loudly and honestly
# ---------------------------------------------------------------------------
def test_bale_gateway_unavailable_without_library():
    from services.bots.adapters.bale import BaleGateway

    gw = BaleGateway("bale-token")
    # In this environment python-bale-bot is not installed -> unavailable
    assert gw.available() is False


def test_bale_gateway_start_raises_with_guidance():
    from services.bots.adapters.bale import BaleGateway

    gw = BaleGateway("bale-token")
    with pytest.raises(RuntimeError, match="python-bale-bot"):
        gw.start()


def test_rubika_gateway_honest():
    from services.bots.adapters.rubika import RubikaGateway

    gw = RubikaGateway("rubika-token")
    assert gw.available() is False
    with pytest.raises(NotImplementedError, match="Rubika"):
        gw.start()


# ---------------------------------------------------------------------------
# Smart alerts engine
# ---------------------------------------------------------------------------
RULES = [
    AlertRule("soil_moisture_pct", "<", 25.0, "critical", "رطوبت خاک پایین است"),
    AlertRule("soil_moisture_pct", ">", 80.0, "warning", "رطوبت خاک بالاست"),
    AlertRule("ph", "<", 6.0, "warning", "pH خاک اسیدی است"),
]


def test_alerts_fire_only_when_threshold_met():
    fired = evaluate_rules(RULES, {"soil_moisture_pct": 18.0, "ph": 5.5})
    assert len(fired) == 2
    assert fired[0].severity == "critical"

    fired_none = evaluate_rules(RULES, {"soil_moisture_pct": 40.0, "ph": 7.0})
    assert fired_none == []


def test_alerts_missing_metric_never_fires():
    fired = evaluate_rules(RULES, {})
    assert fired == []


def test_alerts_unknown_operator_skipped():
    bad = AlertRule("x", "<<", 1.0, "info", "bad")
    assert evaluate_rules([bad], {"x": 0.5}) == []


def test_format_alert_includes_farm_and_values():
    text = format_alert(RULES[0], {"soil_moisture_pct": 18.0}, farm_name="مزرعه نمونه")
    assert "مزرعه «مزرعه نمونه»" in text
    assert "18.0" in text
    assert "25.0" in text
    assert "🚨" in text
