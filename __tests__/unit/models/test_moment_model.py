"""Test MomentModel class."""

import uuid
from datetime import datetime, timezone

import pytest

from orm.ActivityModel import Activity
from orm.MomentModel import Moment
from orm.UserModel import User
from orm.NoteModel import Note


@pytest.fixture
def sample_user(test_db_session) -> User:
    """Create a sample user for testing."""
    user = User(
        username=f"testuser_{uuid.uuid4().hex[:8]}",
        key_id=str(uuid.uuid4()),
        user_secret="test-secret-hash",
    )
    test_db_session.add(user)
    test_db_session.commit()
    test_db_session.refresh(user)
    return user


@pytest.fixture
def sample_activity(
    test_db_session, sample_user
) -> Activity:
    """Create a sample activity for testing."""
    activity = Activity(
        name=f"Test Activity {uuid.uuid4().hex[:8]}",
        description="Test Description",
        user_id=sample_user.id,
        activity_schema={
            "type": "object",
            "properties": {"notes": {"type": "string"}},
            "required": ["notes"],
        },
        icon="📝",
        color="#FF0000",
    )
    test_db_session.add(activity)
    test_db_session.commit()
    test_db_session.refresh(activity)
    return activity


@pytest.fixture
def sample_note(test_db_session, sample_user) -> Note:
    """Create a sample note for testing."""
    note = Note(
        user_id=sample_user.id,
        content="Test Note Content",
        attachments=[],
    )
    test_db_session.add(note)
    test_db_session.commit()
    test_db_session.refresh(note)
    return note


def test_moment_model_initialization(
    sample_activity: Activity, sample_user: User
) -> None:
    """Test that a moment can be created with valid data."""
    moment = Moment(
        activity_id=sample_activity.id,
        user_id=sample_user.id,
        data={"notes": "Test moment"},
        timestamp=datetime.now(timezone.utc),
    )

    assert moment.activity_id == sample_activity.id
    assert moment.user_id == sample_user.id
    assert moment.data == {"notes": "Test moment"}
    assert moment.note_id is None
    assert moment.note is None


def test_moment_with_note(
    test_db_session,
    sample_activity: Activity,
    sample_user: User,
    sample_note: Note,
) -> None:
    """Test moment creation with an associated note."""
    moment = Moment(
        activity_id=sample_activity.id,
        user_id=sample_user.id,
        data={"notes": "Test moment"},
        timestamp=datetime.now(timezone.utc),
        note_id=sample_note.id,
    )
    test_db_session.add(moment)
    test_db_session.commit()
    test_db_session.refresh(moment)

    assert moment.note_id == sample_note.id
    assert moment.note == sample_note


def test_moment_note_relationship_optional(
    test_db_session,
    sample_activity: Activity,
    sample_user: User,
    sample_note: Note,
) -> None:
    """Test that note relationship is optional and can be modified."""
    # Create moment without note
    moment = Moment(
        activity_id=sample_activity.id,
        user_id=sample_user.id,
        data={"notes": "Test moment"},
        timestamp=datetime.now(timezone.utc),
    )
    test_db_session.add(moment)
    test_db_session.commit()

    # Verify no note
    assert moment.note_id is None
    assert moment.note is None

    # Add note
    moment.note_id = sample_note.id
    test_db_session.commit()
    test_db_session.refresh(moment)

    # Verify note was added
    assert moment.note_id == sample_note.id
    assert moment.note == sample_note

    # Remove note
    moment.note_id = None
    test_db_session.commit()
    test_db_session.refresh(moment)

    # Verify note was removed
    assert moment.note_id is None
    assert moment.note is None


def test_moment_model_db_persistence(
    test_db_session,
    sample_activity: Activity,
    sample_user: User,
) -> None:
    """Test that a moment can be persisted to the database."""
    moment = Moment(
        activity_id=sample_activity.id,
        user_id=sample_user.id,
        data={"notes": "Test moment"},
        timestamp=datetime.now(timezone.utc),
    )
    test_db_session.add(moment)
    test_db_session.commit()
    test_db_session.refresh(moment)

    saved_moment = (
        test_db_session.query(Moment)
        .filter(Moment.activity_id == sample_activity.id)
        .first()
    )

    assert saved_moment is not None
    assert saved_moment.activity_id == sample_activity.id
    assert saved_moment.user_id == sample_user.id
    assert saved_moment.data == {"notes": "Test moment"}


def test_moment_activity_relationship(
    test_db_session,
    sample_activity: Activity,
    sample_user: User,
) -> None:
    """Test the relationship between Moment and Activity models."""
    moment = Moment(
        activity_id=sample_activity.id,
        user_id=sample_user.id,
        data={"notes": "Test moment"},
        timestamp=datetime.now(timezone.utc),
    )
    test_db_session.add(moment)
    test_db_session.commit()
    test_db_session.refresh(moment)

    assert moment.activity == sample_activity
    assert moment in sample_activity.moments


def test_moment_cascade_delete(
    test_db_session,
    sample_activity: Activity,
    sample_user: User,
    sample_note: Note,
) -> None:
    """Test that moments are deleted when their activity is deleted."""
    moment = Moment(
        activity_id=sample_activity.id,
        user_id=sample_user.id,
        data={"notes": "Test moment"},
        timestamp=datetime.now(timezone.utc),
        note_id=sample_note.id,
    )
    test_db_session.add(moment)
    test_db_session.commit()
    test_db_session.refresh(moment)

    # Delete activity should cascade to moment
    test_db_session.delete(sample_activity)
    test_db_session.commit()

    # Verify moment is deleted but note remains
    result = test_db_session.execute(
        Moment.__table__.select().where(
            Moment.id == moment.id
        )
    )
    assert result.first() is None

    # Verify note still exists
    saved_note = (
        test_db_session.query(Note)
        .filter_by(id=sample_note.id)
        .first()
    )
    assert saved_note is not None


def test_moment_note_set_null_on_delete(
    test_db_session,
    sample_activity: Activity,
    sample_user: User,
    sample_note: Note,
) -> None:
    """Test that note_id is set to NULL when note is deleted."""
    moment = Moment(
        activity_id=sample_activity.id,
        user_id=sample_user.id,
        data={"notes": "Test moment"},
        timestamp=datetime.now(timezone.utc),
        note_id=sample_note.id,
    )
    test_db_session.add(moment)
    test_db_session.commit()
    test_db_session.refresh(moment)

    # Delete note
    test_db_session.delete(sample_note)
    test_db_session.commit()
    test_db_session.refresh(moment)

    # Verify moment still exists but note_id is NULL
    assert moment.note_id is None
    assert moment.note is None


def test_moment_data_validation(
    test_db_session,
    sample_activity: Activity,
    sample_user: User,
) -> None:
    """Test that moment data is validated against activity schema."""
    # Test with invalid data structure
    with pytest.raises(
        ValueError,
        match="moment data must be a valid JSON object",
    ):
        Moment(
            activity_id=sample_activity.id,
            user_id=sample_user.id,
            data="not a dict",  # Invalid data type
            timestamp=datetime.now(timezone.utc),
        )

    # Test with missing required field in schema
    moment = Moment(
        activity_id=sample_activity.id,
        user_id=sample_user.id,
        data={
            "invalid": "data"
        },  # Missing required 'notes' field
        timestamp=datetime.now(timezone.utc),
    )
    test_db_session.add(moment)
    test_db_session.flush()  # This will load relationships

    with pytest.raises(ValueError):
        moment.validate_data(
            test_db_session
        )  # Validate with session

    # Test with valid data
    moment = Moment(
        activity_id=sample_activity.id,
        user_id=sample_user.id,
        data={"notes": "Test moment"},  # Valid data
        timestamp=datetime.now(timezone.utc),
    )
    test_db_session.add(moment)
    test_db_session.flush()  # This will load relationships

    # This should not raise any errors
    moment.validate_data(test_db_session)
    test_db_session.commit()


def test_moment_required_fields(
    test_db_session,
    sample_activity: Activity,
    sample_user: User,
) -> None:
    """Test that required fields raise appropriate errors when missing."""
    # Test missing user_id
    with pytest.raises(
        ValueError, match="user_id is required"
    ):
        Moment(
            activity_id=sample_activity.id,
            data={"notes": "Test moment"},
            timestamp=datetime.now(timezone.utc),
        )

    # Test missing activity_id
    with pytest.raises(
        ValueError, match="activity_id is required"
    ):
        Moment(
            user_id=sample_user.id,
            data={"notes": "Test moment"},
            timestamp=datetime.now(timezone.utc),
        )

    # Test missing data
    with pytest.raises(
        ValueError, match="data is required"
    ):
        Moment(
            activity_id=sample_activity.id,
            user_id=sample_user.id,
            timestamp=datetime.now(timezone.utc),
        )
