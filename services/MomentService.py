from typing import Optional, List, Dict, cast
from fastapi import HTTPException, Depends
from sqlalchemy.orm import Session
from jsonschema import validate, ValidationError
from datetime import datetime

from schemas.base.moment_schema import MomentData
from schemas.graphql.types.Moment import Moment
from repositories.MomentRepository import MomentRepository
from schemas.graphql.Activity import Activity

from configs.Database import get_db_connection
from repositories.ActivityRepository import (
    ActivityRepository,
)
from schemas.pydantic.MomentSchema import (
    MomentCreate,
    MomentUpdate,
    MomentList,
    MomentResponse,
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

        # Get activity to validate data against schema
        activity = (
            self.activity_repository.validate_existence(
                domain_data.activity_id, user_id
            )
        )

        try:
            # Validate moment data against activity schema
            validate(
                instance=domain_data.data,
                schema=activity.activity_schema_dict,
            )
        except ValidationError as e:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid moment data: {str(e)}",
            )

        # Create the moment
        moment = self.moment_repository.create(
            activity_id=domain_data.activity_id,
            data=domain_data.data,
            user_id=user_id,
            timestamp=domain_data.timestamp,
        )

        return MomentResponse.from_orm(moment)

    def list_moments(
        self,
        page: int,
        size: int,
        activity_id: Optional[int] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        user_id: Optional[str] = None,
    ) -> MomentList:
        """List moments with filtering and pagination

        Args:
            page: Page number (1-based)
            size: Items per page
            activity_id: Optional activity ID to filter by
            start_date: Optional start date to filter by
            end_date: Optional end date to filter by
            user_id: Optional user ID to filter by

        Returns:
            List of moments with pagination metadata

        Raises:
            HTTPException: If pagination parameters are invalid
        """
        self._validate_pagination(page, size)

        moments = self.moment_repository.list_moments(
            page=page,
            size=size,
            activity_id=activity_id,
            start_time=start_date,
            end_time=end_date,
            user_id=user_id,
        )
        return moments

    def get_moment(
        self, moment_id: int, user_id: str
    ) -> MomentResponse:
        """Get a moment by ID

        Args:
            moment_id: ID of the moment to get
            user_id: ID of the user requesting the moment

        Returns:
            Moment response

        Raises:
            HTTPException: If moment not found or user not authorized
        """
        moment = self.moment_repository.get_by_id(moment_id)
        if not moment or moment.activity.user_id != user_id:
            raise HTTPException(
                status_code=404, detail="Moment not found"
            )
        return MomentResponse.from_orm(moment)

    def get_moment_graphql(
        self, moment_id: int, user_id: str
    ) -> Optional[Moment]:
        """Get a moment by ID for GraphQL

        Args:
            moment_id: ID of the moment to get
            user_id: ID of the user requesting the moment

        Returns:
            Moment or None if not found
        """
        try:
            moment = self.get_moment(moment_id, user_id)
            return Moment.from_db(moment)
        except HTTPException:
            return None

    def update_moment(
        self,
        moment_id: int,
        moment_data: MomentUpdate,
        user_id: str,
    ) -> MomentResponse:
        """Update a moment

        Args:
            moment_id: ID of the moment to update
            moment_data: New moment data
            user_id: ID of the user updating the moment

        Returns:
            Updated moment response

        Raises:
            HTTPException: If moment not found, user not authorized,
            or validation fails
        """
        moment = self.moment_repository.get_by_id(moment_id)
        if not moment or moment.activity.user_id != user_id:
            raise HTTPException(
                status_code=404, detail="Moment not found"
            )

        # If updating data, validate against activity schema
        if moment_data.data is not None:
            try:
                validate(
                    instance=moment_data.data,
                    schema=moment.activity.activity_schema_dict,
                )
            except ValidationError as e:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid moment data: {str(e)}",
                )

        update_dict = moment_data.dict(exclude_unset=True)
        updated = self.moment_repository.update(
            moment_id=moment_id, **update_dict
        )
        if not updated:
            raise HTTPException(
                status_code=404, detail="Moment not found"
            )
        return MomentResponse.from_orm(updated)

    def list_recent_activities(
        self, user_id: str, limit: int = 5
    ) -> List[Activity]:
        """Get recently used activities for a user

        Args:
            user_id: ID of the user
            limit: Maximum number of activities to return

        Returns:
            List of unique activities from recent moments

        Raises:
            HTTPException: If limit is invalid
        """
        if limit < 1 or limit > 100:
            raise HTTPException(
                status_code=400,
                detail="Limit must be between 1 and 100",
            )

        recent_moments = (
            self.moment_repository.get_recent_by_user(
                user_id=user_id, limit=limit
            )
        )
        # Get unique activities from recent moments
        activities: Dict[int, Activity] = {}
        for moment in recent_moments:
            activity_id = cast(int, moment.activity_id)
            if activity_id not in activities:
                activities[activity_id] = Activity.from_db(
                    moment.activity
                )
        return list(activities.values())
