from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException

from models.ActivityModel import Activity


class ActivityRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(
        self,
        name: str,
        description: str,
        activity_schema: dict,
        icon: str,
        color: str,
        user_id: str,
    ) -> Activity:
        """Create a new activity"""
        try:
            activity = Activity(
                name=name,
                description=description,
                activity_schema=activity_schema,
                icon=icon,
                color=color,
                user_id=user_id,
            )
            self.db.add(activity)
            self.db.commit()
            self.db.refresh(activity)
            return activity
        except IntegrityError:
            self.db.rollback()
            raise HTTPException(
                status_code=400,
                detail="Activity with this name already exists",
            )

    def get_by_id(
        self, activity_id: int, user_id: str
    ) -> Optional[Activity]:
        """Get an activity by ID and user_id"""
        activity = (
            self.db.query(Activity)
            .filter(
                Activity.id == activity_id,
                Activity.user_id == user_id,
            )
            .first()
        )
        if not activity:
            raise HTTPException(
                status_code=404,
                detail="Activity not found or access denied",
            )
        return activity

    def get_by_name(
        self, name: str, user_id: str
    ) -> Optional[Activity]:
        """Get an activity by name and verify ownership"""
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
        """List all activities for a user"""
        return (
            self.db.query(Activity)
            .filter(Activity.user_id == user_id)
            .offset(skip)
            .limit(limit)
            .all()
        )

    def update(
        self, activity_id: int, user_id: str, **kwargs
    ) -> Optional[Activity]:
        """Update an activity"""
        activity = self.get_by_id(activity_id, user_id)
        if not activity:
            return None

        for key, value in kwargs.items():
            if value is not None:
                setattr(activity, key, value)

        try:
            self.db.commit()
            self.db.refresh(activity)
            return activity
        except IntegrityError:
            self.db.rollback()
            raise HTTPException(
                status_code=400,
                detail="Activity with this name already exists",
            )

    def delete(self, activity_id: int, user_id: str) -> bool:
        """Delete an activity"""
        activity = self.get_by_id(activity_id, user_id)
        if not activity:
            return False

        self.db.delete(activity)
        self.db.commit()
        return True

    def validate_existence(
        self, activity_id: int, user_id: str
    ) -> Activity:
        """Validate activity exists and user owns it"""
        activity = self.get_by_id(activity_id, user_id)
        if not activity:
            raise HTTPException(
                status_code=404,
                detail="Activity not found or access denied",
            )
        return activity
