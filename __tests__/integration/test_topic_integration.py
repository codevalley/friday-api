"""Integration tests for Topic functionality.

This test suite verifies the complete flow of Topic operations,
including database interactions and API responses.
"""

import pytest
from datetime import datetime
from fastapi import FastAPI
from fastapi.testclient import TestClient
from domain.user import UserData
from services.TopicService import TopicService
from repositories.TopicRepository import TopicRepository
from dependencies import get_current_user
from routers.v1.TopicRouter import router as topic_router
from schemas.pydantic.TopicSchema import (
    TopicCreate,
    TopicUpdate,
)
from utils.security import hash_user_secret


@pytest.fixture
def mock_current_user(sample_user):
    """Create a mock user for testing."""
    return UserData(
        id=sample_user.id,
        username="testuser123",
        key_id="12345678-1234-5678-1234-567812345678",
        user_secret=hash_user_secret("test-password"),
    )


@pytest.fixture
def topic_service(test_db_session):
    """Create a TopicService instance with test database."""
    return TopicService(test_db_session)


@pytest.fixture
def app(mock_current_user, topic_service):
    """Create FastAPI test application with mocked dependencies."""
    app = FastAPI()

    async def mock_get_current_user():
        return mock_current_user

    app.dependency_overrides[
        get_current_user
    ] = mock_get_current_user
    app.dependency_overrides[
        TopicService
    ] = lambda: topic_service
    app.include_router(topic_router)
    return app


@pytest.fixture
def client(app):
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def valid_topic_data():
    """Create valid topic data for testing."""
    return {
        "name": "Work",
        "icon": "💼",
    }


@pytest.fixture
def auth_headers(mock_current_user):
    """Create authentication headers for testing."""
    return {
        "Authorization": f"Bearer {mock_current_user.key_id}"
    }


@pytest.mark.integration
def test_topic_crud_flow(
    test_db_session,
    topic_service,
    sample_user,
    another_user,
    client,
):
    """Test complete CRUD flow for topics."""
    # Create topic
    topic_data = TopicCreate(
        name="Work",
        icon="💼",
    )
    topic_response = topic_service.create_topic(
        user_id=sample_user.id,
        data=topic_data,
    )

    # Verify created topic
    assert topic_response.name == topic_data.name
    assert topic_response.icon == topic_data.icon
    assert topic_response.user_id == sample_user.id
    assert isinstance(topic_response.id, int)
    assert isinstance(topic_response.created_at, datetime)

    # Get topic directly from repository
    topic_repo = TopicRepository(test_db_session)
    topic = topic_repo.get_by_owner(
        topic_response.id, sample_user.id
    )
    assert topic is not None
    assert topic.name == topic_data.name

    # Update topic
    update_data = TopicUpdate(name="Updated Work")
    updated_response = topic_service.update_topic(
        user_id=sample_user.id,
        topic_id=topic_response.id,
        data=update_data,
    )
    assert updated_response.name == update_data.name
    assert (
        updated_response.icon == topic_data.icon
    )  # Unchanged
    assert updated_response.updated_at is not None

    # List topics
    list_response = topic_service.list_topics(
        user_id=sample_user.id,
        page=1,
        size=10,
    )
    assert len(list_response["items"]) == 1
    assert list_response["total"] == 1
    assert list_response["page"] == 1
    assert list_response["size"] == 10

    # Verify user isolation
    other_user_list = topic_service.list_topics(
        user_id=another_user.id,
        page=1,
        size=10,
    )
    assert len(other_user_list["items"]) == 0

    # Delete topic
    assert topic_service.delete_topic(
        user_id=sample_user.id,
        topic_id=topic_response.id,
    )

    # Verify deletion
    assert (
        topic_repo.get_by_owner(
            topic_response.id, sample_user.id
        )
        is None
    )


@pytest.mark.integration
def test_topic_api_responses(
    client,
    topic_service,
    sample_user,
    auth_headers,
):
    """Test API response formats and status codes."""
    # Create topic
    create_response = client.post(
        "/v1/topics",
        json={"name": "Work", "icon": "💼"},
        headers=auth_headers,
    )
    assert create_response.status_code == 201
    created_topic = create_response.json()["data"]
    assert created_topic["name"] == "Work"
    assert created_topic["icon"] == "💼"

    # Get topic
    get_response = client.get(
        f"/v1/topics/{created_topic['id']}",
        headers=auth_headers,
    )
    assert get_response.status_code == 200
    assert get_response.json()["data"] == created_topic

    # Update topic
    update_response = client.put(
        f"/v1/topics/{created_topic['id']}",
        json={"name": "Updated Work"},
        headers=auth_headers,
    )
    assert update_response.status_code == 200
    updated_topic = update_response.json()["data"]
    assert updated_topic["name"] == "Updated Work"
    assert updated_topic["icon"] == "💼"

    # List topics
    list_response = client.get(
        "/v1/topics", headers=auth_headers
    )
    assert list_response.status_code == 200
    topics_data = list_response.json()["data"]
    assert "items" in topics_data
    assert "total" in topics_data
    assert "page" in topics_data
    assert "size" in topics_data
    assert "pages" in topics_data
    assert len(topics_data["items"]) == 1

    # Delete topic
    delete_response = client.delete(
        f"/v1/topics/{created_topic['id']}",
        headers=auth_headers,
    )
    assert delete_response.status_code == 200
    assert (
        delete_response.json()["message"]
        == "Topic deleted successfully"
    )


@pytest.mark.integration
def test_topic_error_handling(
    client,
    topic_service,
    sample_user,
    auth_headers,
):
    """Test error handling in topic operations."""
    # Try to get non-existent topic
    get_response = client.get(
        "/v1/topics/999",
        headers=auth_headers,
    )
    assert get_response.status_code == 404
    assert (
        "Topic not found" in get_response.json()["detail"]
    )

    # Try to create topic with invalid data
    create_response = client.post(
        "/v1/topics",
        json={"name": "", "icon": "💼"},
        headers=auth_headers,
    )
    assert create_response.status_code == 422

    # Create a topic for duplicate name test
    client.post(
        "/v1/topics",
        json={"name": "Work", "icon": "💼"},
        headers=auth_headers,
    )

    # Try to create topic with duplicate name
    duplicate_response = client.post(
        "/v1/topics",
        json={"name": "Work", "icon": "📊"},
        headers=auth_headers,
    )
    assert duplicate_response.status_code == 409
    assert (
        "already exists"
        in duplicate_response.json()["detail"]
    )

    # Try to access without authentication
    unauth_response = client.get("/v1/topics")
    assert unauth_response.status_code == 401


@pytest.mark.integration
def test_topic_pagination(
    client,
    topic_service,
    sample_user,
    auth_headers,
):
    """Test topic listing pagination."""
    # Create multiple topics
    topics = [
        ("Work", "💼"),
        ("Personal", "🏠"),
        ("Shopping", "🛒"),
        ("Health", "💪"),
        ("Study", "📚"),
    ]
    for name, icon in topics:
        client.post(
            "/v1/topics",
            json={"name": name, "icon": icon},
            headers=auth_headers,
        )

    # Test first page
    page1_response = client.get(
        "/v1/topics?page=1&size=2",
        headers=auth_headers,
    )
    assert page1_response.status_code == 200
    page1_data = page1_response.json()["data"]
    assert len(page1_data["items"]) == 2
    assert page1_data["total"] == 5
    assert page1_data["page"] == 1
    assert page1_data["size"] == 2
    assert page1_data["pages"] == 3

    # Test second page
    page2_response = client.get(
        "/v1/topics?page=2&size=2",
        headers=auth_headers,
    )
    assert page2_response.status_code == 200
    page2_data = page2_response.json()["data"]
    assert len(page2_data["items"]) == 2
    assert page2_data["page"] == 2

    # Test last page
    page3_response = client.get(
        "/v1/topics?page=3&size=2",
        headers=auth_headers,
    )
    assert page3_response.status_code == 200
    page3_data = page3_response.json()["data"]
    assert len(page3_data["items"]) == 1
    assert page3_data["page"] == 3
