from typing import List, Optional, Dict, Any, Union
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException, status

from models.ActivityModel import Activity
from .BaseRepository import BaseRepository


class ActivityRepository(BaseRepository[Activity, int]):
    """Repository for managing Activity entities"""

    def __init__(self, db: Session):
        """Initialize with database session

        Args:
            db: SQLAlchemy database session
        """
        super().__init__(db, Activity)

    def create(
        self,
        instance_or_name: Union[Activity, str],
        *,  # Force keyword arguments
        description: Optional[str] = None,
        activity_schema: Optional[dict] = None,
        icon: Optional[str] = None,
        color: Optional[str] = None,
        user_id: Optional[str] = None,
    ) -> Activity:
        """Create a new activity

        This method supports two ways of creating an activity:
        1. Passing an Activity instance directly
        2. Passing individual fields

        Args:
            instance_or_name: Either an Activity instance or the activity name
            description: Activity description (if creating by fields)
            activity_schema: Activity schema (if creating by fields)
            icon: Activity icon (if creating by fields)
            color: Activity color (if creating by fields)
            user_id: Owner's user ID (if creating by fields)

        Returns:
            Created Activity instance
        """
        if isinstance(instance_or_name, Activity):
            return super().create(instance_or_name)

        # Create new instance from fields
        activity = Activity(
            name=instance_or_name,
            description=description,
            activity_schema=activity_schema,
            icon=icon,
            color=color,
            user_id=user_id,
        )
        return super().create(activity)

    def get_by_user(
        self, activity_id: int, user_id: str
    ) -> Optional[Activity]:
        """Get an activity by ID and verify ownership

        Args:
            activity_id: Activity ID
            user_id: User ID to verify ownership

        Returns:
            Activity if found and owned by user, None otherwise
        """
        return (
            self.db.query(Activity)
            .filter(
                Activity.id == activity_id,
                Activity.user_id == user_id,
            )
            .first()
        )

    def get_by_name(
        self, name: str, user_id: str
    ) -> Optional[Activity]:
        """Get an activity by name and verify ownership

        Args:
            name: Activity name
            user_id: User ID to verify ownership

        Returns:
            Activity if found and owned by user, None otherwise
        """
        return (
            self.db.query(Activity)
            .filter(
                Activity.name == name,
                Activity.user_id == user_id,
            )
            .first()
        )

    def list_activities(
        self, user_id: str, skip: int = 0, limit: int = 100
    ) -> List[Activity]:
        """List all activities for a user

        Args:
            user_id: User ID to filter activities
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of activities owned by the user
        """
        return (
            self.db.query(Activity)
            .filter(Activity.user_id == user_id)
            .offset(skip)
            .limit(limit)
            .all()
        )

    def update_activity(
        self,
        activity_id: int,
        user_id: str,
        data: Dict[str, Any],
    ) -> Optional[Activity]:
        """Update an activity

        Args:
            activity_id: Activity ID
            user_id: User ID to verify ownership
            data: Dictionary of fields to update

        Returns:
            Updated Activity if found and owned by user, None otherwise
        """
        activity = self.get_by_user(activity_id, user_id)
        if not activity:
            return None
        return self.update(activity_id, data)

    def delete_activity(
        self, activity_id: int, user_id: str
    ) -> bool:
        """Delete an activity

        Args:
            activity_id: Activity ID
            user_id: User ID to verify ownership

        Returns:
            True if activity was deleted, False if not found or not owned by user
        """
        activity = self.get_by_user(activity_id, user_id)
        if not activity:
            return False
        return self.delete(activity_id)

    def validate_existence(
        self, activity_id: int, user_id: str
    ) -> Activity:
        """Validate activity exists and user owns it

        Args:
            activity_id: Activity ID
            user_id: User ID to verify ownership

        Returns:
            Activity instance if found and owned by user

        Raises:
            HTTPException: If activity not found or access denied
        """
        activity = self.get_by_user(activity_id, user_id)
        if not activity:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Activity not found or access denied",
            )
        return activity
