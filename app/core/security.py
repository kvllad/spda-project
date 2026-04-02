from __future__ import annotations

import base64
import hashlib
import hmac
import secrets
from datetime import UTC, datetime, timedelta
from typing import Any

import jwt

from app.core.config import Settings
from app.domain.exceptions import AuthenticationError

_ALGORITHM_NAME = "pbkdf2_sha256"
_ITERATIONS = 390000
_SALT_BYTES = 16


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(_SALT_BYTES)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, _ITERATIONS)
    return "$".join(
        [
            _ALGORITHM_NAME,
            str(_ITERATIONS),
            base64.urlsafe_b64encode(salt).decode("ascii"),
            base64.urlsafe_b64encode(digest).decode("ascii"),
        ],
    )


def verify_password(password: str, password_hash: str) -> bool:
    try:
        algorithm, iterations_raw, salt_raw, digest_raw = password_hash.split("$", maxsplit=3)
        if algorithm != _ALGORITHM_NAME:
            return False
        iterations = int(iterations_raw)
        salt = base64.urlsafe_b64decode(salt_raw.encode("ascii"))
        expected_digest = base64.urlsafe_b64decode(digest_raw.encode("ascii"))
    except (ValueError, TypeError):
        return False

    actual_digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations)
    return hmac.compare_digest(actual_digest, expected_digest)


def create_access_token(payload: dict[str, Any], settings: Settings) -> str:
    expires_at = datetime.now(UTC) + timedelta(minutes=settings.access_token_expire_minutes)
    token_payload = {**payload, "exp": expires_at}
    return jwt.encode(
        token_payload,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )


def decode_access_token(token: str, settings: Settings) -> dict[str, Any]:
    try:
        return jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
        )
    except jwt.PyJWTError as error:
        raise AuthenticationError("Invalid or expired access token.") from error
