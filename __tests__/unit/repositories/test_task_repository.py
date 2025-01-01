"""Test TaskRepository class."""

from datetime import datetime, UTC
import pytest
from sqlalchemy.orm import Session

from repositories.TaskRepository import TaskRepository
from domain.values import TaskStatus, TaskPriority
from orm.TaskModel import Task


@pytest.fixture
def task_repository(
    test_db_session: Session,
) -> TaskRepository:
    """Create TaskRepository instance with test database session."""
    return TaskRepository(db=test_db_session)


@pytest.fixture
def sample_task_data():
    """Create sample task data for testing."""
    return {
        "title": "Test Task",
        "description": "Test Description",
        "status": TaskStatus.TODO,
        "priority": TaskPriority.MEDIUM,
        "due_date": datetime(
            2025, 1, 2, 1, 0, 0, tzinfo=UTC
        ),
        "tags": ["test", "sample"],
    }


def test_create(
    task_repository, sample_user, sample_task_data
):
    """Test creating a task."""
    task = task_repository.create(
        user_id=sample_user.id, **sample_task_data
    )

    assert task.id is not None
    assert task.title == sample_task_data["title"]
    assert (
        task.description == sample_task_data["description"]
    )
    assert task.status == sample_task_data["status"]
    assert task.priority == sample_task_data["priority"]

    # Compare timestamps by converting both to UTC
    # and comparing the total seconds
    task_due_date = task.due_date
    sample_due_date = sample_task_data["due_date"]
    assert int(task_due_date.timestamp()) == int(
        sample_due_date.timestamp()
    )

    assert task.tags == sample_task_data["tags"]
    assert task.user_id == sample_user.id
    assert task.parent_id is None


def test_create_subtask(
    task_repository, sample_user, sample_task_data
):
    """Test creating a subtask."""
    # Create parent task
    parent = task_repository.create(
        user_id=sample_user.id, **sample_task_data
    )

    # Create subtask
    subtask_data = sample_task_data.copy()
    subtask_data["title"] = "Subtask"
    subtask = task_repository.create(
        user_id=sample_user.id,
        parent_id=parent.id,
        **subtask_data,
    )

    assert subtask.id is not None
    assert subtask.parent_id == parent.id
    assert subtask.title == "Subtask"


def test_create_subtask_invalid_parent(
    task_repository, sample_user, sample_task_data
):
    """Test creating a subtask with invalid parent."""
    with pytest.raises(ValueError) as exc_info:
        task_repository.create(
            user_id=sample_user.id,
            parent_id=999,  # Non-existent parent
            **sample_task_data,
        )
    assert "Parent task not found" in str(exc_info.value)


def test_list_tasks(task_repository, sample_user):
    """Test listing tasks for a user."""
    # Create multiple tasks
    tasks = []
    for i in range(3):
        task = task_repository.create(
            title=f"Task {i}",
            description=f"Description {i}",
            user_id=sample_user.id,
            status=TaskStatus.TODO,
            priority=TaskPriority.MEDIUM,
        )
        tasks.append(task)

    # List tasks
    result = task_repository.list_tasks(
        user_id=sample_user.id
    )

    assert len(result) == 3
    assert all(isinstance(task, Task) for task in result)
    assert all(
        task.user_id == sample_user.id for task in result
    )


def test_list_tasks_with_filters(
    task_repository, sample_user
):
    """Test listing tasks with filters."""
    # Create tasks with different statuses and priorities
    task_repository.create(
        title="High Priority",
        description="Urgent task",
        user_id=sample_user.id,
        status=TaskStatus.TODO,
        priority=TaskPriority.HIGH,
    )
    task_repository.create(
        title="Medium Priority",
        description="Normal task",
        user_id=sample_user.id,
        status=TaskStatus.IN_PROGRESS,
        priority=TaskPriority.MEDIUM,
    )

    # Test status filter
    todo_tasks = task_repository.list_tasks(
        user_id=sample_user.id,
        status=TaskStatus.TODO,
    )
    assert len(todo_tasks) == 1
    assert todo_tasks[0].status == TaskStatus.TODO

    # Test priority filter
    high_priority = task_repository.list_tasks(
        user_id=sample_user.id,
        priority=TaskPriority.HIGH,
    )
    assert len(high_priority) == 1
    assert high_priority[0].priority == TaskPriority.HIGH


def test_count_tasks(task_repository, sample_user):
    """Test counting user's tasks."""
    # Create multiple tasks
    for i in range(3):
        task_repository.create(
            title=f"Task {i}",
            description=f"Description {i}",
            user_id=sample_user.id,
            status=TaskStatus.TODO,
        )

    # Count all tasks
    total_count = task_repository.count_tasks(
        user_id=sample_user.id
    )
    assert total_count == 3

    # Count by status
    todo_count = task_repository.count_tasks(
        user_id=sample_user.id,
        status=TaskStatus.TODO,
    )
    assert todo_count == 3


def test_get_subtasks(task_repository, sample_user):
    """Test getting subtasks."""
    # Create parent task
    parent = task_repository.create(
        title="Parent Task",
        description="Parent Description",
        user_id=sample_user.id,
    )

    # Create subtasks
    subtasks = []
    for i in range(2):
        subtask = task_repository.create(
            title=f"Subtask {i}",
            description=f"Subtask Description {i}",
            user_id=sample_user.id,
            parent_id=parent.id,
        )
        subtasks.append(subtask)

    # Get subtasks
    result = task_repository.get_subtasks(
        task_id=parent.id,
        user_id=sample_user.id,
    )

    assert len(result) == 2
    assert all(
        task.parent_id == parent.id for task in result
    )


def test_update_status(task_repository, sample_user):
    """Test updating task status."""
    # Create task
    task = task_repository.create(
        title="Test Task",
        description="Test Description",
        user_id=sample_user.id,
        status=TaskStatus.TODO,
    )

    # Update status
    updated = task_repository.update_status(
        task_id=task.id,
        user_id=sample_user.id,
        new_status=TaskStatus.IN_PROGRESS,
    )

    assert updated is not None
    assert updated.status == TaskStatus.IN_PROGRESS


def test_update_status_nonexistent(
    task_repository, sample_user
):
    """Test updating status of non-existent task."""
    result = task_repository.update_status(
        task_id=999,
        user_id=sample_user.id,
        new_status=TaskStatus.IN_PROGRESS,
    )
    assert result is None
