"""Tests for post-quantum cryptography module."""

import os

import pytest

from services.security.pqcrypto import available, hybrid_kem, hybrid_sign, status


class TestPQCStatus:
    def test_status_returns_dict(self):
        s = status()
        assert isinstance(s, dict)
        assert "available" in s
        assert "kem" in s
        assert "signature" in s

    def test_available_matches_liboqs(self):
        try:
            import oqs  # noqa: F401
            has_liboqs = True
        except Exception:
            try:
                import liboqs  # noqa: F401
                has_liboqs = True
            except Exception:
                has_liboqs = False
        assert available() == has_liboqs


class TestHybridKEM:
    def test_unavailable_when_no_liboqs(self, monkeypatch):
        monkeypatch.setattr("services.security.pqcrypto._OQS_AVAILABLE", False)
        result = hybrid_kem()
        assert result["status"] == "unavailable"

    @pytest.mark.skipif(
        not available(),
        reason="liboqs not installed on this platform",
    )
    def test_hybrid_kem_returns_keys(self):
        result = hybrid_kem()
        assert result["status"] == "ok"
        assert "ciphertext_hex" in result
        assert "shared_secret_hex" in result
        assert "public_key_hex" in result
        assert result["algorithm"] == "KYBER512+X25519"
        assert len(result["ciphertext_hex"]) > 0
        assert len(result["shared_secret_hex"]) > 0

    @pytest.mark.skipif(
        not available(),
        reason="liboqs not installed on this platform",
    )
    def test_hybrid_kem_deterministic_with_seed(self):
        r1 = hybrid_kem()
        r2 = hybrid_kem()
        assert r1["status"] == "ok"
        assert r2["status"] == "ok"
        assert r1["ciphertext_hex"] != r2["ciphertext_hex"]


class TestHybridSign:
    def test_unavailable_when_no_liboqs(self, monkeypatch):
        monkeypatch.setattr("services.security.pqcrypto._OQS_AVAILABLE", False)
        result = hybrid_sign(b"test message")
        assert result["status"] == "unavailable"

    @pytest.mark.skipif(
        not available(),
        reason="liboqs not installed on this platform",
    )
    def test_hybrid_sign_returns_signature(self):
        msg = b"Eco Nojin test message"
        result = hybrid_sign(msg)
        assert result["status"] == "ok"
        assert "signature_hex" in result
        assert "pq_public_hex" in result
        assert result["algorithm"] == "DILITHIUM2+ED25519"
        assert len(result["signature_hex"]) > 0
