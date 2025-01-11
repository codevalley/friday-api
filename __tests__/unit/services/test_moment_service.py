"""Tests for MomentService."""

import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import Mock
from fastapi import HTTPException

from services.MomentService import MomentService
from schemas.pydantic.MomentSchema import (
    MomentCreate,
    MomentUpdate,
    MomentResponse,
    MomentList,
)
from schemas.pydantic.PaginationSchema import (
    PaginationResponse,
)
from domain.exceptions import MomentTimestampError


@pytest.fixture
def moment_service(test_db_session):
    """Create MomentService instance with test database session."""
    return MomentService(db=test_db_session)


@pytest.fixture
def valid_moment_data():
    """Return valid moment data for testing."""
    return {
        "activity_id": 1,
        "data": {"test_field": "test value"},
        "timestamp": datetime.now(timezone.utc),
    }


@pytest.fixture
def mock_activity():
    """Mock activity for tests."""
    activity = Mock()
    activity.id = 1
    activity.name = "Test Activity"
    activity.description = "Test Description"
    activity.activity_schema = {
        "type": "object",
        "properties": {},
    }
    activity.icon = "test-icon"
    activity.color = "#000000"
    activity.user_id = "test-user-id"
    activity.moment_count = 0
    activity.created_at = datetime(
        2024, 12, 16, 18, 41, 0, 140952
    )
    activity.updated_at = datetime(
        2024, 12, 16, 18, 41, 0, 140952
    )
    activity.moments = None
    activity.processing_status = "NOT_PROCESSED"
    activity.schema_render = None
    activity.processed_at = None
    return activity


@pytest.fixture
def mock_moment(mock_activity):
    """Create a mock moment for testing."""
    moment = Mock()
    moment.id = 1
    moment.activity_id = 1
    moment.user_id = "test_user"
    moment.data = {"test_field": "test value"}
    moment.timestamp = datetime.now(timezone.utc)
    moment.created_at = datetime.now(timezone.utc)
    moment.updated_at = datetime.now(timezone.utc)
    moment.activity = mock_activity
    moment.note_id = 1
    return moment


class TestMomentService:
    """Test suite for MomentService."""

    def test_validate_pagination_valid(
        self, moment_service
    ):
        """Test pagination validation with valid parameters."""
        moment_service._validate_pagination(
            1, 10
        )  # Should not raise

    def test_validate_pagination_invalid_page(
        self, moment_service
    ):
        """Test pagination validation with invalid page number."""
        with pytest.raises(HTTPException) as exc:
            moment_service._validate_pagination(0, 10)
        assert exc.value.status_code == 400
        assert (
            "Page number must be positive"
            in exc.value.detail
        )

    def test_validate_pagination_invalid_size(
        self, moment_service
    ):
        """Test pagination validation with invalid page size."""
        with pytest.raises(HTTPException) as exc:
            moment_service._validate_pagination(1, 0)
        assert exc.value.status_code == 400
        assert (
            "Page size must be between 1 and 100"
            in exc.value.detail
        )

    def test_validate_timestamp_valid(self, moment_service):
        """Test timestamp validation with valid timestamp."""
        now = datetime.now(timezone.utc)
        moment_service._validate_timestamp(
            now
        )  # Should not raise

    def test_validate_timestamp_future(
        self, moment_service
    ):
        """Test timestamp validation with future timestamp."""
        future = datetime.now(timezone.utc) + timedelta(
            days=2
        )
        with pytest.raises(MomentTimestampError) as exc:
            moment_service._validate_timestamp(future)
        assert (
            str(exc.value)
            == "timestamp cannot be more than 1 day in the future"
        )

    def test_validate_timestamp_past(self, moment_service):
        """Test timestamp validation with past timestamp."""
        past = datetime.now(timezone.utc) - timedelta(
            days=365 * 11
        )
        with pytest.raises(MomentTimestampError) as exc:
            moment_service._validate_timestamp(past)
        assert (
            str(exc.value)
            == "timestamp cannot be more than 10 years in the past"
        )

    def test_validate_activity_ownership_valid(
        self, moment_service, mock_activity
    ):
        """Test activity ownership validation with valid ownership."""
        moment_service.activity_repository.get_by_user = (
            Mock(return_value=mock_activity)
        )
        moment_service._validate_activity_ownership(
            1, "test_user"
        )  # Should not raise

    def test_validate_activity_ownership_invalid(
        self, moment_service
    ):
        """Test activity ownership validation with invalid ownership."""
        moment_service.activity_repository.get_by_user = (
            Mock(return_value=None)
        )
        with pytest.raises(HTTPException) as exc:
            moment_service._validate_activity_ownership(
                1, "test_user"
            )
        assert exc.value.status_code == 404
        assert (
            "Activity not found or does not belong to user"
            in exc.value.detail
        )

    def test_create_moment_success(
        self,
        moment_service,
        valid_moment_data,
        mock_activity,
        mock_moment,
    ):
        """Test successful moment creation."""
        # Setup mocks
        moment_service.activity_repository.get_by_user = (
            Mock(return_value=mock_activity)
        )
        moment_service.activity_repository.validate_existence = Mock(
            return_value=mock_activity
        )
        moment_service.moment_repository.create = Mock(
            return_value=mock_moment
        )

        # Create moment
        moment_data = MomentCreate(**valid_moment_data)
        result = moment_service.create_moment(
            moment_data, "test_user"
        )

        assert isinstance(result, MomentResponse)
        assert result.id == mock_moment.id
        assert result.activity_id == mock_moment.activity_id

    def test_create_moment_invalid_activity(
        self, moment_service, valid_moment_data
    ):
        """Test moment creation with invalid activity."""
        moment_service.activity_repository.get_by_user = (
            Mock(return_value=None)
        )

        moment_data = MomentCreate(**valid_moment_data)
        with pytest.raises(HTTPException) as exc:
            moment_service.create_moment(
                moment_data, "test_user"
            )
        assert exc.value.status_code == 404
        assert "Activity not found" in exc.value.detail

    def test_create_moment_invalid_data(
        self,
        moment_service,
        valid_moment_data,
        mock_activity,
    ):
        """Test moment creation with invalid data."""
        # Setup mock to fail schema validation
        mock_activity.validate_moment_data.side_effect = (
            ValueError("Invalid data")
        )
        moment_service.activity_repository.get_by_user = (
            Mock(return_value=mock_activity)
        )
        moment_service.activity_repository.validate_existence = Mock(
            return_value=mock_activity
        )

        moment_data = MomentCreate(**valid_moment_data)
        with pytest.raises(HTTPException) as exc:
            moment_service.create_moment(
                moment_data, "test_user"
            )
        assert exc.value.status_code == 400
        assert (
            "Moment data does not match activity schema"
            in exc.value.detail
        )

    def test_list_moments_success(
        self, moment_service, mock_moment
    ):
        """Test successful moment listing."""
        mock_moment_list = MomentList(
            items=[mock_moment],
            total=1,
            page=1,
            size=10,
            pages=1,
        )
        moment_service.moment_repository.list_moments = (
            Mock(return_value=mock_moment_list)
        )

        result = moment_service.list_moments(
            page=1, size=10
        )
        assert isinstance(result, PaginationResponse)
        assert len(result.items) == 1
        assert result.items[0].id == mock_moment.id

    def test_list_moments_with_filters(
        self, moment_service, mock_moment
    ):
        """Test moment listing with filters."""
        mock_moment_list = MomentList(
            items=[mock_moment],
            total=1,
            page=1,
            size=10,
            pages=1,
        )
        moment_service.moment_repository.list_moments = (
            Mock(return_value=mock_moment_list)
        )

        result = moment_service.list_moments(
            page=1,
            size=10,
            activity_id=1,
            start_date=datetime.now(timezone.utc),
            end_date=datetime.now(timezone.utc),
            user_id="test_user",
        )
        assert isinstance(result, PaginationResponse)
        assert len(result.items) == 1
        assert result.items[0].id == mock_moment.id

    def test_get_moment_success(
        self, moment_service, mock_moment
    ):
        """Test successful moment retrieval."""
        moment_service.moment_repository.get = Mock(
            return_value=mock_moment
        )

        result = moment_service.get_moment(1, "test_user")
        assert isinstance(result, MomentResponse)
        assert result.id == mock_moment.id

    def test_get_moment_not_found(self, moment_service):
        """Test moment retrieval when not found."""
        moment_service.moment_repository.get = Mock(
            return_value=None
        )

        with pytest.raises(HTTPException) as exc:
            moment_service.get_moment(1, "test_user")
        assert exc.value.status_code == 404
        assert "Moment not found" in exc.value.detail

    def test_get_moment_wrong_user(
        self, moment_service, mock_moment
    ):
        """Test moment retrieval with wrong user."""
        mock_moment.user_id = "other_user"
        moment_service.moment_repository.get = Mock(
            return_value=mock_moment
        )

        with pytest.raises(HTTPException) as exc:
            moment_service.get_moment(1, "test_user")
        assert exc.value.status_code == 404
        assert "Moment not found" in exc.value.detail

    def test_update_moment_success(
        self, moment_service, mock_moment, mock_activity
    ):
        """Test successful moment update."""
        moment_service.moment_repository.get = Mock(
            return_value=mock_moment
        )
        moment_service.moment_repository.update = Mock(
            return_value=mock_moment
        )
        moment_service.activity_repository.get = Mock(
            return_value=mock_activity
        )

        update_data = MomentUpdate(
            data={"test_field": "updated value"}
        )
        result = moment_service.update_moment(
            1, update_data, "test_user"
        )

        assert isinstance(result, MomentResponse)
        assert result.id == mock_moment.id

    def test_update_moment_not_found(self, moment_service):
        """Test moment update when not found."""
        moment_service.moment_repository.get = Mock(
            return_value=None
        )

        update_data = MomentUpdate(
            data={"test_field": "updated value"}
        )
        with pytest.raises(HTTPException) as exc:
            moment_service.update_moment(
                1, update_data, "test_user"
            )
        assert exc.value.status_code == 404
        assert "Moment not found" in exc.value.detail

    def test_list_recent_activities_success(
        self, moment_service, mock_moment
    ):
        """Test successful retrieval of recent activities."""
        # Setup mock
        moment_service.moment_repository.list_moments = (
            Mock(
                return_value=PaginationResponse(
                    items=[mock_moment],
                    total=1,
                    page=1,
                    size=10,
                    pages=1,
                )
            )
        )

        result = moment_service.list_recent_activities(
            "test_user", limit=10
        )

        assert isinstance(result, list)
        assert len(result) == 1
        assert isinstance(result[0], MomentResponse)
        assert result[0].id == mock_moment.id

    def test_list_recent_activities_empty(
        self, moment_service
    ):
        """Test retrieval of recent activities when none exist."""
        # Setup mock
        moment_service.moment_repository.list_moments = (
            Mock(
                return_value=PaginationResponse(
                    items=[],
                    total=0,
                    page=1,
                    size=10,
                    pages=0,
                )
            )
        )

        result = moment_service.list_recent_activities(
            "test_user", limit=10
        )

        assert isinstance(result, list)
        assert len(result) == 0
