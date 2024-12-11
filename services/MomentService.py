from typing import Dict, List, Optional
from datetime import datetime
from fastapi import HTTPException, Depends
from sqlalchemy.orm import Session

from configs.Database import get_db_connection
from repositories.MomentRepository import MomentRepository
from repositories.ActivityRepository import ActivityRepository
from services.ActivityService import ActivityService
from schemas.pydantic.MomentSchema import MomentCreate, MomentUpdate, MomentList


class MomentService:
    def __init__(self, db: Session = Depends(get_db_connection)):
        self.db = db
        self.moment_repository = MomentRepository(db)
        self.activity_repository = ActivityRepository(db)
        self.activity_service = ActivityService(db)

    def create_moment(self, moment_data: MomentCreate) -> Dict:
        """Create a new moment with data validation"""
        # Validate activity and moment data
        self.activity_service.validate_moment_data(
            activity_id=moment_data.activity_id,
            data=moment_data.data
        )

        # Create moment with validated data
        moment = self.moment_repository.create(
            activity_id=moment_data.activity_id,
            data=moment_data.data,
            timestamp=moment_data.timestamp
        )

        return self._format_moment_response(moment)

    def get_moment(self, moment_id: int) -> Dict:
        """Get a moment by ID"""
        moment = self.moment_repository.get_by_id(moment_id)
        if not moment:
            raise HTTPException(status_code=404, detail="Moment not found")

        return self._format_moment_response(moment)

    def list_moments(
        self,
        page: int = 1,
        size: int = 50,
        activity_id: Optional[int] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> MomentList:
        """List moments with filtering and pagination"""
        # Validate activity if provided
        if activity_id:
            self.activity_repository.validate_existence(activity_id)

        # Calculate pagination
        skip = (page - 1) * size

        # Get moments with total count
        moments, total = self.moment_repository.list_moments(
            skip=skip,
            limit=size,
            activity_id=activity_id,
            start_time=start_time,
            end_time=end_time
        )

        # Calculate total pages
        pages = (total + size - 1) // size

        return MomentList(
            items=[self._format_moment_response(m) for m in moments],
            total=total,
            page=page,
            size=size,
            pages=pages
        )

    def update_moment(self, moment_id: int, moment_data: MomentUpdate) -> Dict:
        """Update a moment"""
        # Check if moment exists
        moment = self.moment_repository.get_by_id(moment_id)
        if not moment:
            raise HTTPException(status_code=404, detail="Moment not found")

        # If data is being updated, validate it against the activity schema
        if moment_data.data is not None:
            self.activity_service.validate_moment_data(
                activity_id=moment.activity_id,
                data=moment_data.data
            )

        # Update only provided fields
        update_data = moment_data.dict(exclude_unset=True)
        moment = self.moment_repository.update(moment_id, **update_data)

        return self._format_moment_response(moment)

    def delete_moment(self, moment_id: int) -> bool:
        """Delete a moment"""
        return self.moment_repository.delete(moment_id)

    def get_recent_activities(self, limit: int = 5) -> List[Dict]:
        """Get recently used activities"""
        activities = self.moment_repository.get_recent_activities(limit)
        return [
            {
                "id": activity.id,
                "name": activity.name,
                "icon": activity.icon,
                "color": activity.color
            }
            for activity in activities
        ]

    def _format_moment_response(self, moment) -> Dict:
        """Format moment response with activity details"""
        return {
            "id": moment.id,
            "timestamp": moment.timestamp,
            "activity_id": moment.activity_id,
            "data": moment.data,
            "activity": {
                "id": moment.activity.id,
                "name": moment.activity.name,
                "description": moment.activity.description,
                "activity_schema": moment.activity.activity_schema,
                "icon": moment.activity.icon,
                "color": moment.activity.color
            }
        }
