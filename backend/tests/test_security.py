import pytest

from app.auth.security import create_access_token, decode_token, hash_password, verify_password


def test_password_roundtrip():
    hashed = hash_password("s3cret-pass")
    assert hashed != "s3cret-pass"
    assert verify_password("s3cret-pass", hashed)
    assert not verify_password("wrong", hashed)


def test_token_roundtrip():
    token = create_access_token(42)
    assert decode_token(token) == 42


def test_invalid_token_returns_none():
    assert decode_token("not-a-jwt") is None
