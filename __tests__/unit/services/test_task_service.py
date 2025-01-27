"""Unit tests for the TaskService."""

import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import Mock, patch
from fastapi import HTTPException

from services.TaskService import TaskService
from domain.values import TaskStatus, TaskPriority
from domain.exceptions import TaskValidationError
from schemas.pydantic.TaskSchema import (
    TaskCreate,
    TaskUpdate,
    TaskResponse,
)


@pytest.fixture
def mock_db():
    """Create a mock database session."""
    return Mock()


@pytest.fixture
def mock_task_repo():
    """Create a mock task repository."""
    with patch(
        "services.TaskService.TaskRepository"
    ) as mock:
        yield mock.return_value


@pytest.fixture
def mock_queue_service():
    """Create a mock queue service."""
    with patch("services.TaskService.QueueService") as mock:
        yield mock.return_value


@pytest.fixture
def task_service(
    mock_db, mock_task_repo, mock_queue_service
):
    """Create a TaskService instance with mocked dependencies."""
    service = TaskService(db=mock_db)
    service.task_repo = mock_task_repo
    service.queue_service = mock_queue_service
    return service


@pytest.fixture
def sample_task_data():
    """Create sample task data."""
    now = datetime.now(timezone.utc)
    return {
        "id": 1,
        "content": "Test Task Content",
        "status": TaskStatus.TODO,
        "priority": TaskPriority.MEDIUM,
        "user_id": "test-user-id",
        "created_at": now,
        "updated_at": None,
        "tags": ["test", "sample"],
        "due_date": now + timedelta(days=30),
        "parent_id": None,
        "topic_id": None,
        "topic": None,
        "processing_status": "not_processed",
        "enrichment_data": None,
        "processed_at": None,
    }


def test_create_task_success(
    task_service,
    sample_task_data,
    sample_user,
):
    """Test successful task creation."""
    # Configure mock to return proper task data
    mock_task = Mock()
    mock_task.id = sample_task_data["id"]
    mock_task.content = sample_task_data["content"]
    mock_task.status = sample_task_data["status"]
    mock_task.priority = sample_task_data["priority"]
    mock_task.user_id = sample_user.id
    mock_task.created_at = sample_task_data["created_at"]
    mock_task.updated_at = None
    mock_task.tags = sample_task_data["tags"]
    mock_task.due_date = sample_task_data["due_date"]
    mock_task.parent_id = sample_task_data["parent_id"]
    mock_task.topic_id = sample_task_data["topic_id"]
    mock_task.topic = sample_task_data["topic"]
    mock_task.processing_status = "not_processed"
    mock_task.enrichment_data = None
    mock_task.processed_at = None
    mock_task.to_dict.return_value = sample_task_data
    task_service.task_repo.create.return_value = mock_task

    # Create a task
    result = task_service.create_task(
        sample_user.id,
        TaskCreate(**sample_task_data),
    )

    # Verify the response model validation worked
    assert isinstance(result, TaskResponse)
    assert result.content == sample_task_data["content"]
    assert result.status == sample_task_data["status"]
    assert result.priority == sample_task_data["priority"]
    # Verify timestamp fields are present and timezone-aware
    assert result.created_at is not None
    assert result.created_at.tzinfo is not None
    assert (
        result.updated_at is None
    )  # Should be None for new tasks


def test_create_task_validation_error(
    task_service, mock_task_repo
):
    """Test task creation with validation error."""
    mock_task_repo.create.side_effect = TaskValidationError(
        "Invalid task data"
    )

    task_data = TaskCreate(
        content="Test Content",
    )

    with pytest.raises(HTTPException) as exc:
        task_service.create_task(
            task_data=task_data,
            user_id="test-user",
        )

    assert exc.value.status_code == 400


def test_get_task_success(
    task_service, mock_task_repo, sample_task_data
):
    """Test successful task retrieval."""
    # Setup mock
    mock_task = Mock()
    mock_task.id = sample_task_data["id"]
    mock_task.content = sample_task_data["content"]
    mock_task.status = sample_task_data["status"]
    mock_task.priority = sample_task_data["priority"]
    mock_task.user_id = "test-user-id"
    mock_task.created_at = sample_task_data["created_at"]
    mock_task.updated_at = None
    mock_task.tags = sample_task_data["tags"]
    mock_task.due_date = sample_task_data["due_date"]
    mock_task.parent_id = sample_task_data["parent_id"]
    mock_task.topic_id = sample_task_data["topic_id"]
    mock_task.topic = sample_task_data["topic"]
    mock_task.processing_status = "not_processed"
    mock_task.enrichment_data = None
    mock_task.processed_at = None
    mock_task.to_dict.return_value = sample_task_data
    mock_task_repo.get_by_user.return_value = mock_task

    # Call service
    result = task_service.get_task(1, "test-user-id")

    # Verify
    assert isinstance(result, TaskResponse)
    assert result.content == sample_task_data["content"]
    mock_task_repo.get_by_user.assert_called_once_with(
        "test-user-id", 1
    )


def test_get_task_not_found(task_service, mock_task_repo):
    """Test task retrieval when task doesn't exist."""
    mock_task_repo.get_by_user.return_value = None

    with pytest.raises(HTTPException) as exc:
        task_service.get_task(1, "test-user-id")

    assert exc.value.status_code == 404


def test_list_tasks_success(
    task_service, mock_task_repo, sample_task_data
):
    """Test successful task listing."""
    # Setup mock
    mock_task = Mock()
    mock_task.id = sample_task_data["id"]
    mock_task.content = sample_task_data["content"]
    mock_task.status = sample_task_data["status"]
    mock_task.priority = sample_task_data["priority"]
    mock_task.user_id = "test-user-id"
    mock_task.created_at = sample_task_data["created_at"]
    mock_task.updated_at = None
    mock_task.tags = sample_task_data["tags"]
    mock_task.due_date = sample_task_data["due_date"]
    mock_task.parent_id = sample_task_data["parent_id"]
    mock_task.topic_id = sample_task_data["topic_id"]
    mock_task.topic = sample_task_data["topic"]
    mock_task.processing_status = "not_processed"
    mock_task.enrichment_data = None
    mock_task.processed_at = None
    mock_task.to_dict.return_value = sample_task_data
    mock_task_repo.list_tasks.return_value = [mock_task]
    mock_task_repo.count_tasks.return_value = 1

    # Call service
    result = task_service.list_tasks(
        user_id="test-user-id",
        status=TaskStatus.TODO,
        page=1,
        size=50,
    )

    # Verify
    assert len(result["items"]) == 1
    assert isinstance(result["items"][0], TaskResponse)
    assert result["total"] == 1
    assert result["page"] == 1
    assert result["size"] == 50
    assert result["pages"] == 1


def test_update_task_success(
    task_service, mock_db, mock_task_repo, sample_task_data
):
    """Test successful task update."""
    # Setup mock
    mock_task = Mock()
    updated_data = {
        **sample_task_data,
        "content": "Updated Task Content",
    }
    mock_task.id = updated_data["id"]
    mock_task.content = updated_data["content"]
    mock_task.status = updated_data["status"]
    mock_task.priority = updated_data["priority"]
    mock_task.user_id = "test-user-id"
    mock_task.created_at = updated_data["created_at"]
    mock_task.updated_at = None
    mock_task.tags = updated_data["tags"]
    mock_task.due_date = updated_data["due_date"]
    mock_task.parent_id = updated_data["parent_id"]
    mock_task.topic_id = updated_data["topic_id"]
    mock_task.topic = updated_data["topic"]
    mock_task.processing_status = "not_processed"
    mock_task.enrichment_data = None
    mock_task.processed_at = None
    mock_task.to_dict.return_value = updated_data
    mock_task_repo.get_by_user.return_value = mock_task
    mock_task_repo.update.return_value = mock_task

    # Create update data
    update_data = TaskUpdate(content="Updated Task Content")

    # Call service
    result = task_service.update_task(
        1, update_data, "test-user-id"
    )

    # Verify
    assert result.content == "Updated Task Content"
    mock_task_repo.update.assert_called_once()
    mock_db.commit.assert_called_once()


def test_update_task_not_found(
    task_service, mock_task_repo
):
    """Test task update when task doesn't exist."""
    mock_task_repo.get_by_user.return_value = None

    update_data = TaskUpdate(content="New Content")

    with pytest.raises(HTTPException) as exc:
        task_service.update_task(
            1, update_data, "test-user-id"
        )

    assert exc.value.status_code == 404


def test_delete_task_success(
    task_service, mock_db, mock_task_repo, sample_task_data
):
    """Test successful task deletion."""
    # Setup mock
    mock_task = Mock()
    mock_task.to_dict.return_value = sample_task_data
    mock_task_repo.get_by_user.return_value = mock_task

    # Call service
    result = task_service.delete_task(1, "test-user-id")

    # Verify
    assert result is True
    mock_task_repo.delete.assert_called_once_with(1)
    mock_db.commit.assert_called_once()


def test_delete_task_not_found(
    task_service, mock_task_repo
):
    """Test task deletion when task doesn't exist."""
    mock_task_repo.get_by_user.return_value = None

    with pytest.raises(HTTPException) as exc:
        task_service.delete_task(1, "test-user-id")

    assert exc.value.status_code == 404


def test_update_task_status_success(
    task_service, mock_db, mock_task_repo, sample_task_data
):
    """Test successful task status update."""
    # Setup mock
    mock_task = Mock()
    updated_data = {
        **sample_task_data,
        "status": TaskStatus.IN_PROGRESS,
    }
    mock_task.id = updated_data["id"]
    mock_task.content = updated_data["content"]
    mock_task.status = updated_data["status"]
    mock_task.priority = updated_data["priority"]
    mock_task.user_id = "test-user-id"
    mock_task.created_at = updated_data["created_at"]
    mock_task.updated_at = None
    mock_task.tags = updated_data["tags"]
    mock_task.due_date = updated_data["due_date"]
    mock_task.parent_id = updated_data["parent_id"]
    mock_task.topic_id = updated_data["topic_id"]
    mock_task.topic = updated_data["topic"]
    mock_task.processing_status = "not_processed"
    mock_task.enrichment_data = None
    mock_task.processed_at = None
    mock_task.to_dict.return_value = updated_data
    mock_task_repo.update_status.return_value = mock_task

    # Call service
    result = task_service.update_task_status(
        1, "test-user-id", TaskStatus.IN_PROGRESS
    )

    # Verify
    assert result.status == TaskStatus.IN_PROGRESS
    mock_task_repo.update_status.assert_called_once()
    mock_db.commit.assert_called_once()


def test_get_subtasks_success(
    task_service, mock_task_repo, sample_task_data
):
    """Test successful subtask retrieval."""
    # Setup mock
    mock_task = Mock()
    mock_task.id = sample_task_data["id"]
    mock_task.content = sample_task_data["content"]
    mock_task.status = sample_task_data["status"]
    mock_task.priority = sample_task_data["priority"]
    mock_task.user_id = "test-user-id"
    mock_task.created_at = sample_task_data["created_at"]
    mock_task.updated_at = None
    mock_task.tags = sample_task_data["tags"]
    mock_task.due_date = sample_task_data["due_date"]
    mock_task.parent_id = sample_task_data["parent_id"]
    mock_task.topic_id = sample_task_data["topic_id"]
    mock_task.topic = sample_task_data["topic"]
    mock_task.processing_status = "not_processed"
    mock_task.enrichment_data = None
    mock_task.processed_at = None
    mock_task.to_dict.return_value = sample_task_data
    mock_task_repo.get_subtasks.return_value = [mock_task]
    mock_task_repo.count_subtasks.return_value = 1

    # Call service
    result = task_service.get_subtasks(
        1, "test-user-id", page=1, size=50
    )

    # Verify
    assert len(result["items"]) == 1
    assert isinstance(result["items"][0], TaskResponse)
    assert result["total"] == 1
    assert result["page"] == 1
    assert result["size"] == 50
    assert result["pages"] == 1


def test_update_task_topic_success(
    task_service, mock_db, mock_task_repo, sample_task_data
):
    """Test successful task topic update."""
    # Setup mock
    mock_task = Mock()
    mock_topic = Mock()
    mock_topic.id = 123
    mock_topic.name = "Test Topic"
    mock_topic.icon = "📝"
    mock_topic.user_id = "test-user-id"
    mock_topic.created_at = sample_task_data["created_at"]
    mock_topic.updated_at = None
    mock_topic.to_dict.return_value = {
        "id": 123,
        "name": "Test Topic",
        "icon": "📝",
        "user_id": "test-user-id",
        "created_at": sample_task_data["created_at"],
        "updated_at": None,
    }

    updated_data = {
        **sample_task_data,
        "content": "Test Task Content",
        "status": "todo",
        "priority": "medium",
        "user_id": "test-user-id",
        "topic_id": 123,
        "topic": mock_topic.to_dict(),
    }
    mock_task.id = updated_data["id"]
    mock_task.content = updated_data["content"]
    mock_task.status = updated_data["status"]
    mock_task.priority = updated_data["priority"]
    mock_task.user_id = "test-user-id"
    mock_task.created_at = updated_data["created_at"]
    mock_task.updated_at = None
    mock_task.tags = updated_data["tags"]
    mock_task.due_date = updated_data["due_date"]
    mock_task.parent_id = updated_data["parent_id"]
    mock_task.topic_id = updated_data["topic_id"]
    mock_task.topic = mock_topic
    mock_task.processing_status = "not_processed"
    mock_task.enrichment_data = None
    mock_task.processed_at = None
    mock_task.to_dict.return_value = updated_data
    mock_task_repo.update_topic.return_value = mock_task

    # Call service
    result = task_service.update_task_topic(
        1,
        "test-user-id",
        123,
    )

    # Verify
    assert result.topic_id == 123
    assert result.topic.name == "Test Topic"
    mock_task_repo.update_topic.assert_called_once()
    mock_db.commit.assert_called_once()


def test_update_task_topic_remove(
    task_service, mock_db, mock_task_repo, sample_task_data
):
    """Test removing task topic."""
    # Setup mock
    mock_task = Mock()
    updated_data = {
        **sample_task_data,
        "content": "Test Task Content",
        "status": "todo",
        "priority": "medium",
        "user_id": "test-user-id",
        "topic_id": None,
        "topic": None,
    }
    mock_task.id = updated_data["id"]
    mock_task.content = updated_data["content"]
    mock_task.status = updated_data["status"]
    mock_task.priority = updated_data["priority"]
    mock_task.user_id = "test-user-id"
    mock_task.created_at = updated_data["created_at"]
    mock_task.updated_at = None
    mock_task.tags = updated_data["tags"]
    mock_task.due_date = updated_data["due_date"]
    mock_task.parent_id = updated_data["parent_id"]
    mock_task.topic_id = updated_data["topic_id"]
    mock_task.topic = updated_data["topic"]
    mock_task.processing_status = "not_processed"
    mock_task.enrichment_data = None
    mock_task.processed_at = None
    mock_task.to_dict.return_value = updated_data
    mock_task_repo.update_topic.return_value = mock_task

    # Call service
    result = task_service.update_task_topic(
        1,
        "test-user-id",
        None,
    )

    # Verify
    assert result.topic_id is None
    assert result.topic is None
    mock_task_repo.update_topic.assert_called_once()
    mock_db.commit.assert_called_once()


def test_get_tasks_by_topic_success(
    task_service, mock_task_repo, sample_task_data
):
    """Test successful task listing by topic."""
    # Setup mock
    mock_task = Mock()
    mock_task.id = sample_task_data["id"]
    mock_task.content = sample_task_data["content"]
    mock_task.status = sample_task_data["status"]
    mock_task.priority = sample_task_data["priority"]
    mock_task.user_id = "test-user-id"
    mock_task.created_at = sample_task_data["created_at"]
    mock_task.updated_at = None
    mock_task.tags = sample_task_data["tags"]
    mock_task.due_date = sample_task_data["due_date"]
    mock_task.parent_id = sample_task_data["parent_id"]
    mock_task.topic_id = sample_task_data["topic_id"]
    mock_task.topic = sample_task_data["topic"]
    mock_task.processing_status = "not_processed"
    mock_task.enrichment_data = None
    mock_task.processed_at = None
    mock_task.to_dict.return_value = sample_task_data
    mock_task_repo.get_tasks_by_topic.return_value = [
        mock_task
    ]
    mock_task_repo.count_tasks.return_value = 1

    # Call service
    result = task_service.get_tasks_by_topic(
        123,
        "test-user-id",
        page=1,
        size=50,
    )

    # Verify
    assert len(result["items"]) == 1
    assert result["total"] == 1
    mock_task_repo.get_tasks_by_topic.assert_called_once_with(
        topic_id=123,
        user_id="test-user-id",
        skip=0,
        limit=50,
    )
    mock_task_repo.count_tasks.assert_called_once_with(
        user_id="test-user-id",
        topic_id=123,
    )


def test_get_tasks_by_topic_not_found(
    task_service, mock_task_repo
):
    """Test task listing by topic when no tasks exist."""
    mock_task_repo.list_tasks.return_value = []
    mock_task_repo.count_tasks.return_value = 0

    result = task_service.get_tasks_by_topic(
        123,
        "test-user-id",
        page=1,
        size=50,
    )

    assert len(result["items"]) == 0
    assert result["total"] == 0
    assert result["page"] == 1
    assert result["size"] == 50
    assert result["pages"] == 0
