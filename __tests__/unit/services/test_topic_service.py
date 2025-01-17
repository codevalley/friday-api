"""Test TopicService class."""

import pytest
from unittest.mock import Mock
from fastapi import HTTPException
from datetime import datetime, UTC
from pydantic import ValidationError

from schemas.pydantic.TopicSchema import (
    TopicCreate,
    TopicUpdate,
)
from services.TopicService import TopicService


@pytest.fixture
def topic_service(test_db_session):
    """Create TopicService instance with test database session."""
    return TopicService(db=test_db_session)


@pytest.fixture
def valid_topic_data():
    """Return valid topic data."""
    return {"name": "Work", "icon": "💼"}


@pytest.fixture
def mock_topic():
    """Create a mock topic with required attributes."""
    topic = Mock()
    topic.id = 1
    topic.name = "Work"
    topic.icon = "💼"
    topic.user_id = "test-user"
    topic.created_at = datetime.now(UTC)
    topic.updated_at = datetime.now(UTC)
    # Add SQLAlchemy state attributes
    topic._sa_instance_state = Mock()
    topic._sa_instance_state.class_ = Mock()
    topic._sa_instance_state.class_.__name__ = "Topic"
    return topic


class TestTopicService:
    """Test suite for TopicService class."""

    def test_create_topic_success(
        self, topic_service, valid_topic_data, mock_topic
    ):
        """Test successful topic creation."""
        # Setup mocks
        topic_service.topic_repo.create = Mock(
            return_value=mock_topic
        )
        topic_service.topic_repo.get_by_name = Mock(
            return_value=None
        )
        topic_service.db.commit = Mock()
        topic_service.db.refresh = Mock()

        # Create topic
        topic_data = TopicCreate(**valid_topic_data)
        result = topic_service.create_topic(
            "test-user", topic_data
        )

        # Verify result
        assert result.name == valid_topic_data["name"]
        assert result.icon == valid_topic_data["icon"]
        assert result.user_id == "test-user"

        # Verify mocks called
        topic_service.topic_repo.get_by_name.assert_called_once_with(
            "test-user", valid_topic_data["name"]
        )
        topic_service.topic_repo.create.assert_called_once_with(
            name=valid_topic_data["name"],
            icon=valid_topic_data["icon"],
            user_id="test-user",
        )
        topic_service.db.commit.assert_called_once()
        topic_service.db.refresh.assert_called_once_with(
            mock_topic
        )

    def test_create_topic_duplicate_name(
        self, topic_service, valid_topic_data, mock_topic
    ):
        """Test topic creation with duplicate name."""
        # Setup mock to simulate existing topic
        topic_service.topic_repo.get_by_name = Mock(
            return_value=mock_topic
        )

        # Try to create topic with same name
        topic_data = TopicCreate(**valid_topic_data)
        with pytest.raises(HTTPException) as exc:
            topic_service.create_topic(
                "test-user", topic_data
            )
        assert exc.value.status_code == 409

    def test_create_topic_validation_error(
        self, topic_service
    ):
        """Test topic creation with invalid data."""
        # Create topic with invalid data
        invalid_data = {"name": "", "icon": "💼"}
        with pytest.raises(ValidationError) as exc:
            TopicCreate(**invalid_data)

        assert (
            "String should have at least 1 character"
            in str(exc.value)
        )

    def test_get_topic_success(
        self, topic_service, mock_topic
    ):
        """Test successful topic retrieval."""
        # Setup mocks
        topic_service.topic_repo.get_by_owner = Mock(
            return_value=mock_topic
        )

        result = topic_service.get_topic(
            "test-user", mock_topic.id
        )

        assert result.id == mock_topic.id
        assert result.name == mock_topic.name
        assert result.icon == mock_topic.icon

    def test_get_topic_not_found(self, topic_service):
        """Test topic retrieval when not found."""
        topic_service.topic_repo.get_by_owner = Mock(
            return_value=None
        )

        with pytest.raises(HTTPException) as exc:
            topic_service.get_topic("test-user", 1)
        assert exc.value.status_code == 404

    def test_update_topic_success(
        self, topic_service, mock_topic
    ):
        """Test successful topic update."""
        topic_service.topic_repo.get_by_owner = Mock(
            return_value=mock_topic
        )
        topic_service.topic_repo.update = Mock(
            return_value=mock_topic
        )

        update_data = TopicUpdate(name="Updated Topic")
        result = topic_service.update_topic(
            "test-user", mock_topic.id, update_data
        )

        assert result.id == mock_topic.id
        assert result.name == mock_topic.name

    def test_update_topic_not_found(
        self, topic_service, mock_topic
    ):
        """Test topic update when not found."""
        topic_service.topic_repo.get_by_owner = Mock(
            return_value=None
        )

        update_data = TopicUpdate(name="Updated Topic")
        with pytest.raises(HTTPException) as exc:
            topic_service.update_topic(
                "test-user", 1, update_data
            )
        assert exc.value.status_code == 404

    def test_delete_topic_success(
        self, topic_service, mock_topic
    ):
        """Test successful topic deletion."""
        topic_service.topic_repo.get_by_owner = Mock(
            return_value=mock_topic
        )
        topic_service.topic_repo.delete = Mock(
            return_value=True
        )

        result = topic_service.delete_topic(
            "test-user", mock_topic.id
        )
        assert result is True

    def test_delete_topic_not_found(self, topic_service):
        """Test topic deletion when not found."""
        topic_service.topic_repo.get_by_owner = Mock(
            return_value=None
        )

        with pytest.raises(HTTPException) as exc:
            topic_service.delete_topic("test-user", 1)
        assert exc.value.status_code == 404

    def test_list_topics_success(
        self, topic_service, mock_topic
    ):
        """Test successful topics listing."""
        # Setup mock to return list of topics
        topic_service.topic_repo.list_topics = Mock(
            return_value=[mock_topic, mock_topic]
        )
        topic_service.topic_repo.count_by_user = Mock(
            return_value=2
        )

        result = topic_service.list_topics(
            "test-user", page=1, size=10
        )

        # Verify the result
        assert isinstance(result, dict)
        assert len(result["items"]) == 2
        assert result["total"] == 2
        assert result["page"] == 1
        assert result["size"] == 10
        assert result["pages"] == 1

        # Verify the mock calls
        topic_service.topic_repo.list_topics.assert_called_once_with(
            user_id="test-user",
            skip=0,
            limit=10,
        )
        topic_service.topic_repo.count_by_user.assert_called_once_with(
            "test-user"
        )

    def test_list_topics_pagination(
        self, topic_service, mock_topic
    ):
        """Test topics listing with pagination."""
        # Setup mock to return list of topics
        topic_service.topic_repo.list_topics = Mock(
            return_value=[mock_topic]
        )
        topic_service.topic_repo.count_by_user = Mock(
            return_value=15
        )

        result = topic_service.list_topics(
            "test-user", page=2, size=10
        )

        # Verify the result
        assert isinstance(result, dict)
        assert len(result["items"]) == 1
        assert result["total"] == 15
        assert result["page"] == 2
        assert result["size"] == 10
        assert result["pages"] == 2

        # Verify the mock calls
        topic_service.topic_repo.list_topics.assert_called_once_with(
            user_id="test-user",
            skip=10,  # (page - 1) * size
            limit=10,
        )
        topic_service.topic_repo.count_by_user.assert_called_once_with(
            "test-user"
        )
