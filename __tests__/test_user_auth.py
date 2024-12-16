"""Test user authentication endpoints."""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from models.UserModel import User


@pytest.mark.asyncio
async def test_register_user(
    async_client: AsyncClient,
    test_db_session: AsyncSession,
) -> None:
    """Test user registration endpoint."""
    response = await async_client.post(
        "/auth/register",
        json={
            "username": "testuser",
            "password": "testpassword",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert "key_id" in data
    assert "user_secret" in data


@pytest.mark.asyncio
async def test_register_duplicate_username(
    async_client: AsyncClient,
    test_db_session: AsyncSession,
    sample_user: User,
) -> None:
    """Test that registering with an existing username fails."""
    user = await sample_user
    response = await async_client.post(
        "/auth/register",
        json={
            "username": user.username,
            "password": "testpassword",
        },
    )
    assert response.status_code == 400
    data = response.json()
    assert "error" in data
    assert (
        "username already exists" in data["error"].lower()
    )


@pytest.mark.asyncio
async def test_login_with_valid_secret(
    async_client: AsyncClient,
    test_db_session: AsyncSession,
    sample_user: User,
) -> None:
    """Test login endpoint with valid credentials."""
    user = await sample_user
    response = await async_client.post(
        "/auth/login",
        json={
            "key_id": user.key_id,
            "user_secret": "test-secret-hash",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "token_type" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_login_with_invalid_secret(
    async_client: AsyncClient,
    test_db_session: AsyncSession,
    sample_user: User,
) -> None:
    """Test login endpoint with invalid credentials."""
    user = await sample_user
    response = await async_client.post(
        "/auth/login",
        json={
            "key_id": user.key_id,
            "user_secret": "wrong-secret",
        },
    )
    assert response.status_code == 401
    data = response.json()
    assert "error" in data
    assert "invalid credentials" in data["error"].lower()


@pytest.mark.asyncio
async def test_protected_endpoint_with_valid_token(
    async_client: AsyncClient,
    test_db_session: AsyncSession,
    sample_user: User,
) -> None:
    """Test accessing a protected endpoint with a valid token."""
    user = await sample_user
    # First, get a valid token
    login_response = await async_client.post(
        "/auth/login",
        json={
            "key_id": user.key_id,
            "user_secret": "test-secret-hash",
        },
    )
    token = login_response.json()["access_token"]

    # Then use the token to access a protected endpoint
    response = await async_client.get(
        "/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "username" in data
    assert data["username"] == user.username


@pytest.mark.asyncio
async def test_protected_endpoint_without_token(
    async_client: AsyncClient,
) -> None:
    """Test accessing a protected endpoint without a token."""
    response = await async_client.get("/auth/me")
    assert response.status_code == 401
    data = response.json()
    assert "error" in data
    assert "not authenticated" in data["error"].lower()


@pytest.mark.asyncio
async def test_protected_endpoint_with_invalid_token(
    async_client: AsyncClient,
) -> None:
    """Test accessing a protected endpoint with an invalid token."""
    response = await async_client.get(
        "/auth/me",
        headers={"Authorization": "Bearer invalid-token"},
    )
    assert response.status_code == 401
    data = response.json()
    assert "error" in data
    assert "invalid token" in data["error"].lower()
