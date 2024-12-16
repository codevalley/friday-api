"""Test user authentication endpoints."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from models.UserModel import User


def test_register_user(
    test_client: TestClient,
    test_db_session: AsyncSession,
) -> None:
    """Test user registration endpoint."""
    response = test_client.post(
        "/v1/auth/register",
        json={
            "username": "testuser",
        },
    )
    assert response.status_code == 201
    data = response.json()["data"]
    assert "id" in data
    assert "username" in data
    assert "user_secret" in data
    assert data["username"] == "testuser"


def test_register_duplicate_username(
    test_client: TestClient,
    test_db_session: AsyncSession,
) -> None:
    """Test registering a user with a duplicate username."""
    # First registration
    response = test_client.post(
        "/v1/auth/register",
        json={
            "username": "testuser",
        },
    )
    assert response.status_code == 201

    # Second registration with same username
    response = test_client.post(
        "/v1/auth/register",
        json={
            "username": "testuser",
        },
    )
    assert response.status_code == 400
    assert "already exists" in response.json()["detail"]


def test_login_with_valid_secret(
    test_client: TestClient,
) -> None:
    """Test user login with valid credentials."""
    # First register a user to get their API key
    register_response = test_client.post(
        "/v1/auth/register",
        json={
            "username": "testuser_login",
        },
    )
    assert register_response.status_code == 201
    user_secret = register_response.json()["data"]["user_secret"]

    # Now try to login with the API key
    response = test_client.post(
        "/v1/auth/token",
        json={
            "user_secret": user_secret,
        },
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert "access_token" in data
    assert "token_type" in data
    assert data["token_type"] == "bearer"


def test_login_with_invalid_secret(
    test_client: TestClient,
) -> None:
    """Test user login with invalid credentials."""
    response = test_client.post(
        "/v1/auth/token",
        json={
            "user_secret": "invalid-api-key",
        },
    )
    assert response.status_code == 401
    assert "Invalid API key" in response.json()["detail"]


def test_protected_endpoint_with_valid_token(
    test_client: TestClient,
) -> None:
    """Test accessing a protected endpoint with a valid token."""
    # First register a user to get their API key
    register_response = test_client.post(
        "/v1/auth/register",
        json={
            "username": "testuser_protected",
        },
    )
    assert register_response.status_code == 201
    user_secret = register_response.json()["data"]["user_secret"]

    # Get a valid token
    token_response = test_client.post(
        "/v1/auth/token",
        json={
            "user_secret": user_secret,
        },
    )
    assert token_response.status_code == 200
    access_token = token_response.json()["data"]["access_token"]

    # Use the token to access a protected endpoint
    response = test_client.get(
        "/v1/auth/me",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert "id" in data
    assert "username" in data


def test_protected_endpoint_without_token(
    test_client: TestClient,
) -> None:
    """Test accessing a protected endpoint without a token."""
    response = test_client.get("/v1/auth/me")
    assert response.status_code == 401
    assert "Not authenticated" in response.json()["detail"]


def test_protected_endpoint_with_invalid_token(
    test_client: TestClient,
) -> None:
    """Test accessing a protected endpoint with an invalid token."""
    response = test_client.get(
        "/v1/auth/me",
        headers={"Authorization": "Bearer invalid-token"},
    )
    assert response.status_code == 401
    assert "Could not validate credentials" in response.json()["detail"]
