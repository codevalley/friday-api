from typing import List, Optional, Tuple
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import desc

from models.MomentModel import Moment
from models.ActivityModel import Activity


class MomentRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, activity_id: int, data: dict, timestamp: Optional[datetime] = None) -> Moment:
        """Create a new moment"""
        moment = Moment(
            activity_id=activity_id,
            data=data,
            timestamp=timestamp or datetime.utcnow()
        )
        self.db.add(moment)
        self.db.commit()
        self.db.refresh(moment)
        return moment

    def get_by_id(self, moment_id: int) -> Optional[Moment]:
        """Get a moment by ID"""
        return self.db.query(Moment).filter(Moment.id == moment_id).first()

    def list_moments(
        self,
        skip: int = 0,
        limit: int = 50,
        activity_id: Optional[int] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> Tuple[List[Moment], int]:
        """
        List moments with filtering and pagination
        Returns a tuple of (moments, total_count)
        """
        query = self.db.query(Moment)

        # Apply filters
        if activity_id is not None:
            query = query.filter(Moment.activity_id == activity_id)
        if start_time is not None:
            query = query.filter(Moment.timestamp >= start_time)
        if end_time is not None:
            query = query.filter(Moment.timestamp <= end_time)

        # Get total count before pagination
        total = query.count()

        # Apply pagination and ordering
        moments = query.order_by(desc(Moment.timestamp)).offset(skip).limit(limit).all()

        return moments, total

    def update(self, moment_id: int, **kwargs) -> Optional[Moment]:
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

    def get_activity_moments_count(self, activity_id: int) -> int:
        """Get the count of moments for a specific activity"""
        return self.db.query(Moment).filter(Moment.activity_id == activity_id).count()

    def get_recent_activities(self, limit: int = 5) -> List[Activity]:
        """Get recently used activities based on moment timestamps"""
        return (
            self.db.query(Activity)
            .join(Moment)
            .order_by(desc(Moment.timestamp))
            .distinct()
            .limit(limit)
            .all()
        )
