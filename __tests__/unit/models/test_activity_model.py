"""Test ActivityModel class."""

import pytest
from datetime import datetime, timezone
from sqlalchemy.exc import IntegrityError

from orm.ActivityModel import Activity
from orm.MomentModel import Moment


def test_activity_initialization():
    """Test basic activity model initialization."""
    activity = Activity(
        user_id="test-user-id",
        name="Test Activity",
        description="Test Description",
        activity_schema={
            "type": "object",
            "properties": {},
        },
        icon="📝",
        color="#FF0000",
        processing_status="pending",
        schema_render={"rendered": "schema"},
        processed_at=datetime(2023, 1, 1, tzinfo=timezone.utc),
    )

    assert activity.name == "Test Activity"
    assert activity.description == "Test Description"
    assert activity.icon == "📝"
    assert activity.color == "#FF0000"
    assert activity.activity_schema == {
        "type": "object",
        "properties": {},
    }
    assert activity.processing_status == "pending"
    assert activity.schema_render == {"rendered": "schema"}
    assert activity.processed_at == datetime(2023, 1, 1, tzinfo=timezone.utc)


def test_activity_database_persistence(
    test_db_session, sample_user
):
    """Test activity persistence in database."""
    activity = Activity(
        user_id=sample_user.id,
        name="Test Activity",
        description="Test Description",
        activity_schema={
            "type": "object",
            "properties": {},
        },
        icon="📝",
        color="#FF0000",
        processing_status="pending",
        schema_render={"rendered": "schema"},
        processed_at=datetime(2023, 1, 1, tzinfo=timezone.utc),
    )
    test_db_session.add(activity)
    test_db_session.commit()
    test_db_session.refresh(activity)

    saved_activity = (
        test_db_session.query(Activity)
        .filter(Activity.id == activity.id)
        .first()
    )
    assert saved_activity is not None
    assert saved_activity.name == "Test Activity"
    assert saved_activity.user_id == sample_user.id
    assert isinstance(saved_activity.created_at, datetime)
    assert saved_activity.updated_at is None
    assert saved_activity.processing_status == "pending"
    assert saved_activity.schema_render == {"rendered": "schema"}
    assert saved_activity.processed_at == datetime(2023, 1, 1, tzinfo=timezone.utc)


def test_activity_relationships(
    test_db_session, sample_activity
):
    """Test activity relationships with user and moments."""
    # Test user relationship
    assert sample_activity.user is not None
    # Don't test the exact username since it's randomly generated
    assert sample_activity.user.username.startswith(
        "testuser_"
    )

    # Test moments relationship
    moment = Moment(
        user_id=sample_activity.user_id,
        activity_id=sample_activity.id,
        data={"test": "data"},
        timestamp=datetime.now(timezone.utc),
    )
    test_db_session.add(moment)
    test_db_session.commit()
    test_db_session.refresh(
        sample_activity
    )  # Refresh to update relationships

    assert len(sample_activity.moments) == 1
    assert sample_activity.moments[0].data == {
        "test": "data"
    }
    assert sample_activity.moment_count == 1


def test_activity_constraints(test_db_session, sample_user):
    """Test activity model constraints."""
    # Test name uniqueness per user
    activity1 = Activity(
        user_id=sample_user.id,
        name="Same Name",
        description="First Activity",
        activity_schema={
            "type": "object",
            "properties": {},
        },
        icon="📝",
        color="#FF0000",
        processing_status="pending",
        schema_render={"rendered": "schema"},
        processed_at=datetime(2023, 1, 1, tzinfo=timezone.utc),
    )
    test_db_session.add(activity1)
    test_db_session.commit()

    # Try to create another activity with the same name for the same user
    with pytest.raises(IntegrityError):
        activity2 = Activity(
            user_id=sample_user.id,
            name="Same Name",
            description="Second Activity",
            activity_schema={
                "type": "object",
                "properties": {},
            },
            icon="📝",
            color="#00FF00",
            processing_status="pending",
            schema_render={"rendered": "schema"},
            processed_at=datetime(2023, 1, 1, tzinfo=timezone.utc),
        )
        test_db_session.add(activity2)
        test_db_session.commit()


def test_activity_schema_validation(
    test_db_session, sample_user
):
    """Test activity schema validation."""
    # Test valid schema
    valid_schema = {
        "type": "object",
        "properties": {
            "field1": {"type": "string"},
            "field2": {"type": "number"},
        },
        "required": ["field1"],
    }

    activity = Activity(
        user_id=sample_user.id,
        name="Schema Test",
        description="Testing Schema",
        activity_schema=valid_schema,
        icon="📝",
        color="#FF0000",
        processing_status="pending",
        schema_render={"rendered": "schema"},
        processed_at=datetime(2023, 1, 1, tzinfo=timezone.utc),
    )
    test_db_session.add(activity)
    test_db_session.commit()

    assert activity.activity_schema == valid_schema

    # Test invalid schema format
    with pytest.raises(
        ValueError,
        match="Invalid schema: activity_schema must be a valid JSON object",
    ):
        Activity(
            user_id=sample_user.id,
            name="Invalid Schema",
            description="Testing Invalid Schema",
            activity_schema="not a dict",
            icon="📝",
            color="#FF0000",
            processing_status="pending",
            schema_render={"rendered": "schema"},
            processed_at=datetime(2023, 1, 1, tzinfo=timezone.utc),
        )

    # Test invalid schema structure
    with pytest.raises(
        ValueError,
        match=(
            r"Invalid schema: Invalid JSON Schema: "
            "'type' is a required property"
        ),
    ):
        Activity(
            user_id=sample_user.id,
            name="Invalid Schema Structure",
            description="Testing Invalid Schema Structure",
            activity_schema={"invalid": "schema"},
            icon="📝",
            color="#FF0000",
            processing_status="pending",
            schema_render={"rendered": "schema"},
            processed_at=datetime(2023, 1, 1, tzinfo=timezone.utc),
        )


def test_color_validation(test_db_session, sample_user):
    """Test color validation."""
    # Test valid colors
    valid_colors = [
        "#FF0000",
        "#00FF00",
        "#0000FF",
        "#123456",
    ]

    for color in valid_colors:
        activity = Activity(
            user_id=sample_user.id,
            name=f"Color Test {color}",
            description="Testing Color",
            activity_schema={
                "type": "object",
                "properties": {},
            },
            icon="📝",
            color=color,
            processing_status="pending",
            schema_render={"rendered": "schema"},
            processed_at=datetime(2023, 1, 1, tzinfo=timezone.utc),
        )
        test_db_session.add(activity)
        test_db_session.commit()
        assert activity.color == color

    # Test invalid color format
    with pytest.raises(
        ValueError,
        match="Color must be a valid hex code \\(e\\.g\\., #FF0000\\)",
    ):
        Activity(
            user_id=sample_user.id,
            name="Invalid Color",
            description="Testing Invalid Color",
            activity_schema={
                "type": "object",
                "properties": {},
            },
            icon="📝",
            color="invalid-color",
            processing_status="pending",
            schema_render={"rendered": "schema"},
            processed_at=datetime(2023, 1, 1, tzinfo=timezone.utc),
        )

    # Test invalid hex characters
    with pytest.raises(
        ValueError,
        match="Color must be a valid hex code \\(e\\.g\\., #FF0000\\)",
    ):
        Activity(
            user_id=sample_user.id,
            name="Invalid Hex",
            description="Testing Invalid Hex",
            activity_schema={
                "type": "object",
                "properties": {},
            },
            icon="📝",
            color="#GGHHII",
            processing_status="pending",
            schema_render={"rendered": "schema"},
            processed_at=datetime(2023, 1, 1, tzinfo=timezone.utc),
        )


def test_cascade_deletion(test_db_session, sample_activity):
    """Test cascade deletion of moments when activity is deleted."""
    # Create some moments
    for i in range(3):
        moment = Moment(
            user_id=sample_activity.user_id,
            activity_id=sample_activity.id,
            data={"test": f"data{i}"},
            timestamp=datetime.now(timezone.utc),
        )
        test_db_session.add(moment)
    test_db_session.commit()
    test_db_session.refresh(
        sample_activity
    )  # Refresh to update moment_count

    # Verify moments exist
    assert sample_activity.moment_count == 3

    # Delete activity
    test_db_session.delete(sample_activity)
    test_db_session.commit()

    # Verify moments were deleted
    moments = (
        test_db_session.query(Moment)
        .filter(Moment.activity_id == sample_activity.id)
        .all()
    )
    assert len(moments) == 0


def test_string_representation(sample_activity):
    """Test string representation of activity."""
    expected_str = (
        f"<Activity(id={sample_activity.id}, "
        f"name='{sample_activity.name}')>"
    )
    assert str(sample_activity) == expected_str


def test_schema_validation_methods(
    test_db_session, sample_user
):
    """Test schema validation methods."""
    # Test valid moment data
    activity = Activity(
        user_id=sample_user.id,
        name="Validation Test",
        description="Testing Validation",
        activity_schema={
            "type": "object",
            "properties": {
                "note": {"type": "string"},
                "rating": {"type": "number"},
            },
            "required": ["note"],
        },
        icon="📝",
        color="#FF0000",
        processing_status="pending",
        schema_render={"rendered": "schema"},
        processed_at=datetime(2023, 1, 1, tzinfo=timezone.utc),
    )
    test_db_session.add(activity)
    test_db_session.commit()

    # Valid data should not raise any exceptions
    activity.validate_moment_data(
        {"note": "Test note", "rating": 5}
    )

    # Missing required field
    with pytest.raises(
        ValueError, match="'note' is a required property"
    ):
        activity.validate_moment_data({"rating": 5})

    # Invalid type
    with pytest.raises(
        ValueError, match="5 is not of type 'string'"
    ):
        activity.validate_moment_data(
            {"note": 5, "rating": 5}
        )

    # Additional properties when not allowed
    activity.activity_schema["additionalProperties"] = False
    with pytest.raises(
        ValueError,
        match="Additional properties are not allowed",
    ):
        activity.validate_moment_data(
            {"note": "Test", "rating": 5, "extra": "field"}
        )


def test_activity_initialization_validation():
    """Test activity initialization validation."""
    # Test missing user_id
    with pytest.raises(
        ValueError, match="user_id is required"
    ):
        Activity(
            name="Test Activity",
            description="Test Description",
            activity_schema={
                "type": "object",
                "properties": {},
            },
            icon="📝",
            color="#FF0000",
            processing_status="pending",
            schema_render={"rendered": "schema"},
            processed_at=datetime(2023, 1, 1, tzinfo=timezone.utc),
        )


def test_schema_meta_validation(
    test_db_session, sample_user
):
    """Test schema meta-schema validation."""
    # Test schema without properties
    with pytest.raises(
        ValueError,
        match=(
            r"Invalid schema: Invalid JSON Schema: "
            "'properties' is a required property"
        ),
    ):
        Activity(
            user_id=sample_user.id,
            name="Invalid Meta Schema",
            description="Testing Invalid Meta Schema",
            activity_schema={
                "type": "object",
            },
            icon="📝",
            color="#FF0000",
            processing_status="pending",
            schema_render={"rendered": "schema"},
            processed_at=datetime(2023, 1, 1, tzinfo=timezone.utc),
        )

    # Test schema with invalid type
    with pytest.raises(
        ValueError,
        match=(
            r"Invalid schema: activity_schema must be a valid JSON object"
        ),
    ):
        Activity(
            user_id=sample_user.id,
            name="Invalid Type Schema",
            description="Testing Invalid Type Schema",
            activity_schema={
                "type": "array",
                "properties": {},
            },
            icon="📝",
            color="#FF0000",
            processing_status="pending",
            schema_render={"rendered": "schema"},
            processed_at=datetime(2023, 1, 1, tzinfo=timezone.utc),
        )


def test_moment_data_complex_validation(
    test_db_session, sample_user
):
    """Test complex moment data validation scenarios."""
    activity = Activity(
        user_id=sample_user.id,
        name="Complex Validation",
        description="Testing Complex Validation",
        activity_schema={
            "type": "object",
            "properties": {
                "nested": {
                    "type": "object",
                    "properties": {
                        "field": {"type": "string"}
                    },
                    "required": ["field"],
                },
                "array": {
                    "type": "array",
                    "items": {"type": "number"},
                },
            },
            "required": ["nested"],
        },
        icon="📝",
        color="#FF0000",
        processing_status="pending",
        schema_render={"rendered": "schema"},
        processed_at=datetime(2023, 1, 1, tzinfo=timezone.utc),
    )
    test_db_session.add(activity)
    test_db_session.commit()

    # Test nested object validation
    with pytest.raises(
        ValueError, match="'nested' is a required property"
    ):
        activity.validate_moment_data({"array": [1, 2, 3]})

    # Test nested field type validation
    with pytest.raises(
        ValueError, match="'field' is a required property"
    ):
        activity.validate_moment_data({"nested": {}})

    # Test array type validation
    with pytest.raises(
        ValueError, match="'string' is not of type 'number'"
    ):
        activity.validate_moment_data(
            {
                "nested": {"field": "valid"},
                "array": [1, "string", 3],
            }
        )

    # Test valid complex data
    activity.validate_moment_data(
        {"nested": {"field": "valid"}, "array": [1, 2, 3]}
    )


def test_string_representation_edge_cases(
    test_db_session, sample_user
):
    """Test string representation with edge cases."""
    # Test with special characters in name
    activity = Activity(
        user_id=sample_user.id,
        name="Test 'quotes' and \"double quotes\"",
        description="Testing special characters",
        activity_schema={
            "type": "object",
            "properties": {},
        },
        icon="📝",
        color="#FF0000",
        processing_status="pending",
        schema_render={"rendered": "schema"},
        processed_at=datetime(2023, 1, 1, tzinfo=timezone.utc),
    )
    test_db_session.add(activity)
    test_db_session.commit()

    expected_str = (
        f"<Activity(id={activity.id}, "
        f"name='Test \\'quotes\\' and \"double quotes\"')>"
    )
    assert str(activity) == expected_str

    # Test with very long name
    long_name = "A" * 100
    activity = Activity(
        user_id=sample_user.id,
        name=long_name,
        description="Testing long name",
        activity_schema={
            "type": "object",
            "properties": {},
        },
        icon="📝",
        color="#FF0000",
        processing_status="pending",
        schema_render={"rendered": "schema"},
        processed_at=datetime(2023, 1, 1, tzinfo=timezone.utc),
    )
    test_db_session.add(activity)
    test_db_session.commit()

    expected_str = (
        f"<Activity(id={activity.id}, "
        f"name='{long_name}')>"
    )
    assert str(activity) == expected_str
