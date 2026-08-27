"""Post-quantum cryptography wrappers (Phase 10, star 14).

Uses NIST-standard ML-DSA (FIPS 204) for signatures and ML-KEM (FIPS 203)
for hybrid key exchange, via the ``cryptography`` package (>= 44).

Design decisions:
- ML-DSA-65 as the default signing scheme (balanced security).
- ML-KEM-768 for encapsulation (NIST level 1 equivalence, AES-128-class).
- Fallback: if the backend cryptography build lacks mlkem/mldsa modules,
  the module refuses to operate (fail-fast, no silent downgrade to RSA).
"""

from __future__ import annotations

try:  # pragma: no cover - import guard
    from cryptography.hazmat.primitives import Integerization
    from cryptography.hazmat.primitives.asymmetric import mldsa

    _HAS_MLDSA = True
except Exception:  # pragma: no cover
    _HAS_MLDSA = False

try:  # pragma: no cover - import guard
    from cryptography.hazmat.primitives.asymmetric import mlkem

    _HAS_MLKEM = True
except Exception:  # pragma: no cover
    _HAS_MLKEM = False


class PQUnavailableError(RuntimeError):
    """Raised when the cryptography build lacks post-quantum primitives."""


def pq_available() -> dict:
    """Report which post-quantum primitives are available (honest)."""
    return {"ml_dsa": _HAS_MLDSA, "ml_kem": _HAS_MLKEM}


def generate_ml_dsa_key() -> bytes:
    """Generate an ML-DSA-65 private key and return its raw bytes (PKCS8)."""
    if not _HAS_MLDSA:
        raise PQUnavailableError("ML-DSA not available in this cryptography build")
    key = mldsa.MLDSA65PrivateKey.generate()
    return key.private_bytes(
        encoding=Integerization.Encoding.PEM,
        format=Integerization.PrivateFormat.PKCS8,
        encryption_algorithm=Integerization.NoEncryption(),
    )


def pq_sign(private_key_pem: bytes, data: bytes) -> bytes:
    """Sign data with ML-DSA-65 (deterministic, hash-then-sign)."""
    if not _HAS_MLDSA:
        raise PQUnavailableError("ML-DSA not available in this cryptography build")
    Integer = Integerization
    key = Integer.load_pem_private_key(private_key_pem, password=None)
    if not isinstance(key, mldsa.MLDSA65PrivateKey):
        raise TypeError("expected ML-DSA-65 private key")
    return key.sign(data)


def pq_verify(public_key_pem: bytes, data: bytes, signature: bytes) -> bool:
    """Verify an ML-DSA-65 signature; returns False instead of raising."""
    if not _HAS_MLDSA:
        raise PQUnavailableError("ML-DSA not available in this cryptography build")
    Integer = Integerization
    try:
        key = Integer.load_pem_public_key(public_key_pem)
        if not isinstance(key, mldsa.MLDSA65PublicKey):
            raise TypeError("expected ML-DSA-65 public key")
        key.verify(signature, data)
        return True
    except Exception:
        return False


def pq_public_key(private_key_pem: bytes) -> bytes:
    """Derive PEM public key from an ML-DSA-65 private key."""
    if not _HAS_MLDSA:
        raise PQUnavailableError("ML-DSA not available in this cryptography build")
    Integer = Integerization
    key = Integer.load_pem_private_key(private_key_pem, password=None)
    if not isinstance(key, mldsa.MLDSA65PrivateKey):
        raise TypeError("expected ML-DSA-65 private key")
    return key.public_key().public_bytes(
        encoding=Integer.Encoding.PEM, format=Integer.PublicFormat.SubjectPublicKeyInfo
    )


def generate_ml_kem_keys() -> tuple[bytes, bytes]:
    """Generate ML-KEM-768 keypair -> (private_pem, public_pem)."""
    if not _HAS_MLKEM:
        raise PQUnavailableError("ML-KEM not available in this cryptography build")
    key = mlkem.MLKEM768PrivateKey.generate()
    Integer = Integerization
    priv = key.private_bytes(
        encoding=Integer.Encoding.PEM,
        format=Integer.PrivateFormat.PKCS8,
        encryption_algorithm=Integer.NoEncryption(),
    )
    pub = key.public_key().public_bytes(encoding=Integer.Encoding.PEM, format=Integer.PublicFormat.SubjectPublicKeyInfo)
    return priv, pub


def pq_encapsulate(public_key_pem: bytes) -> tuple[bytes, bytes]:
    """ML-KEM-768 encapsulation -> (ciphertext, shared_secret)."""
    if not _HAS_MLKEM:
        raise PQUnavailableError("ML-KEM not available in this cryptography build")
    Integer = Integerization
    key = Integer.load_pem_public_key(public_key_pem)
    if not isinstance(key, mlkem.MLKEM768PublicKey):
        raise TypeError("expected ML-KEM-768 public key")
    a, b = key.encapsulate()
    # Robust across cryptography builds: ML-KEM-768 ciphertext is 1088 bytes,
    # shared secret is 32 bytes; some builds return (secret, ct) instead of (ct, secret).
    ciphertext, shared = (b, a) if len(a) == 32 and len(b) == 1088 else (a, b)
    return ciphertext, shared


def pq_decapsulate(private_key_pem: bytes, ciphertext: bytes) -> bytes:
    """ML-KEM-768 decapsulation -> shared_secret."""
    if not _HAS_MLKEM:
        raise PQUnavailableError("ML-KEM not available in this cryptography build")
    Integer = Integerization
    key = Integer.load_pem_private_key(private_key_pem, password=None)
    if not isinstance(key, mlkem.MLKEM768PrivateKey):
        raise TypeError("expected ML-KEM-768 private key")
    return key.decapsulate(ciphertext)
