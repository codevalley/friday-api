"""Test TopicRouter class."""

import pytest
from datetime import datetime, timezone
from fastapi import FastAPI, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials
from fastapi.testclient import TestClient
from unittest.mock import Mock

from dependencies import get_current_user
from orm.UserModel import User
from routers.v1.TopicRouter import router as topic_router
from schemas.pydantic.TopicSchema import (
    TopicResponse,
    TopicCreate,
)
from services.TopicService import TopicService


@pytest.fixture
def mock_topic_service():
    """Create mock TopicService."""
    service = Mock(spec=TopicService)

    # Set up the mock methods
    service.create_topic = Mock()
    service.get_topic = Mock()
    service.update_topic = Mock()
    service.delete_topic = Mock()
    service.list_topics = Mock(return_value=[])
    return service


@pytest.fixture
def mock_current_user():
    """Create mock current user."""
    return User(
        id="test_user",
        username="test_user",
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
def valid_topic_data():
    """Create valid topic data."""
    return {
        "name": "Work",
        "icon": "💼",
    }


@pytest.fixture
def app(mock_current_user, mock_topic_service):
    """Create FastAPI test application with mocked dependencies."""
    app = FastAPI()

    async def mock_get_current_user():
        return mock_current_user

    app.dependency_overrides[
        get_current_user
    ] = mock_get_current_user
    app.dependency_overrides[
        TopicService
    ] = lambda: mock_topic_service
    app.include_router(topic_router)
    return app


@pytest.fixture
def client(app):
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def sample_topic(mock_topic_service, valid_topic_data):
    """Create a sample topic response."""
    current_time = datetime.now(timezone.utc)
    return TopicResponse(
        id=1,
        name=valid_topic_data["name"],
        icon=valid_topic_data["icon"],
        user_id="test_user",
        created_at=current_time,
        updated_at=current_time,
    )


@pytest.fixture
def auth_headers(mock_auth_credentials):
    """Create authorization headers."""
    return {
        "Authorization": f"Bearer {mock_auth_credentials.credentials}"
    }


class TestTopicRouter:
    """Test cases for TopicRouter."""

    def test_create_topic_success(
        self,
        client,
        mock_topic_service,
        valid_topic_data,
        auth_headers,
        sample_topic,
    ):
        """Test successful topic creation."""
        mock_topic_service.create_topic.return_value = (
            sample_topic
        )

        response = client.post(
            "/v1/topics",
            json=valid_topic_data,
            headers=auth_headers,
        )

        assert (
            response.status_code == status.HTTP_201_CREATED
        )
        assert (
            response.json()["data"]["name"]
            == valid_topic_data["name"]
        )
        assert (
            response.json()["data"]["icon"]
            == valid_topic_data["icon"]
        )
        mock_topic_service.create_topic.assert_called_once_with(
            user_id="test_user",
            data=TopicCreate(**valid_topic_data),
        )

    def test_create_topic_unauthorized(
        self, client, valid_topic_data
    ):
        """Test topic creation without authentication."""
        response = client.post(
            "/v1/topics", json=valid_topic_data
        )

        assert (
            response.status_code
            == status.HTTP_401_UNAUTHORIZED
        )
        response_data = response.json()
        assert (
            response_data["detail"]["code"]
            == "UNAUTHORIZED"
        )
        assert (
            "Invalid or missing authentication token"
            in response_data["detail"]["message"]
        )

    def test_create_topic_invalid_data(
        self, client, auth_headers
    ):
        """Test topic creation with invalid data."""
        invalid_data = {"name": "", "icon": "💼"}
        response = client.post(
            "/v1/topics",
            json=invalid_data,
            headers=auth_headers,
        )

        assert (
            response.status_code
            == status.HTTP_422_UNPROCESSABLE_ENTITY
        )

    def test_get_topic_success(
        self,
        client,
        mock_topic_service,
        auth_headers,
        sample_topic,
    ):
        """Test successful topic retrieval."""
        mock_topic_service.get_topic.return_value = (
            sample_topic
        )

        response = client.get(
            f"/v1/topics/{sample_topic.id}",
            headers=auth_headers,
        )

        assert response.status_code == status.HTTP_200_OK
        assert (
            response.json()["data"]["id"] == sample_topic.id
        )
        mock_topic_service.get_topic.assert_called_once_with(
            sample_topic.id, "test_user"
        )

    def test_get_topic_not_found(
        self, client, mock_topic_service, auth_headers
    ):
        """Test topic retrieval when not found."""
        mock_topic_service.get_topic.side_effect = (
            HTTPException(
                status_code=404, detail="Topic not found"
            )
        )

        response = client.get(
            "/v1/topics/999",
            headers=auth_headers,
        )

        assert (
            response.status_code
            == status.HTTP_404_NOT_FOUND
        )
        assert (
            response.json()["detail"] == "Topic not found"
        )

    def test_update_topic_success(
        self,
        client,
        mock_topic_service,
        auth_headers,
        sample_topic,
    ):
        """Test successful topic update."""
        update_data = {"name": "Updated Work"}
        mock_topic_service.update_topic.return_value = (
            TopicResponse(
                **{
                    **sample_topic.model_dump(),
                    "name": update_data["name"],
                }
            )
        )

        response = client.put(
            f"/v1/topics/{sample_topic.id}",
            json=update_data,
            headers=auth_headers,
        )

        assert response.status_code == status.HTTP_200_OK
        assert (
            response.json()["data"]["name"]
            == update_data["name"]
        )
        mock_topic_service.update_topic.assert_called_once()

    def test_update_topic_not_found(
        self, client, mock_topic_service, auth_headers
    ):
        """Test topic update when not found."""
        update_data = {"name": "Updated Work"}
        mock_topic_service.update_topic.side_effect = (
            HTTPException(
                status_code=404, detail="Topic not found"
            )
        )

        response = client.put(
            "/v1/topics/999",
            json=update_data,
            headers=auth_headers,
        )

        assert (
            response.status_code
            == status.HTTP_404_NOT_FOUND
        )
        assert (
            response.json()["detail"] == "Topic not found"
        )

    def test_delete_topic_success(
        self,
        client,
        mock_topic_service,
        auth_headers,
        sample_topic,
    ):
        """Test successful topic deletion."""
        mock_topic_service.delete_topic.return_value = True

        response = client.delete(
            f"/v1/topics/{sample_topic.id}",
            headers=auth_headers,
        )

        assert response.status_code == status.HTTP_200_OK
        assert (
            response.json()["message"]
            == "Topic deleted successfully"
        )
        mock_topic_service.delete_topic.assert_called_once_with(
            sample_topic.id, "test_user"
        )

    def test_delete_topic_not_found(
        self, client, mock_topic_service, auth_headers
    ):
        """Test topic deletion when not found."""
        mock_topic_service.delete_topic.side_effect = (
            HTTPException(
                status_code=404, detail="Topic not found"
            )
        )

        response = client.delete(
            "/v1/topics/999",
            headers=auth_headers,
        )

        assert (
            response.status_code
            == status.HTTP_404_NOT_FOUND
        )
        assert (
            response.json()["detail"] == "Topic not found"
        )

    def test_list_topics_success(
        self,
        client,
        mock_topic_service,
        auth_headers,
        sample_topic,
    ):
        """Test successful topics listing."""
        mock_topic_service.list_topics.return_value = {
            "items": [sample_topic],
            "total": 1,
            "page": 1,
            "size": 50,
            "pages": 1,
        }

        response = client.get(
            "/v1/topics",
            headers=auth_headers,
        )

        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()["data"]
        assert len(response_data["items"]) == 1
        assert response_data["total"] == 1
        assert response_data["page"] == 1
        assert response_data["size"] == 50
        assert response_data["pages"] == 1
        mock_topic_service.list_topics.assert_called_once_with(
            user_id="test_user",
            page=1,
            size=50,
        )

    def test_list_topics_pagination(
        self, client, mock_topic_service, auth_headers
    ):
        """Test topics listing with pagination."""
        mock_topic_service.list_topics.return_value = {
            "items": [],
            "total": 0,
            "page": 2,
            "size": 10,
            "pages": 0,
        }

        response = client.get(
            "/v1/topics?page=2&size=10",
            headers=auth_headers,
        )

        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()["data"]
        assert len(response_data["items"]) == 0
        assert response_data["total"] == 0
        assert response_data["page"] == 2
        assert response_data["size"] == 10
        assert response_data["pages"] == 0
        mock_topic_service.list_topics.assert_called_once_with(
            user_id="test_user",
            page=2,
            size=10,
        )

    def test_user_isolation(
        self,
        client,
        mock_topic_service,
        auth_headers,
        sample_topic,
    ):
        """Test that users can only access their own topics."""
        # Mock get_topic to raise 404 for different user
        mock_topic_service.get_topic.side_effect = (
            HTTPException(
                status_code=404, detail="Topic not found"
            )
        )

        response = client.get(
            f"/v1/topics/{sample_topic.id}",
            headers=auth_headers,
        )

        assert (
            response.status_code
            == status.HTTP_404_NOT_FOUND
        )
        mock_topic_service.get_topic.assert_called_once_with(
            sample_topic.id, "test_user"
        )
