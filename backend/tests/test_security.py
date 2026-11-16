import pytest

from app.auth.security import create_access_token, decode_token, hash_password, verify_password
from app.config import Settings


def test_password_roundtrip():
    hashed = hash_password("s3cret-pass")
    assert hashed != "s3cret-pass"
    assert verify_password("s3cret-pass", hashed)
    assert not verify_password("wrong", hashed)


def test_default_secret_key_is_at_least_32_bytes():
    """HS256 needs a 32-byte key. A short default lets anyone forge tokens."""
    default = Settings.model_fields["secret_key"].default
    assert len(default.encode()) >= 32


def test_token_roundtrip():
    token = create_access_token(42)
    assert decode_token(token) == 42


def test_invalid_token_returns_none():
    assert decode_token("not-a-jwt") is None
