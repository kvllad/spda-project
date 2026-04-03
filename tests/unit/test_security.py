from __future__ import annotations

import pytest

from app.core.config import Settings
from app.core.security import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)
from app.domain.exceptions import AuthenticationError


def _settings() -> Settings:
    return Settings(
        database_url="sqlite+aiosqlite:///unit.db",
        jwt_secret_key="0123456789abcdef0123456789abcdef",
        log_file_path="logs/unit-security.log",
    )


def test_hash_password_roundtrip() -> None:
    password_hash = hash_password("SecretPass123")

    assert password_hash != "SecretPass123"
    assert verify_password("SecretPass123", password_hash)
    assert not verify_password("WrongPass123", password_hash)


def test_verify_password_returns_false_for_invalid_hash_format() -> None:
    assert not verify_password("SecretPass123", "not-a-valid-password-hash")


def test_create_and_decode_access_token_roundtrip() -> None:
    token = create_access_token(
        {"sub": "user-1", "role": "doctor", "profile_id": "doctor-1"},
        _settings(),
    )

    payload = decode_access_token(token, _settings())

    assert payload["sub"] == "user-1"
    assert payload["role"] == "doctor"
    assert payload["profile_id"] == "doctor-1"
    assert "exp" in payload


def test_decode_access_token_raises_for_invalid_token() -> None:
    with pytest.raises(AuthenticationError, match="Invalid or expired access token"):
        decode_access_token("invalid-token", _settings())
