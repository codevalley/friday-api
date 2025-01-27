"""Unit tests for TaskRepository."""

from datetime import datetime, UTC, timedelta
from unittest.mock import MagicMock, create_autospec

import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from domain.exceptions import (
    TaskValidationError,
    TaskReferenceError,
)
from domain.values import TaskStatus, TaskPriority
from orm.TaskModel import Task
from orm.TopicModel import Topic
from repositories.TaskRepository import TaskRepository


@pytest.fixture
def mock_db():
    """Create a mock database session."""
    return create_autospec(Session)


@pytest.fixture
def task_repo(mock_db):
    """Create a TaskRepository instance with mock db."""
    return TaskRepository(mock_db)


@pytest.fixture
def mock_task():
    """Create a mock task."""
    task = MagicMock(spec=Task)
    task.id = 1
    task.content = "Test Task"
    task.description = "Test Description"
    task.user_id = "test-user-id"
    task.status = TaskStatus.TODO
    task.priority = TaskPriority.MEDIUM
    task.due_date = datetime.now(UTC)
    task.tags = ["test"]
    task.parent_id = None
    task.topic_id = None
    task.created_at = datetime.now(UTC)
    task.updated_at = None
    return task


@pytest.fixture
def mock_topic():
    """Create a mock topic."""
    topic = MagicMock(spec=Topic)
    topic.id = 1
    topic.name = "Test Topic"
    topic.icon = "📝"
    topic.user_id = "test-user-id"
    topic.created_at = datetime.now(UTC)
    topic.updated_at = None
    return topic


class TestTaskRepository:
    """Test cases for TaskRepository."""

    def test_create_task_with_topic(
        self,
        task_repo: TaskRepository,
        mock_db: Session,
        mock_topic: Topic,
    ):
        """Test creating a task with a topic."""
        # Arrange
        content = "Test Task"
        user_id = "test-user-id"
        topic_id = mock_topic.id

        # Mock the database query
        mock_db.add.return_value = None
        mock_db.commit.return_value = None
        mock_db.refresh.return_value = None

        # Act
        task = task_repo.create(
            {
                "content": content,
                "user_id": user_id,
                "topic_id": topic_id,
            }
        )

        # Assert
        assert task.content == content
        assert task.user_id == user_id
        assert task.topic_id == topic_id
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()

    def test_list_tasks_with_topic_filter(
        self,
        task_repo: TaskRepository,
        mock_db: Session,
        mock_task: Task,
        mock_topic: Topic,
    ):
        """Test listing tasks with topic filter."""
        # Arrange
        user_id = "test-user-id"
        topic_id = mock_topic.id
        mock_task.topic_id = topic_id

        # Mock the database query chain
        query = mock_db.query.return_value
        filter_result = query.filter.return_value
        filter_result.filter.return_value = filter_result
        order_result = filter_result.order_by.return_value
        offset_result = order_result.offset.return_value
        limit_result = offset_result.limit.return_value
        limit_result.all.return_value = [mock_task]

        # Act
        tasks = task_repo.list_tasks(
            user_id=user_id,
            topic_id=topic_id,
        )

        # Assert
        assert len(tasks) == 1
        assert tasks[0] == mock_task
        mock_db.query.assert_called_once_with(Task)
        query.filter.assert_called()
        filter_result.order_by.assert_called()

    def test_count_tasks_with_topic_filter(
        self,
        task_repo: TaskRepository,
        mock_db: Session,
        mock_task: Task,
        mock_topic: Topic,
    ):
        """Test counting tasks with topic filter."""
        # Arrange
        user_id = "test-user-id"
        topic_id = mock_topic.id
        mock_task.topic_id = topic_id

        # Mock the database query chain
        query = mock_db.query.return_value
        filter_result = query.filter.return_value
        filter_result.filter.return_value = filter_result
        filter_result.count.return_value = 1

        # Act
        count = task_repo.count_tasks(
            user_id=user_id,
            topic_id=topic_id,
        )

        # Assert
        assert count == 1
        mock_db.query.assert_called_once_with(Task)
        query.filter.assert_called()

    def test_get_tasks_by_topic(
        self,
        task_repo: TaskRepository,
        mock_db: Session,
        mock_task: Task,
        mock_topic: Topic,
    ):
        """Test getting tasks by topic."""
        # Arrange
        user_id = "test-user-id"
        topic_id = mock_topic.id
        mock_task.topic_id = topic_id
        query = mock_db.query.return_value
        filter_result = query.filter.return_value
        order_result = filter_result.order_by.return_value
        offset_result = order_result.offset.return_value
        limit_result = offset_result.limit.return_value
        limit_result.all.return_value = [mock_task]

        # Act
        tasks = task_repo.get_tasks_by_topic(
            topic_id=topic_id,
            user_id=user_id,
        )

        # Assert
        assert len(tasks) == 1
        assert tasks[0].topic_id == topic_id
        mock_db.query.assert_called_once_with(Task)

    def test_update_task_topic(
        self,
        task_repo: TaskRepository,
        mock_db: Session,
        mock_task: Task,
        mock_topic: Topic,
    ):
        """Test updating a task's topic."""
        # Arrange
        task_id = mock_task.id
        user_id = "test-user-id"
        topic_id = mock_topic.id
        mock_db.query.return_value.filter.return_value.first.return_value = (
            mock_task
        )

        # Act
        task = task_repo.update_topic(
            task_id=task_id,
            user_id=user_id,
            topic_id=topic_id,
        )

        # Assert
        assert task is not None
        assert task.topic_id == topic_id
        mock_db.add.assert_called_once_with(mock_task)
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once_with(mock_task)

    def test_update_task_topic_remove(
        self,
        task_repo: TaskRepository,
        mock_db: Session,
        mock_task: Task,
    ):
        """Test removing a task's topic."""
        # Arrange
        task_id = mock_task.id
        user_id = "test-user-id"
        mock_task.topic_id = 1  # Initial topic
        mock_db.query.return_value.filter.return_value.first.return_value = (
            mock_task
        )

        # Act
        task = task_repo.update_topic(
            task_id=task_id,
            user_id=user_id,
            topic_id=None,
        )

        # Assert
        assert task is not None
        assert task.topic_id is None
        mock_db.add.assert_called_once_with(mock_task)
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once_with(mock_task)

    def test_update_task_topic_not_found(
        self,
        task_repo: TaskRepository,
        mock_db: Session,
    ):
        """Test updating topic for a non-existent task.

        Should raise TaskReferenceError.
        """
        # Arrange
        mock_db.query.return_value.filter.return_value.first.return_value = (
            None
        )

        # Act & Assert
        with pytest.raises(TaskReferenceError):
            task_repo.update_topic(1, "test-user-id", 1)

    def test_create_task_with_invalid_topic(
        self,
        task_repo: TaskRepository,
        mock_db: Session,
    ):
        """Test creating a task with an invalid topic ID."""
        # Arrange
        content = "Test Task"
        user_id = "test-user-id"
        topic_id = 999  # Non-existent topic ID

        # Mock the database to raise IntegrityError
        mock_db.add.return_value = None
        mock_db.commit.side_effect = IntegrityError(
            "mock", "mock", "mock"
        )
        mock_db.rollback.return_value = None

        # Act & Assert
        with pytest.raises(TaskValidationError) as exc:
            task_repo.create(
                {
                    "content": content,
                    "user_id": user_id,
                    "topic_id": topic_id,
                }
            )
        assert "Invalid topic" in str(exc.value)
        mock_db.rollback.assert_called_once()

    def test_list_tasks_with_invalid_filters(
        self,
        task_repo: TaskRepository,
        mock_db: Session,
    ):
        """Test listing tasks with invalid filter combinations."""
        # Arrange
        user_id = "test-user-id"

        # Mock the database query chain
        query = mock_db.query.return_value
        filter_result = query.filter.return_value
        filter_result.filter.return_value = filter_result
        order_result = filter_result.order_by.return_value
        offset_result = order_result.offset.return_value
        limit_result = offset_result.limit.return_value
        limit_result.all.return_value = []

        # Act
        tasks = task_repo.list_tasks(
            user_id=user_id,
            topic_id=999,  # Non-existent topic
            status=TaskStatus.DONE,
            priority=TaskPriority.HIGH,
            due_before=datetime.now(),
            due_after=datetime.now() - timedelta(days=1),
        )

        # Assert
        assert (
            len(tasks) == 0
        )  # No tasks found with invalid filters

    def test_get_tasks_by_topic_not_found(
        self,
        task_repo: TaskRepository,
        mock_db: Session,
    ):
        """Test getting tasks for a non-existent topic."""
        # Arrange
        user_id = "test-user-id"
        topic_id = 999

        # Mock the database query chain
        query = mock_db.query.return_value
        filter_result = query.filter.return_value
        filter_result.filter.return_value = filter_result
        order_result = filter_result.order_by.return_value
        offset_result = order_result.offset.return_value
        limit_result = offset_result.limit.return_value
        limit_result.all.return_value = []

        # Act
        tasks = task_repo.get_tasks_by_topic(
            user_id=user_id,
            topic_id=topic_id,
        )

        # Assert
        assert len(tasks) == 0
        mock_db.query.assert_called_once_with(Task)

    def test_update_task_topic_invalid_topic(
        self,
        task_repo: TaskRepository,
        mock_db: Session,
        mock_task: Task,
    ):
        """Test updating a task with an invalid topic ID."""
        # Arrange
        user_id = "test-user-id"
        task_id = 1
        topic_id = 999  # Non-existent topic ID

        # Mock the database query
        query = mock_db.query.return_value
        filter_result = query.filter.return_value
        filter_result.filter.return_value = filter_result
        filter_result.first.return_value = mock_task

        # Mock commit to raise IntegrityError
        mock_db.commit.side_effect = IntegrityError(
            "mock", "mock", "mock"
        )
        mock_db.rollback.return_value = None

        # Act & Assert
        with pytest.raises(TaskValidationError) as exc:
            task_repo.update_topic(
                task_id, user_id, topic_id
            )
        assert "Invalid topic" in str(exc.value)
        mock_db.rollback.assert_called_once()

    def test_update_task_topic_remove_not_found(
        self,
        task_repo: TaskRepository,
        mock_db: Session,
    ):
        """Test removing topic from a non-existent task.

        Should raise TaskReferenceError.
        """
        # Arrange
        mock_db.query.return_value.filter.return_value.first.return_value = (
            None
        )

        # Act & Assert
        with pytest.raises(TaskReferenceError):
            task_repo.update_topic(1, "test-user-id", None)
