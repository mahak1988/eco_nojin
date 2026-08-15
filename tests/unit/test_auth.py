"""Phase 0 tests: JWT auth utilities (hash, tokens, roles)."""

from datetime import timedelta

from services.api_gateway.auth import (
    ROLE_ADMIN,
    ROLE_FARMER,
    create_access_token,
    decode_token,
    hash_password,
    verify_password,
)


class TestPasswordHashing:
    def test_hash_and_verify(self):
        hashed = hash_password("s3cret-pass")
        assert hashed != "s3cret-pass"
        assert verify_password("s3cret-pass", hashed) is True
        assert verify_password("wrong", hashed) is False

    def test_salting(self):
        assert hash_password("same") != hash_password("same")


class TestTokens:
    def test_roundtrip(self):
        token = create_access_token(data={"scope": "soil"}, subject="42", role=ROLE_FARMER)
        payload = decode_token(token)
        assert payload is not None
        assert payload["sub"] == "42"
        assert payload["role"] == ROLE_FARMER
        assert payload["scope"] == "soil"

    def test_role_admin(self):
        token = create_access_token(data={}, subject="1", role=ROLE_ADMIN)
        assert decode_token(token)["role"] == ROLE_ADMIN

    def test_expired_token_rejected(self):
        token = create_access_token(
            data={}, subject="1", role=ROLE_FARMER,
            expires_delta=timedelta(seconds=-10),
        )
        assert decode_token(token) is None

    def test_garbage_rejected(self):
        assert decode_token("not.a.jwt") is None
        assert decode_token("") is None
