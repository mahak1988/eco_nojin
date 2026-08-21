"""Phase 9/10 integration tests: model cards, AGROVOC, Zenodo, PQC, insurance, watchdog, AI citations."""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from fastapi.testclient import TestClient  # noqa: E402

from services.api_gateway.main import app  # noqa: E402

client = TestClient(app)


# ---- Phase 9 star 11: model cards API -------------------------------------
def test_model_cards_index():
    r = client.get("/api/v1/science/model-cards")
    assert r.status_code == 200
    body = r.json()
    assert body["count"] == 22
    assert body["cards"][0]["card"]["limitations"]


def test_model_cards_single():
    r = client.get("/api/v1/science/model-cards", params={"slug": "et0_hargreaves"})
    assert r.status_code == 200
    body = r.json()
    assert body["slug"] == "et0_hargreaves"
    assert body["card"]["validity"]


def test_model_cards_unknown():
    r = client.get("/api/v1/science/model-cards", params={"slug": "nope"})
    assert r.status_code == 404


# ---- Phase 9 star 12: AGROVOC --------------------------------------------
def test_agrovoc_search_fa():
    r = client.get("/api/v1/science/agrovoc", params={"q": "گندم"})
    assert r.status_code == 200
    results = r.json()["results"]
    assert results
    assert "agrovoc.fao.org" in results[0]["uri"]


def test_agrovoc_search_en_and_empty():
    r = client.get("/api/v1/science/agrovoc", params={"q": "drought"})
    assert r.status_code == 200
    assert r.json()["results"]
    r2 = client.get("/api/v1/science/agrovoc")
    assert r2.status_code == 200
    assert r2.json()["stats"]["water"] >= 1


# ---- Phase 9 star 9: Zenodo honest status ---------------------------------
def test_zenodo_status_not_configured():
    r = client.get("/api/v1/science/zenodo/status")
    assert r.status_code == 200
    assert r.json()["status"] == "not_configured"


def test_zenodo_doi_without_token_501():
    r = client.post("/api/v1/science/datasets/era5_land/doi")
    assert r.status_code in (404, 501)
    if r.status_code == 501:
        assert r.json()["detail"]["status"] == "not_configured"


# ---- Phase 10 star 14: PQC -------------------------------------------------
def test_pqc_signature_roundtrip():
    from services.ledger.pqc import (
        generate_ml_dsa_key,
        pq_public_key,
        pq_sign,
        pq_verify,
    )

    priv = generate_ml_dsa_key()
    pub = pq_public_key(priv)
    data = b"eco-nojin-ledger-v1"
    sig = pq_sign(priv, data)
    assert pq_verify(pub, data, sig)
    assert not pq_verify(pub, b"tampered", sig)


def test_pqc_kem_roundtrip():
    from services.ledger.pqc import generate_ml_kem_keys, pq_decapsulate, pq_encapsulate

    priv, pub = generate_ml_kem_keys()
    ct, secret = pq_encapsulate(pub)
    assert pq_decapsulate(priv, ct) == secret


# ---- Phase 10: index insurance ---------------------------------------------
def test_insurance_endpoint_payout():
    r = client.post(
        "/api/v1/insurance/index",
        json={
            "farm_id": "farm-1",
            "ndvi_values": [0.30, 0.32, 0.28, 0.31],
            "reference_ndvi": 0.60,
        },
    )
    assert r.status_code == 200
    body = r.json()
    assert body["trigger_active"] is True
    assert body["payout_rate"] > 0.0


def test_insurance_endpoint_no_trigger():
    r = client.post(
        "/api/v1/insurance/index",
        json={
            "farm_id": "farm-2",
            "ndvi_values": [0.55, 0.58, 0.57],
            "reference_ndvi": 0.60,
        },
    )
    assert r.status_code == 200
    assert r.json()["trigger_active"] is False
    assert r.json()["payout_rate"] == 0.0


def test_insurance_endpoint_bad_input():
    r = client.post(
        "/api/v1/insurance/index",
        json={"farm_id": "f", "ndvi_values": [0.1], "reference_ndvi": 0.6},
    )
    assert r.status_code == 422  # pydantic min_length=3
    r2 = client.post(
        "/api/v1/insurance/index",
        json={"farm_id": "f", "ndvi_values": [0.5, 1.5, 0.4], "reference_ndvi": 0.6},
    )
    assert r2.status_code == 422  # domain error


# ---- Phase 10 star 13: watchdog logic --------------------------------------
def test_watchdog_analysis():
    from scripts.watchdog import analyze_samples

    ok = analyze_samples([100, 120, 90], [False, False, False])
    assert ok["status"] == "ok"
    bad = analyze_samples([3000, 4000, 5000], [True, True, True])
    assert bad["status"] == "failing"
    mixed = analyze_samples([100, 900, 1100, 1300], [False, True, False, False])
    assert mixed["status"] == "degraded"
    with pytest.raises(ValueError):
        analyze_samples([100], [])


# ---- Phase 9 star 10: AI auto-citations ------------------------------------
def test_ai_chat_includes_citations():
    r = client.post("/api/v1/ai/chat", json={"question": "پیش‌بینی عملکرد گندم و آبیاری"})
    assert r.status_code == 200
    body = r.json()
    assert "citations" in body
    assert isinstance(body["citations"], list)
