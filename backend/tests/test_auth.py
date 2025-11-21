import pytest
from fastapi import status


class TestRegistration:
    """Test user registration."""

    def test_register_success(self, client, test_user_data):
        """Test successful user registration."""
        response = client.post("/api/v1/auth/register", json=test_user_data)

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert "user" in data
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
        assert data["user"]["email"] == test_user_data["email"]
        assert data["user"]["first_name"] == test_user_data["first_name"]
        assert "hashed_password" not in data["user"]

    def test_register_duplicate_email(self, client, test_user_data):
        """Test registration with duplicate email fails."""
        # First registration
        response = client.post("/api/v1/auth/register", json=test_user_data)
        assert response.status_code == status.HTTP_201_CREATED

        # Duplicate registration
        response = client.post("/api/v1/auth/register", json=test_user_data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "email already registered" in response.json()["error"]["message"].lower()

    def test_register_invalid_email(self, client, test_user_data):
        """Test registration with invalid email format."""
        test_user_data["email"] = "invalid-email"
        response = client.post("/api/v1/auth/register", json=test_user_data)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_register_weak_password(self, client, test_user_data):
        """Test registration with weak password fails."""
        test_user_data["password"] = "weak"
        response = client.post("/api/v1/auth/register", json=test_user_data)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_register_missing_fields(self, client):
        """Test registration with missing required fields."""
        response = client.post(
            "/api/v1/auth/register", json={"email": "test@example.com"}
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


class TestLogin:
    """Test user login."""

    def test_login_success(self, client, test_user_data, test_user):
        """Test successful login."""
        response = client.post(
            "/api/v1/auth/login",
            json={"email": test_user_data["email"], "password": test_user_data["password"]},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "user" in data
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["user"]["email"] == test_user_data["email"]

    def test_login_wrong_password(self, client, test_user_data, test_user):
        """Test login with wrong password fails."""
        response = client.post(
            "/api/v1/auth/login",
            json={"email": test_user_data["email"], "password": "WrongPassword123"},
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "incorrect" in response.json()["error"]["message"].lower()

    def test_login_nonexistent_user(self, client):
        """Test login with non-existent user."""
        response = client.post(
            "/api/v1/auth/login",
            json={"email": "nonexistent@example.com", "password": "Password123"},
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_login_invalid_format(self, client):
        """Test login with invalid data format."""
        response = client.post("/api/v1/auth/login", json={"email": "invalid"})
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


class TestTokenRefresh:
    """Test token refresh."""

    def test_refresh_token_success(self, client, test_user):
        """Test successful token refresh."""
        refresh_token = test_user["refresh_token"]
        response = client.post(
            "/api/v1/auth/refresh", json={"refresh_token": refresh_token}
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"

    def test_refresh_invalid_token(self, client):
        """Test refresh with invalid token fails."""
        response = client.post(
            "/api/v1/auth/refresh", json={"refresh_token": "invalid_token"}
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_refresh_with_access_token(self, client, test_user):
        """Test refresh with access token instead of refresh token fails."""
        access_token = test_user["access_token"]
        response = client.post(
            "/api/v1/auth/refresh", json={"refresh_token": access_token}
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestLogout:
    """Test user logout."""

    def test_logout_success(self, client, auth_headers):
        """Test successful logout."""
        response = client.post("/api/v1/auth/logout", headers=auth_headers)
        assert response.status_code == status.HTTP_204_NO_CONTENT

    def test_logout_without_auth(self, client):
        """Test logout without authentication fails."""
        response = client.post("/api/v1/auth/logout")
        assert response.status_code == status.HTTP_403_FORBIDDEN


class TestPasswordReset:
    """Test password reset functionality."""

    def test_request_password_reset(self, client, test_user_data, test_user):
        """Test password reset request."""
        response = client.post(
            "/api/v1/auth/password-reset/request",
            json={"email": test_user_data["email"]},
        )

        assert response.status_code == status.HTTP_200_OK
        assert "message" in response.json()

    def test_request_password_reset_nonexistent_email(self, client):
        """Test password reset for non-existent email doesn't reveal existence."""
        response = client.post(
            "/api/v1/auth/password-reset/request",
            json={"email": "nonexistent@example.com"},
        )

        # Should still return 200 to not reveal if email exists
        assert response.status_code == status.HTTP_200_OK


class TestPasswordChange:
    """Test password change functionality."""

    def test_change_password_success(self, client, auth_headers, test_user_data):
        """Test successful password change."""
        response = client.post(
            "/api/v1/auth/password/change",
            headers=auth_headers,
            json={
                "current_password": test_user_data["password"],
                "new_password": "NewPassword123",
            },
        )

        assert response.status_code == status.HTTP_200_OK

        # Verify can login with new password
        login_response = client.post(
            "/api/v1/auth/login",
            json={"email": test_user_data["email"], "password": "NewPassword123"},
        )
        assert login_response.status_code == status.HTTP_200_OK

    def test_change_password_wrong_current(self, client, auth_headers):
        """Test password change with wrong current password fails."""
        response = client.post(
            "/api/v1/auth/password/change",
            headers=auth_headers,
            json={
                "current_password": "WrongPassword123",
                "new_password": "NewPassword123",
            },
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_change_password_weak_new_password(self, client, auth_headers, test_user_data):
        """Test password change with weak new password fails."""
        response = client.post(
            "/api/v1/auth/password/change",
            headers=auth_headers,
            json={"current_password": test_user_data["password"], "new_password": "weak"},
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_change_password_without_auth(self, client):
        """Test password change without authentication fails."""
        response = client.post(
            "/api/v1/auth/password/change",
            json={
                "current_password": "OldPassword123",
                "new_password": "NewPassword123",
            },
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN
