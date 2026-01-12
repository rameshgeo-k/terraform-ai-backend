"""
Tests for user endpoints.
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def get_auth_token():
    """Helper function to get authentication token."""
    # Register and login
    client.post(
        "/api/auth/register",
        json={
            "email": "usertest@example.com",
            "username": "usertest",
            "password": "password123"
        }
    )
    
    response = client.post(
        "/api/auth/login",
        json={
            "email": "usertest@example.com",
            "password": "password123"
        }
    )
    return response.json()["access_token"]


def test_get_current_user():
    """Test getting current user profile."""
    token = get_auth_token()
    
    response = client.get(
        "/api/users/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "usertest@example.com"
    assert data["username"] == "usertest"


def test_update_user_profile():
    """Test updating user profile."""
    token = get_auth_token()
    
    response = client.put(
        "/api/users/me",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "full_name": "Updated Name"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["full_name"] == "Updated Name"


def test_unauthorized_access():
    """Test accessing protected endpoint without token."""
    response = client.get("/api/users/me")
    assert response.status_code == 422  # Missing authorization header
