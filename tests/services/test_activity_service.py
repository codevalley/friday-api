import pytest
from domain.activity import ActivityData
from utils.errors.exceptions import ValidationError
from services.ActivityService import ActivityService


class TestActivityService:
    """Test cases for ActivityService."""

    @pytest.fixture
    def service(self, db_session):
        """Create an ActivityService instance for testing."""
        return ActivityService(db_session)

    def test_validate_color_invalid(self, service):
        """Test color validation with invalid inputs."""
        # Test invalid color format
        try:
            service._validate_color("invalid")
            pytest.fail(
                "Should have raised ValidationError"
            )
        except ValidationError as e:
            assert str(e) == (
                "Invalid color format: invalid. Must be in #RRGGBB format"
            )

        # Test invalid hex characters
        try:
            service._validate_color("#GGHHII")
            pytest.fail(
                "Should have raised ValidationError"
            )
        except ValidationError as e:
            assert str(e) == (
                "Invalid color format: #GGHHII. Must be in #RRGGBB format"
            )

    def test_validate_activity_schema_invalid(
        self, service
    ):
        """Test schema validation with invalid inputs."""
        # Test missing required fields
        try:
            service._validate_activity_schema(
                {"invalid": "schema"}
            )
            pytest.fail(
                "Should have raised ValidationError"
            )
        except ValidationError as e:
            assert str(e) == (
                "Activity schema must contain 'type' and 'properties' fields"
            )

        # Test non-dict schema
        try:
            service._validate_activity_schema("not a dict")
            pytest.fail(
                "Should have raised ValidationError"
            )
        except ValidationError as e:
            assert str(e) == "Schema must be a dictionary"

    def test_to_graphql_json_format(self, service):
        """Test conversion of activity data to GraphQL format."""
        activity_data = ActivityData(
            id=1,
            name="Test Activity",
            color="#FF0000",
            activity_schema={
                "type": "object",
                "properties": {},
            },
        )

        graphql_json = service.to_graphql_json(
            activity_data
        )
        assert graphql_json["id"] == 1
        assert graphql_json["name"] == "Test Activity"
        assert graphql_json["color"] == "#FF0000"
        assert graphql_json["activitySchema"] == {
            "type": "object",
            "properties": {},
        }

    def test_validate_color_valid(self, service):
        """Test color validation with valid inputs."""
        # These should not raise any exceptions
        service._validate_color("#FF0000")  # Red
        service._validate_color("#00FF00")  # Green
        service._validate_color("#0000FF")  # Blue
        service._validate_color(
            "#123456"
        )  # Random valid color

    def test_validate_activity_schema_valid(self, service):
        """Test schema validation with valid inputs."""
        # Test valid schema
        valid_schema = {
            "type": "object",
            "properties": {
                "test_field": {"type": "string"}
            },
        }
        service._validate_activity_schema(valid_schema)

        # Test valid schema with additional fields
        valid_schema_with_extra = {
            "type": "object",
            "properties": {
                "test_field": {"type": "string"}
            },
            "required": ["test_field"],
            "additionalProperties": False,
        }
        service._validate_activity_schema(
            valid_schema_with_extra
        )
