"""Service for handling moment-related operations"""

from typing import Optional, List
from fastapi import HTTPException, Depends
from sqlalchemy.orm import Session
from datetime import datetime, timedelta, timezone

from schemas.base.moment_schema import MomentData
from schemas.graphql.types.Moment import Moment
from repositories.MomentRepository import MomentRepository
from configs.Database import get_db_connection
from repositories.ActivityRepository import (
    ActivityRepository,
)
from schemas.pydantic.MomentSchema import (
    MomentCreate,
    MomentUpdate,
    MomentResponse,
)
from schemas.pydantic.PaginationSchema import (
    PaginationResponse,
)


class MomentService:
    """Service for handling moment-related operations"""

    def __init__(
        self, db: Session = Depends(get_db_connection)
    ) -> None:
        """Initialize the service with database session

        Args:
            db: SQLAlchemy database session
        """
        self.db = db
        self.moment_repository = MomentRepository(db)
        self.activity_repository = ActivityRepository(db)

    def _validate_pagination(
        self, page: int, size: int
    ) -> None:
        """Validate pagination parameters

        Args:
            page: Page number (1-based)
            size: Items per page

        Raises:
            HTTPException: If parameters are invalid
        """
        if page < 1:
            raise HTTPException(
                status_code=400,
                detail="Page number must be positive",
            )
        if size < 1 or size > 100:
            raise HTTPException(
                status_code=400,
                detail="Page size must be between 1 and 100",
            )

    def _validate_timestamp(
        self, timestamp: datetime
    ) -> None:
        """Validate moment timestamp

        Args:
            timestamp: Moment timestamp to validate

        Raises:
            HTTPException: If timestamp is invalid
        """
        # Convert naive datetime to UTC if needed
        if timestamp.tzinfo is None:
            timestamp = timestamp.replace(
                tzinfo=timezone.utc
            )

        now = datetime.now(timezone.utc)
        max_future = now + timedelta(
            days=1
        )  # Allow up to 1 day in future
        min_past = now - timedelta(
            days=365 * 10
        )  # Allow up to 10 years in past

        if timestamp > max_future:
            raise HTTPException(
                status_code=400,
                detail="Timestamp cannot be more than 1 day in the future",
            )
        if timestamp < min_past:
            raise HTTPException(
                status_code=400,
                detail="Timestamp cannot be more than 10 years in the past",
            )

    def _validate_activity_ownership(
        self, activity_id: int, user_id: str
    ) -> None:
        """Validate that activity belongs to user

        Args:
            activity_id: ID of activity to validate
            user_id: ID of user to check ownership against

        Raises:
            HTTPException: If activity doesn't exist or doesn't belong to user
        """
        activity = self.activity_repository.get_by_user(
            activity_id, user_id
        )
        if not activity:
            raise HTTPException(
                status_code=404,
                detail="Activity not found or does not belong to user",
            )

    def create_moment(
        self,
        moment_data: MomentCreate | MomentData,
        user_id: str,
    ) -> MomentResponse:
        """Create a new moment with data validation

        Args:
            moment_data: Moment data to create
            user_id: ID of the user creating the moment

        Returns:
            Created moment response

        Raises:
            HTTPException: If validation fails or activity not found
        """
        # Convert to domain model if needed
        domain_data = (
            moment_data
            if isinstance(moment_data, MomentData)
            else moment_data.to_domain()
        )

        # Ensure timestamp has timezone info
        if domain_data.timestamp.tzinfo is None:
            domain_data.timestamp = (
                domain_data.timestamp.replace(
                    tzinfo=timezone.utc
                )
            )

        # Validate activity ownership
        self._validate_activity_ownership(
            domain_data.activity_id, user_id
        )

        # Validate timestamp
        self._validate_timestamp(domain_data.timestamp)

        # Get activity and validate data against its schema
        activity = (
            self.activity_repository.validate_existence(
                domain_data.activity_id, user_id
            )
        )

        # Validate moment data against activity schema
        try:
            activity.validate_moment_data(domain_data.data)
        except ValueError as e:
            raise HTTPException(
                status_code=400,
                detail=f"Moment data does not match"
                f" activity schema: {str(e)}",
            )

        # Create the moment - validation handled by Pydantic
        moment = self.moment_repository.create(
            instance_or_activity_id=activity.id,  # Use validated activity
            data=domain_data.data,
            user_id=user_id,
            timestamp=domain_data.timestamp,
        )

        return MomentResponse.model_validate(moment)

    def list_moments(
        self,
        page: int,
        size: int,
        activity_id: Optional[int] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        user_id: Optional[str] = None,
    ) -> PaginationResponse[MomentResponse]:
        """List moments with optional filters

        Args:
            page: Page number (1-based)
            size: Items per page
            activity_id: Optional activity ID filter
            start_date: Optional start date filter
            end_date: Optional end date filter
            user_id: Optional user ID filter

        Returns:
            List of moments matching filters

        Raises:
            HTTPException: If pagination parameters are invalid
        """
        self._validate_pagination(page, size)

        # Apply filters
        moment_list = self.moment_repository.list_moments(
            page=page,
            size=size,
            activity_id=activity_id,
            start_time=start_date,
            end_time=end_date,
            user_id=user_id,
            include_activity=True,
        )

        # Convert to response models
        items = [
            MomentResponse.model_validate(m)
            for m in moment_list.items
        ]

        return PaginationResponse[MomentResponse](
            items=items,
            total=moment_list.total,
            page=moment_list.page,
            size=moment_list.size,
            pages=moment_list.pages,
        )

    def get_moment(
        self, moment_id: int, user_id: str
    ) -> MomentResponse:
        """Get a moment by ID

        Args:
            moment_id: ID of moment to get
            user_id: ID of user requesting moment

        Returns:
            Moment if found and belongs to user

        Raises:
            HTTPException: If moment not found or doesn't belong to user
        """
        moment = self.moment_repository.get(moment_id)
        if not moment or moment.activity.user_id != user_id:
            raise HTTPException(
                status_code=404,
                detail="Moment not found",
            )

        return MomentResponse.model_validate(moment)

    def get_moment_graphql(
        self, moment_id: int, user_id: str
    ) -> Moment:
        """Get a moment by ID for GraphQL

        Args:
            moment_id: ID of moment to get
            user_id: ID of user requesting moment

        Returns:
            Moment if found and belongs to user

        Raises:
            HTTPException: If moment not found or doesn't belong to user
        """
        moment = self.moment_repository.get(moment_id)
        if not moment or moment.activity.user_id != user_id:
            raise HTTPException(
                status_code=404,
                detail="Moment not found",
            )

        return Moment.from_db(moment)

    def update_moment(
        self,
        moment_id: int,
        moment_data: MomentUpdate,
        user_id: str,
    ) -> MomentResponse:
        """Update an existing moment

        Args:
            moment_id: ID of moment to update
            moment_data: New moment data
            user_id: ID of user updating moment

        Returns:
            Updated moment

        Raises:
            HTTPException: If moment not found or validation fails
        """
        # Get existing moment
        moment = self.moment_repository.get(moment_id)
        if not moment or moment.activity.user_id != user_id:
            raise HTTPException(
                status_code=404,
                detail="Moment not found",
            )

        # Validate new data against activity schema
        try:
            moment.activity.validate_moment_data(
                moment_data.data
            )
        except ValueError as e:
            raise HTTPException(
                status_code=400,
                detail=f"Moment data does not match"
                f" activity schema: {str(e)}",
            )

        # Update moment
        update_dict = moment_data.model_dump(
            exclude_unset=True,
            exclude_none=True,
        )
        updated = self.moment_repository.update(
            moment_id, update_dict
        )
        return MomentResponse.model_validate(updated)

    def list_recent_activities(
        self, user_id: str, limit: int = 10
    ) -> List[MomentResponse]:
        """List recent activities for a user

        Args:
            user_id: ID of user to get activities for
            limit: Maximum number of activities to return

        Returns:
            List of recent activities

        Raises:
            HTTPException: If limit is invalid
        """
        if limit < 1 or limit > 100:
            raise HTTPException(
                status_code=400,
                detail="Limit must be between 1 and 100",
            )

        moments = self.moment_repository.get_recent_by_user(
            user_id, limit
        )
        return [
            MomentResponse.model_validate(m)
            for m in moments
        ]
