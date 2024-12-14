from typing import List, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import desc
from fastapi import HTTPException

from models.MomentModel import Moment as MomentModel
from models.ActivityModel import Activity
from schemas.pydantic.MomentSchema import (
    MomentList,
    MomentResponse,
)


class MomentRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(
        self,
        activity_id: int,
        data: dict,
        user_id: str,
        timestamp: Optional[datetime] = None,
    ) -> MomentModel:
        """Create a new moment"""
        moment = MomentModel(
            activity_id=activity_id,
            data=data,
            user_id=user_id,
            timestamp=timestamp or datetime.utcnow(),
        )
        self.db.add(moment)
        self.db.commit()
        self.db.refresh(moment)
        return moment

    def get_by_id(
        self, moment_id: int
    ) -> Optional[MomentModel]:
        """Get a moment by ID"""
        return (
            self.db.query(MomentModel)
            .filter(MomentModel.id == moment_id)
            .first()
        )

    def validate_existence(
        self, moment_id: int
    ) -> MomentModel:
        """Validate that a moment exists and return it"""
        moment = self.get_by_id(moment_id)
        if not moment:
            raise HTTPException(
                status_code=404, detail="Moment not found"
            )
        return moment

    def list_moments(
        self,
        page: int = 1,
        size: int = 50,
        activity_id: Optional[int] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        user_id: Optional[str] = None,
    ) -> MomentList:
        """
        List moments with filtering and pagination
        Returns a MomentList with pagination metadata
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

    def update(
        self, moment_id: int, **kwargs
    ) -> Optional[MomentModel]:
        """Update a moment"""
        moment = self.get_by_id(moment_id)
        if not moment:
            return None

        for key, value in kwargs.items():
            if value is not None:
                setattr(moment, key, value)

        self.db.commit()
        self.db.refresh(moment)
        return moment

    def delete(self, moment_id: int) -> bool:
        """Delete a moment"""
        moment = self.get_by_id(moment_id)
        if not moment:
            return False

        self.db.delete(moment)
        self.db.commit()
        return True

    def get_activity_moments_count(
        self, activity_id: int
    ) -> int:
        """Get the count of moments for a specific activity"""
        return (
            self.db.query(MomentModel)
            .filter(MomentModel.activity_id == activity_id)
            .count()
        )

    def get_recent_activities(
        self, limit: int = 5
    ) -> List[Activity]:
        """Get recently used activities based on moment timestamps"""
        return (
            self.db.query(Activity)
            .join(MomentModel)
            .order_by(desc(MomentModel.timestamp))
            .distinct()
            .limit(limit)
            .all()
        )

    def get_recent_by_user(
        self, user_id: str, limit: int = 5
    ) -> List[MomentModel]:
        """Get recent moments for a user"""
        return (
            self.db.query(MomentModel)
            .filter(MomentModel.user_id == user_id)
            .order_by(desc(MomentModel.timestamp))
            .limit(limit)
            .all()
        )
