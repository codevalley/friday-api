import pytest
from sqlalchemy.exc import IntegrityError

from models.ActivityModel import Activity
from models.MomentModel import Moment


def test_activity_model_initialization(sample_activity):
    """Test that an activity can be created with valid data"""
    activity = Activity(**sample_activity)

    assert activity.name == sample_activity["name"]
    assert (
        activity.description
        == sample_activity["description"]
    )
    assert (
        activity.activity_schema
        == sample_activity["activity_schema"]
    )
    assert activity.icon == sample_activity["icon"]
    assert activity.color == sample_activity["color"]
    assert activity.moments == []


def test_activity_model_db_persistence(
    db_session, sample_activity
):
    """Test that an activity can be persisted to the database"""
    activity = Activity(**sample_activity)
    db_session.add(activity)
    db_session.commit()

    saved_activity = (
        db_session.query(Activity)
        .filter_by(name=sample_activity["name"])
        .first()
    )
    assert saved_activity is not None
    assert saved_activity.name == sample_activity["name"]


def test_activity_moment_relationship(
    db_session, sample_activity, sample_moment
):
    """Test the relationship between Activity and Moment models"""
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

    # Refresh activity to get updated relationships
    db_session.refresh(activity)
    assert len(activity.moments) == 1
    assert activity.moments[0].data == sample_moment["data"]


def test_activity_name_unique_constraint(
    db_session, sample_activity
):
    """Test that activity names must be unique"""
    activity1 = Activity(**sample_activity)
    db_session.add(activity1)
    db_session.commit()

    activity2 = Activity(**sample_activity)
    db_session.add(activity2)

    with pytest.raises(IntegrityError):
        db_session.commit()


def test_activity_required_fields(db_session):
    """Test that required fields raise appropriate errors when missing"""
    activity = Activity()  # Missing required fields
    db_session.add(activity)

    with pytest.raises(IntegrityError):
        db_session.commit()


def test_activity_schema_validation():
    """Test that activity_schema must be a valid JSON object"""
    invalid_schema_activity = Activity(
        name="test_activity",
        activity_schema="invalid_json",  # Should be a dict
        icon="📝",
        color="#000000",
    )

    with pytest.raises(ValueError):
        invalid_schema_activity.validate_schema()
