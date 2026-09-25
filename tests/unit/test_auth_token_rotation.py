from services.api_gateway.auth import create_refresh_token, decode_refresh_token


def test_refresh_token_preserves_supplied_jti() -> None:
    token = create_refresh_token({"jti": "known-jti"}, subject="user-1", role="farmer")
    payload = decode_refresh_token(token)
    assert payload is not None
    assert payload["jti"] == "known-jti"
    assert payload["sub"] == "user-1"
    assert payload["type"] == "refresh"
