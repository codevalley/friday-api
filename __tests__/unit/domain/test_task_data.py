"""Test cases for TaskData domain model."""

import pytest
from datetime import datetime, timedelta, UTC
from domain.task import TaskData
from domain.values import TaskStatus, TaskPriority
from domain.exceptions import (
    TaskValidationError,
    TaskContentError,
    TaskDateError,
    TaskPriorityError,
    TaskStatusError,
    TaskParentError,
)


@pytest.fixture
def valid_task_data():
    """Fixture providing valid task data."""
    return {
        "title": "Test Task",
        "description": "This is a test task",
        "user_id": "test_user_id",
        "status": TaskStatus.TODO,
        "priority": TaskPriority.MEDIUM,
        "due_date": datetime.now(UTC) + timedelta(days=1),
        "tags": ["test", "example"],
    }


def test_create_task_with_valid_data(valid_task_data):
    """Test creating a task with valid data."""
    task = TaskData(**valid_task_data)
    assert task.title == valid_task_data["title"]
    assert (
        task.description == valid_task_data["description"]
    )
    assert task.user_id == valid_task_data["user_id"]
    assert task.status == valid_task_data["status"]
    assert task.priority == valid_task_data["priority"]
    assert task.due_date == valid_task_data["due_date"]
    assert task.tags == valid_task_data["tags"]
    assert task.id is None
    assert task.parent_id is None
    assert isinstance(task.created_at, datetime)
    assert isinstance(task.updated_at, datetime)


def test_create_task_with_minimal_data():
    """Test creating task with minimal required data."""
    task = TaskData(
        title="Minimal Task",
        description="Minimal description",
        user_id="test_user",
    )
    assert task.title == "Minimal Task"
    assert task.status == TaskStatus.TODO
    assert task.priority == TaskPriority.MEDIUM


def test_invalid_title():
    """Test task creation with invalid title."""
    with pytest.raises(TaskContentError):
        TaskData(
            title="", description="desc", user_id="user"
        )

    with pytest.raises(TaskContentError):
        TaskData(
            title="x" * 256,
            description="desc",
            user_id="user",
        )


def test_invalid_description():
    """Test task creation with invalid description."""
    with pytest.raises(TaskContentError):
        TaskData(
            title="Task",
            description=123,  # type: ignore
            user_id="user",
        )


def test_invalid_user_id():
    """Test task creation with invalid user_id."""
    with pytest.raises(TaskValidationError):
        TaskData(
            title="Task", description="desc", user_id=""
        )


def test_invalid_status():
    """Test task creation with invalid status."""
    with pytest.raises(TaskStatusError):
        TaskData(
            title="Task",
            description="desc",
            user_id="user",
            status="invalid",  # type: ignore
        )


def test_invalid_priority():
    """Test task creation with invalid priority."""
    with pytest.raises(TaskPriorityError):
        TaskData(
            title="Task",
            description="desc",
            user_id="user",
            priority="invalid",  # type: ignore
        )


def test_invalid_due_date():
    """Test task creation with invalid due date."""
    past_date = datetime.now(UTC) - timedelta(days=1)
    with pytest.raises(TaskDateError):
        TaskData(
            title="Task",
            description="desc",
            user_id="user",
            due_date=past_date,
        )


def test_invalid_tags():
    """Test task creation with invalid tags."""
    with pytest.raises(TaskValidationError):
        TaskData(
            title="Task",
            description="desc",
            user_id="user",
            tags="not-a-list",  # type: ignore
        )

    with pytest.raises(TaskValidationError):
        TaskData(
            title="Task",
            description="desc",
            user_id="user",
            tags=["valid", ""],  # empty tag
        )


def test_invalid_parent_id():
    """Test task creation with invalid parent_id."""
    with pytest.raises(TaskParentError):
        TaskData(
            title="Task",
            description="desc",
            user_id="user",
            parent_id=0,
        )

    # Test self-referential parent
    with pytest.raises(TaskParentError):
        TaskData(
            title="Task",
            description="desc",
            user_id="user",
            id=1,
            parent_id=1,
        )


def test_status_transitions():
    """Test task status transitions."""
    task = TaskData(
        title="Task",
        description="desc",
        user_id="user",
        status=TaskStatus.TODO,
    )

    # Valid transitions
    task.update_status(TaskStatus.IN_PROGRESS)
    assert task.status == TaskStatus.IN_PROGRESS

    task.update_status(TaskStatus.DONE)
    assert task.status == TaskStatus.DONE

    # Invalid transition: try to go directly from TODO to DONE
    task = TaskData(  # Create new task starting at TODO
        title="Task",
        description="desc",
        user_id="user",
        status=TaskStatus.TODO,
    )
    with pytest.raises(TaskStatusError):
        task.update_status(
            TaskStatus.DONE
        )  # Should fail: can't go directly from TODO to DONE


def test_priority_update():
    """Test task priority updates."""
    task = TaskData(
        title="Task",
        description="desc",
        user_id="user",
    )

    task.update_priority(TaskPriority.HIGH)
    assert task.priority == TaskPriority.HIGH

    with pytest.raises(TaskPriorityError):
        task.update_priority("invalid")  # type: ignore


def test_due_date_update():
    """Test task due date updates."""
    task = TaskData(
        title="Task",
        description="desc",
        user_id="user",
    )

    new_date = datetime.now(UTC) + timedelta(days=7)
    task.update_due_date(new_date)
    assert task.due_date == new_date

    # Test with past date
    past_date = datetime.now(UTC) - timedelta(days=1)
    with pytest.raises(TaskDateError):
        task.update_due_date(past_date)


def test_to_dict_conversion(valid_task_data):
    """Test converting TaskData to dictionary."""
    task = TaskData(**valid_task_data)
    data = task.to_dict()

    assert data["title"] == valid_task_data["title"]
    assert (
        data["description"]
        == valid_task_data["description"]
    )
    assert data["user_id"] == valid_task_data["user_id"]
    assert data["status"] == valid_task_data["status"].value
    assert (
        data["priority"]
        == valid_task_data["priority"].value
    )
    assert data["due_date"] == valid_task_data["due_date"]
    assert data["tags"] == valid_task_data["tags"]


def test_from_dict_conversion():
    """Test creating TaskData from dictionary."""
    data = {
        "title": "Dict Task",
        "description": "From dict",
        "user_id": "test_user",
        "status": "todo",  # String value
        "priority": "high",  # String value
        "tags": ["test"],
    }

    task = TaskData.from_dict(data)
    assert task.title == data["title"]
    assert task.status == TaskStatus.TODO
    assert task.priority == TaskPriority.HIGH
    assert task.tags == data["tags"]
