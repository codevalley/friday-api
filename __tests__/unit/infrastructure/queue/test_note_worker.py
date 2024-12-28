"""Tests for the note worker module."""

import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime

from domain.values import ProcessingStatus
from domain.exceptions import RoboServiceError
from infrastructure.queue.note_worker import (
    process_note_job,
)


@pytest.fixture
def mock_session():
    """Create a mock session."""
    session = MagicMock()
    session.commit = MagicMock()
    return session


@pytest.fixture
def mock_note_repo():
    """Create a mock note repository."""
    repo = MagicMock()
    return repo


@pytest.fixture
def mock_note():
    """Create a mock note."""
    note = MagicMock()
    note.id = 1
    note.content = "Test note content"
    note.processing_status = ProcessingStatus.PENDING
    note.enrichment_data = None
    note.processed_at = None
    return note


@pytest.fixture
def mock_robo_service():
    """Create a mock robo service."""
    service = MagicMock()
    service.enrich_note.return_value = {"enriched": True}
    return service


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

    # Execute
    process_note_job(1)

    # Verify state transitions
    assert (
        mock_note.processing_status
        == ProcessingStatus.COMPLETED
    )
    assert mock_note.enrichment_data == {"enriched": True}
    assert isinstance(mock_note.processed_at, datetime)

    # Verify method calls
    mock_note_repo.get_by_id.assert_called_once_with(1)
    mock_session.commit.assert_called()
    mock_robo_service.enrich_note.assert_called_once_with(
        "Test note content"
    )


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
    mock_robo_service.enrich_note.side_effect = Exception(
        "Processing failed"
    )

    # Execute
    with pytest.raises(RoboServiceError) as exc:
        process_note_job(1)
    assert "Failed to process note" in str(exc.value)

    # Verify state transitions
    assert (
        mock_note.processing_status
        == ProcessingStatus.FAILED
    )
    assert mock_note.enrichment_data is None

    # Verify method calls - should be called 4 times (initial + 3 retries)
    assert mock_robo_service.enrich_note.call_count == 4
    for (
        call
    ) in mock_robo_service.enrich_note.call_args_list:
        assert call[0][0] == "Test note content"

    # Verify session commits
    mock_session.commit.assert_called()
