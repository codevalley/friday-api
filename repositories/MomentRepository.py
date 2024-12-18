from typing import List, Optional, Dict, Any, Union
from datetime import datetime
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import desc, func

from orm.MomentModel import Moment as MomentModel
from orm.ActivityModel import Activity
from schemas.pydantic.MomentSchema import MomentList
from .BaseRepository import BaseRepository


class MomentRepository(BaseRepository[MomentModel, int]):
    """Repository for managing Moment entities"""

    def __init__(self, db: Session):
        """Initialize with database session

        Args:
            db: SQLAlchemy database session
        """
        super().__init__(db, MomentModel)

    def create(
        self,
        instance_or_activity_id: Union[MomentModel, int],
        *,  # Force keyword arguments
        data: Optional[dict] = None,
        user_id: Optional[str] = None,
        timestamp: Optional[datetime] = None,
    ) -> MomentModel:
        """Create a new moment

        This method supports two ways of creating a moment:
        1. Passing a MomentModel instance directly
        2. Passing individual fields

        Args:
            instance_or_activity_id: Either a MomentModel instance
                or activity ID
            data: Moment data conforming to activity schema
                (if creating by fields)
            user_id: Owner's user ID (if creating by fields)
            timestamp: Optional timestamp (if creating by fields)

        Returns:
            Created Moment instance

        Raises:
            ValueError: If moment data is invalid
        """
        if isinstance(instance_or_activity_id, MomentModel):
            # Validate data before saving
            instance_or_activity_id.validate_data(self.db)
            return super().create(instance_or_activity_id)

        # Create new instance from fields
        moment = MomentModel(
            activity_id=instance_or_activity_id,
            data=data,
            user_id=user_id,
            timestamp=timestamp or datetime.utcnow(),
        )
        # Validate data before saving
        moment.validate_data(self.db)
        return super().create(moment)

    def get(self, id: int) -> Optional[MomentModel]:
        """Get a moment by ID with eagerly loaded activity

        Args:
            id: ID of the moment to get

        Returns:
            Moment if found, None otherwise
        """
        return (
            self.db.query(MomentModel)
            .options(joinedload(MomentModel.activity))
            .filter(MomentModel.id == id)
            .first()
        )

    def get_recent_by_user(
        self, user_id: str, limit: int = 5
    ) -> List[MomentModel]:
        """Get recent moments for a user

        Args:
            user_id: User ID to filter moments
            limit: Maximum number of moments to return

        Returns:
            List of recent moments with activities eager loaded
        """
        return (
            self.db.query(MomentModel)
            .options(joinedload(MomentModel.activity))
            .filter(MomentModel.user_id == user_id)
            .order_by(desc(MomentModel.timestamp))
            .limit(limit)
            .all()
        )

    def get_recent_activities(
        self, limit: int = 5
    ) -> List[Activity]:
        """Get recently used activities based on moment timestamps

        Args:
            limit: Maximum number of activities to return

        Returns:
            List of unique activities from recent moments
        """
        # Get the most recent moment for each activity
        latest_moments = (
            self.db.query(
                MomentModel.activity_id,
                func.max(MomentModel.timestamp).label(
                    "latest_timestamp"
                ),
            )
            .group_by(MomentModel.activity_id)
            .subquery()
        )

        # Join with activities and order by latest timestamp
        activities = (
            self.db.query(Activity)
            .join(
                latest_moments,
                Activity.id == latest_moments.c.activity_id,
            )
            .order_by(
                desc(latest_moments.c.latest_timestamp)
            )
            .limit(limit)
            .all()
        )

        return activities

    def get_activity_moments_count(
        self, activity_id: int
    ) -> int:
        """Get the count of moments for a specific activity

        Args:
            activity_id: Activity ID to count moments for

        Returns:
            Number of moments for the activity
        """
        return (
            self.db.query(MomentModel)
            .filter(MomentModel.activity_id == activity_id)
            .count()
        )

    def list_moments(
        self,
        page: int = 1,
        size: int = 50,
        activity_id: Optional[int] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        user_id: Optional[str] = None,
        include_activity: bool = True,
    ) -> MomentList:
        """List moments with filtering and pagination

        Args:
            page: Page number (1-based)
            size: Page size
            activity_id: Optional activity ID to filter by
            start_time: Optional start time to filter by
            end_time: Optional end time to filter by
            user_id: Optional user ID to filter by
            include_activity: Whether to eager load activities

        Returns:
            MomentList containing paginated moments and metadata
        """
        # Start with base query
        base_query = self.db.query(MomentModel)

        # Add eager loading if requested
        if include_activity:
            base_query = base_query.options(
                joinedload(MomentModel.activity)
            )

        # Apply filters
        if activity_id is not None:
            base_query = base_query.filter(
                MomentModel.activity_id == activity_id
            )
        if user_id is not None:
            base_query = base_query.filter(
                MomentModel.user_id == user_id
            )
        if start_time is not None:
            base_query = base_query.filter(
                MomentModel.timestamp >= start_time
            )
        if end_time is not None:
            base_query = base_query.filter(
                MomentModel.timestamp <= end_time
            )

        # Order by timestamp descending
        base_query = base_query.order_by(
            desc(MomentModel.timestamp)
        )

        # Get total count before pagination
        total = base_query.count()

        # Apply pagination
        offset = (page - 1) * size
        items = base_query.offset(offset).limit(size).all()

        # Calculate total pages
        pages = (
            (total + size - 1) // size if total > 0 else 0
        )

        return MomentList(
            items=items,
            total=total,
            page=page,
            size=size,
            pages=pages,
        )

    def update_moment(
        self, moment_id: int, data: Dict[str, Any]
    ) -> Optional[MomentModel]:
        """Update a moment

        Args:
            moment_id: Moment ID
            data: Dictionary of fields to update

        Returns:
            Updated Moment if found, None otherwise

        Raises:
            ValueError: If moment data is invalid
        """
        # Get existing moment
        moment = self.get(moment_id)
        if moment is None:
            return None

        # If updating data field, validate it
        if "data" in data:
            # Create a copy of the moment to validate the new data
            test_moment = MomentModel(
                user_id=moment.user_id,
                activity_id=moment.activity_id,
                data=data["data"],
            )
            test_moment.validate_data(self.db)

        # Update fields
        for key, value in data.items():
            setattr(moment, key, value)

        self.db.commit()
        return moment

    def delete_moment(self, moment_id: int) -> bool:
        """Delete a moment

        Args:
            moment_id: Moment ID

        Returns:
            True if moment was deleted, False if not found
        """
        return self.delete(moment_id)

    def validate_existence(
        self, moment_id: int
    ) -> MomentModel:
        """Validate that a moment exists

        Args:
            moment_id: Moment ID

        Returns:
            Moment instance if found

        Raises:
            HTTPException: If moment not found
        """
        return super().validate_existence(
            moment_id, "Moment not found"
        )
