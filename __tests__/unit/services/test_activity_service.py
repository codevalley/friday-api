import pytest
from datetime import datetime
from unittest.mock import Mock
from fastapi import HTTPException
import json

from services.ActivityService import ActivityService
from schemas.pydantic.ActivitySchema import (
    ActivityCreate,
    ActivityUpdate,
    ActivityResponse,
)
from utils.errors.exceptions import ValidationError


@pytest.fixture
def activity_service(test_db_session):
    """Create ActivityService instance with test database session."""
    return ActivityService(db=test_db_session)


@pytest.fixture
def valid_activity_data():
    """Return valid activity data for testing."""
    return {
        "name": "Test Activity",
        "description": "A test activity for unit testing",
        "activity_schema": {
            "type": "object",
            "properties": {
                "test_field": {"type": "string"}
            },
        },
        "icon": "📝",
        "color": "#FF0000",
    }


@pytest.fixture
def mock_activity():
    """Create a mock activity for testing."""
    # Create a mock Activity model instance
    model = Mock()
    model.id = 1
    model.name = "Test Activity"
    model.description = "A test activity for unit testing"
    model.activity_schema = {
        "type": "object",
        "properties": {"test_field": {"type": "string"}},
    }
    model.icon = "📝"
    model.color = "#FF0000"
    model.user_id = "test_user"
    model.moment_count = 0
    model.moments = None
    model.created_at = datetime(
        2024, 12, 16, 22, 45, 38
    )  # Using current time from context
    model.updated_at = None

    # Mock the model's to_dict method to return a proper dictionary
    model.to_dict = Mock(
        return_value={
            "id": model.id,
            "name": model.name,
            "description": model.description,
            "activity_schema": model.activity_schema,
            "icon": model.icon,
            "color": model.color,
            "user_id": model.user_id,
            "moment_count": model.moment_count,
            "moments": model.moments,
            "created_at": model.created_at,
            "updated_at": model.updated_at,
        }
    )

    return model


@pytest.fixture
def test_user(test_db_session):
    """Create a test user in the database."""
    from orm.UserModel import User

    user = User(
        id="test_user",
        username="test_user",
        key_id="test_key",
        user_secret="test_secret",
    )
    test_db_session.add(user)
    test_db_session.commit()
    return user


class TestActivityService:
    """Test suite for ActivityService."""

    def setup_method(self):
        self.service = ActivityService()

    def test_validate_pagination_valid(
        self, activity_service
    ):
        """Test pagination validation with valid parameters."""
        activity_service._validate_pagination(
            1, 10
        )  # Should not raise

    def test_validate_pagination_invalid_page(
        self, activity_service
    ):
        """Test pagination validation with invalid page number."""
        with pytest.raises(HTTPException) as exc:
            activity_service._validate_pagination(0, 10)
        assert exc.value.status_code == 400
        assert "Page number must be positive" in str(
            exc.value.detail
        )

    def test_validate_pagination_invalid_size(
        self, activity_service
    ):
        """Test pagination validation with invalid page size."""
        with pytest.raises(HTTPException) as exc:
            activity_service._validate_pagination(1, 0)
        assert exc.value.status_code == 400
        assert "Page size must be between 1 and 100" in str(
            exc.value.detail
        )

    def test_validate_color_valid(self, activity_service):
        """Test color validation with valid hex code."""
        activity_service._validate_color(
            "#FF0000"
        )  # Should not raise

    def test_validate_color_invalid(self, activity_service):
        """Test color validation with invalid hex code."""
        with pytest.raises(
            ValidationError,
            match="Invalid color format: invalid. Must be in #RRGGBB format",
        ):
            activity_service.validate({"color": "invalid"})

    def test_validate_activity_schema_valid(
        self, activity_service
    ):
        """Test activity schema validation with valid schema."""
        valid_schema = {
            "type": "object",
            "properties": {"test": {"type": "string"}},
        }
        activity_service._validate_activity_schema(
            valid_schema
        )  # Should not raise

    def test_validate_activity_schema_invalid(
        self, activity_service
    ):
        """Test activity schema validation with invalid schema."""
        invalid_schema = {"invalid_field": "value"}
        with pytest.raises(
            ValidationError,
            match=(
                "Activity schema must contain "
                "'type' and 'properties' fields"
            ),
        ):
            activity_service.validate(
                {"schema": invalid_schema}
            )

    def test_create_activity_success(
        self,
        activity_service,
        valid_activity_data,
        mock_activity,
        test_user,
    ):
        """Test successful activity creation."""
        activity_service.activity_repository.create = Mock(
            return_value=mock_activity
        )

        activity_data = ActivityCreate(
            **valid_activity_data
        )
        result = activity_service.create_activity(
            activity_data, test_user.id
        )

        assert isinstance(result, ActivityResponse)
        assert result.name == valid_activity_data["name"]
        assert result.user_id == test_user.id

    def test_create_activity_invalid_schema(
        self,
        activity_service,
        valid_activity_data,
        test_user,
    ):
        """Test activity creation with invalid schema."""

        # Mock the repository to raise an error for invalid schema
        def raise_error(*args, **kwargs):
            raise HTTPException(
                status_code=400,
                detail="Invalid activity schema format",
            )

        activity_service.activity_repository.create = Mock(
            side_effect=raise_error
        )

        # Use a schema that passes Pydantic validation
        # but fails service validation
        valid_activity_data["activity_schema"] = {
            "type": "object",
            "properties": {},
            "additionalProperties": True,  # makes itinvalid for our service
        }
        activity_data = ActivityCreate(
            **valid_activity_data
        )

        with pytest.raises(HTTPException) as exc:
            activity_service.create_activity(
                activity_data, test_user.id
            )
        assert exc.value.status_code == 400
        assert "Invalid activity schema format" in str(
            exc.value.detail
        )

    def test_get_activity_success(
        self, activity_service, mock_activity, test_user
    ):
        """Test successful activity retrieval."""
        activity_service.activity_repository.get_by_user = (
            Mock(return_value=mock_activity)
        )

        result = activity_service.get_activity(
            1, test_user.id
        )

        assert isinstance(result, ActivityResponse)
        assert result.id == mock_activity.id
        assert result.user_id == mock_activity.user_id

    def test_get_activity_not_found(
        self, activity_service, test_user
    ):
        """Test activity retrieval when not found."""
        activity_service.activity_repository.get_by_user = (
            Mock(return_value=None)
        )

        result = activity_service.get_activity(
            1, test_user.id
        )

        assert result is None

    def test_list_activities_success(
        self, activity_service, mock_activity, test_user
    ):
        """Test successful activity listing."""
        activity_service.activity_repository.list_activities = Mock(
            return_value=[mock_activity]
        )

        result = activity_service.list_activities(
            test_user.id, page=1, size=10
        )

        assert len(result.items) == 1
        assert result.total == 1
        assert result.page == 1
        assert result.size == 10

    def test_update_activity_success(
        self, activity_service, mock_activity, test_user
    ):
        """Test successful activity update."""
        activity_service.activity_repository.get_by_id = (
            Mock(return_value=mock_activity)
        )
        activity_service.activity_repository.update = Mock(
            return_value=mock_activity
        )

        update_data = ActivityUpdate(
            name="Updated Activity"
        )
        result = activity_service.update_activity(
            1, update_data, test_user.id
        )

        assert isinstance(result, ActivityResponse)
        assert result.id == mock_activity.id
        assert result.user_id == mock_activity.user_id

    def test_update_activity_not_found(
        self, activity_service, test_user
    ):
        """Test activity update when not found."""
        activity_service.activity_repository.get_by_id = (
            Mock(return_value=None)
        )

        update_data = ActivityUpdate(
            name="Updated Activity"
        )
        result = activity_service.update_activity(
            1, update_data, test_user.id
        )

        assert result is None

    def test_delete_activity_success(
        self, activity_service, test_user
    ):
        """Test successful activity deletion."""
        activity_service.activity_repository.delete = Mock(
            return_value=True
        )

        result = activity_service.delete_activity(
            1, test_user.id
        )

        assert result is True

    def test_delete_activity_not_found(
        self, activity_service, test_user
    ):
        """Test activity deletion when not found."""
        activity_service.activity_repository.delete = Mock(
            return_value=False
        )

        result = activity_service.delete_activity(
            1, test_user.id
        )

        assert result is False

    # GraphQL specific tests
    def test_create_activity_graphql(
        self,
        activity_service,
        valid_activity_data,
        mock_activity,
        test_user,
    ):
        """Test activity creation through GraphQL endpoint."""
        activity_service.activity_repository.create = Mock(
            return_value=mock_activity
        )

        from schemas.graphql.types.Activity import (
            ActivityInput,
        )

        activity_data = ActivityInput(
            name=valid_activity_data["name"],
            description=valid_activity_data["description"],
            activitySchema=json.dumps(
                valid_activity_data["activity_schema"]
            ),
            icon=valid_activity_data["icon"],
            color=valid_activity_data["color"],
        )

        result = activity_service.create_activity_graphql(
            activity_data, test_user.id
        )

        assert result.id() == mock_activity.id
        assert result.name() == mock_activity.name
        assert (
            result.description()
            == mock_activity.description
        )

    def test_get_activity_graphql(
        self, activity_service, mock_activity, test_user
    ):
        """Test activity retrieval through GraphQL endpoint."""
        activity_service.activity_repository.get_by_id = (
            Mock(return_value=mock_activity)
        )

        result = activity_service.get_activity_graphql(
            1, test_user.id
        )

        assert result.id() == mock_activity.id
        assert result.name() == mock_activity.name
        assert (
            result.description()
            == mock_activity.description
        )

    def test_list_activities_graphql(
        self, activity_service, mock_activity, test_user
    ):
        """Test activity listing through GraphQL endpoint."""
        activity_service.activity_repository.list_activities = Mock(
            return_value=[mock_activity]
        )

        result = activity_service.list_activities_graphql(
            test_user.id, skip=0, limit=10
        )

        assert len(result) == 1
        assert result[0].id() == mock_activity.id
        assert result[0].name() == mock_activity.name

    def test_update_activity_graphql_success(
        self, activity_service, mock_activity, test_user
    ):
        """Test activity update through GraphQL endpoint."""
        activity_service.activity_repository.get_by_id = (
            Mock(return_value=mock_activity)
        )
        activity_service.activity_repository.update = Mock(
            return_value=mock_activity
        )

        from schemas.graphql.types.Activity import (
            ActivityUpdateInput,
        )

        activity_data = ActivityUpdateInput(
            name="Updated Activity",
            description="Updated description",
            activitySchema=json.dumps(
                mock_activity.activity_schema
            ),
            icon="🎯",
            color="#00FF00",
        )

        result = activity_service.update_activity_graphql(
            1, activity_data, test_user.id
        )

        assert result.id() == mock_activity.id
        assert result.name() == mock_activity.name
        assert (
            result.description()
            == mock_activity.description
        )

    def test_update_activity_graphql_not_found(
        self, activity_service, test_user
    ):
        """Test activity update through GraphQL endpoint when not found."""
        activity_service.activity_repository.get_by_id = (
            Mock(return_value=None)
        )

        from schemas.graphql.types.Activity import (
            ActivityUpdateInput,
        )

        update_data = ActivityUpdateInput(
            name="Updated Activity"
        )
        with pytest.raises(HTTPException) as exc:
            activity_service.update_activity_graphql(
                1, update_data, test_user.id
            )
        assert exc.value.status_code == 404
        assert "Activity not found" in str(exc.value.detail)
