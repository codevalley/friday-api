import pytest
from datetime import datetime, timezone
from sqlalchemy.exc import IntegrityError

from models.ActivityModel import Activity
from models.MomentModel import Moment


def test_moment_model_initialization(
    db_session, sample_activity, sample_moment
):
    """Test that a moment can be created with valid data"""
    activity = Activity(**sample_activity)
    db_session.add(activity)
    db_session.flush()

    moment = Moment(
        activity_id=activity.id,
        timestamp=sample_moment["timestamp"],
        data=sample_moment["data"],
    )

    assert moment.activity_id == activity.id
    assert moment.timestamp == sample_moment["timestamp"]
    assert moment.data == sample_moment["data"]


def test_moment_model_db_persistence(
    db_session, sample_activity, sample_moment
):
    """Test that a moment can be persisted to the database"""
    activity = Activity(**sample_activity)
    db_session.add(activity)
    db_session.flush()

    moment = Moment(
        activity_id=activity.id,
        timestamp=sample_moment["timestamp"],
        data=sample_moment["data"],
    )
    db_session.add(moment)
    db_session.commit()

    saved_moment = (
        db_session.query(Moment)
        .filter_by(activity_id=activity.id)
        .first()
    )
    assert saved_moment is not None
    assert saved_moment.data == sample_moment["data"]


def test_moment_activity_relationship(
    db_session, sample_activity, sample_moment
):
    """Test the relationship between Moment and Activity models"""
    activity = Activity(**sample_activity)
    db_session.add(activity)
    db_session.flush()

    moment = Moment(
        activity_id=activity.id,
        timestamp=sample_moment["timestamp"],
        data=sample_moment["data"],
    )
    db_session.add(moment)
    db_session.commit()

    assert moment.activity == activity
    assert moment.activity.name == sample_activity["name"]


def test_moment_cascade_delete(
    db_session, sample_activity, sample_moment
):
    """Test that moments are deleted when their activity is deleted"""
    activity = Activity(**sample_activity)
    db_session.add(activity)
    db_session.flush()

    moment = Moment(
        activity_id=activity.id,
        timestamp=sample_moment["timestamp"],
        data=sample_moment["data"],
    )
    db_session.add(moment)
    db_session.commit()

    # Delete the activity
    db_session.delete(activity)
    db_session.commit()

    # Check that the moment was also deleted
    assert (
        db_session.query(Moment)
        .filter_by(id=moment.id)
        .first()
        is None
    )


def test_moment_required_fields(db_session):
    """Test that required fields raise appropriate errors when missing"""
    moment = Moment()  # Missing required fields
    db_session.add(moment)

    with pytest.raises(IntegrityError):
        db_session.commit()


def test_moment_data_validation(
    db_session, sample_activity
):
    """Test that moment data must be a valid JSON object"""
    activity = Activity(**sample_activity)
    db_session.add(activity)
    db_session.flush()

    moment = Moment(
        activity_id=activity.id,
        timestamp=datetime.now(timezone.utc),
        data="invalid_json",  # Should be a dict
    )

    with pytest.raises(ValueError):
        moment.validate_data()
