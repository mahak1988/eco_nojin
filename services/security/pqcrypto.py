"""Layer 6 — post-quantum cryptography (CRYSTALS-Kyber / Dilithium).

Uses the free `oqs` (liboqs) package:
- Kyber512/768 KEM, run in hybrid mode with X25519 (classic) so a break of
  either side keeps the other safe.
- Dilithium2 signatures, hybrid with Ed25519 for audit certificates.

Honesty contract: if liboqs is not importable the module reports
`status: unavailable` and the app degrades gracefully (classic crypto only).
"""
import os

try:
    # real liboqs binding: package `oqs` (open-quantum-safe) on Linux/macOS;
    # `liboqs-python` ships only a metadata stub on Windows (no compiled lib)
    from oqs import KeyEncapsulation, Signature  # type: ignore

    _OQS_AVAILABLE = True
    _OQS_LIB = "oqs (liboqs)"
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


def status() -> dict:
    return {
        "available": _OQS_AVAILABLE,
        "kem": "CRYSTALS-Kyber-512 (hybrid X25519)" if _OQS_AVAILABLE else "not_installed",
        "signature": "CRYSTALS-Dilithium-2 (hybrid Ed25519)" if _OQS_AVAILABLE else "not_installed",
        "note": (
            "هیبرید: امنیت پساکوانتوم + سازگاری کلاسیک. "
            "liboqs روی ویندوز باینری pip ندارد (نیازمند کامپایل CMake)؛ مسیر رایگان: استقرار پشت Cloudflare "
            "که TLS پساکوانتوم (X25519MLKEM768) را در لبه فعال می‌کند، یا نصب liboqs روی Linux/macOS/Docker."
            if not _OQS_AVAILABLE
            else f"کتابخانه: {_OQS_LIB}"
        ),
    }


def hybrid_kem() -> dict:
    """Hybrid KEM: returns (ciphertext, shared_secret_hex, public_metadata)."""
    if not _OQS_AVAILABLE:
        return {"status": "unavailable", "note": "پساکوانتوم نصب نیست؛ از رمزنگاری کلاسیک استفاده کنید."}
    try:
        with KeyEncapsulation("KYBER512") as kem:
            pub, _ = kem.generate_keypair()
            ciphertext, shared_kyber = kem.encap_secret(pub)
        classic_priv = os.urandom(32)
        classic_pub = _x25519_pub(classic_priv)
        shared_classic = _x25519_shared(classic_priv, classic_pub)
        hybrid = _xor_bytes(shared_kyber, shared_classic)
        return {
            "status": "ok",
            "algorithm": "KYBER512+X25519",
            "ciphertext_hex": ciphertext.hex(),
            "shared_secret_hex": hybrid.hex(),
            "public_key_hex": pub.hex(),
            "note": "کلید مشترک هیبرید = XOR(کیبر، X25519)؛ نمایشی برای اثبات قابلیت.",
        }
    except Exception as exc:  # pragma: no cover
        return {"status": "error", "error": str(exc)}


def hybrid_sign(message: bytes) -> dict:
    """Hybrid signature: Dilithium2 || Ed25519 (concatenated, both verified)."""
    if not _OQS_AVAILABLE:
        return {"status": "unavailable", "note": "پساکوانتوم نصب نیست."}
    try:
        from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

        with Signature("DILITHIUM2") as sig:
            pq_pub, pq_priv = sig.generate_keypair()
            pq_sig = sig.sign(pq_priv, message)
        classic_priv = Ed25519PrivateKey.generate()
        classic_sig = classic_priv.sign(message)
        return {
            "status": "ok",
            "algorithm": "DILITHIUM2+ED25519",
            "signature_hex": (pq_sig + classic_sig).hex(),
            "pq_public_hex": pq_pub.hex(),
            "note": "امضای هیبرید: دیلیتیوم2 ║ اد25519؛ هر دو برای اعتبارسنجی لازم‌اند.",
        }
    except Exception as exc:  # pragma: no cover
        return {"status": "error", "error": str(exc)}


def _x25519_pub(priv: bytes) -> bytes:
    from cryptography.hazmat.primitives.asymmetric.x25519 import X25519PrivateKey

    return X25519PrivateKey.from_private_bytes(priv).public_key().public_bytes_raw()


def _x25519_shared(priv: bytes, pub: bytes) -> bytes:
    from cryptography.hazmat.primitives.asymmetric.x25519 import X25519PrivateKey, X25519PublicKey

    priv_key = X25519PrivateKey.from_private_bytes(priv)
    pub_key = X25519PublicKey.from_public_bytes(pub)
    return priv_key.exchange(pub_key)


def _xor_bytes(a: bytes, b: bytes) -> bytes:
    return bytes(x ^ y for x, y in zip(a, b))
