from typing import List, Optional, Dict, Any, Union
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import desc
from fastapi import HTTPException, status

from models.MomentModel import Moment as MomentModel
from models.ActivityModel import Activity
from schemas.pydantic.MomentSchema import (
    MomentList,
    MomentResponse,
)
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
        """
        if isinstance(instance_or_activity_id, MomentModel):
            return super().create(instance_or_activity_id)

        # Create new instance from fields
        moment = MomentModel(
            activity_id=instance_or_activity_id,
            data=data,
            user_id=user_id,
            timestamp=timestamp or datetime.utcnow(),
        )
        return super().create(moment)

    def get_recent_by_user(
        self, user_id: str, limit: int = 5
    ) -> List[MomentModel]:
        """Get recent moments for a user

        Args:
            user_id: User ID to filter moments
            limit: Maximum number of moments to return

        Returns:
            List of recent moments
        """
        return (
            self.db.query(MomentModel)
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
        return (
            self.db.query(Activity)
            .join(MomentModel)
            .order_by(desc(MomentModel.timestamp))
            .distinct()
            .limit(limit)
            .all()
        )

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
    ) -> MomentList:
        """List moments with filtering and pagination

        Args:
            page: Page number (1-based)
            size: Page size
            activity_id: Optional activity ID filter
            start_time: Optional start time filter
            end_time: Optional end time filter
            user_id: Optional user ID filter

        Returns:
            MomentList with pagination metadata
        """
        query = self.db.query(MomentModel).join(Activity)

        # Apply filters
        if activity_id is not None:
            query = query.filter(
                MomentModel.activity_id == activity_id
            )
        if start_time is not None:
            query = query.filter(
                MomentModel.timestamp >= start_time
            )
        if end_time is not None:
            query = query.filter(
                MomentModel.timestamp <= end_time
            )
        if user_id is not None:
            query = query.filter(
                Activity.user_id == user_id
            )

        # Get total count
        total = query.count()

        # Calculate pagination
        pages = (total + size - 1) // size
        skip = (page - 1) * size

        # Get paginated results with activities eager loaded
        moments = (
            query.order_by(desc(MomentModel.timestamp))
            .offset(skip)
            .limit(size)
            .all()
        )

        # Convert to response type
        moment_responses = [
            MomentResponse.from_orm(moment)
            for moment in moments
        ]

        return MomentList(
            items=moment_responses,
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
        """
        return self.update(moment_id, data)

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
        moment = self.get(moment_id)
        if not moment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Moment not found",
            )
        return moment
