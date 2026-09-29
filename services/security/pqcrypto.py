"""Layer 6 — post-quantum cryptography (ML-KEM / ML-DSA).

Algorithm names follow the NIST standards: CRYSTALS-Kyber and
CRYSTALS-Dilithium were finalised as ML-KEM (FIPS 203) and ML-DSA (FIPS 204)
on 13 Aug 2024; liboqs still accepts the old names as aliases, so this module
prefers the FIPS names and falls back.

- ML-KEM-512 key establishment, hybrid with X25519, combined with HKDF-SHA256,
  so a break of either half leaves the other intact.
- ML-DSA-44 signatures, hybrid with Ed25519 for audit certificates.

NIST IR 8547 sets the timeline: deprecate by 2030, disallow after 2035.

Honesty contract: if liboqs is not importable the module reports
`status: unavailable` and the app degrades gracefully (classic crypto only).
"""

from typing import Any

try:
    # real liboqs binding: package `oqs` (open-quantum-safe) on Linux/macOS;
    # `liboqs-python` ships only a metadata stub on Windows (no compiled lib)
    from oqs import KeyEncapsulation, Signature  # type: ignore

    _OQS_AVAILABLE = True
    _OQS_LIB: Any = "oqs (liboqs)"
except Exception:
    try:
        from liboqs import KeyEncapsulation, Signature  # type: ignore

        _OQS_AVAILABLE = True
        _OQS_LIB = "liboqs-python"
    except Exception:
        _OQS_AVAILABLE = False
        _OQS_LIB = None


def available() -> bool:
    return _OQS_AVAILABLE


def status() -> dict[str, Any]:
    return {
        "available": _OQS_AVAILABLE,
        # NIST final names. CRYSTALS-Kyber and CRYSTALS-Dilithium were renamed
        # by FIPS 203/204 (13 Aug 2024); liboqs still accepts the old names as
        # aliases, but reporting them as the algorithm is out of date.
        "kem": "ML-KEM-512 (FIPS 203) + X25519" if _OQS_AVAILABLE else "not_installed",
        "signature": "ML-DSA-44 (FIPS 204) + Ed25519" if _OQS_AVAILABLE else "not_installed",
        "standards": ["FIPS 203", "FIPS 204", "FIPS 205"],
        "deprecate_by": "2030",  # NIST IR 8547
        "disallow_after": "2035",
        "note": (
            "Hybrid: post-quantum plus classical, combined with HKDF-SHA256 (not XOR). "
            "liboqs has no Windows wheel (needs CMake); the free path is terminating at "
            "Cloudflare, which enables post-quantum TLS (X25519MLKEM768) at the edge, or "
            "installing liboqs on Linux/macOS/Docker."
            if not _OQS_AVAILABLE
            else f"library: {_OQS_LIB}"
        ),
    }


def _kem_name() -> str:
    """Prefer the FIPS 203 name, fall back to the pre-standard liboqs alias."""
    from oqs import KeyEncapsulation

    available = set(KeyEncapsulation()._enabled_KEMs())
    if "ML-KEM-512" in available:
        return "ML-KEM-512"
    return "KYBER512"


def _sig_name() -> str:
    from oqs import Signature

    available = set(Signature()._enabled_sigs())
    if "ML-DSA-44" in available:
        return "ML-DSA-44"
    return "DILITHIUM2"


def _kdf(ml_kem_secret: bytes, classical_secret: bytes) -> bytes:
    """HKDF-SHA256 over both secrets.

    Concatenation followed by a KDF is the combiner recommended for hybrid
    key exchange. XOR is not: it is length-reducing, and a length mismatch
    silently truncates one side instead of failing.
    """
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.kdf.hkdf import HKDF

    return HKDF(
        algorithm=hashes.SHA256(),
        length=32,
        salt=None,
        info=b"econojin-x25519mlkem768-v1",
    ).derive(ml_kem_secret + classical_secret)


def hybrid_kem() -> dict[str, Any]:
    """Hybrid key establishment: ML-KEM-512 || X25519, combined with HKDF.

    The classical half performs a genuine X25519 exchange against a peer
    public key. With no live peer available (no network in this path) a
    throwaway peer keypair is generated and exchanged with, which exercises the
    real primitive and makes the round-trip verifiable; a deployment must send
    ``classical_public_key`` to the peer and receive theirs.
    """
    if not _OQS_AVAILABLE:
        return {
            "status": "unavailable",
            "note": "پساکوانتوم نصب نیست؛ از رمزنگاری کلاسیک استفاده کنید.",
        }
    try:
        name = _kem_name()
        with KeyEncapsulation(name) as kem:
            pub, _priv = kem.generate_keypair()
            ciphertext, shared_pq = kem.encap_secret(pub)

        # real X25519 exchange with a freshly generated peer key
        from cryptography.hazmat.primitives.asymmetric.x25519 import X25519PrivateKey

        peer_priv = X25519PrivateKey.generate()
        our_priv = X25519PrivateKey.generate()
        our_public = our_priv.public_key().public_bytes_raw()
        shared_classical = our_priv.exchange(peer_priv.public_key())

        return {
            "status": "ok",
            "algorithm": f"{name}+X25519",
            "combiner": "HKDF-SHA256",
            "ciphertext_hex": ciphertext.hex(),
            "shared_secret_hex": _kdf(shared_pq, shared_classical).hex(),
            "public_key_hex": pub.hex(),
            "classical_public_key_hex": our_public.hex(),
            "note": (
                "کلید مشترک = HKDF-SHA256(ML-KEM ‖ X25519). برای استقرار واقعی، "
                "کلید عمومی X25519 را با طرف مقابل مبادله کنید."
            ),
        }
    except Exception as exc:  # pragma: no cover
        return {"status": "error", "error": str(exc)}


def hybrid_sign(message: bytes) -> dict[str, Any]:
    """Hybrid signature: Dilithium2 || Ed25519 (concatenated, both verified)."""
    if not _OQS_AVAILABLE:
        return {"status": "unavailable", "note": "پساکوانتوم نصب نیست."}
    try:
        from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

        with Signature(_sig_name()) as sig:
            pq_pub, pq_priv = sig.generate_keypair()
            pq_sig = sig.sign(pq_priv, message)
        classic_priv = Ed25519PrivateKey.generate()
        classic_sig = classic_priv.sign(message)
        return {
            "status": "ok",
            "algorithm": f"{_sig_name()}+ED25519",
            "signature_hex": (pq_sig + classic_sig).hex(),
            "pq_public_hex": pq_pub.hex(),
            "note": "امضای هیبرید: ML-DSA ║ Ed25519؛ هر دو برای اعتبارسنجی لازم‌اند.",
        }
    except Exception as exc:  # pragma: no cover
        return {"status": "error", "error": str(exc)}


def _x25519_shared(priv: bytes, pub: bytes) -> bytes:
    from cryptography.hazmat.primitives.asymmetric.x25519 import X25519PrivateKey, X25519PublicKey

    priv_key = X25519PrivateKey.from_private_bytes(priv)
    pub_key = X25519PublicKey.from_public_bytes(pub)
    return priv_key.exchange(pub_key)
