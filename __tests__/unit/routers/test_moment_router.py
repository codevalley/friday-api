"""Test MomentRouter class."""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from unittest.mock import Mock
from fastapi.security import HTTPAuthorizationCredentials
from datetime import datetime

from routers.v1.MomentRouter import router, MomentService
from schemas.pydantic.MomentSchema import (
    MomentResponse,
    MomentList,
)
from schemas.pydantic.ActivitySchema import ActivityResponse
from orm.UserModel import User
from dependencies import get_current_user


@pytest.fixture
def mock_moment_service():
    """Create mock MomentService."""
    service = Mock()
    return service


@pytest.fixture
def mock_current_user():
    """Create mock current user."""
    return User(
        id=1,
        username="testuser",
        key_id="test-key-id",
        user_secret="test-secret-hash",
    )


@pytest.fixture
def mock_auth_credentials():
    """Create mock auth credentials."""
    return HTTPAuthorizationCredentials(
        scheme="Bearer", credentials="test-token"
    )


@pytest.fixture
def app(mock_current_user, mock_moment_service):
    """Create FastAPI test application with mocked dependencies."""
    app = FastAPI()

    async def mock_get_current_user():
        return mock_current_user

    app.dependency_overrides[
        get_current_user
    ] = mock_get_current_user
    app.dependency_overrides[
        MomentService
    ] = lambda: mock_moment_service
    app.include_router(router)
    return app


@pytest.fixture
def client(app):
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def valid_moment_data():
    """Create valid moment data."""
    return {
        "activity_id": 1,
        "data": {"notes": "Test notes"},
        "timestamp": "2024-12-16T18:41:00.140952",
    }


class TestMomentRouter:
    """Test cases for MomentRouter."""

    @pytest.mark.asyncio
    async def test_create_moment_success(
        self,
        client,
        mock_moment_service,
        mock_current_user,
        mock_auth_credentials,
        valid_moment_data,
    ):
        """Test successful moment creation."""
        # Mock service response
        activity_response = ActivityResponse(
            id="1",
            name="Test Activity",
            description="Test Description",
            activity_schema={
                "type": "object",
                "properties": {},
            },
            icon="test-icon",
            color="#000000",
            user_id="test-user-id",
            created_at=datetime(
                2024, 12, 16, 18, 41, 0, 140952
            ),
            updated_at=datetime(
                2024, 12, 16, 18, 41, 0, 140952
            ),
        )
        response = MomentResponse(
            id=1,
            activity=activity_response,
            activity_id=1,
            data=valid_moment_data["data"],
            timestamp=datetime(
                2024, 12, 16, 18, 41, 0, 140952
            ),
        )
        mock_moment_service.create_moment.return_value = (
            response
        )

        # Make request
        response = client.post(
            "/v1/moments",
            json=valid_moment_data,
            headers={
                "Authorization": f"Bearer {mock_auth_credentials.credentials}"
            },
        )

        assert response.status_code == 201
        assert (
            response.json()["data"]["activity"]["id"]
            == activity_response.id
        )
        mock_moment_service.create_moment.assert_called_once()

    @pytest.mark.asyncio
    async def test_list_moments_success(
        self,
        client,
        mock_moment_service,
        mock_current_user,
        mock_auth_credentials,
    ):
        """Test successful moments listing."""
        # Mock service response
        mock_moment_service.list_moments.return_value = (
            MomentList(
                items=[
                    MomentResponse(
                        id=1,
                        activity=ActivityResponse(
                            id="1",
                            name="Test Activity",
                            description="Test Description",
                            activity_schema={
                                "type": "object",
                                "properties": {},
                            },
                            icon="test-icon",
                            color="#000000",
                            user_id="test-user-id",
                            created_at=datetime(
                                2024,
                                12,
                                16,
                                18,
                                41,
                                0,
                                140952,
                            ),
                            updated_at=datetime(
                                2024,
                                12,
                                16,
                                18,
                                41,
                                0,
                                140952,
                            ),
                        ),
                        activity_id=1,
                        data={"notes": "Test notes"},
                        timestamp=datetime(
                            2024, 12, 16, 18, 41, 0, 140952
                        ),
                    )
                ],
                total=1,
                page=1,
                size=10,
                pages=1,
            )
        )

        # Make request
        response = client.get(
            "/v1/moments?page=1&size=10",
            headers={
                "Authorization": f"Bearer {mock_auth_credentials.credentials}"
            },
        )

        assert response.status_code == 200
        assert len(response.json()["data"]["items"]) == 1
        mock_moment_service.list_moments.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_moment_success(
        self,
        client,
        mock_moment_service,
        mock_current_user,
        mock_auth_credentials,
    ):
        """Test successful moment retrieval."""
        moment_id = 1
        # Mock service response
        mock_moment_service.get_moment.return_value = (
            MomentResponse(
                id=moment_id,
                activity=ActivityResponse(
                    id="1",
                    name="Test Activity",
                    description="Test Description",
                    activity_schema={
                        "type": "object",
                        "properties": {},
                    },
                    icon="test-icon",
                    color="#000000",
                    user_id="test-user-id",
                    created_at=datetime(
                        2024, 12, 16, 18, 41, 0, 140952
                    ),
                    updated_at=datetime(
                        2024, 12, 16, 18, 41, 0, 140952
                    ),
                ),
                activity_id=1,
                data={"notes": "Test notes"},
                timestamp=datetime(
                    2024, 12, 16, 18, 41, 0, 140952
                ),
            )
        )

        # Make request
        response = client.get(
            f"/v1/moments/{moment_id}",
            headers={
                "Authorization": f"Bearer {mock_auth_credentials.credentials}"
            },
        )

        assert response.status_code == 200
        assert response.json()["data"]["id"] == moment_id
        mock_moment_service.get_moment.assert_called_once_with(
            moment_id, mock_current_user.id
        )

    @pytest.mark.asyncio
    async def test_update_moment_success(
        self,
        client,
        mock_moment_service,
        mock_current_user,
        mock_auth_credentials,
    ):
        """Test successful moment update."""
        moment_id = 1
        update_data = {
            "data": {"notes": "Updated notes"},
            "timestamp": "2024-12-16T18:41:00.140952",
        }

        # Mock service response
        mock_moment_service.update_moment.return_value = (
            MomentResponse(
                id=moment_id,
                activity=ActivityResponse(
                    id="1",
                    name="Test Activity",
                    description="Test Description",
                    activity_schema={
                        "type": "object",
                        "properties": {},
                    },
                    icon="test-icon",
                    color="#000000",
                    user_id="test-user-id",
                    created_at=datetime(
                        2024, 12, 16, 18, 41, 0, 140952
                    ),
                    updated_at=datetime(
                        2024, 12, 16, 18, 41, 0, 140952
                    ),
                ),
                activity_id=1,
                data=update_data["data"],
                timestamp=datetime(
                    2024, 12, 16, 18, 41, 0, 140952
                ),
            )
        )

        # Make request
        response = client.put(
            f"/v1/moments/{moment_id}",
            json=update_data,
            headers={
                "Authorization": f"Bearer {mock_auth_credentials.credentials}"
            },
        )

        assert response.status_code == 200
        assert (
            response.json()["data"]["data"]["notes"]
            == update_data["data"]["notes"]
        )
        mock_moment_service.update_moment.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_moment_success(
        self,
        client,
        mock_moment_service,
        mock_current_user,
        mock_auth_credentials,
    ):
        """Test successful moment deletion."""
        moment_id = 1

        # Mock service response
        mock_moment_service.delete_moment.return_value = (
            True
        )

        # Make request
        response = client.delete(
            f"/v1/moments/{moment_id}",
            headers={
                "Authorization": f"Bearer {mock_auth_credentials.credentials}"
            },
        )

        assert response.status_code == 200
        assert (
            response.json()["message"]
            == "Moment deleted successfully"
        )
        mock_moment_service.delete_moment.assert_called_once_with(
            moment_id, mock_current_user.id
        )

    @pytest.mark.asyncio
    async def test_get_recent_activities_success(
        self,
        client,
        mock_moment_service,
        mock_current_user,
        mock_auth_credentials,
    ):
        """Test successful recent activities retrieval."""
        # Mock service response
        mock_moment_service.list_recent_activities.return_value = [
            ActivityResponse(
                id=1,
                name="Test Activity",
                description="Test Description",
                activity_schema={
                    "type": "object",
                    "properties": {},
                },
                icon="test-icon",
                color="#000000",
                user_id="test-user-id",
                created_at=datetime(
                    2024, 12, 16, 18, 41, 0, 140952
                ),
                updated_at=datetime(
                    2024, 12, 16, 18, 41, 0, 140952
                ),
                moment_count=0,
            )
        ]

        # Make request
        response = client.get(
            "/v1/moments/activities/recent?limit=5",
            headers={
                "Authorization": f"Bearer {mock_auth_credentials.credentials}"
            },
        )

        assert response.status_code == 200
        assert response.json()["data"] == [
            {
                "id": 1,
                "name": "Test Activity",
                "description": "Test Description",
                "activity_schema": {
                    "type": "object",
                    "properties": {},
                },
                "icon": "test-icon",
                "color": "#000000",
                "user_id": "test-user-id",
                "moment_count": 0,
                "created_at": "2024-12-16T18:41:00.140952",
                "updated_at": "2024-12-16T18:41:00.140952",
                "moments": None,
            }
        ]
        mock_moment_service.list_recent_activities.assert_called_once_with(
            str(mock_current_user.id), 5
        )

    @pytest.mark.asyncio
    async def test_create_moment_unauthenticated(
        self,
        client,
        mock_moment_service,
        valid_moment_data,
    ):
        """Test moment creation without authentication."""
        response = client.post(
            "/v1/moments",
            json=valid_moment_data,
        )

        assert response.status_code == 401
        response_data = response.json()
        assert (
            response_data["detail"]["code"]
            == "UNAUTHORIZED"
        )
        assert (
            "Invalid or missing authentication token"
            in response_data["detail"]["message"]
        )
        assert (
            response_data["detail"]["type"]
            == "AuthenticationError"
        )
