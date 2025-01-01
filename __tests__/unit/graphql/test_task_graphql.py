"""Tests for Task GraphQL functionality."""

from datetime import datetime
import pytest
from unittest.mock import Mock
from fastapi import HTTPException
from domain.task import TaskData, TaskStatus, TaskPriority
from domain.user import UserData
from schemas.graphql.types.Task import (
    Task,
    TaskConnection,
    TaskInput,
    TaskUpdateInput,
)
from schemas.graphql.mutations.TaskMutation import (
    TaskMutation,
)
from schemas.graphql.Query import Query
from services.TaskService import TaskService


@pytest.fixture
def mock_user():
    """Create a mock user."""
    return UserData(
        id=1,
        username="testuser",
        key_id="12345678-1234-5678-1234-567812345678",
        user_secret=(
            "$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY.5AuXxz/pmpy."
        ),
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )


@pytest.fixture
def mock_task(mock_user):
    """Create a mock task."""
    return TaskData(
        id=1,
        title="Test Task",
        description="Test Description",
        status=TaskStatus.TODO,
        priority=TaskPriority.MEDIUM,
        user_id=str(mock_user.id),
        parent_id=None,
        created_at=datetime.now(),
        updated_at=datetime.now(),
        tags=[],
        due_date=None,
    )


@pytest.fixture
def mock_info(mock_user, mocker):
    """Create a mock GraphQL info object."""
    db = Mock()
    info = Mock()
    info.context = {
        "db": db,
        "user": mock_user,
    }
    return info


def test_create_task_mutation(
    mocker, mock_user, mock_task, mock_info
):
    """Test creating a task."""
    # Mock the task service
    task_service = mocker.Mock(spec=TaskService)
    task_service.create_task.return_value = mock_task

    # Mock get_db_from_context and TaskService
    mocker.patch(
        "schemas.graphql.mutations.TaskMutation.get_db_from_context",
        return_value=mock_info.context["db"],
    )
    mocker.patch(
        "schemas.graphql.mutations.TaskMutation.TaskService",
        return_value=task_service,
    )

    # Create mutation
    mutation = TaskMutation()

    # Create input
    task_input = TaskInput(
        title="Test Task",
        description="Test Description",
        status=TaskStatus.TODO,
        priority=TaskPriority.MEDIUM,
    )

    # Execute mutation
    result = mutation.create_task(mock_info, task_input)

    # Verify result
    assert isinstance(result, Task)
    assert result._domain.title == "Test Task"
    assert result._domain.description == "Test Description"
    assert result._domain.status == TaskStatus.TODO
    assert result._domain.priority == TaskPriority.MEDIUM


def test_update_task_mutation(
    mocker, mock_user, mock_task, mock_info
):
    """Test updating a task."""
    # Mock the task service
    task_service = mocker.Mock(spec=TaskService)
    task_service.get_task.return_value = mock_task

    # Create an updated task with new values
    updated_task = TaskData(
        id=mock_task.id,
        title="Updated Task",
        description=mock_task.description,
        status=TaskStatus.IN_PROGRESS,
        priority=mock_task.priority,
        user_id=mock_task.user_id,
        created_at=mock_task.created_at,
        updated_at=mock_task.updated_at,
    )
    task_service.update_task.return_value = updated_task

    # Mock get_db_from_context and TaskService
    mocker.patch(
        "schemas.graphql.mutations.TaskMutation.get_db_from_context",
        return_value=mock_info.context["db"],
    )
    mocker.patch(
        "schemas.graphql.mutations.TaskMutation.TaskService",
        return_value=task_service,
    )

    # Create mutation
    mutation = TaskMutation()

    # Create input
    update_input = TaskUpdateInput(
        title="Updated Task",
        status=TaskStatus.IN_PROGRESS,
    )

    # Execute mutation
    result = mutation.update_task(
        mock_info, 1, update_input
    )

    # Verify result
    assert isinstance(result, Task)
    assert (
        result._domain.title == "Updated Task"
    )  # Check new title
    assert (
        result._domain.status == TaskStatus.IN_PROGRESS
    )  # Check new status

    # Verify service calls
    task_service.get_task.assert_called_once_with(
        1, mock_user.id
    )
    task_service.update_task.assert_called_once()


def test_get_task_query(
    mocker, mock_user, mock_task, mock_info
):
    """Test getting a task by ID."""
    # Mock the task service
    task_service = mocker.Mock(spec=TaskService)
    task_service.get_task.return_value = mock_task

    # Mock get_db_from_context and TaskService
    mocker.patch(
        "schemas.graphql.Query.get_db_from_context",
        return_value=mock_info.context["db"],
    )
    mocker.patch(
        "schemas.graphql.Query.TaskService",
        return_value=task_service,
    )

    # Create query
    query = Query()

    # Execute query
    result = query.get_task(mock_info, 1)

    # Verify result
    assert isinstance(result, Task)
    assert result._domain.id == 1
    assert result._domain.title == "Test Task"


def test_list_tasks_query(
    mocker, mock_user, mock_task, mock_info
):
    """Test listing tasks."""
    # Mock the task service
    task_service = mocker.Mock(spec=TaskService)
    task_service.list_tasks.return_value = {
        "items": [mock_task],
        "total": 1,
        "page": 1,
        "size": 10,
    }

    # Mock get_db_from_context and TaskService
    mocker.patch(
        "schemas.graphql.Query.get_db_from_context",
        return_value=mock_info.context["db"],
    )
    mocker.patch(
        "schemas.graphql.Query.TaskService",
        return_value=task_service,
    )

    # Create query
    query = Query()

    # Execute query
    result = query.list_tasks(mock_info, page=1, size=10)

    # Verify result
    assert isinstance(result, TaskConnection)
    assert len([task for task in result._items]) == 1
    assert result._total == 1
    assert result._page == 1
    assert result._size == 10


def test_get_subtasks_query(
    mocker, mock_user, mock_task, mock_info
):
    """Test getting subtasks."""
    # Mock the task service
    task_service = mocker.Mock(spec=TaskService)
    task_service.list_tasks.return_value = {
        "items": [mock_task],
        "total": 1,
        "page": 1,
        "size": 10,
    }

    # Mock get_db_from_context and TaskService
    mocker.patch(
        "schemas.graphql.Query.get_db_from_context",
        return_value=mock_info.context["db"],
    )
    mocker.patch(
        "schemas.graphql.Query.TaskService",
        return_value=task_service,
    )

    # Create query
    query = Query()

    # Execute query
    result = query.get_subtasks(
        mock_info, 1, page=1, size=10
    )

    # Verify result
    assert isinstance(result, TaskConnection)
    assert len([task for task in result._items]) == 1
    assert result._total == 1
    assert result._page == 1
    assert result._size == 10


def test_unauthorized_access(mocker):
    """Test unauthorized access."""
    # Create query
    query = Query()

    # Create mock info without user
    info = Mock()
    info.context = {"db": Mock(), "user": None}

    # Execute query without user
    with pytest.raises(HTTPException) as exc:
        query.get_task(info, 1)
    assert exc.value.status_code == 401
