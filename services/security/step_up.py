"""Step-up authentication — recent, strong proof required for sensitive acts.

A valid access token proves *who* the caller is. It does not prove they are
still present and still in possession of a second factor, which is exactly
what a transfer or a withdrawal needs. Step-up closes that gap: the caller
first performs a strong re-authentication, receives a short-lived proof bound
to one purpose, and presents it on the sensitive request.

Deliberate design points, each of which a forged or replayed token depends on:

``typ == "step_up"``
    Checked before anything else. Without it an ordinary access token would
    verify against the same signing key and could be presented as a step-up
    proof, which would defeat the entire mechanism.

``purpose``
    Bound to the act. A proof minted to change a password cannot move funds,
    so a stolen proof is useless against a different endpoint.

``auth_time`` with a short ceiling
    Age is measured from the moment of the *strong* authentication, not from
    issue time, so a proof cannot be hoarded. ``MAX_AGE_SECONDS`` is small by
    design.

``amr``
    Records how the user proved themselves. Only strong methods qualify; a
    plain session refresh does not.

``jti`` with single use
    A proof is consumed on first successful presentation, so intercepting one
    does not yield a replay window.

Storage for the single-use set is in-process. Behind multiple workers a jti is
only honoured by the worker that saw it, so the same proof could be replayed
against a different worker within its validity window. Move the set to Redis
before treating single use as a hard guarantee; the age, purpose, user and
method bindings hold regardless.
"""

from __future__ import annotations

import secrets
import threading
import time
import uuid
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from fastapi import Depends, Header, HTTPException, status

# How long a strong authentication keeps satisfying step-up requirements.
MAX_AGE_SECONDS = 300
TOKEN_TTL_SECONDS = 120  # the proof itself is short-lived
STEP_UP_TYP = "step_up"

# Methods that count as strong. "pwd" alone does not: the whole point is to
# require something the stolen access token does not already carry.
STRONG_METHODS = frozenset({"otp", "totp", "webauthn", "passkey", "recovery_code"})

# Purposes we issue proofs for. Endpoints reference these by name.
PURPOSE_TRANSFER = "transfer"
PURPOSE_WITHDRAW = "wallet.withdraw"
PURPOSE_PASSWORD_CHANGE = "password.change"
PURPOSE_KEYS = "security.keys"
PURPOSE_ACCOUNT_DELETE = "account.delete"
PURPOSES = frozenset(
    {
        PURPOSE_TRANSFER,
        PURPOSE_WITHDRAW,
        PURPOSE_PASSWORD_CHANGE,
        PURPOSE_KEYS,
        PURPOSE_ACCOUNT_DELETE,
    }
)

STEP_UP_HEADER = "X-Step-Up-Token"
_MAX_CONSUMED = 50_000


@dataclass(frozen=True)
class StepUpProof:
    user_id: str
    purpose: str
    method: str
    auth_time: int
    jti: str

    @property
    def age_seconds(self) -> float:
        return max(0.0, time.time() - self.auth_time)


class _Consumed:
    """Bounded single-use set for jti values."""

    def __init__(self, capacity: int = _MAX_CONSUMED) -> None:
        self._seen: dict[str, float] = {}
        self._capacity = capacity
        self._lock = threading.Lock()

    def consume(self, jti: str, now: float) -> bool:
        """True if this jti had not been used before."""
        with self._lock:
            cutoff = now - TOKEN_TTL_SECONDS
            if len(self._seen) > self._capacity:
                self._seen = {k: v for k, v in self._seen.items() if v > cutoff}
            if jti in self._seen:
                return False
            self._seen[jti] = now
            return True


_consumed = _Consumed()


def _token_module() -> tuple[Callable[..., str], Callable[..., dict[str, Any] | None]]:
    # Imported lazily: this module is used by the security package, and
    # services.api_gateway.auth pulls in settings plus a database session.
    from services.api_gateway.auth import create_access_token, decode_token

    return create_access_token, decode_token


def issue_step_up(
    user_id: str,
    purpose: str,
    method: str,
    auth_time: int | None = None,
    ttl_seconds: int = TOKEN_TTL_SECONDS,
) -> str:
    """Mint a step-up proof after the caller proved themselves.

    ``auth_time`` is the unix second of the strong authentication. It is
    accepted as an argument so the caller records when the user actually
    re-authenticated rather than when this function happened to run.
    """
    if purpose not in PURPOSES:
        raise ValueError(f"unknown step-up purpose {purpose!r}")
    if method not in STRONG_METHODS:
        raise ValueError(
            f"{method!r} is not a strong authentication method; "
            f"expected one of {sorted(STRONG_METHODS)}"
        )
    create_access_token, _ = _token_module()
    now = int(time.time())
    return create_access_token(
        {
            "typ": STEP_UP_TYP,
            "purpose": purpose,
            "amr": [method],
            "auth_time": auth_time if auth_time is not None else now,
            "jti": uuid.uuid4().hex,
            "nonce": secrets.token_urlsafe(8),
        },
        subject=str(user_id),
    )


def verify_step_up(
    token: str | None,
    user_id: str,
    purpose: str,
    max_age_seconds: int = MAX_AGE_SECONDS,
    consume: bool = True,
) -> StepUpProof:
    """Validate a proof or raise ``HTTPException`` with a precise reason.

    Returns the proof on success. Every rejection is a 401 except a purpose
    mismatch, which is a 403: the token is genuine, it is just for something
    else.
    """
    _, decode_token = _token_module()
    unauthenticated = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Step-up authentication required",
        headers={"WWW-Authenticate": "StepUp"},
    )
    if not token:
        raise unauthenticated

    payload = decode_token(token)
    if payload is None:
        raise unauthenticated

    # 1. type gate: an access token must never pass as a step-up proof
    if payload.get("typ") != STEP_UP_TYP:
        raise unauthenticated

    if str(payload.get("sub") or "") != str(user_id):
        raise unauthenticated

    if payload.get("purpose") != purpose:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                f"Step-up proof is for {payload.get('purpose')!r}, "
                f"not {purpose!r}. Re-authenticate for this action."
            ),
        )

    amr = payload.get("amr") or []
    method = amr[0] if isinstance(amr, list) and amr else None
    if method not in STRONG_METHODS:
        raise unauthenticated

    try:
        auth_time = int(payload.get("auth_time") or 0)
    except (TypeError, ValueError):
        raise unauthenticated from None
    if auth_time <= 0 or (time.time() - auth_time) > max_age_seconds:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Step-up proof is stale; re-authenticate",
            headers={"WWW-Authenticate": "StepUp"},
        )

    jti = str(payload.get("jti") or "")
    if not jti:
        raise unauthenticated
    if consume and not _consumed.consume(jti, time.time()):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Step-up proof already used",
            headers={"WWW-Authenticate": "StepUp"},
        )

    return StepUpProof(
        user_id=str(user_id),
        purpose=purpose,
        method=str(method),
        auth_time=auth_time,
        jti=jti,
    )


def require_step_up(
    purpose: str, max_age_seconds: int = MAX_AGE_SECONDS
) -> Callable[..., StepUpProof]:
    """FastAPI dependency factory.

    ``Depends(require_step_up(PURPOSE_TRANSFER))`` guards an endpoint so that a
    plain access token is no longer sufficient.
    """
    if purpose not in PURPOSES:
        raise ValueError(f"unknown step-up purpose {purpose!r}")

    def _dependency(
        user: Any = Depends(_current_user_dependency()),
        step_up_token: str | None = Header(default=None, alias=STEP_UP_HEADER),
    ) -> StepUpProof:
        return verify_step_up(
            step_up_token,
            user_id=str(getattr(user, "id", user)),
            purpose=purpose,
            max_age_seconds=max_age_seconds,
        )

    return _dependency


def _current_user_dependency() -> Any:
    from services.api_gateway.auth import get_current_user

    return get_current_user


def reset_for_tests() -> None:
    """Clear the single-use set so tests are order-independent."""
    _consumed._seen.clear()
