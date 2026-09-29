"""Passkeys (FIDO2 / WebAuthn) — server-side ceremonies and storage.

A passkey replaces the shared secret with a per-device key pair: the private
half never leaves the authenticator and is not phishable, which removes the
credential-stuffing and password-replay surface that OTP alone does not.

Ceremony shape
--------------
Registration (once per device)::

    options  = generate_registration_options(rp, user, challenge)
    <- JSON sent to the browser
    response = browser calls navigator.credentials.create(options)
    verify_registration_response(response, expected_challenge, rp_id, ...)
    -> store credential_id, public_key (COSE), sign_count

Authentication (every sign-in)::

    options  = generate_authentication_options(rp_id, challenge, allow=[credential_id])
    <- JSON sent to the browser
    response = browser calls navigator.credentials.get(options)
    verify_authentication_response(response, credential, expected_challenge, ...)

Both ceremonies are bound to a single-use challenge that is stored per process
and checked on completion, so an intercepted ``options`` payload cannot be
replayed to register or authenticate.

Storage is injected rather than imported, so the ceremony logic is testable
without a database and the module carries no import-time dependency on the
ORM.
"""

from __future__ import annotations

import base64
import json
import secrets
import threading
import time
from dataclasses import dataclass, field
from typing import Any, Protocol

from webauthn import (
    generate_authentication_options,
    generate_registration_options,
    verify_authentication_response,
    verify_registration_response,
)
from webauthn.helpers import base64url_to_bytes, bytes_to_base64url, options_to_json
from webauthn.helpers.cose import COSEAlgorithmIdentifier
from webauthn.helpers.exceptions import InvalidAuthenticationResponse, InvalidRegistrationResponse
from webauthn.helpers.structs import (
    AttestationConveyancePreference,
    AuthenticatorSelectionCriteria,
    PublicKeyCredentialDescriptor,
    ResidentKeyRequirement,
    UserVerificationRequirement,
)

CHALLENGE_TTL = 300.0
MAX_PENDING = 10_000
MAX_PASSKEYS_PER_USER = 10

REGISTRATION = "registration"
AUTHENTICATION = "authentication"


class PasskeyError(Exception):
    """Raised for any rejected ceremony, with a caller-safe message."""


@dataclass(frozen=True)
class StoredCredential:
    credential_id: str
    public_key: str
    sign_count: int = 0
    transports: tuple[str, ...] = ()
    backed_up: bool = False
    name: str | None = None
    aaguid: str | None = None


class CredentialStore(Protocol):
    """Persistence contract. Implemented over SQLAlchemy in the API layer."""

    def get(self, credential_id: str) -> StoredCredential | None: ...

    def get_for_user(self, user_id: str) -> list[StoredCredential]: ...

    def owner_of(self, credential_id: str) -> str | None:
        """Which user a credential belongs to.

        Preferred over the ``userHandle`` in the response, which the client
        supplies and can therefore claim. The server-side mapping is the only
        trustworthy answer to "who authenticated".
        """
        ...

    def save(self, user_id: str, credential: StoredCredential) -> None: ...

    def update_sign_count(self, credential_id: str, sign_count: int) -> None: ...

    def delete(self, user_id: str, credential_id: str) -> bool: ...


class InMemoryCredentialStore:
    """Reference store. Used by tests and by single-process deployments."""

    def __init__(self) -> None:
        self._data: dict[str, StoredCredential] = {}
        self._owner: dict[str, str] = {}
        self._lock = threading.Lock()

    def get(self, credential_id: str) -> StoredCredential | None:
        with self._lock:
            return self._data.get(credential_id)

    def get_for_user(self, user_id: str) -> list[StoredCredential]:
        with self._lock:
            return [c for cid, c in self._data.items() if self._owner.get(cid) == user_id]

    def owner_of(self, credential_id: str) -> str | None:
        with self._lock:
            return self._owner.get(credential_id)

    def save(self, user_id: str, credential: StoredCredential) -> None:
        with self._lock:
            owned = sum(1 for cid in self._data if self._owner.get(cid) == user_id)
            if owned >= MAX_PASSKEYS_PER_USER:
                raise PasskeyError(
                    f"passkey limit reached ({MAX_PASSKEYS_PER_USER}); remove one first"
                )
            self._data[credential.credential_id] = credential
            self._owner[credential.credential_id] = user_id

    def update_sign_count(self, credential_id: str, sign_count: int) -> None:
        with self._lock:
            current = self._data.get(credential_id)
            if current is not None:
                self._data[credential_id] = StoredCredential(
                    credential_id=current.credential_id,
                    public_key=current.public_key,
                    sign_count=sign_count,
                    transports=current.transports,
                    backed_up=current.backed_up,
                    name=current.name,
                    aaguid=current.aaguid,
                )

    def delete(self, user_id: str, credential_id: str) -> bool:
        with self._lock:
            if self._owner.get(credential_id) != user_id:
                return False
            self._owner.pop(credential_id, None)
            return self._data.pop(credential_id, None) is not None


@dataclass
class _Pending:
    challenge: str
    kind: str
    user_id: str
    created_at: float


@dataclass
class PasskeyService:
    """Ceremony orchestration. Bind the store at construction."""

    store: CredentialStore = field(default_factory=InMemoryCredentialStore)
    rp_id: str = "localhost"
    rp_name: str = "Eco Nojin"
    origin: str = "http://localhost:3000"
    _pending: dict[str, _Pending] = field(default_factory=dict)
    _lock: threading.Lock = field(default_factory=threading.Lock)

    # -- challenge bookkeeping -------------------------------------------
    def _remember(self, key: str, challenge: bytes, kind: str, user_id: str) -> None:
        now = time.time()
        with self._lock:
            for k, p in list(self._pending.items()):
                if now - p.created_at > CHALLENGE_TTL:
                    del self._pending[k]
            overflow = len(self._pending) - MAX_PENDING
            if overflow > 0:
                oldest = sorted(self._pending.items(), key=lambda kv: kv[1].created_at)
                for k, _p in oldest[:overflow]:
                    self._pending.pop(k, None)
            self._pending[key] = _Pending(bytes_to_base64url(challenge), kind, user_id, now)

    def _consume(self, key: str, kind: str) -> _Pending | None:
        with self._lock:
            pending = self._pending.pop(key, None)
        if pending is None or pending.kind != kind:
            return None
        if time.time() - pending.created_at > CHALLENGE_TTL:
            return None
        return pending

    # -- registration ----------------------------------------------------
    def begin_registration(self, user_id: str, user_name: str, user_display_name: str) -> str:
        options = generate_registration_options(
            rp_id=self.rp_id,
            rp_name=self.rp_name,
            user_id=user_id.encode("utf-8"),
            user_name=user_name,
            user_display_name=user_display_name or user_name,
            attestation=AttestationConveyancePreference.NONE,
            authenticator_selection=AuthenticatorSelectionCriteria(
                resident_key=ResidentKeyRequirement.DISCOURAGED,
                user_verification=UserVerificationRequirement.REQUIRED,
            ),
            supported_pub_key_algs=[
                COSEAlgorithmIdentifier.ECDSA_SHA_256,
                COSEAlgorithmIdentifier.EDDSA,
            ],
        )
        self._remember(f"reg:{user_id}", options.challenge, REGISTRATION, user_id)
        return options_to_json(options)

    def finish_registration(
        self, user_id: str, response: dict[str, Any], name: str | None = None
    ) -> dict[str, Any]:
        pending = self._consume(f"reg:{user_id}", REGISTRATION)
        if pending is None:
            raise PasskeyError("no registration in progress, or it expired")
        try:
            verification = verify_registration_response(
                credential=_as_json(response),
                expected_challenge=base64url_to_bytes(pending.challenge),
                expected_origin=self.origin,
                expected_rp_id=self.rp_id,
                require_user_verification=True,
            )
        except InvalidRegistrationResponse as exc:
            raise PasskeyError(str(exc)) from exc

        transports = response.get("transports") or response.get("transportsHint") or []
        credential = StoredCredential(
            # The library hands back raw bytes; the store is keyed and typed on
            # base64url so the same encoding works for a DB column and for
            # memory. Encoding here rather than at each read site is what keeps
            # the two backends interchangeable.
            credential_id=bytes_to_base64url(verification.credential_id),
            public_key=verification.credential_public_key
            if isinstance(verification.credential_public_key, str)
            else bytes_to_base64url(verification.credential_public_key),
            sign_count=verification.sign_count,
            transports=tuple(str(t) for t in transports),
            backed_up=bool(getattr(verification, "credential_backed_up", False)),
            name=name,
            aaguid=verification.aaguid,
        )
        self.store.save(user_id, credential)
        return {
            "credential_id": credential.credential_id,
            "name": name,
            "sign_count": credential.sign_count,
            "aaguid": credential.aaguid,
        }

    # -- authentication --------------------------------------------------
    def begin_authentication(self, user_id: str | None = None) -> str:
        # The library expects descriptor objects with raw-byte ids, not the
        # base64url strings the store keeps.
        allow: list[PublicKeyCredentialDescriptor] | None = None
        if user_id:
            allow = [
                PublicKeyCredentialDescriptor(id=base64url_to_bytes(c.credential_id))
                for c in self.store.get_for_user(user_id)
            ]
        options = generate_authentication_options(rp_id=self.rp_id, allow_credentials=allow)
        key = f"auth:{user_id}" if user_id else "auth:any"
        self._remember(key, options.challenge, AUTHENTICATION, user_id or "")
        return options_to_json(options)

    def finish_authentication(self, response: dict[str, Any], user_id: str | None = None) -> str:
        raw_id = response.get("id") or response.get("rawId") or ""
        credential_id = _to_base64url(raw_id)
        stored = self.store.get(credential_id)
        if stored is None:
            raise PasskeyError("unknown credential")

        key = f"auth:{user_id}" if user_id else "auth:any"
        pending = self._consume(key, AUTHENTICATION) or self._consume(
            f"auth:{user_id}" if not user_id else "auth:any", AUTHENTICATION
        )
        if pending is None:
            raise PasskeyError("no authentication in progress, or it expired")

        try:
            verification = verify_authentication_response(
                credential=_as_json(response),
                credential_public_key=base64url_to_bytes(stored.public_key),
                credential_current_sign_count=stored.sign_count,
                expected_challenge=base64url_to_bytes(pending.challenge),
                expected_origin=self.origin,
                expected_rp_id=self.rp_id,
                require_user_verification=True,
            )
        except InvalidAuthenticationResponse as exc:
            raise PasskeyError(str(exc)) from exc

        self.store.update_sign_count(credential_id, verification.new_sign_count)
        # Resolve the account from the server-side mapping, never from the
        # client-supplied userHandle.
        owner = self.store.owner_of(credential_id)
        if owner is None:
            raise PasskeyError("credential is not bound to an account")
        return owner

    # -- management ------------------------------------------------------
    def list_passkeys(self, user_id: str) -> list[dict[str, Any]]:
        return [
            {
                "credential_id": c.credential_id,
                "name": c.name,
                "sign_count": c.sign_count,
                "backed_up": c.backed_up,
                "transports": list(c.transports),
            }
            for c in self.store.get_for_user(user_id)
        ]

    def remove_passkey(self, user_id: str, credential_id: str) -> bool:
        return self.store.delete(user_id, credential_id)


def _as_json(response: dict[str, Any] | str) -> str:
    """The library takes the credential as a JSON *string*.

    Accepting a dict here too keeps call sites (and tests) from having to know
    which version of the library is installed.
    """
    if isinstance(response, str):
        return response
    return json.dumps(response)


def _to_base64url(value: str | bytes) -> str:
    if isinstance(value, bytes):
        return bytes_to_base64url(value)
    candidate = value.strip()
    # browsers send standard base64; normalise to base64url
    try:
        raw = base64.urlsafe_b64decode(candidate + "=" * (-len(candidate) % 4))
    except Exception:
        return candidate
    return bytes_to_base64url(raw)


def generate_challenge() -> str:
    return secrets.token_urlsafe(32)
