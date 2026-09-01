"""Real end-to-end smoke tests against the live API (port 8011).

Skips gracefully when the server is not running — never fails the suite
for a local dev setup.
"""
import os

import pytest
import httpx

BASE = "http://os.environ.get('HOST', '127.0.0.1'):8011"


def _server_up() -> bool:
    try:
        return httpx.get(f"{BASE}/health", timeout=2).status_code == 200
    except Exception:
        return False


pytestmark = pytest.mark.skipif(not _server_up(), reason="API server not running on :8011")


def test_health():
    r = httpx.get(f"{BASE}/health", timeout=5)
    assert r.status_code == 200
    assert r.json()["status"] == "healthy"


def test_security_firewall_active():
    r = httpx.get(f"{BASE}/api/v1/security/status", timeout=5)
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    assert body["layers"]["waf"]["active"] is True


def test_materials_compost_real():
    r = httpx.post(
        f"{BASE}/api/v1/materials/calculate-compost",
        json={"materials": [{"name": "Straw", "mass_kg": 200, "carbon_content": 45, "nitrogen_content": 0.5},
                            {"name": "Cow Manure", "mass_kg": 300, "carbon_content": 25, "nitrogen_content": 1.5}]},
        timeout=10,
    )
    assert r.status_code == 200
    assert 25 <= r.json()["cn_ratio"] <= 35


def test_ogc_features_landing():
    r = httpx.get(f"{BASE}/ogc/features/v1/", timeout=5)
    assert r.status_code == 200
    assert r.json()["title"].startswith("Eco Nojin")


def test_tourism_honest_status():
    r = httpx.get(f"{BASE}/api/v1/tourism/status", timeout=5)
    assert r.status_code == 200
    assert r.json()["status"] == "requires_setup"


def test_waf_blocks_sqli_live():
    r = httpx.post(
        f"{BASE}/api/v1/ai/advise",
        json={"question": "x' union select 1--"},
        timeout=10,
    )
    assert r.status_code == 403
