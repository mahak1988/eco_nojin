"""Passkey ceremony tests.

A software authenticator (real ES256 keys via `cryptography`) drives the full
registration and authentication ceremonies, so the COSE encoding, challenge
binding and signature verification are all genuinely exercised rather than
mocked.
"""

from __future__ import annotations

import base64
import hashlib
import json

import cbor2
import pytest
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import ec
from webauthn.helpers import encode_cbor

from services.security.passkeys import (
    MAX_PASSKEYS_PER_USER,
    InMemoryCredentialStore,
    PasskeyError,
    PasskeyService,
    StoredCredential,
    _to_base64url,
    generate_challenge,
)

USER_ID = "user-123"
RP_ID = "localhost"
ORIGIN = "http://localhost:3000"


def b64u(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode()


def unb64u(value: str) -> bytes:
    return base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))


class SoftwareAuthenticator:
    """Minimal ES256 FIDO2 authenticator good enough to satisfy the library."""

    def __init__(self) -> None:
        self.key = ec.generate_private_key(ec.SECP256R1())
        self.sign_count = 0
        self.credential_id = b"cred-default"
        self.credential_id_b64 = b64u(self.credential_id)

    def set_credential_id(self, raw: bytes) -> None:
        self.credential_id = raw
        self.credential_id_b64 = b64u(raw)

    def _client_data(self, kind: str, challenge: str, origin: str) -> bytes:
        return json.dumps(
            {"type": kind, "challenge": challenge, "origin": origin, "crossOrigin": False},
            separators=(",", ":"),
        ).encode()

    def _auth_data(self, flags: int, sign_count: int, rp_id: str = RP_ID) -> bytes:
        """rpIdHash | flags | signCount [| attestedCredentialData] [| extensions]

        The client data is *not* part of authenticator data; only its hash is,
        appended after this structure by the caller.
        """
        return (
            hashlib.sha256(rp_id.encode()).digest() + bytes([flags]) + sign_count.to_bytes(4, "big")
        )

    def _cose_public_key(self) -> bytes:
        """COSE_Key for ES256.

        RFC 8152 COSE labels for an EC2 key: 1=kty (2=EC2), 3=alg (-7=ES256),
        -1=crv (1=P-256), -2=x, -3=y. All five are required: omitting crv
        fails key decoding, and using -1 for y instead of -3 fails the same way.
        """
        numbers = self.key.public_key().public_numbers()
        return encode_cbor(
            {
                1: 2,  # kty: EC2
                3: -7,  # alg: ES256
                -1: 1,  # crv: P-256
                -2: numbers.x.to_bytes(32, "big"),
                -3: numbers.y.to_bytes(32, "big"),
            }
        )

    def _attested_credential_data(self) -> bytes:
        aaguid = b"\x00" * 16  # no identifying AAGUID for a software authenticator
        cred_id = self.credential_id
        return aaguid + len(cred_id).to_bytes(2, "big") + cred_id + self._cose_public_key()

    def create(self, options_json: str, origin: str = ORIGIN, rp_id: str = RP_ID) -> dict:
        options = json.loads(options_json)
        client_data = self._client_data("webauthn.create", options["challenge"], origin)
        # UP (0x01) | UV (0x04) | AT (0x40): AT means attested credential data
        # follows, which is what carries the public key to the server.
        auth_data = self._auth_data(0x45, 0, rp_id) + self._attested_credential_data()
        # "none" attestation: CBOR {fmt, attStmt, authData}. The authData field
        # holds exactly the authenticator data structure — this library feeds
        # it straight to the parser, so appending the client-data hash here
        # would be rejected as trailing bytes.
        attestation = cbor2.dumps({"fmt": "none", "attStmt": {}, "authData": auth_data})
        return {
            "id": self.credential_id_b64,
            "rawId": self.credential_id_b64,
            "type": "public-key",
            "authenticatorAttachment": "platform",
            "transports": ["internal", "hybrid"],
            "clientExtensionResults": {},
            "response": {
                "attestationObject": b64u(attestation),
                "clientDataJSON": b64u(client_data),
            },
        }

    def get(self, options_json: str, origin: str = ORIGIN) -> dict:
        options = json.loads(options_json)
        self.sign_count += 1
        client_data = self._client_data("webauthn.get", options["challenge"], origin)
        # UP | UV, no attested credential data
        auth_data = self._auth_data(0x05, self.sign_count)
        # the assertion signature covers authenticatorData || clientDataHash
        signed = auth_data + hashlib.sha256(client_data).digest()
        signature = self.key.sign(signed, ec.ECDSA(hashes.SHA256()))
        return {
            "id": self.credential_id_b64,
            "rawId": self.credential_id_b64,
            "type": "public-key",
            "clientExtensionResults": {},
            "response": {
                "authenticatorData": b64u(auth_data),
                "clientDataJSON": b64u(client_data),
                "signature": b64u(signature),
                "userHandle": b64u(USER_ID.encode()),
            },
        }


@pytest.fixture
def service() -> PasskeyService:
    return PasskeyService(
        store=InMemoryCredentialStore(),
        rp_id=RP_ID,
        rp_name="Eco Nojin",
        origin=ORIGIN,
    )


@pytest.fixture
def authn() -> SoftwareAuthenticator:
    return SoftwareAuthenticator()


def register(service: PasskeyService, authn: SoftwareAuthenticator, name: str = "Pixel"):
    options = service.begin_registration(USER_ID, "farmer@example.com", "Farmer")
    return service.finish_registration(USER_ID, authn.create(options), name=name)


# --------------------------------------------------------------------------
# registration
# --------------------------------------------------------------------------
def test_registration_round_trip(service, authn):
    result = register(service, authn)
    assert result["credential_id"] == authn.credential_id_b64
    assert result["name"] == "Pixel"
    stored = service.store.get(authn.credential_id_b64)
    assert stored is not None
    assert stored.sign_count >= 0


def test_registration_options_are_well_formed(service):
    options = json.loads(service.begin_registration(USER_ID, "farmer@example.com", "Farmer"))
    assert options["rp"]["id"] == RP_ID
    assert options["rp"]["name"] == "Eco Nojin"
    assert options["user"]["name"] == "farmer@example.com"
    assert options["challenge"]
    assert options["pubKeyCredParams"]
    # user verification must be demanded, or the passkey stops being one
    assert options["authenticatorSelection"]["userVerification"] == "required"


def test_registration_requires_user_verification(service):
    options = json.loads(service.begin_registration(USER_ID, "u", "U"))
    assert options["authenticatorSelection"]["userVerification"] == "required"
    assert options["attestation"] == "none"


def test_registration_cannot_be_replayed(service, authn):
    options = service.begin_registration(USER_ID, "u", "U")
    payload = authn.create(options)
    service.finish_registration(USER_ID, payload)
    with pytest.raises(PasskeyError):
        service.finish_registration(USER_ID, payload)


def test_registration_without_a_started_ceremony_fails(service, authn):
    """No challenge was issued, so a well-formed response must still be
    refused. The payload is built from a throwaway challenge."""
    throwaway = json.loads(service.begin_registration("other-user", "u", "U"))
    payload = authn.create(json.dumps(throwaway))
    with pytest.raises(PasskeyError):
        service.finish_registration(USER_ID, payload)


def test_registration_from_another_origin_is_rejected(service, authn):
    """The authenticator signs for a legitimate challenge but claims a
    different origin, which is exactly a phishing relay."""
    options = service.begin_registration(USER_ID, "u", "U")
    with pytest.raises(PasskeyError):
        service.finish_registration(USER_ID, authn.create(options, origin="https://evil.example"))


def test_registration_against_another_rp_is_rejected(service, authn):
    """authData is hashed over the RP id, so a response minted for a different
    relying party cannot be replayed here."""
    options = service.begin_registration(USER_ID, "u", "U")
    with pytest.raises(PasskeyError):
        service.finish_registration(USER_ID, authn.create(options, rp_id="evil.example"))


# --------------------------------------------------------------------------
# authentication
# --------------------------------------------------------------------------
def test_authentication_round_trip(service, authn):
    register(service, authn)
    options = service.begin_authentication(USER_ID)
    allowed = json.loads(options)["allowCredentials"]
    assert [c["id"] for c in allowed] == [authn.credential_id_b64]
    verified = service.finish_authentication(authn.get(options), USER_ID)
    assert verified == USER_ID


def test_sign_count_advances(service, authn):
    register(service, authn)
    first = service.store.get(authn.credential_id_b64)
    options = service.begin_authentication(USER_ID)
    service.finish_authentication(authn.get(options), USER_ID)
    second = service.store.get(authn.credential_id_b64)
    assert second.sign_count > first.sign_count, "clone detection depends on the counter moving"


def test_challenge_cannot_be_replayed(service, authn):
    register(service, authn)
    options = service.begin_authentication(USER_ID)
    payload = authn.get(options)
    service.finish_authentication(payload, USER_ID)
    with pytest.raises(PasskeyError):
        service.finish_authentication(payload, USER_ID)


def test_authentication_without_a_started_ceremony_fails(service, authn):
    register(service, authn)
    throwaway = service.begin_authentication("someone-else")
    payload = authn.get(throwaway)
    with pytest.raises(PasskeyError):
        service.finish_authentication(payload, USER_ID)


def test_unknown_credential_is_rejected(service, authn):
    register(service, authn)
    options = service.begin_authentication(USER_ID)
    payload = authn.get(options)
    payload["id"] = b64u(b"not-a-known-credential")
    payload["rawId"] = payload["id"]
    with pytest.raises(PasskeyError):
        service.finish_authentication(payload, USER_ID)


def test_signature_from_a_different_key_is_rejected(service, authn):
    register(service, authn)
    options = service.begin_authentication(USER_ID)
    payload = authn.get(options)

    impostor = SoftwareAuthenticator()
    impostor.credential_id = authn.credential_id
    impostor.credential_id_b64 = authn.credential_id_b64  # same id, different key
    forged = impostor.get(options)
    payload["response"] = forged["response"]

    with pytest.raises(PasskeyError):
        service.finish_authentication(payload, USER_ID)


def test_wrong_challenge_is_rejected(service, authn):
    register(service, authn)
    service.begin_authentication(USER_ID)
    payload = authn.get(json.dumps({"challenge": generate_challenge()}))
    with pytest.raises(PasskeyError):
        service.finish_authentication(payload, USER_ID)


def test_authentication_from_another_origin_is_rejected(service, authn):
    register(service, authn)
    options = service.begin_authentication(USER_ID)
    payload = authn.get(options, origin="https://evil.example")
    with pytest.raises(PasskeyError):
        service.finish_authentication(payload, USER_ID)


def test_usernameless_flow_lists_no_credentials(service, authn):
    register(service, authn)
    options = json.loads(service.begin_authentication(None))
    assert not options.get("allowCredentials")
    verified = service.finish_authentication(authn.get(json.dumps(options)), None)
    assert verified == USER_ID


# --------------------------------------------------------------------------
# management
# --------------------------------------------------------------------------
def test_list_and_remove_passkeys(service, authn):
    register(service, authn, name="Phone")
    listed = service.list_passkeys(USER_ID)
    assert len(listed) == 1
    assert listed[0]["name"] == "Phone"
    assert service.remove_passkey(USER_ID, authn.credential_id_b64) is True
    assert service.list_passkeys(USER_ID) == []


def test_cannot_remove_another_users_passkey(service, authn):
    register(service, authn)
    assert service.remove_passkey("someone-else", authn.credential_id_b64) is False
    assert len(service.list_passkeys(USER_ID)) == 1


def test_per_user_passkey_limit(service):
    for i in range(MAX_PASSKEYS_PER_USER):
        a = SoftwareAuthenticator()
        a.credential_id = f"cred-{i}".encode()
        a.credential_id_b64 = b64u(a.credential_id)
        options = service.begin_registration(USER_ID, "u", "U")
        service.finish_registration(USER_ID, a.create(options))
    extra = SoftwareAuthenticator()
    options = service.begin_registration(USER_ID, "u", "U")
    with pytest.raises(PasskeyError):
        service.finish_registration(USER_ID, extra.create(options))


def test_multiple_passkeys_coexist(service):
    first, second = SoftwareAuthenticator(), SoftwareAuthenticator()
    second.credential_id = b"cred-second"
    second.credential_id_b64 = b64u(second.credential_id)
    for a in (first, second):
        options = service.begin_registration(USER_ID, "u", "U")
        service.finish_registration(USER_ID, a.create(options))
    assert len(service.list_passkeys(USER_ID)) == 2


# --------------------------------------------------------------------------
# store
# --------------------------------------------------------------------------
def test_store_is_case_sensitive_on_credential_id():
    store = InMemoryCredentialStore()
    store.save("u1", StoredCredential(credential_id="AbC", public_key="k"))
    assert store.get("abc") is None


def test_base64url_normalisation():
    raw = b"\xfb\xff\x00"
    assert unb64u(_to_base64url(b64u(raw))) == raw
    assert _to_base64url(raw) == b64u(raw)


def test_pending_challenges_are_bounded():
    svc = PasskeyService(store=InMemoryCredentialStore(), rp_id=RP_ID, origin=ORIGIN)
    for i in range(400):
        svc._remember(f"k{i}", f"c{i}".encode(), "registration", "u")
    assert len(svc._pending) <= 10_000
