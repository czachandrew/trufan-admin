import pytest
from fastapi import status


class TestUserProfile:
    """Test user profile endpoints."""

    def test_get_current_user_profile(self, client, auth_headers, test_user_data):
        """Test getting current user profile."""
        response = client.get("/api/v1/users/me", headers=auth_headers)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["email"] == test_user_data["email"]
        assert data["first_name"] == test_user_data["first_name"]
        assert data["last_name"] == test_user_data["last_name"]
        assert "hashed_password" not in data

    def test_get_profile_without_auth(self, client):
        """Test getting profile without authentication fails."""
        response = client.get("/api/v1/users/me")
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_update_user_profile(self, client, auth_headers):
        """Test updating user profile."""
        update_data = {"first_name": "Updated", "last_name": "Name"}
        response = client.patch(
            "/api/v1/users/me", headers=auth_headers, json=update_data
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["first_name"] == "Updated"
        assert data["last_name"] == "Name"

    def test_update_profile_partial(self, client, auth_headers, test_user_data):
        """Test partial profile update."""
        response = client.patch(
            "/api/v1/users/me", headers=auth_headers, json={"first_name": "NewName"}
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["first_name"] == "NewName"
        assert data["last_name"] == test_user_data["last_name"]  # Unchanged

    def test_update_profile_without_auth(self, client):
        """Test updating profile without authentication fails."""
        response = client.patch("/api/v1/users/me", json={"first_name": "Test"})
        assert response.status_code == status.HTTP_403_FORBIDDEN
