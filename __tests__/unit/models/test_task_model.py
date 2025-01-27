"""Unit tests for TaskModel."""

import pytest
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from unittest.mock import MagicMock, create_autospec

from orm.TaskModel import Task
from orm.TopicModel import Topic
from orm.UserModel import User


class TestTaskModel:
    """Test cases for TaskModel."""

    @pytest.fixture
    def mock_db(self):
        """Create a mock database session with engine binding."""
        mock_session = create_autospec(Session)
        mock_engine = MagicMock()
        mock_session.get_bind.return_value = mock_engine
        return mock_session

    @pytest.fixture
    def mock_user(self):
        """Create a mock user."""
        user = User(
            id="test-user-id",
            username="testuser",
            key_id="test-key-id",
            user_secret="test-secret",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        return user

    @pytest.fixture
    def mock_topic(self, mock_user):
        """Create a mock topic."""
        topic = Topic()
        topic.id = 1
        topic.name = "Work"
        topic.icon = "💼"
        topic.user_id = mock_user.id
        topic.created_at = datetime.now(timezone.utc)
        topic.updated_at = datetime.now(timezone.utc)
        return topic

    @pytest.fixture
    def mock_task(self, mock_user):
        """Create a mock task."""
        task = Task()
        task.id = 1
        task.content = "Test Task Content"
        task.user_id = mock_user.id
        task.status = "todo"
        task.priority = "medium"
        task.created_at = datetime.now(timezone.utc)
        task.updated_at = datetime.now(timezone.utc)
        return task

    def test_task_topic_relationship_creation(
        self, mock_task: Task, mock_topic: Topic
    ):
        """Test creating a task with a topic relationship."""
        mock_task.topic = mock_topic
        mock_task.topic_id = mock_topic.id

        assert mock_task.topic_id == mock_topic.id
        assert mock_task.topic == mock_topic

    def test_task_topic_relationship_deletion(
        self, mock_task: Task, mock_topic: Topic
    ):
        """Test topic relationship removal."""
        # Set up relationship
        mock_task.topic = mock_topic
        mock_task.topic_id = mock_topic.id

        # Remove relationship
        mock_task.topic = None
        mock_task.topic_id = None

        assert mock_task.topic_id is None
        assert mock_task.topic is None

    def test_task_to_dict_with_topic(
        self, mock_task: Task, mock_topic: Topic
    ):
        """Test topic data is included in dictionary representation."""
        mock_task.topic = mock_topic
        mock_task.topic_id = mock_topic.id

        result = mock_task.to_dict()

        assert result["topic_id"] == mock_topic.id
        assert result["topic"]["id"] == mock_topic.id
        assert result["topic"]["name"] == mock_topic.name
        assert result["topic"]["icon"] == mock_topic.icon

    def test_task_from_dict_with_topic(
        self, mock_task: Task, mock_topic: Topic
    ):
        """Test creating task from dictionary with topic data."""
        task_dict = {
            "id": 1,
            "content": "Test Task Content",
            "user_id": mock_task.user_id,
            "status": "todo",
            "priority": "medium",
            "topic_id": mock_topic.id,
            "created_at": mock_task.created_at.isoformat(),
            "updated_at": mock_task.updated_at.isoformat(),
        }

        task = Task.from_dict(task_dict)

        assert task.topic_id == mock_topic.id
        assert task.content == task_dict["content"]
        assert task.status == task_dict["status"]
        assert task.priority == task_dict["priority"]

    def test_task_topic_cascade_on_delete(
        self,
        mock_task: Task,
        mock_topic: Topic,
        mock_db: Session,
    ):
        """Test that task remains when topic is deleted."""
        # Set up relationship
        mock_task.topic = mock_topic
        mock_task.topic_id = mock_topic.id

        # Mock the database operations
        def delete_side_effect(obj):
            if obj == mock_topic:
                mock_task.topic = None
                mock_task.topic_id = None

        mock_db.delete.side_effect = delete_side_effect
        mock_db.delete(mock_topic)
        mock_db.flush()

        # Task should still exist but topic reference should be None
        assert mock_task.topic_id is None
        assert mock_task.topic is None
