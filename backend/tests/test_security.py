import pytest
from app.core.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    create_refresh_token,
    verify_token,
)


class TestPasswordHashing:
    """Test password hashing functions."""

    def test_hash_password(self):
        """Test password hashing."""
        password = "TestPassword123"
        hashed = get_password_hash(password)

        assert hashed != password
        assert len(hashed) > 0

    def test_verify_password_correct(self):
        """Test password verification with correct password."""
        password = "TestPassword123"
        hashed = get_password_hash(password)

        assert verify_password(password, hashed) is True

    def test_verify_password_incorrect(self):
        """Test password verification with incorrect password."""
        password = "TestPassword123"
        hashed = get_password_hash(password)

        assert verify_password("WrongPassword", hashed) is False

    def test_same_password_different_hashes(self):
        """Test that same password produces different hashes (salt)."""
        password = "TestPassword123"
        hash1 = get_password_hash(password)
        hash2 = get_password_hash(password)

        assert hash1 != hash2
        assert verify_password(password, hash1) is True
        assert verify_password(password, hash2) is True


class TestJWTTokens:
    """Test JWT token creation and verification."""

    def test_create_access_token(self):
        """Test access token creation."""
        data = {"sub": "user123"}
        token = create_access_token(data)

        assert isinstance(token, str)
        assert len(token) > 0

    def test_create_refresh_token(self):
        """Test refresh token creation."""
        data = {"sub": "user123"}
        token = create_refresh_token(data)

        assert isinstance(token, str)
        assert len(token) > 0

    def test_verify_access_token(self):
        """Test access token verification."""
        user_id = "user123"
        data = {"sub": user_id}
        token = create_access_token(data)

        payload = verify_token(token, token_type="access")
        assert payload["sub"] == user_id
        assert payload["type"] == "access"

    def test_verify_refresh_token(self):
        """Test refresh token verification."""
        user_id = "user123"
        data = {"sub": user_id}
        token = create_refresh_token(data)

        payload = verify_token(token, token_type="refresh")
        assert payload["sub"] == user_id
        assert payload["type"] == "refresh"

    def test_verify_wrong_token_type(self):
        """Test that verifying token with wrong type fails."""
        data = {"sub": "user123"}
        access_token = create_access_token(data)

        with pytest.raises(Exception):
            verify_token(access_token, token_type="refresh")

    def test_verify_invalid_token(self):
        """Test that invalid token verification fails."""
        with pytest.raises(Exception):
            verify_token("invalid_token", token_type="access")
