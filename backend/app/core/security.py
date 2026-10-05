"""Password hashing and signed access-token helpers."""

from __future__ import annotations

import base64
import hashlib
import hmac
import secrets
from datetime import UTC, datetime, timedelta

from jose import JWTError, jwt

from app.config import settings

_SCRYPT_N = 2**14
_SCRYPT_R = 8
_SCRYPT_P = 1
_SCRYPT_DKLEN = 32


def _encode_bytes(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).decode("ascii").rstrip("=")


def _decode_bytes(value: str) -> bytes:
    return base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.scrypt(
        password.encode("utf-8"),
        salt=salt,
        n=_SCRYPT_N,
        r=_SCRYPT_R,
        p=_SCRYPT_P,
        dklen=_SCRYPT_DKLEN,
    )
    return (
        f"scrypt${_SCRYPT_N}${_SCRYPT_R}${_SCRYPT_P}"
        f"${_encode_bytes(salt)}${_encode_bytes(digest)}"
    )


def verify_password(password: str, encoded_hash: str) -> bool:
    try:
        algorithm, n, r, p, salt_b64, digest_b64 = encoded_hash.split("$")
        if (
            algorithm != "scrypt"
            or int(n) != _SCRYPT_N
            or int(r) != _SCRYPT_R
            or int(p) != _SCRYPT_P
        ):
            return False
        salt = _decode_bytes(salt_b64)
        expected_digest = _decode_bytes(digest_b64)
        if len(salt) != 16 or len(expected_digest) != _SCRYPT_DKLEN:
            return False
        actual_digest = hashlib.scrypt(
            password.encode("utf-8"),
            salt=salt,
            n=_SCRYPT_N,
            r=_SCRYPT_R,
            p=_SCRYPT_P,
            dklen=len(expected_digest),
        )
        return hmac.compare_digest(actual_digest, expected_digest)
    except (ValueError, TypeError, OverflowError):
        return False


def create_access_token(subject: str) -> str:
    now = datetime.now(UTC)
    expires_at = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    return jwt.encode(
        {"sub": subject, "iat": now, "exp": expires_at, "type": "access"},
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )


def decode_access_token(token: str) -> str | None:
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
        )
    except JWTError:
        return None
    subject = payload.get("sub")
    if payload.get("type") != "access" or not isinstance(subject, str) or not subject:
        return None
    return subject
