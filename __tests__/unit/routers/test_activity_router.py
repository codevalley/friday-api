"""Test suite for ActivityRouter."""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from unittest.mock import Mock
from fastapi.security import (
    HTTPAuthorizationCredentials,
)
from sqlalchemy.orm import Session
from datetime import datetime

from routers.v1.ActivityRouter import (
    router,
    ActivityService,
)
from schemas.pydantic.ActivitySchema import (
    ActivityUpdate,
    ActivityResponse,
    ActivityList,
)
from orm.UserModel import User
from dependencies import get_current_user


@pytest.fixture
def mock_current_user():
    """Create mock authenticated user."""
    return User(
        id="test_user",
        username="test_user",
    )


@pytest.fixture
def mock_activity_service():
    """Create mock ActivityService."""
    service = Mock()
    service.check_exists.return_value = False
    service.activity_repository.get_by_name.return_value = (
        None
    )
    return service


@pytest.fixture
def mock_auth_credentials():
    """Create mock auth credentials."""
    return HTTPAuthorizationCredentials(
        scheme="Bearer",
        credentials="test_token",
    )


@pytest.fixture
def mock_db():
    """Create mock database session."""
    return Mock(spec=Session)


@pytest.fixture
def valid_activity_data():
    """Return valid activity data for testing."""
    return {
        "name": "Test Activity",
        "description": "Test Description",
        "icon": "test-icon",
        "color": "#000000",
        "activity_schema": {
            "type": "object",
            "properties": {
                "test_field": {"type": "string"}
            },
        },
    }


@pytest.fixture
def app(mock_current_user, mock_activity_service):
    """Create FastAPI test application with mocked dependencies."""
    app = FastAPI()

    async def mock_get_current_user():
        return mock_current_user

    app.dependency_overrides[
        get_current_user
    ] = mock_get_current_user
    app.dependency_overrides[
        ActivityService
    ] = lambda: mock_activity_service
    app.include_router(router)
    return app


@pytest.fixture
def client(app):
    """Create test client."""
    return TestClient(app)


class TestActivityRouter:
    """Test suite for ActivityRouter endpoints."""

    @pytest.mark.asyncio
    async def test_create_activity_success(
        self,
        client,
        mock_activity_service,
        mock_current_user,
        mock_auth_credentials,
        mock_db,
        valid_activity_data,
    ):
        """Test successful activity creation."""
        # Mock activity repository to avoid conflict
        mock_activity_service.activity_repository.get_by_name.return_value = (
            None
        )

        # Mock service response
        response = ActivityResponse(
            id=1,
            user_id=mock_current_user.id,
            name=valid_activity_data["name"],
            description=valid_activity_data["description"],
            activity_schema=valid_activity_data[
                "activity_schema"
            ],
            icon=valid_activity_data["icon"],
            color=valid_activity_data["color"],
            moment_count=0,
            created_at=datetime(
                2024, 12, 16, 18, 41, 0, 140952
            ),
            updated_at=datetime(
                2024, 12, 16, 18, 41, 0, 140952
            ),
        )
        mock_activity_service.create_activity.return_value = (
            response
        )

        # Make request
        response = client.post(
            "/v1/activities",
            json=valid_activity_data,
            headers={
                "Authorization": f"Bearer {mock_auth_credentials.credentials}"
            },
        )

        assert response.status_code == 201
        assert (
            response.json()["data"]["name"]
            == valid_activity_data["name"]
        )
        mock_activity_service.create_activity.assert_called_once()

    @pytest.mark.asyncio
    async def test_list_activities_success(
        self,
        client,
        mock_activity_service,
        mock_current_user,
        mock_auth_credentials,
        mock_db,
    ):
        """Test successful activities listing."""
        # Mock service response
        mock_activity_service.list_activities.return_value = ActivityList(
            items=[
                ActivityResponse(
                    id=1,
                    user_id=mock_current_user.id,
                    name="Test Activity",
                    description="Test Description",
                    activity_schema={
                        "type": "object",
                        "properties": {},
                    },
                    icon="test-icon",
                    color="#000000",
                    moment_count=0,
                    created_at=datetime(
                        2024, 12, 16, 18, 41, 0, 140952
                    ),
                    updated_at=datetime(
                        2024, 12, 16, 18, 41, 0, 140952
                    ),
                )
            ],
            total=1,
            page=1,
            size=10,
            pages=1,
        )

        # Make request
        response = client.get(
            "/v1/activities?page=1&size=10",
            headers={
                "Authorization": f"Bearer {mock_auth_credentials.credentials}"
            },
        )

        assert response.status_code == 200
        assert "items" in response.json()["data"]
        mock_activity_service.list_activities.assert_called_once_with(
            user_id=mock_current_user.id, page=1, size=10
        )

    @pytest.mark.asyncio
    async def test_get_activity_success(
        self,
        client,
        mock_activity_service,
        mock_current_user,
        mock_auth_credentials,
        mock_db,
        valid_activity_data,
    ):
        """Test successful activity retrieval."""
        activity_id = 1
        # Mock service response
        mock_activity_service.get_activity.return_value = (
            ActivityResponse(
                id=activity_id,
                user_id=mock_current_user.id,
                name=valid_activity_data["name"],
                description=valid_activity_data[
                    "description"
                ],
                activity_schema=valid_activity_data[
                    "activity_schema"
                ],
                icon=valid_activity_data["icon"],
                color=valid_activity_data["color"],
                moment_count=0,
                created_at=datetime(
                    2024, 12, 16, 18, 41, 0, 140952
                ),
                updated_at=datetime(
                    2024, 12, 16, 18, 41, 0, 140952
                ),
            )
        )

        # Make request
        response = client.get(
            f"/v1/activities/{activity_id}",
            headers={
                "Authorization": f"Bearer {mock_auth_credentials.credentials}"
            },
        )

        assert response.status_code == 200
        assert response.json()["data"]["id"] == activity_id
        mock_activity_service.get_activity.assert_called_once_with(
            activity_id, mock_current_user.id
        )

    @pytest.mark.asyncio
    async def test_update_activity_success(
        self,
        client,
        mock_activity_service,
        mock_current_user,
        mock_auth_credentials,
        mock_db,
        valid_activity_data,
    ):
        """Test successful activity update."""
        activity_id = 1
        update_data = {
            "name": "Updated Activity",
            "description": "Updated Description",
        }

        # Mock service response
        mock_activity_service.update_activity.return_value = ActivityResponse(
            id=activity_id,
            user_id=mock_current_user.id,
            name=update_data["name"],
            description=update_data["description"],
            activity_schema=valid_activity_data[
                "activity_schema"
            ],
            icon=valid_activity_data["icon"],
            color=valid_activity_data["color"],
            moment_count=0,
            created_at=datetime(
                2024, 12, 16, 18, 41, 0, 140952
            ),
            updated_at=datetime(
                2024, 12, 16, 18, 41, 0, 140952
            ),
        )

        # Make request
        response = client.put(
            f"/v1/activities/{activity_id}",
            json=update_data,
            headers={
                "Authorization": f"Bearer {mock_auth_credentials.credentials}"
            },
        )

        assert response.status_code == 200
        assert (
            response.json()["data"]["name"]
            == update_data["name"]
        )
        assert (
            response.json()["data"]["description"]
            == update_data["description"]
        )
        mock_activity_service.update_activity.assert_called_once_with(
            activity_id,
            ActivityUpdate(**update_data),
            mock_current_user.id,
        )

    @pytest.mark.asyncio
    async def test_delete_activity_success(
        self,
        client,
        mock_activity_service,
        mock_current_user,
        mock_auth_credentials,
        mock_db,
    ):
        """Test successful activity deletion."""
        activity_id = 1

        # Mock service response
        mock_activity_service.delete_activity.return_value = (
            True
        )

        # Make request
        response = client.delete(
            f"/v1/activities/{activity_id}",
            headers={
                "Authorization": f"Bearer {mock_auth_credentials.credentials}"
            },
        )

        assert response.status_code == 200
        assert (
            response.json()["message"]
            == "Activity deleted successfully"
        )
        mock_activity_service.delete_activity.assert_called_once_with(
            activity_id, mock_current_user.id
        )
