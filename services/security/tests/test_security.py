"""Phase 8-C security layer tests (offline/deterministic)."""
from services.security import pqcrypto
from services.security.anti_phishing import domain_squatting
from services.security.honeypot import honeypot
from services.security.rate_limit import rate_limiter
from services.security.waf import waf_engine


def test_waf_blocks_sqli():
    allowed, score, hits, _ = waf_engine.check("POST", "/api/v1/x", "", "a' union select 1--", "test")
    assert not allowed
    assert score >= 40
    assert "sqli-union" in hits


def test_waf_blocks_xss():
    allowed, _, hits, _ = waf_engine.check("POST", "/api/v1/x", "", "<script>alert(1)</script>", "test")
    assert not allowed
    assert "xss-script" in hits


def test_waf_blocks_traversal():
    allowed, _, hits, _ = waf_engine.check("GET", "/api/v1/x", "f=../../etc/passwd", "", "test")
    assert not allowed
    assert "traversal-dotdot" in hits


def test_waf_allows_normal():
    allowed, score, hits, _ = waf_engine.check("GET", "/api/v1/health", "a=1", "", "Mozilla/5.0")
    assert allowed
    assert score < 40
    assert hits == []


def test_waf_blocks_scanner_ua():
    allowed, _, hits, _ = waf_engine.check("GET", "/", "", "", "sqlmap/1.7")
    assert not allowed
    assert "scanner-ua" in hits


def test_rate_limiter_budget():
    rate_limiter._ip.clear()
    ok_until_120 = all(rate_limiter.check("10.0.0.1", "/api/v1/x")[0] for _ in range(120))
    assert ok_until_120
    ok, _ = rate_limiter.check("10.0.0.1", "/api/v1/x")
    assert not ok


def test_rate_limiter_auth_strict():
    rate_limiter._auth_ip.clear()
    for _ in range(10):
        rate_limiter.check("10.0.0.2", "/api/v1/auth/login")
    ok, _ = rate_limiter.check("10.0.0.2", "/api/v1/auth/login")
    assert not ok


def test_honeypot_traps_and_blocks():
    assert honeypot.is_trap("/admin.php")
    assert honeypot.is_trap("/.env")
    assert not honeypot.is_trap("/api/v1/land")
    honeypot.hit("10.0.0.3", "/admin.php", "scanner")
    assert honeypot.is_blocked("10.0.0.3")


def test_squatting_detects_lookalike():
    r = domain_squatting("econojin.co")
    assert r["verdict"] == "suspicious"
    assert r["squatting"][0]["distance"] <= 2


def test_squatting_ok_for_exact():
    r = domain_squatting("econojin.com")
    assert r["verdict"] == "ok"


def test_pqcrypto_status_honest():
    st = pqcrypto.status()
    assert "available" in st
    assert st["note"]  # always carries an honest note


def test_pqcrypto_hybrid_unavailable_or_ok():
    r = pqcrypto.hybrid_kem()
    assert r["status"] in ("ok", "unavailable")


def test_waterml_builds_valid_timeseries():
    from services.ogc.waterml import build_timeseries

    series = [
        {"month": "2024-01", "spi": -0.5, "spei": -0.3},
        {"month": "2024-02", "spi": 0.0, "spei": None},
        {"month": "2024-03", "spi": 1.25},
    ]
    xml = build_timeseries(series, index="spi", title="SPI")
    assert "OM_Observation" in xml
    assert "wml2:MeasurementTimeseries" in xml
    assert "2024-01-01T00:00:00Z" in xml
    assert "-0.500" in xml
    assert "nan" not in xml  # NaN / None omitted honestly


def test_ogc_landing_and_conformance():
    from services.ogc import features as ogc

    assert ogc._LANDING["title"].startswith("Eco Nojin")
    assert any("core" in c for c in ogc._CONFORMANCE["conformsTo"])
    assert ogc._COLLECTIONS["collections"][0]["id"] == ogc.COLLECTION_ID


def test_rag_index_and_search():
    from services.ai.rag import index

    n = index.build()
    assert n > 50  # Persian docs indexed
    results = index.search("بندسار رواناب", k=3)
    assert len(results) >= 1
    assert results[0]["file"].endswith(".md")


def test_nlg_advise_returns_evidence():
    from services.ai.nlg import advise

    out = advise("بندسار برای کاهش رواناب", {"spi": -0.812})
    assert out["provider"] == "local-nlg"
    assert "بندسار" in out["answer"]
    assert out["metrics"]["spi"] == -0.812
    assert len(out["evidence"]) >= 1
