"""Test AuthRouter class."""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch
from sqlalchemy.orm import Session
from datetime import datetime
from routers.v1.AuthRouter import router
from orm.UserModel import User


@pytest.fixture
def mock_user_service():
    """Create mock UserService."""
    service = Mock()
    return service


@pytest.fixture
def mock_db():
    """Create mock database session."""
    return Mock(spec=Session)


@pytest.fixture
def app(mock_db, mock_user_service):
    """Create FastAPI test application with mocked dependencies."""
    app = FastAPI()

    def get_mock_db():
        return mock_db

    app.dependency_overrides[
        "configs.Database.get_db_connection"
    ] = get_mock_db
    app.include_router(router)
    return app


@pytest.fixture
def client(app):
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def valid_register_data():
    """Create valid registration data."""
    return {"username": "testuser"}


@pytest.fixture
def valid_login_data():
    """Create valid login data."""
    return {
        "user_secret": "test-secret",
    }


class TestAuthRouter:
    """Test cases for AuthRouter."""

    @pytest.mark.asyncio
    async def test_register_user_success(
        self,
        client,
        mock_user_service,
        mock_db,
        valid_register_data,
    ):
        """Test successful user registration."""
        # Mock service response
        user = User(
            id="1",
            username=valid_register_data["username"],
            key_id="test-key-id",
            user_secret="test-secret-hash",
        )
        user_secret = "test-secret"
        mock_user_service.register_user.return_value = (
            user,
            user_secret,
        )

        with patch(
            "routers.v1.AuthRouter.UserService",
            return_value=mock_user_service,
        ):
            # Make request
            response = client.post(
                "/v1/auth/register",
                json=valid_register_data,
            )

        assert response.status_code == 201
        assert (
            response.json()["data"]["username"]
            == valid_register_data["username"]
        )
        assert response.json()["data"]["id"] == "1"
        assert (
            response.json()["data"]["user_secret"]
            == user_secret
        )
        mock_user_service.register_user.assert_called_once_with(
            username=valid_register_data["username"]
        )

    @pytest.mark.asyncio
    async def test_login_success(
        self,
        client,
        mock_user_service,
        mock_db,
        valid_login_data,
    ):
        """Test successful user login."""
        # Mock service response
        user = User(
            id="1",
            username="testuser",
            key_id="test-key-id",
            user_secret="test-secret-hash",
        )
        mock_user_service.authenticate_user.return_value = (
            user
        )

        with patch(
            "routers.v1.AuthRouter.UserService",
            return_value=mock_user_service,
        ), patch(
            "routers.v1.AuthRouter.create_access_token",
            return_value="test-token",
        ):
            # Make request
            response = client.post(
                "/v1/auth/token",
                json=valid_login_data,
            )

        assert response.status_code == 200
        assert (
            response.json()["data"]["access_token"]
            == "test-token"
        )
        assert (
            response.json()["data"]["token_type"]
            == "bearer"
        )
        mock_user_service.authenticate_user.assert_called_once_with(
            valid_login_data["user_secret"]
        )

    @pytest.mark.asyncio
    async def test_get_current_user_success(
        self,
        client,
        mock_user_service,
        mock_db,
    ):
        """Test successful current user retrieval."""
        # current_user = {
        #     "user_id": "1",
        #     "sub": "1",
        # }
        user = User(
            id="1",
            username="testuser",
            key_id="test-key-id",
            user_secret="test-secret-hash",
            created_at=datetime(
                2024, 12, 16, 18, 41, 0, 140952
            ),
            updated_at=datetime(
                2024, 12, 16, 18, 41, 0, 140952
            ),
        )
        mock_user_service.get_user_by_id.return_value = user

        with patch(
            "routers.v1.AuthRouter.UserService",
            return_value=mock_user_service,
        ), patch(
            "utils.security.decode_token",
            return_value={"sub": "1"},
        ), patch(
            "routers.v1.AuthRouter.get_db_connection",
            return_value=mock_db,
        ):
            # Make request
            response = client.get(
                "/v1/auth/me",
                headers={
                    "Authorization": "Bearer test-token"
                },
            )

        assert response.status_code == 200
        assert response.json()["data"] == {
            "id": "1",
            "username": "testuser",
            "created_at": "2024-12-16T18:41:00.140952",
            "updated_at": "2024-12-16T18:41:00.140952",
        }
        mock_user_service.get_user_by_id.assert_called_once_with(
            "1"
        )
