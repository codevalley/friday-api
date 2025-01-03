"""Integration tests for note processing."""

import pytest
from datetime import datetime, timezone

from domain.values import ProcessingStatus
from schemas.pydantic.NoteSchema import NoteCreate
from domain.robo import RoboProcessingResult
from repositories.NoteRepository import NoteRepository
from infrastructure.queue.note_worker import (
    process_note_job,
)


def test_note_processing_success(
    test_db_session,
    note_service,
    queue_service,
    sample_user,
    robo_service,
):
    """Test successful note processing flow."""
    # Create note
    note_data = NoteCreate(
        content="Test note content",
        activity_id=None,
        moment_id=None,
        attachments=[],
    )
    note_response = note_service.create_note(
        note_data, sample_user.id
    )

    # Get the actual note model from repository
    note_repo = NoteRepository(test_db_session)
    note = note_repo.get(note_response.id)

    # Process note
    process_note_job(
        note.id,
        test_db_session,
        robo_service,
        note_repo,
    )

    # Refresh session to see worker's changes
    test_db_session.expire_all()
    test_db_session.refresh(note)

    # Verify final state
    assert (
        note.processing_status == ProcessingStatus.COMPLETED
    )
    assert note.enrichment_data is not None
    assert (
        note.enrichment_data["formatted"] == "Test Content"
    )
    assert note.enrichment_data["title"] == "Test Title"
    assert note.enrichment_data["tokens_used"] == 100
    assert (
        note.enrichment_data["model_name"] == "test-model"
    )
    assert "created_at" in note.enrichment_data


def test_note_processing_failure(
    test_db_session,
    note_service,
    queue_service,
    sample_user,
    robo_service,
):
    """Test note processing failure handling."""
    # Create note
    note_data = NoteCreate(
        content="Test note for failure",
        activity_id=None,
        moment_id=None,
        attachments=[],
    )
    note_response = note_service.create_note(
        note_data, sample_user.id
    )

    # Get the actual note model from repository
    note_repo = NoteRepository(test_db_session)
    note = note_repo.get(note_response.id)

    # Mock RoboService to raise an error
    def mock_process_text(*args, **kwargs):
        raise Exception("Test processing failure")

    robo_service.process_text = mock_process_text

    # Process note
    with pytest.raises(Exception):
        process_note_job(
            note.id,
            test_db_session,
            robo_service,
            note_repo,
        )

    # Refresh session to see worker's changes
    test_db_session.expire_all()
    test_db_session.refresh(note)

    # Verify final state
    assert note.processing_status == ProcessingStatus.FAILED
    assert note.enrichment_data is None


def test_note_processing_retry(
    test_db_session,
    note_service,
    queue_service,
    sample_user,
    robo_service,
):
    """Test note processing retry mechanism."""
    # Create note
    note_data = NoteCreate(
        content="Test note for retry",
        activity_id=None,
        moment_id=None,
        attachments=[],
    )
    note_response = note_service.create_note(
        note_data, sample_user.id
    )

    # Get the actual note model from repository
    note_repo = NoteRepository(test_db_session)
    note = note_repo.get(note_response.id)

    # Mock RoboService to fail twice then succeed
    attempts = 0

    def mock_process_text(*args, **kwargs):
        nonlocal attempts
        attempts += 1
        if attempts <= 2:
            raise Exception(
                f"Test failure attempt {attempts}"
            )
        return RoboProcessingResult(
            content="Processed after retries",
            metadata={
                "title": "Test Note",
                "processed": True,
                "attempts": attempts,
            },
            tokens_used=0,
            model_name="test_model",
            created_at=datetime.now(timezone.utc),
        )

    robo_service.process_text = mock_process_text

    # Process note
    process_note_job(
        note.id,
        test_db_session,
        robo_service,
        note_repo,
    )

    # Refresh session to see worker's changes
    test_db_session.expire_all()
    test_db_session.refresh(note)

    # Verify final state
    assert (
        note.processing_status == ProcessingStatus.COMPLETED
    )
    assert note.enrichment_data is not None
    assert (
        note.enrichment_data["formatted"]
        == "Processed after retries"
    )
    assert note.enrichment_data["title"] == "Test Note"
    assert note.enrichment_data["metadata"]["attempts"] == 3
