from typing import List, Optional, Dict, Any, Union
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from orm.ActivityModel import Activity
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
        **kwargs,
    ) -> Activity:
        """Create a new activity

        Args:
            instance_or_name: Activity instance or name
            **kwargs: Additional fields for activity creation

        Returns:
            Created activity

        Raises:
            ValueError: If validation fails
            HTTPException: If database constraints are violated
        """
        try:
            if isinstance(instance_or_name, str):
                # Set default values for required fields
                defaults = {
                    "name": instance_or_name,
                    "activity_schema": {"type": "default"},
                    "icon": "default-icon",
                    "color": "#000000",
                }
                # Override defaults with any provided kwargs
                defaults.update(kwargs)
                activity = Activity(**defaults)
            else:
                activity = instance_or_name

            return super().create(activity)
        except ValueError as e:
            print(e)
            # Re-raise validation errors
            raise
        except IntegrityError as e:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Resource already exists: {str(e)}",
            )
        except SQLAlchemyError as e:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Database error: {str(e)}",
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
        try:
            activity = self.get_by_user(
                activity_id, user_id
            )
            if not activity:
                return None

            # Pre-validate any fields that require validation
            if "color" in data:
                Activity.validate_color(data["color"])
            if "activity_schema" in data:
                Activity.validate_schema_dict(
                    data["activity_schema"]
                )

            for key, value in data.items():
                setattr(activity, key, value)

            self.db.commit()
            self.db.refresh(activity)
            return activity
        except ValueError as e:
            print(e)
            # Re-raise validation errors
            raise
        except IntegrityError as e:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Update violates constraints: {str(e)}",
            )
        except SQLAlchemyError as e:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Database error: {str(e)}",
            )

    def delete_activity(
        self, activity_id: int, user_id: str
    ) -> bool:
        """Delete an activity

        Args:
            activity_id: Activity ID
            user_id: User ID to verify ownership

        Returns:
            True if activity was deleted,
            False if not found or not owned by user
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
                detail=(
                    "Activity not found or access denied"
                ),
            )
        return activity
