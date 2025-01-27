"""Test note worker module."""

import pytest
from datetime import datetime, timezone
from unittest.mock import patch, MagicMock

from domain.values import ProcessingStatus
from domain.exceptions import RoboServiceError
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
    return note


@pytest.fixture
def mock_robo_service():
    """Create a mock RoboService."""
    return MagicMock()


@patch("infrastructure.queue.note_worker.NoteRepository")
@patch("infrastructure.queue.note_worker.get_robo_service")
@patch("infrastructure.queue.note_worker.SessionLocal")
def test_process_note_success(
    mock_session_local,
    mock_get_robo_service,
    mock_note_repo_class,
    mock_session,
    mock_note_repo,
    mock_note,
    mock_robo_service,
):
    """Test successful note processing.

    Should:
    1. Update status to PROCESSING
    2. Process with RoboService
    3. Update with results and COMPLETED status
    4. Commit all changes
    """
    # Setup
    mock_session_local.return_value = mock_session
    mock_note_repo_class.return_value = mock_note_repo
    mock_get_robo_service.return_value = mock_robo_service
    mock_note_repo.get_by_id.return_value = mock_note

    # Mock RoboService response
    mock_result = RoboProcessingResult(
        content="Processed content",
        metadata={
            "title": "Test Note",
            "model": "test_model",
            "usage": {
                "prompt_tokens": 50,
                "completion_tokens": 50,
                "total_tokens": 100,
            },
        },
        tokens_used=100,
        model_name="test_model",
        created_at=datetime.now(timezone.utc),
    )
    mock_robo_service.process_note.return_value = (
        mock_result
    )

    # Execute
    process_note_job(1)

    # Verify state transitions
    assert (
        mock_note.processing_status
        == ProcessingStatus.COMPLETED
    )
    assert mock_note.enrichment_data == {
        "title": mock_result.metadata["title"],
        "formatted": mock_result.content,
        "tokens_used": mock_result.tokens_used,
        "model_name": mock_result.model_name,
        "created_at": mock_result.created_at.isoformat(),
        "metadata": mock_result.metadata,
    }

    # Verify method calls
    mock_robo_service.process_note.assert_called_once_with(
        mock_note.content,
        context={
            "type": "note_enrichment",
            "related_notes": mock_note.related_notes,
            "topics": mock_note.topics,
        },
    )
    assert mock_session.commit.call_count >= 2


@patch("infrastructure.queue.note_worker.NoteRepository")
@patch("infrastructure.queue.note_worker.get_robo_service")
@patch("infrastructure.queue.note_worker.SessionLocal")
def test_process_note_not_found(
    mock_session_local,
    mock_get_robo_service,
    mock_note_repo_class,
    mock_session,
    mock_note_repo,
):
    """Test handling of non-existent note."""
    # Setup
    mock_session_local.return_value = mock_session
    mock_note_repo_class.return_value = mock_note_repo
    mock_note_repo.get_by_id.return_value = None

    # Execute and verify
    with pytest.raises(ValueError) as exc:
        process_note_job(1)
    assert "Note 1 not found" in str(exc.value)

    # Verify no updates were made
    mock_session.commit.assert_not_called()


@patch("infrastructure.queue.note_worker.NoteRepository")
@patch("infrastructure.queue.note_worker.get_robo_service")
@patch("infrastructure.queue.note_worker.SessionLocal")
def test_process_note_robo_service_failure(
    mock_session_local,
    mock_get_robo_service,
    mock_note_repo_class,
    mock_session,
    mock_note_repo,
    mock_note,
    mock_robo_service,
):
    """Test handling of RoboService failure.

    Should:
    1. Update status to PROCESSING
    2. Attempt to process with RoboService (with retries)
    3. Update status to FAILED after all retries fail
    4. Commit all changes
    """
    # Setup
    mock_session_local.return_value = mock_session
    mock_note_repo_class.return_value = mock_note_repo
    mock_get_robo_service.return_value = mock_robo_service
    mock_note_repo.get_by_id.return_value = mock_note
    mock_robo_service.process_note.side_effect = Exception(
        "Test processing failure"
    )

    # Explicitly set enrichment_data to None
    mock_note.enrichment_data = None

    # Execute
    with pytest.raises(RoboServiceError) as exc_info:
        process_note_job(1)

    # Verify error handling
    assert str(exc_info.value) == (
        "Failed to process note 1: Test processing failure"
    )

    # Verify retries
    assert mock_robo_service.process_note.call_count == 4
    for (
        call
    ) in mock_robo_service.process_note.call_args_list:
        assert call == (
            (mock_note.content,),
            {
                "context": {
                    "type": "note_enrichment",
                    "related_notes": mock_note.related_notes,
                    "topics": mock_note.topics,
                }
            },
        )

    # Verify state transitions
    assert (
        mock_note.processing_status
        == ProcessingStatus.FAILED
    )
    assert mock_note.enrichment_data is None

    # Verify session commits
    mock_session.commit.assert_called()
