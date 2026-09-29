"""Passkey and step-up authentication endpoints.

Routes are grouped under ``/api/v1/security/…`` and are the only place the
passkey ceremony and the step-up proof are exposed. Handlers stay thin: all
ceremony logic lives in ``services.security.passkeys`` and
``services.security.step_up`` so it can be tested without HTTP.
"""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field

from services.security.passkeys import PasskeyError, PasskeyService
from services.security.step_up import (
    PURPOSES,
    STRONG_METHODS,
    TOKEN_TTL_SECONDS,
    issue_step_up,
    verify_step_up,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/security", tags=["passkeys", "step-up"])

# rp_id and origin must be the real deployment values; set them per environment
# rather than accepting them from the request, or an attacker could mint a
# ceremony for a domain they control.
RP_ID = "localhost"
ORIGIN = "http://localhost:3000"

_passkeys = PasskeyService(rp_id=RP_ID, origin=ORIGIN)


class RegistrationOptionsResponse(BaseModel):
    options: str = Field(description="JSON for navigator.credentials.create()")


class FinishRegistrationRequest(BaseModel):
    credential: dict[str, Any]
    name: str | None = None


class PasskeyResponse(BaseModel):
    credential_id: str
    name: str | None = None
    sign_count: int = 0
    aaguid: str | None = None


class AuthenticationOptionsResponse(BaseModel):
    options: str = Field(description="JSON for navigator.credentials.get()")


class FinishAuthenticationRequest(BaseModel):
    credential: dict[str, Any]


class AuthenticationResult(BaseModel):
    user_id: str


class StepUpRequest(BaseModel):
    purpose: str
    method: str
    # Proof material. Required for "totp" (the code) and for
    # "passkey"/"webauthn" (a WebAuthn assertion). Ignored otherwise.
    code: str | None = None
    credential: dict[str, Any] | None = None
    # auth_time is deliberately absent. It used to be client-supplied, and
    # issue_step_up() stamps `now` when it is None, so a caller could assert
    # their own freshness. The server records the time it verified the factor.


# Strong methods this endpoint can actually verify end to end. STRONG_METHODS
# also lists "otp" and "recovery_code"; those are refused here rather than
# accepted unverified, because no code store or delivery channel is wired up.
VERIFIABLE_METHODS = {"totp", "webauthn", "passkey"}


class StepUpResponse(BaseModel):
    token: str
    expires_in: int
    purpose: str


def _current_user_id(request: Request) -> str:
    """Resolve the caller from the bearer token or the access cookie.

    The user id comes from the *verified* token, never from the request body,
    so a caller cannot register or authenticate a passkey against an account
    they do not hold. An unbound id is refused rather than defaulted.
    """
    from services.api_gateway.auth import ACCESS_TOKEN_COOKIE, decode_token

    header = request.headers.get("authorization") or ""
    token = header[7:] if header.lower().startswith("bearer ") else None
    if not token:
        token = request.cookies.get(ACCESS_TOKEN_COOKIE)
    payload = decode_token(token) if token else None
    sub = (payload or {}).get("sub")
    if not sub:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required"
        )
    return str(sub)


# ---------------------------------------------------------------- passkeys


@router.post("/passkeys/register/options", response_model=RegistrationOptionsResponse)
async def passkey_registration_options(
    user_id: str = Depends(_current_user_id),
) -> RegistrationOptionsResponse:
    options = _passkeys.begin_registration(user_id, user_id, user_id)
    return RegistrationOptionsResponse(options=options)


@router.post("/passkeys/register", response_model=PasskeyResponse)
async def finish_passkey_registration(
    payload: FinishRegistrationRequest,
    user_id: str = Depends(_current_user_id),
) -> PasskeyResponse:
    try:
        result = _passkeys.finish_registration(user_id, payload.credential, payload.name)
    except PasskeyError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return PasskeyResponse(**result)


@router.post("/passkeys/authenticate/options", response_model=AuthenticationOptionsResponse)
async def passkey_authentication_options(
    user_id: str = Depends(_current_user_id),
) -> AuthenticationOptionsResponse:
    return AuthenticationOptionsResponse(options=_passkeys.begin_authentication(user_id))


@router.post("/passkeys/authenticate", response_model=AuthenticationResult)
async def finish_passkey_authentication(
    payload: FinishAuthenticationRequest,
) -> AuthenticationResult:
    try:
        user_id = _passkeys.finish_authentication(payload.credential)
    except PasskeyError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc
    return AuthenticationResult(user_id=user_id)


@router.get("/passkeys")
async def list_passkeys(user_id: str = Depends(_current_user_id)) -> dict[str, Any]:
    return {"passkeys": _passkeys.list_passkeys(user_id)}


@router.delete("/passkeys/{credential_id}")
async def delete_passkey(credential_id: str, user_id: str = Depends(_current_user_id)) -> dict:
    if not _passkeys.remove_passkey(user_id, credential_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Passkey not found")
    return {"removed": True}


# ------------------------------------------------------------------ step-up


@router.get("/step-up/purposes")
async def list_purposes() -> dict[str, Any]:
    return {"purposes": sorted(PURPOSES), "methods": sorted(STRONG_METHODS)}


@router.get("/step-up/methods")
async def list_step_up_methods() -> dict[str, Any]:
    """Which step-up methods this deployment can actually verify.

    STRONG_METHODS is the full set the proof format accepts; the subset that
    is verifiable depends on whether the user has provisioned TOTP or a
    passkey, so callers should not assume every method is available.
    """
    return {
        "accepted": sorted(STRONG_METHODS),
        "verifiable": sorted(VERIFIABLE_METHODS),
    }


@router.post("/step-up", response_model=StepUpResponse)
async def create_step_up(
    payload: StepUpRequest,
    user_id: str = Depends(_current_user_id),
) -> StepUpResponse:
    """Mint a step-up proof after verifying a strong factor.

    A step-up proof is what authorises account deletion, key rotation and
    payment limits, so the factor has to be checked here rather than assumed.
    The previous version accepted any string in STRONG_METHODS plus a
    client-supplied ``auth_time``: ``{"purpose": "account.delete",
    "method": "totp"}`` was enough to mint a fully valid proof, with no TOTP
    code ever computed.

    ``auth_time`` is now stamped by the server from the moment of
    verification, which is what the 300-second freshness ceiling in
    ``verify_step_up`` is meant to bound.
    """
    if payload.purpose not in PURPOSES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Unknown step-up purpose"
        )
    if payload.method not in STRONG_METHODS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Method must be one of {sorted(STRONG_METHODS)}",
        )
    if payload.method not in VERIFIABLE_METHODS:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail=(
                f"{payload.method} is not provisioned. "
                "No code store or delivery channel is wired up, so it cannot be verified."
            ),
        )

    if payload.method == "totp":
        _verify_totp_factor(user_id, payload.code)
    else:
        _verify_webauthn_factor(user_id, payload.credential)

    token = issue_step_up(
        user_id=user_id,
        purpose=payload.purpose,
        method=payload.method,
        auth_time=None,  # stamped server-side on issue
    )
    return StepUpResponse(token=token, expires_in=TOKEN_TTL_SECONDS, purpose=payload.purpose)


def _verify_totp_factor(user_id: str, code: str | None) -> None:
    if not code:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A TOTP code is required for method 'totp'",
        )
    from database.hub import hub
    from database.models import User
    from services.two_factor import verify_totp

    with hub.get_session() as session:
        row = session.get(User, user_id)
        secret = getattr(row, "two_factor_secret", None) if row else None
        enabled = bool(getattr(row, "two_factor_enabled", False)) if row else False

    if not enabled or not secret:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="TOTP is not provisioned for this account",
        )
    if not verify_totp(secret, code):
        # Deliberately identical to the "not provisioned" shape: a distinct
        # message would confirm whether an account has TOTP enabled.
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Step-up verification failed",
        )


def _verify_webauthn_factor(user_id: str, credential: dict[str, Any] | None) -> None:
    if not credential:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A WebAuthn assertion is required for method 'webauthn'/'passkey'",
        )
    try:
        resolved = _passkeys.finish_authentication(credential)
    except PasskeyError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Step-up verification failed"
        ) from exc
    if str(resolved) != str(user_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Step-up verification failed",
        )


@router.get("/step-up/verify")
async def check_step_up(token: str, purpose: str, user_id: str = Depends(_current_user_id)) -> dict:
    proof = verify_step_up(token, user_id, purpose, consume=False)
    return {
        "valid": True,
        "purpose": proof.purpose,
        "method": proof.method,
        "age_seconds": round(proof.age_seconds, 1),
    }
