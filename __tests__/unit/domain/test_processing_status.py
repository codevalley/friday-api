import pytest
from domain.values import ProcessingStatus
from domain.note import NoteData


def test_default_status():
    """Test default processing status."""
    assert (
        ProcessingStatus.default()
        == ProcessingStatus.NOT_PROCESSED
    )


def test_terminal_states():
    """Test terminal state detection."""
    terminal_states = {
        ProcessingStatus.COMPLETED,
        ProcessingStatus.FAILED,
        ProcessingStatus.SKIPPED,
    }
    non_terminal_states = {
        ProcessingStatus.NOT_PROCESSED,
        ProcessingStatus.PENDING,
        ProcessingStatus.PROCESSING,
    }

    for state in terminal_states:
        assert state.is_terminal_state()

    for state in non_terminal_states:
        assert not state.is_terminal_state()


def test_valid_transitions():
    """Test valid state transitions."""
    valid_cases = [
        (
            ProcessingStatus.NOT_PROCESSED,
            ProcessingStatus.PENDING,
        ),
        (
            ProcessingStatus.NOT_PROCESSED,
            ProcessingStatus.SKIPPED,
        ),
        (
            ProcessingStatus.PENDING,
            ProcessingStatus.PROCESSING,
        ),
        (ProcessingStatus.PENDING, ProcessingStatus.FAILED),
        (
            ProcessingStatus.PROCESSING,
            ProcessingStatus.COMPLETED,
        ),
        (
            ProcessingStatus.PROCESSING,
            ProcessingStatus.FAILED,
        ),
        (ProcessingStatus.FAILED, ProcessingStatus.PENDING),
        (
            ProcessingStatus.SKIPPED,
            ProcessingStatus.PENDING,
        ),
    ]

    for current, next_state in valid_cases:
        assert current.can_transition_to(next_state)


def test_invalid_transitions():
    """Test invalid state transitions."""
    invalid_cases = [
        (
            ProcessingStatus.NOT_PROCESSED,
            ProcessingStatus.COMPLETED,
        ),
        (
            ProcessingStatus.COMPLETED,
            ProcessingStatus.FAILED,
        ),
        (
            ProcessingStatus.COMPLETED,
            ProcessingStatus.PENDING,
        ),
        (
            ProcessingStatus.PROCESSING,
            ProcessingStatus.NOT_PROCESSED,
        ),
    ]

    for current, next_state in invalid_cases:
        assert not current.can_transition_to(next_state)


def test_note_status_update():
    """Test note status updates."""
    note = NoteData(
        content="Test note", user_id="test_user"
    )

    # Test initial state
    assert (
        note.processing_status
        == ProcessingStatus.NOT_PROCESSED
    )

    # Test valid transition
    note.update_processing_status(ProcessingStatus.PENDING)
    assert (
        note.processing_status == ProcessingStatus.PENDING
    )

    # Test invalid transition
    with pytest.raises(ValueError):
        note.update_processing_status(
            ProcessingStatus.NOT_PROCESSED
        )
