"""Test task worker module."""

import pytest
from datetime import datetime, timezone
from unittest.mock import patch, MagicMock

from domain.values import ProcessingStatus
from domain.robo import RoboProcessingResult
from domain.exceptions import RoboServiceError
from infrastructure.queue.task_worker import (
    create_task,
    process_task_job,
)


@pytest.fixture
def mock_session():
    """Create a mock database session."""
    return MagicMock()


@pytest.fixture
def mock_task_repo():
    """Create a mock task repository."""
    repo = MagicMock()
    repo.create.return_value = MagicMock(id=1)

    # Create a task mock with controlled attributes
    task = MagicMock()
    task.id = 1
    task.content = "Test task content"
    task.priority = "MEDIUM"
    task.status = "TODO"
    task.enrichment_data = {}
    task.due_date = None
    task.parent = None

    repo.get.return_value = task
    return repo


@pytest.fixture
def mock_robo_service():
    """Create a mock RoboService."""
    service = MagicMock()
    # Mock process_task response
    process_result = RoboProcessingResult(
        content="Formatted task content",
        metadata={
            "title": "Test Task",
            "priority": "high",
            "due_date": "2024-02-01",
            "model": "gpt-4",
            "usage": {
                "prompt_tokens": 100,
                "completion_tokens": 50,
                "total_tokens": 150,
            },
        },
        tokens_used=150,
        model_name="gpt-4",
        created_at=datetime.now(timezone.utc),
    )
    service.process_task.return_value = process_result
    return service


@patch("infrastructure.queue.task_worker.TaskRepository")
@patch("infrastructure.queue.task_worker.get_robo_service")
@patch("infrastructure.queue.task_worker.SessionLocal")
def test_create_task_success(
    mock_session_local,
    mock_get_robo_service,
    mock_task_repo_class,
    mock_session,
    mock_task_repo,
    mock_robo_service,
):
    """Test successful task creation."""
    # Setup
    mock_session_local.return_value = mock_session
    mock_task_repo_class.return_value = mock_task_repo
    mock_get_robo_service.return_value = mock_robo_service

    # Execute
    task_id = create_task(
        content="Test task",
        user_id=123,
        priority="high",
        status="todo",
        session=mock_session,
    )

    # Verify
    assert task_id == 1
    mock_task_repo.create.assert_called_once()
    create_args = mock_task_repo.create.call_args[0][0]
    assert create_args["content"] == "Test task"
    assert create_args["user_id"] == 123
    assert create_args["priority"] == "HIGH"
    assert create_args["status"] == "TODO"
    assert (
        create_args["processing_status"]
        == ProcessingStatus.PENDING
    )


@patch("infrastructure.queue.task_worker.TaskRepository")
@patch("infrastructure.queue.task_worker.get_robo_service")
@patch("infrastructure.queue.task_worker.SessionLocal")
def test_process_task_job_success(
    mock_session_local,
    mock_get_robo_service,
    mock_task_repo_class,
    mock_session,
    mock_task_repo,
    mock_robo_service,
):
    """Test successful task processing."""
    # Setup
    mock_session_local.return_value = mock_session
    mock_task_repo_class.return_value = mock_task_repo
    mock_get_robo_service.return_value = mock_robo_service

    # Execute
    process_task_job(
        task_id=1,
        session=mock_session,
        robo_service=mock_robo_service,
    )

    # Verify task was processed
    mock_robo_service.process_task.assert_called_once_with(
        "Test task content",
        context={
            "type": "task_enrichment",
            "priority": "MEDIUM",
            "due_date": None,
            "parent_task": None,
        },
    )

    # Verify task was updated
    task = mock_task_repo.get.return_value
    assert (
        task.processing_status == ProcessingStatus.COMPLETED
    )
    assert task.enrichment_data == {
        "title": "Test Task",
        "formatted": "Formatted task content",
        "tokens_used": 150,
        "model_name": "gpt-4",
        "created_at": task.enrichment_data["created_at"],
        "metadata": {
            "title": "Test Task",
            "priority": "high",
            "due_date": "2024-02-01",
            "model": "gpt-4",
            "usage": {
                "prompt_tokens": 100,
                "completion_tokens": 50,
                "total_tokens": 150,
            },
        },
    }


@patch("infrastructure.queue.task_worker.TaskRepository")
@patch("infrastructure.queue.task_worker.get_robo_service")
@patch("infrastructure.queue.task_worker.SessionLocal")
def test_process_task_job_not_found(
    mock_session_local,
    mock_get_robo_service,
    mock_task_repo_class,
    mock_session,
    mock_task_repo,
):
    """Test task processing when task not found."""
    # Setup
    mock_session_local.return_value = mock_session
    mock_task_repo_class.return_value = mock_task_repo
    mock_task_repo.get.return_value = None

    # Execute
    with pytest.raises(ValueError) as exc_info:
        process_task_job(task_id=999, session=mock_session)

    assert "Task 999 not found" in str(exc_info.value)


@patch("infrastructure.queue.task_worker.TaskRepository")
@patch("infrastructure.queue.task_worker.get_robo_service")
@patch("infrastructure.queue.task_worker.SessionLocal")
def test_process_task_job_processing_error(
    mock_session_local,
    mock_get_robo_service,
    mock_task_repo_class,
    mock_session,
    mock_task_repo,
    mock_robo_service,
):
    """Test task processing with error."""
    # Setup
    mock_session_local.return_value = mock_session
    mock_task_repo_class.return_value = mock_task_repo
    mock_get_robo_service.return_value = mock_robo_service
    mock_robo_service.process_task.side_effect = Exception(
        "Processing failed"
    )

    # Execute
    with pytest.raises(RoboServiceError) as exc_info:
        process_task_job(
            task_id=1,
            session=mock_session,
            robo_service=mock_robo_service,
            max_retries=1,
        )

    assert (
        "Failed to process task 1: Processing failed"
        in str(exc_info.value)
    )

    # Verify task was marked as failed
    task = mock_task_repo.get.return_value
    assert task.processing_status == ProcessingStatus.FAILED
