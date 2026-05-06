"""
Unit tests for JWT handler utilities.
Run: venv/Scripts/python.exe -m pytest tests/unit/test_jwt_handler.py -v
"""
import sys
import os
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "backend"))

from app.utils.jwt_handler import (
    create_access_token,
    decode_access_token,
    get_password_hash,
    verify_password,
)


class TestJWTHandler:
    def test_create_and_decode_token(self):
        data = {"sub": "user-123", "role": "patient", "email": "test@test.com"}
        token = create_access_token(data)
        assert isinstance(token, str)
        assert len(token) > 20

        decoded = decode_access_token(token)
        assert decoded is not None
        assert decoded["sub"] == "user-123"
        assert decoded["role"] == "patient"
        assert decoded["email"] == "test@test.com"

    def test_invalid_token_returns_none(self):
        result = decode_access_token("not.a.valid.token")
        assert result is None

    def test_tampered_token_returns_none(self):
        token = create_access_token({"sub": "user-123"})
        tampered = token[:-5] + "XXXXX"
        result = decode_access_token(tampered)
        assert result is None

    def test_empty_token_returns_none(self):
        assert decode_access_token("") is None

    def test_token_contains_expiry(self):
        token = create_access_token({"sub": "user-123"})
        decoded = decode_access_token(token)
        assert "exp" in decoded
        assert decoded["exp"] > time.time()


class TestPasswordHashing:
    def test_hash_is_not_plaintext(self):
        hashed = get_password_hash("mypassword123")
        assert hashed != "mypassword123"
        assert len(hashed) > 20

    def test_verify_correct_password(self):
        hashed = get_password_hash("securepass99")
        assert verify_password("securepass99", hashed) is True

    def test_verify_wrong_password(self):
        hashed = get_password_hash("securepass99")
        assert verify_password("wrongpassword", hashed) is False

    def test_same_password_different_hashes(self):
        """bcrypt generates different salts each time."""
        h1 = get_password_hash("samepassword")
        h2 = get_password_hash("samepassword")
        assert h1 != h2
        # But both should verify correctly
        assert verify_password("samepassword", h1) is True
        assert verify_password("samepassword", h2) is True
