"""Tests for Task GraphQL functionality."""

from datetime import datetime, timedelta, timezone
import pytest
from unittest.mock import Mock
from fastapi import HTTPException
from domain.task import TaskData, TaskStatus, TaskPriority
from domain.user import UserData
from domain.exceptions import (
    TaskStatusError,
    TaskReferenceError,
    TaskContentError,
    TaskParentError,
)
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
    assert result.title == "Test Task"
    assert result.description == "Test Description"
    assert result.status == TaskStatus.TODO
    assert result.priority == TaskPriority.MEDIUM


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
    assert result.title == "Updated Task"
    assert result.status == TaskStatus.IN_PROGRESS


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
    assert result.id == 1
    assert result.title == mock_task.title
    assert result.description == mock_task.description


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


def test_unauthorized_access(mocker, mock_info):
    """Test unauthorized access."""
    # Remove user from context
    mock_info.context["user"] = None

    # Create mutation
    mutation = TaskMutation()

    # Create input
    task_input = TaskInput(
        title="Test Task",
        description="Test Description",
        status=TaskStatus.TODO,
        priority=TaskPriority.MEDIUM,
    )

    # Execute mutation and verify it raises HTTPException
    with pytest.raises(HTTPException) as exc:
        mutation.create_task(mock_info, task_input)
    assert exc.value.status_code == 401
    assert exc.value.detail["code"] == "UNAUTHORIZED"


def test_create_task_validation_error(
    mocker, mock_user, mock_info
):
    """Test task creation with validation error."""
    # Mock the task service
    task_service = mocker.Mock(spec=TaskService)
    task_service.create_task.side_effect = TaskContentError(
        "title cannot be empty"
    )

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

    # Create input with empty title
    task_input = TaskInput(
        title="",
        description="Test Description",
        status=TaskStatus.TODO,
        priority=TaskPriority.MEDIUM,
    )

    # Execute mutation and verify it raises HTTPException
    with pytest.raises(HTTPException) as exc:
        mutation.create_task(mock_info, task_input)
    assert exc.value.status_code == 400
    assert "title cannot be empty" in str(exc.value.detail)


def test_update_task_invalid_status(
    mocker, mock_user, mock_task, mock_info
):
    """Test updating a task with invalid status transition."""
    # Mock the task service
    task_service = mocker.Mock(spec=TaskService)
    task_service.get_task.return_value = mock_task
    task_service.update_task.side_effect = TaskStatusError(
        "Invalid status transition"
    )

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

    # Create input with invalid status transition
    update_input = TaskUpdateInput(
        status=TaskStatus.DONE,
    )

    # Execute mutation and verify it raises HTTPException
    with pytest.raises(HTTPException) as exc:
        mutation.update_task(mock_info, 1, update_input)
    assert exc.value.status_code == 400
    assert "Invalid status transition" in str(
        exc.value.detail
    )


def test_update_task_invalid_parent(
    mocker, mock_user, mock_task, mock_info
):
    """Test updating a task with invalid parent."""
    # Mock the task service
    task_service = mocker.Mock(spec=TaskService)
    task_service.get_task.return_value = mock_task
    task_service.update_task.side_effect = TaskParentError(
        "Invalid parent task"
    )

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

    # Create input with invalid parent
    update_input = TaskUpdateInput(
        parent_id=999,
    )

    # Execute mutation and verify it raises HTTPException
    with pytest.raises(HTTPException) as exc:
        mutation.update_task(mock_info, 1, update_input)
    assert exc.value.status_code == 404
    assert "Invalid parent task" in str(exc.value.detail)


def test_delete_task_not_found(
    mocker, mock_user, mock_info
):
    """Test deleting a non-existent task."""
    # Mock the task service
    task_service = mocker.Mock(spec=TaskService)
    task_service.get_task.side_effect = TaskReferenceError(
        "Task not found"
    )

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

    # Execute mutation and verify it raises HTTPException
    with pytest.raises(HTTPException) as exc:
        mutation.delete_task(mock_info, 999)
    assert exc.value.status_code == 404
    assert "Task not found" in str(exc.value.detail)


def test_create_task_with_all_fields(
    mocker, mock_user, mock_info
):
    """Test creating a task with all fields set."""
    # Mock the task service
    task_service = mocker.Mock(spec=TaskService)

    # Create a task with all fields
    now = datetime.now(timezone.utc)
    task = TaskData(
        id=1,
        title="Test Task",
        description="Test Description",
        status=TaskStatus.TODO,
        priority=TaskPriority.HIGH,
        user_id=str(mock_user.id),
        parent_id=None,
        created_at=now,
        updated_at=now,
        tags=["test", "important"],
        due_date=now + timedelta(days=7),
    )
    task_service.create_task.return_value = task

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

    # Create input with all fields
    task_input = TaskInput(
        title="Test Task",
        description="Test Description",
        status=TaskStatus.TODO,
        priority=TaskPriority.HIGH,
        tags=["test", "important"],
        due_date=now + timedelta(days=7),
    )

    # Execute mutation
    result = mutation.create_task(mock_info, task_input)

    # Verify result
    assert isinstance(result, Task)
    assert result.title == "Test Task"
    assert result.description == "Test Description"
    assert result.status == TaskStatus.TODO
    assert result.priority == TaskPriority.HIGH
    assert result.tags == ["test", "important"]
    assert result.due_date is not None


def test_update_task_clear_optional_fields(
    mocker, mock_user, mock_task, mock_info
):
    """Test updating a task by clearing optional fields."""
    # Mock the task service
    task_service = mocker.Mock(spec=TaskService)
    task_service.get_task.return_value = mock_task

    # Create an updated task with cleared fields
    updated_task = TaskData(
        id=mock_task.id,
        title=mock_task.title,
        description="",  # Clear description
        status=mock_task.status,
        priority=mock_task.priority,
        user_id=mock_task.user_id,
        parent_id=None,  # Clear parent
        created_at=mock_task.created_at,
        updated_at=mock_task.updated_at,
        tags=[],  # Clear tags
        due_date=None,  # Clear due date
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

    # Create input to clear optional fields
    update_input = TaskUpdateInput(
        description="",
        parent_id=None,
        tags=[],
        due_date=None,
    )

    # Execute mutation
    result = mutation.update_task(
        mock_info, 1, update_input
    )

    # Verify result
    assert isinstance(result, Task)
    assert result.description == ""
    assert result.parent_id is None
    assert result.tags == []
    assert result.due_date is None


def test_update_task_cyclic_parent(
    mocker, mock_user, mock_task, mock_info
):
    """Test updating a task to create a cyclic parent reference."""
    # Mock the task service
    task_service = mocker.Mock(spec=TaskService)
    task_service.get_task.return_value = mock_task
    task_service.update_task.side_effect = TaskParentError(
        "task cannot be its own parent"
    )

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

    # Create input that would create a cycle
    update_input = TaskUpdateInput(
        parent_id=mock_task.id,  # Set parent to self
    )

    # Execute mutation and verify it raises HTTPException
    with pytest.raises(HTTPException) as exc:
        mutation.update_task(
            mock_info, mock_task.id, update_input
        )
    assert exc.value.status_code == 404
    assert exc.value.detail["code"] == "TASK_PARENT_ERROR"
    assert "task cannot be its own parent" in str(
        exc.value.detail["message"]
    )


def test_create_task_invalid_priority(mocker, mock_info):
    """Test creating a task with invalid priority."""
    # Create mutation
    mutation = TaskMutation()

    # Create input with invalid priority
    task_input = TaskInput(
        title="Test Task",
        description="Test Description",
        status=TaskStatus.TODO,
        priority="INVALID_PRIORITY",  # Invalid priority
    )

    # Execute mutation and verify it raises HTTPException
    with pytest.raises(HTTPException) as exc:
        mutation.create_task(mock_info, task_input)
    assert exc.value.status_code == 400
    assert exc.value.detail["code"] == "TASK_PRIORITY_ERROR"
    assert "priority must be one of" in str(
        exc.value.detail["message"]
    )


def test_create_task_invalid_due_date(mocker, mock_info):
    """Test creating a task with invalid due date."""
    # Create mutation
    mutation = TaskMutation()

    # Create input with past due date (timezone-aware)
    past_date = datetime.now(timezone.utc) - timedelta(
        days=1
    )
    task_input = TaskInput(
        title="Test Task",
        description="Test Description",
        status=TaskStatus.TODO,
        priority=TaskPriority.MEDIUM,
        due_date=past_date,  # Past due date
    )

    # Execute mutation and verify it raises HTTPException
    with pytest.raises(HTTPException) as exc:
        mutation.create_task(mock_info, task_input)
    assert exc.value.status_code == 400
    assert exc.value.detail["code"] == "TASK_DATE_ERROR"
    assert (
        "due_date cannot be earlier than created_at"
        in str(exc.value.detail["message"])
    )


def test_update_task_invalid_status_transition(
    mocker, mock_user, mock_task, mock_info
):
    """Test updating a task with invalid status transition."""
    # Mock the task service
    task_service = mocker.Mock(spec=TaskService)
    task_service.get_task.return_value = mock_task
    task_service.update_task.side_effect = TaskStatusError(
        "Cannot transition from TODO to DONE directly"
    )

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

    # Create input with invalid status transition
    update_input = TaskUpdateInput(
        status=TaskStatus.DONE,  # Invalid transition from TODO to DONE
    )

    # Execute mutation and verify it raises HTTPException
    with pytest.raises(HTTPException) as exc:
        mutation.update_task(
            mock_info, mock_task.id, update_input
        )
    assert exc.value.status_code == 400
    assert exc.value.detail["code"] == "TASK_INVALID_STATUS"
    assert (
        "Cannot transition from TODO to DONE directly"
        in str(exc.value.detail["message"])
    )


def test_create_task_invalid_date_format(mocker, mock_info):
    """Test creating a task with invalid date format."""
    # Create mutation
    mutation = TaskMutation()

    # Create input with invalid date format
    task_input = TaskInput(
        title="Test Task",
        description="Test Description",
        status=TaskStatus.TODO,
        priority=TaskPriority.MEDIUM,
        due_date="invalid-date",  # Invalid date format
    )

    # Execute mutation and verify it raises HTTPException
    with pytest.raises(HTTPException) as exc:
        mutation.create_task(mock_info, task_input)
    assert exc.value.status_code == 400
    assert exc.value.detail["code"] == "TASK_DATE_ERROR"
    assert "due_date must be a datetime object" in str(
        exc.value.detail["message"]
    )


def test_create_task_missing_auth_token(mocker, mock_info):
    """Test creating a task without authentication."""
    # Remove user from context
    mock_info.context["user"] = None

    # Create mutation
    mutation = TaskMutation()

    # Create input
    task_input = TaskInput(
        title="Test Task",
        description="Test Description",
        status=TaskStatus.TODO,
        priority=TaskPriority.MEDIUM,
    )

    # Execute mutation and verify it raises HTTPException
    with pytest.raises(HTTPException) as exc:
        mutation.create_task(mock_info, task_input)
    assert exc.value.status_code == 401
    assert exc.value.detail["code"] == "UNAUTHORIZED"
    assert "Authentication required" in str(
        exc.value.detail["message"]
    )


def test_update_task_not_owner(
    mocker, mock_user, mock_task, mock_info
):
    """Test updating a task owned by another user."""
    # Mock the task service
    task_service = mocker.Mock(spec=TaskService)
    mock_task.user_id = (
        "different-user-id"  # Different user
    )
    task_service.get_task.return_value = mock_task

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
    )

    # Execute mutation and verify it raises HTTPException
    with pytest.raises(HTTPException) as exc:
        mutation.update_task(mock_info, 1, update_input)
    assert exc.value.status_code == 403
    assert exc.value.detail["code"] == "FORBIDDEN"
    assert "Not authorized to access this task" in str(
        exc.value.detail["message"]
    )


def test_delete_task_internal_error(
    mocker, mock_user, mock_task, mock_info
):
    """Test deleting a task with internal server error."""
    # Mock the task service
    task_service = mocker.Mock(spec=TaskService)
    task_service.get_task.return_value = mock_task
    task_service.delete_task.side_effect = Exception(
        "Database error"
    )

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

    # Execute mutation and verify it raises HTTPException
    with pytest.raises(HTTPException) as exc:
        mutation.delete_task(mock_info, 1)
    assert exc.value.status_code == 500
    assert (
        exc.value.detail["code"] == "INTERNAL_SERVER_ERROR"
    )
    assert "Internal server error" in str(
        exc.value.detail["message"]
    )


def test_create_task_invalid_priority_type(
    mocker, mock_info
):
    """Test creating a task with invalid priority type."""
    # Create mutation
    mutation = TaskMutation()

    # Create input with invalid priority type
    task_input = TaskInput(
        title="Test Task",
        description="Test Description",
        status=TaskStatus.TODO,
        priority="not-a-priority-enum",  # Invalid priority type
    )

    # Execute mutation and verify it raises HTTPException
    with pytest.raises(HTTPException) as exc:
        mutation.create_task(mock_info, task_input)
    assert exc.value.status_code == 400
    assert exc.value.detail["code"] == "TASK_PRIORITY_ERROR"
    assert "priority must be one of" in str(
        exc.value.detail["message"]
    )
