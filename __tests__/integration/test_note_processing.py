"""Integration tests for note processing flow."""

import pytest

from domain.values import ProcessingStatus
from infrastructure.queue.RQNoteQueue import RQNoteQueue
from infrastructure.queue.note_worker import (
    process_note_job,
)
from services.NoteService import NoteService
from services.RoboService import RoboService
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
    return RoboService(config)


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


def test_note_processing_flow(
    test_db_session,
    note_service,
    queue_service,
    sample_user,
    robo_service,
):
    """Test end-to-end note processing flow.

    Should:
    1. Create note via NoteService
    2. Verify note is enqueued
    3. Process note with worker
    4. Verify final note state
    """
    # Create note
    note_data = NoteCreate(
        content="Test note for processing",
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

    assert (
        note.processing_status == ProcessingStatus.PENDING
    )

    # Get job from queue
    job = queue_service.queue.jobs[0]
    assert job is not None
    assert job.args[0] == note.id

    # Process note
    process_note_job(
        note.id, test_db_session, robo_service, note_repo
    )

    # Refresh session to see worker's changes
    test_db_session.expire_all()
    test_db_session.refresh(note)

    # Verify final state
    assert (
        note.processing_status == ProcessingStatus.COMPLETED
    )
    assert note.enrichment_data is not None
    assert note.processed_at is not None


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
    def mock_enrich_note(content):
        raise Exception("Test processing failure")

    robo_service.enrich_note = mock_enrich_note

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
    """Test note processing retry capability."""
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
    attempt = 0

    def mock_enrich_note(content):
        nonlocal attempt
        attempt += 1
        if attempt < 3:
            raise Exception(f"Test failure {attempt}")
        return {"enriched": True, "attempts": attempt}

    robo_service.enrich_note = mock_enrich_note

    # Process note
    process_note_job(
        note.id, test_db_session, robo_service, note_repo
    )

    # Refresh session to see worker's changes
    test_db_session.expire_all()
    test_db_session.refresh(note)

    # Verify final state
    assert (
        note.processing_status == ProcessingStatus.COMPLETED
    )
    assert note.enrichment_data is not None
    assert note.enrichment_data["attempts"] == 3
    assert note.processed_at is not None
