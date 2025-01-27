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
    robo_service.process_note.return_value = mock_result

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
    assert "formatted" in note.enrichment_data
    assert "title" in note.enrichment_data
    assert "tokens_used" in note.enrichment_data
    assert "model_name" in note.enrichment_data
    assert "created_at" in note.enrichment_data
    assert "metadata" in note.enrichment_data
    assert isinstance(
        note.enrichment_data["tokens_used"], int
    )
    assert isinstance(
        note.enrichment_data["model_name"], str
    )
    assert isinstance(
        note.enrichment_data["created_at"], str
    )


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
    def mock_process_note(*args, **kwargs):
        raise Exception("Test processing failure")

    robo_service.process_note = mock_process_note

    # Process note
    with pytest.raises(Exception) as exc_info:
        process_note_job(
            note.id,
            test_db_session,
            robo_service,
            note_repo,
        )

    assert "Test processing failure" in str(exc_info.value)

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
    call_count = 0

    def mock_process_note(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count <= 2:
            raise Exception(f"Test failure #{call_count}")
        return RoboProcessingResult(
            content="Processed after retry",
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

    robo_service.process_note = mock_process_note

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
        == "Processed after retry"
    )
    assert call_count == 3  # Two failures + one success
