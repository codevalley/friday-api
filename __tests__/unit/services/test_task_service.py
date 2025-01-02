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
def task_service(mock_db, mock_task_repo):
    """Create a TaskService instance with mocked dependencies."""
    service = TaskService(db=mock_db)
    service.task_repo = mock_task_repo
    return service


@pytest.fixture
def sample_task_data():
    """Create sample task data."""
    now = datetime.now(timezone.utc)
    return {
        "id": 1,
        "title": "Test Task",
        "description": "Test Description",
        "status": TaskStatus.TODO,
        "priority": TaskPriority.MEDIUM,
        "user_id": "test-user-id",
        "created_at": now,
        "updated_at": None,
        "tags": ["test", "sample"],
        "due_date": now + timedelta(days=30),
        "parent_id": None,
    }


def test_create_task_success(
    task_service,
    sample_task_data,
    sample_user,
):
    """Test successful task creation."""
    # Configure mock to return proper task data
    mock_task = Mock()
    mock_task.to_dict.return_value = sample_task_data
    task_service.task_repo.create.return_value = mock_task

    # Create a task
    result = task_service.create_task(
        TaskCreate(**sample_task_data),
        sample_user.id,
    )

    # Verify the response model validation worked
    assert isinstance(result, TaskResponse)
    assert result.title == sample_task_data["title"]
    assert (
        result.description
        == sample_task_data["description"]
    )
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
        title="Test",
        description="Test",
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
    mock_task.to_dict.return_value = sample_task_data
    mock_task.id = sample_task_data["id"]
    mock_task.created_at = sample_task_data["created_at"]
    mock_task_repo.get_by_user.return_value = mock_task

    # Call service
    result = task_service.get_task(1, "test-user-id")

    # Verify
    assert isinstance(result, TaskResponse)
    assert result.title == sample_task_data["title"]
    assert (
        result.description
        == sample_task_data["description"]
    )
    mock_task_repo.get_by_user.assert_called_once_with(
        1, "test-user-id"
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
    mock_task.to_dict.return_value = sample_task_data
    mock_task.id = sample_task_data["id"]
    mock_task.created_at = sample_task_data["created_at"]
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
        "title": "Updated Title",
    }
    mock_task.to_dict.return_value = updated_data
    mock_task.id = updated_data["id"]
    mock_task.created_at = updated_data["created_at"]
    mock_task_repo.get_by_user.return_value = mock_task

    # Create update data
    update_data = TaskUpdate(title="Updated Title")

    # Call service
    result = task_service.update_task(
        1,
        "test-user-id",
        update_data,
    )

    # Verify
    assert isinstance(result, TaskResponse)
    assert result.title == "Updated Title"
    mock_task.update.assert_called_once_with(
        {"title": "Updated Title"}
    )
    mock_db.commit.assert_called_once()


def test_update_task_not_found(
    task_service, mock_task_repo
):
    """Test task update when task doesn't exist."""
    mock_task_repo.get_by_user.return_value = None

    update_data = TaskUpdate(title="New Title")

    with pytest.raises(HTTPException) as exc:
        task_service.update_task(
            1, "test-user-id", update_data
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
    mock_task.to_dict.return_value = updated_data
    mock_task.id = updated_data["id"]
    mock_task.created_at = updated_data["created_at"]
    mock_task_repo.update_status.return_value = mock_task

    # Call service
    result = task_service.update_task_status(
        1, "test-user-id", TaskStatus.IN_PROGRESS
    )

    # Verify
    assert isinstance(result, TaskResponse)
    assert result.status == TaskStatus.IN_PROGRESS
    mock_task_repo.update_status.assert_called_once_with(
        task_id=1,
        user_id="test-user-id",
        new_status=TaskStatus.IN_PROGRESS,
    )
    mock_db.commit.assert_called_once()


def test_get_subtasks_success(
    task_service, mock_task_repo, sample_task_data
):
    """Test successful subtask retrieval."""
    # Setup mocks
    parent_task = Mock()
    mock_task_repo.get_by_user.return_value = parent_task

    subtask = Mock()
    subtask_data = {
        **sample_task_data,
        "id": 2,
        "parent_id": 1,
    }
    subtask.to_dict.return_value = subtask_data
    subtask.id = subtask_data["id"]
    subtask.created_at = subtask_data["created_at"]
    mock_task_repo.get_subtasks.return_value = [subtask]

    # Call service
    result = task_service.get_subtasks(
        1, "test-user-id", page=1, size=50
    )

    # Verify
    assert len(result["items"]) == 1
    assert isinstance(result["items"][0], TaskResponse)
    assert result["items"][0].parent_id == 1
    mock_task_repo.get_subtasks.assert_called_once_with(
        task_id=1,
        user_id="test-user-id",
        skip=0,
        limit=50,
    )
