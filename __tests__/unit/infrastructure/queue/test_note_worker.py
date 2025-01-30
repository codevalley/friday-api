"""Test note worker module."""

import pytest
from datetime import datetime, timezone
from unittest.mock import patch, MagicMock

from domain.values import ProcessingStatus
from domain.robo import RoboProcessingResult
from infrastructure.queue.note_worker import (
    process_note_job,
)


@pytest.fixture
def mock_session():
    """Create a mock database session."""
    return MagicMock()


@pytest.fixture
def mock_note_repo():
    """Create a mock note repository."""
    return MagicMock()


@pytest.fixture
def mock_note():
    """Create a mock note."""
    note = MagicMock()
    note.content = "Test note content"
    note.related_notes = []
    note.topics = []
    note.enrichment_data = {}
    note.user_id = 123
    return note


@pytest.fixture
def mock_robo_service():
    """Create a mock RoboService."""
    service = MagicMock()
    # Mock process_note response
    process_result = RoboProcessingResult(
        content="Formatted content",
        metadata={
            "title": "Test Note",
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
    service.process_note.return_value = process_result

    # Mock extract_tasks response
    service.extract_tasks.return_value = [
        {
            "content": "Task 1",
            "priority": "high",
            "status": "todo",
        },
        {
            "content": "Task 2",
            "priority": "medium",
            "status": "todo",
        },
    ]

    # Mock config
    service.config = MagicMock()
    service.config.task_extraction_prompt = (
        "Extract tasks from this note"
    )
    service.config.task_enrichment_prompt = (
        "Format this task"
    )
    service.config.note_enrichment_prompt = (
        "Format this note"
    )

    return service


@patch("infrastructure.queue.note_worker.NoteRepository")
@patch("infrastructure.queue.note_worker.get_robo_service")
@patch("infrastructure.queue.note_worker.SessionLocal")
@patch("infrastructure.queue.note_worker.create_task")
def test_process_note_success(
    mock_create_task,
    mock_session_local,
    mock_get_robo_service,
    mock_note_repo_class,
    mock_session,
    mock_note_repo,
    mock_note,
    mock_robo_service,
):
    """Test successful note processing."""
    # Setup
    mock_session_local.return_value = mock_session
    mock_note_repo_class.return_value = mock_note_repo
    mock_get_robo_service.return_value = mock_robo_service
    mock_note_repo.get_by_id.return_value = mock_note
    mock_create_task.side_effect = [1, 2]  # Return task IDs

    # Execute
    process_note_job(
        note_id=1,
        session=mock_session,
        robo_service=mock_robo_service,
        note_repository=mock_note_repo,
    )

    # Verify note processing
    mock_robo_service.process_note.assert_called_once()
    assert (
        mock_note.processing_status
        == ProcessingStatus.COMPLETED
    )

    # Verify task extraction was attempted
    mock_robo_service.extract_tasks.assert_called_once_with(
        mock_note.content
    )

    # Verify task creation was called
    assert mock_create_task.call_count == 2
    mock_create_task.assert_any_call(
        content="Task 1",
        user_id=mock_note.user_id,
        source_note_id=1,
        priority="high",
        status="todo",
        due_date=None,
        session=mock_session,
        max_retries=3,
    )
    mock_create_task.assert_any_call(
        content="Task 2",
        user_id=mock_note.user_id,
        source_note_id=1,
        priority="medium",
        status="todo",
        due_date=None,
        session=mock_session,
        max_retries=3,
    )

    # Verify enrichment data
    expected_enrichment = {
        "title": "Test Note",
        "formatted": "Formatted content",
        "tokens_used": 150,
        "model_name": "gpt-4",
        "metadata": {
            "title": "Test Note",
            "model": "gpt-4",
            "usage": {
                "prompt_tokens": 100,
                "completion_tokens": 50,
                "total_tokens": 150,
            },
        },
    }

    # Verify core enrichment data (ignoring task stats which may vary)
    for key, value in expected_enrichment.items():
        assert mock_note.enrichment_data[key] == value

    # Verify task stats exist but don't check specific values
    assert (
        "task_extraction_stats" in mock_note.enrichment_data
    )
    assert (
        "task_extraction_completed_at"
        in mock_note.enrichment_data
    )
    assert (
        mock_note.enrichment_data["task_extraction_stats"][
            "tasks_found"
        ]
        == 2
    )
    assert (
        mock_note.enrichment_data["task_extraction_stats"][
            "tasks_created"
        ]
        == 2
    )


@patch("infrastructure.queue.note_worker.NoteRepository")
@patch("infrastructure.queue.note_worker.get_robo_service")
@patch("infrastructure.queue.note_worker.SessionLocal")
@patch("infrastructure.queue.note_worker.create_task")
def test_process_note_with_tasks(
    mock_create_task,
    mock_session_local,
    mock_get_robo_service,
    mock_note_repo_class,
    mock_session,
    mock_note_repo,
    mock_note,
    mock_robo_service,
):
    """Test note processing with task extraction."""
    # Setup
    mock_session_local.return_value = mock_session
    mock_note_repo_class.return_value = mock_note_repo
    mock_get_robo_service.return_value = mock_robo_service
    mock_note_repo.get_by_id.return_value = mock_note
    mock_create_task.side_effect = [1, 2]  # Return task IDs

    # Execute
    process_note_job(
        note_id=1,
        session=mock_session,
        robo_service=mock_robo_service,
        note_repository=mock_note_repo,
    )

    # Verify task creation
    assert mock_create_task.call_count == 2
    mock_create_task.assert_any_call(
        content="Task 1",
        user_id=mock_note.user_id,
        source_note_id=1,
        priority="high",
        status="todo",
        due_date=None,
        session=mock_session,
        max_retries=3,
    )
    mock_create_task.assert_any_call(
        content="Task 2",
        user_id=mock_note.user_id,
        source_note_id=1,
        priority="medium",
        status="todo",
        due_date=None,
        session=mock_session,
        max_retries=3,
    )

    # Verify task stats
    assert (
        mock_note.enrichment_data["task_extraction_stats"][
            "tasks_found"
        ]
        == 2
    )
    assert (
        mock_note.enrichment_data["task_extraction_stats"][
            "tasks_created"
        ]
        == 2
    )


@patch("infrastructure.queue.note_worker.NoteRepository")
@patch("infrastructure.queue.note_worker.get_robo_service")
@patch("infrastructure.queue.note_worker.SessionLocal")
@patch("infrastructure.queue.note_worker.create_task")
def test_process_note_task_extraction_failure(
    mock_create_task,
    mock_session_local,
    mock_get_robo_service,
    mock_note_repo_class,
    mock_session,
    mock_note_repo,
    mock_note,
    mock_robo_service,
):
    """Test note processing succeeds even when task extraction fails."""
    # Setup
    mock_session_local.return_value = mock_session
    mock_note_repo_class.return_value = mock_note_repo
    mock_get_robo_service.return_value = mock_robo_service
    mock_note_repo.get_by_id.return_value = mock_note

    # Mock task extraction failure
    mock_robo_service.extract_tasks.side_effect = Exception(
        "Task extraction failed"
    )

    # Execute
    process_note_job(
        note_id=1,
        session=mock_session,
        robo_service=mock_robo_service,
        note_repository=mock_note_repo,
    )

    # Verify note processing completed despite task extraction failure
    assert (
        mock_note.processing_status
        == ProcessingStatus.COMPLETED
    )

    # Verify task extraction stats reflect failure
    assert (
        mock_note.enrichment_data["task_extraction_stats"][
            "error"
        ]
        == "Task extraction failed"
    )
    assert (
        mock_note.enrichment_data["task_extraction_stats"][
            "tasks_found"
        ]
        == 0
    )
    assert (
        mock_note.enrichment_data["task_extraction_stats"][
            "tasks_created"
        ]
        == 0
    )
