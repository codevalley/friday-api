"""Integration tests for note processing flow."""

import pytest
from datetime import datetime, timezone

from domain.values import ProcessingStatus
from domain.robo import RoboProcessingResult
from infrastructure.queue.RQNoteQueue import RQNoteQueue
from infrastructure.queue.note_worker import (
    process_note_job,
)
from services.NoteService import NoteService
from services.TestRoboService import TestRoboService
from schemas.pydantic.NoteSchema import NoteCreate
from repositories.NoteRepository import NoteRepository
from configs.RoboConfig import RoboConfig


@pytest.fixture
def robo_service():
    """Create a RoboService instance for testing."""
    config = RoboConfig(
        api_key="test_key",
        model_name="test_model",
        is_test=True,
    )
    return TestRoboService(config)


@pytest.fixture
def note_service(test_db_session, queue_service):
    """Create a note service with test dependencies."""
    return NoteService(
        db=test_db_session,
        queue_service=queue_service,
    )


@pytest.fixture
def queue_service(redis_connection):
    """Create a queue service with test Redis connection."""
    from rq import Queue

    queue = Queue(
        "test_note_processing",
        connection=redis_connection,
    )
    return RQNoteQueue(queue=queue)


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
        note.enrichment_data["content"]
        == "Test note content"
    )
    assert note.enrichment_data["metadata"] == {
        "processed": True
    }
    assert note.enrichment_data["tokens_used"] == 0
    assert (
        note.enrichment_data["model_name"] == "test_model"
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
        note.enrichment_data["content"]
        == "Processed after retries"
    )
    assert note.enrichment_data["metadata"]["attempts"] == 3
