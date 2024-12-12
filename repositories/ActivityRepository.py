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
    ) -> Activity:
        """Create a new activity"""
        try:
            activity = Activity(
                name=name,
                description=description,
                activity_schema=activity_schema,
                icon=icon,
                color=color,
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
        self, activity_id: int
    ) -> Optional[Activity]:
        """Get an activity by ID"""
        return (
            self.db.query(Activity)
            .filter(Activity.id == activity_id)
            .first()
        )

    def get_by_name(self, name: str) -> Optional[Activity]:
        """Get an activity by name"""
        return (
            self.db.query(Activity)
            .filter(Activity.name == name)
            .first()
        )

    def list_all(
        self, skip: int = 0, limit: int = 100
    ) -> List[Activity]:
        """List all activities with pagination"""
        return (
            self.db.query(Activity)
            .offset(skip)
            .limit(limit)
            .all()
        )

    def update(
        self, activity_id: int, **kwargs
    ) -> Optional[Activity]:
        """Update an activity"""
        activity = self.get_by_id(activity_id)
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

    def delete(self, activity_id: int) -> bool:
        """Delete an activity"""
        activity = self.get_by_id(activity_id)
        if not activity:
            return False

        self.db.delete(activity)
        self.db.commit()
        return True

    def validate_existence(
        self, activity_id: int
    ) -> Activity:
        """Validate activity exists and return it"""
        activity = self.get_by_id(activity_id)
        if not activity:
            raise HTTPException(
                status_code=404, detail="Activity not found"
            )
        return activity
