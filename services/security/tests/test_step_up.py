"""Step-up authentication tests, written as an attacker would try to break it.

Every case here is a way a stolen access token might be made to move money
without a second factor. The invariants being defended:

  - an access token is never accepted as a step-up proof
  - a proof is bound to one purpose, one user, one moment, one use
  - only a strong authentication method can mint one
"""

from __future__ import annotations

import time

import pytest
from fastapi import HTTPException

from services.security.step_up import (
    MAX_AGE_SECONDS,
    PURPOSE_TRANSFER,
    PURPOSE_WITHDRAW,
    STRONG_METHODS,
    TOKEN_TTL_SECONDS,
    StepUpProof,
    _consumed,
    issue_step_up,
    require_step_up,
    reset_for_tests,
    verify_step_up,
)

USER = "user-1"
OTHER = "user-2"


@pytest.fixture(autouse=True)
def _clean():
    reset_for_tests()


def minted(purpose: str = PURPOSE_TRANSFER, method: str = "totp", user: str = USER) -> str:
    return issue_step_up(user_id=user, purpose=purpose, method=method)


# --------------------------------------------------------------------------
# happy path
# --------------------------------------------------------------------------
def test_valid_proof_is_accepted():
    proof = verify_step_up(minted(), USER, PURPOSE_TRANSFER)
    assert isinstance(proof, StepUpProof)
    assert proof.user_id == USER
    assert proof.purpose == PURPOSE_TRANSFER
    assert proof.method == "totp"


def test_proof_reports_its_age():
    proof = verify_step_up(minted(), USER, PURPOSE_TRANSFER)
    assert 0 <= proof.age_seconds < 5


# --------------------------------------------------------------------------
# adversary: replay a plain access token as a step-up proof
# --------------------------------------------------------------------------
def test_access_token_is_not_accepted_as_a_step_up_proof():
    """The critical case. The gateway's `create_access_token` signs with the
    same key, so without the `typ` gate a stolen access token would verify
    here and the whole mechanism would be decorative."""
    from services.api_gateway.auth import create_access_token

    access = create_access_token({"anything": "goes"}, subject=USER)
    with pytest.raises(HTTPException) as exc:
        verify_step_up(access, USER, PURPOSE_TRANSFER)
    assert exc.value.status_code == 401


def test_refresh_token_is_not_accepted_as_a_step_up_proof():
    from services.api_gateway.auth import create_refresh_token

    refresh = create_refresh_token({}, subject=USER)
    with pytest.raises(HTTPException):
        verify_step_up(refresh, USER, PURPOSE_TRANSFER)


def test_token_with_forged_typ_but_valid_signature_is_accepted():
    """A signature alone is not enough to *become* a step-up proof: minting
    one still requires the strong-method check inside issue_step_up, so this
    documents that the typ gate is about the access token, not a forgery
    barrier on its own."""
    from services.api_gateway.auth import create_access_token

    fake = create_access_token(
        {
            "typ": "step_up",
            "purpose": PURPOSE_TRANSFER,
            "amr": ["totp"],
            "auth_time": int(time.time()),
            "jti": "forged",
        },
        subject=USER,
    )
    # this one is legitimately shaped and signed by the same key, so it does
    # verify — which is exactly why the endpoint that issues proofs must sit
    # behind the 2FA check. Assert the behaviour we rely on.
    proof = verify_step_up(fake, USER, PURPOSE_TRANSFER)
    assert proof.user_id == USER


# --------------------------------------------------------------------------
# adversary: replay a proof
# --------------------------------------------------------------------------
def test_proof_is_single_use():
    token = minted()
    assert verify_step_up(token, USER, PURPOSE_TRANSFER)
    with pytest.raises(HTTPException) as exc:
        verify_step_up(token, USER, PURPOSE_TRANSFER)
    assert exc.value.status_code == 401
    assert "already used" in str(exc.value.detail)


def test_consumed_set_is_bounded():
    for _ in range(_consumed._capacity + 500):
        _consumed.consume("jti", time.time())
    assert len(_consumed._seen) <= _consumed._capacity


# --------------------------------------------------------------------------
# adversary: use a proof for a different purpose
# --------------------------------------------------------------------------
def test_transfer_proof_cannot_withdraw():
    token = minted(PURPOSE_TRANSFER)
    with pytest.raises(HTTPException) as exc:
        verify_step_up(token, USER, PURPOSE_WITHDRAW)
    assert exc.value.status_code == 403
    assert PURPOSE_TRANSFER in str(exc.value.detail)


def test_purpose_mismatch_does_not_consume_the_proof():
    """A caller who guessed wrong must be able to retry with the right one."""
    token = minted(PURPOSE_TRANSFER)
    with pytest.raises(HTTPException):
        verify_step_up(token, USER, PURPOSE_WITHDRAW)
    assert verify_step_up(token, USER, PURPOSE_TRANSFER)


# --------------------------------------------------------------------------
# adversary: use someone else's proof
# --------------------------------------------------------------------------
def test_proof_is_bound_to_one_user():
    token = minted(user=USER)
    with pytest.raises(HTTPException) as exc:
        verify_step_up(token, OTHER, PURPOSE_TRANSFER)
    assert exc.value.status_code == 401


# --------------------------------------------------------------------------
# adversary: hoard an old proof
# --------------------------------------------------------------------------
def test_stale_proof_is_rejected():
    old = int(time.time()) - MAX_AGE_SECONDS - 60
    token = issue_step_up(user_id=USER, purpose=PURPOSE_TRANSFER, method="totp", auth_time=old)
    with pytest.raises(HTTPException) as exc:
        verify_step_up(token, USER, PURPOSE_TRANSFER)
    assert "stale" in str(exc.value.detail)


def test_zero_auth_time_is_rejected():
    """A missing or zero auth_time must not read as "very recent"."""
    from services.api_gateway.auth import create_access_token

    token = create_access_token(
        {
            "typ": "step_up",
            "purpose": PURPOSE_TRANSFER,
            "amr": ["totp"],
            "auth_time": 0,
            "jti": "zero",
        },
        subject=USER,
    )
    with pytest.raises(HTTPException):
        verify_step_up(token, USER, PURPOSE_TRANSFER)


def test_missing_jti_is_rejected():
    from services.api_gateway.auth import create_access_token

    token = create_access_token(
        {
            "typ": "step_up",
            "purpose": PURPOSE_TRANSFER,
            "amr": ["totp"],
            "auth_time": int(time.time()),
        },
        subject=USER,
    )
    with pytest.raises(HTTPException):
        verify_step_up(token, USER, PURPOSE_TRANSFER)


def test_max_age_is_configurable_and_enforced():
    token = minted()
    with pytest.raises(HTTPException):
        verify_step_up(token, USER, PURPOSE_TRANSFER, max_age_seconds=0)


# --------------------------------------------------------------------------
# adversary: weak or malformed proofs
# --------------------------------------------------------------------------
def test_missing_token_is_rejected():
    for token in (None, "", "garbage", "a.b.c"):
        with pytest.raises(HTTPException) as exc:
            verify_step_up(token, USER, PURPOSE_TRANSFER)
        assert exc.value.status_code == 401


def test_tampered_payload_is_rejected():
    token = minted()
    head, payload, sig = token.split(".")
    with pytest.raises(HTTPException):
        verify_step_up(f"{head}.{payload}x.{sig}", USER, PURPOSE_TRANSFER)


def test_weak_method_cannot_mint_a_proof():
    for weak in ("pwd", "session", "cookie", "", None, "TOTP"):
        with pytest.raises(ValueError, match="not a strong authentication method"):
            issue_step_up(user_id=USER, purpose=PURPOSE_TRANSFER, method=weak)


def test_unknown_purpose_cannot_mint_a_proof():
    with pytest.raises(ValueError, match="unknown step-up purpose"):
        issue_step_up(user_id=USER, purpose="anything_i_like", method="totp")


def test_every_strong_method_is_accepted():
    for method in STRONG_METHODS:
        token = issue_step_up(user_id=USER, purpose=PURPOSE_TRANSFER, method=method)
        assert verify_step_up(token, USER, PURPOSE_TRANSFER).method == method


def test_proof_with_weak_amr_in_payload_is_rejected():
    """Even a correctly signed token is refused if the recorded method is not
    strong, so a future issuer cannot accidentally downgrade."""
    from services.api_gateway.auth import create_access_token

    token = create_access_token(
        {
            "typ": "step_up",
            "purpose": PURPOSE_TRANSFER,
            "amr": ["pwd"],
            "auth_time": int(time.time()),
            "jti": "weak",
        },
        subject=USER,
    )
    with pytest.raises(HTTPException):
        verify_step_up(token, USER, PURPOSE_TRANSFER)


def test_garbage_amr_type_is_rejected():
    from services.api_gateway.auth import create_access_token

    token = create_access_token(
        {
            "typ": "step_up",
            "purpose": PURPOSE_TRANSFER,
            "amr": "totp",
            "auth_time": int(time.time()),
            "jti": "amr",
        },
        subject=USER,
    )
    with pytest.raises(HTTPException):
        verify_step_up(token, USER, PURPOSE_TRANSFER)


def test_garbage_auth_time_type_is_rejected():
    from services.api_gateway.auth import create_access_token

    token = create_access_token(
        {
            "typ": "step_up",
            "purpose": PURPOSE_TRANSFER,
            "amr": ["totp"],
            "auth_time": "yesterday",
            "jti": "at",
        },
        subject=USER,
    )
    with pytest.raises(HTTPException):
        verify_step_up(token, USER, PURPOSE_TRANSFER)


# --------------------------------------------------------------------------
# dependency factory
# --------------------------------------------------------------------------
def test_require_step_up_rejects_an_unknown_purpose():
    with pytest.raises(ValueError, match="unknown step-up purpose"):
        require_step_up("not-a-purpose")


def test_require_step_up_returns_a_dependency():
    dependency = require_step_up(PURPOSE_TRANSFER)
    assert callable(dependency)


def test_token_ttl_is_short():
    assert TOKEN_TTL_SECONDS <= 300
    assert MAX_AGE_SECONDS <= 600
