from typing import List, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import desc

from orm.TimelineModel import Timeline as TimelineModel
from domain.timeline import TimelineEventType
from schemas.pydantic.TimelineSchema import TimelineList
from utils.pagination import page_to_skip, calculate_pages


class TimelineRepository:
    """Repository for reading Timeline events"""

    def __init__(self, db: Session):
        """Initialize with database session

        Args:
            db: SQLAlchemy database session
        """
        self.db = db

    def get_recent_by_user(
        self, user_id: str, limit: int = 5
    ) -> List[TimelineModel]:
        """Get recent timeline events for a user

        Args:
            user_id: User ID to filter events
            limit: Maximum number of events to return

        Returns:
            List of recent timeline events
        """
        return (
            self.db.query(TimelineModel)
            .filter(TimelineModel.user_id == user_id)
            .order_by(desc(TimelineModel.timestamp))
            .limit(limit)
            .all()
        )

    def list_events(
        self,
        page: int = 1,
        size: int = 50,
        event_type: Optional[TimelineEventType] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        user_id: Optional[str] = None,
    ) -> TimelineList:
        """List timeline events with pagination and filtering

        Args:
            page: Page number (1-based)
            size: Items per page
            event_type: Optional event type to filter by
            start_time: Optional start time filter
            end_time: Optional end time filter
            user_id: Optional user ID filter

        Returns:
            TimelineList with items and pagination info
        """
        # Convert page/size to skip/limit
        skip, limit = page_to_skip(page, size)

        # Build base query
        base_query = self.db.query(TimelineModel)

        # Apply filters
        if event_type is not None:
            base_query = base_query.filter(
                TimelineModel.event_type == event_type
            )
        if user_id is not None:
            base_query = base_query.filter(
                TimelineModel.user_id == user_id
            )
        if start_time is not None:
            base_query = base_query.filter(
                TimelineModel.timestamp >= start_time
            )
        if end_time is not None:
            base_query = base_query.filter(
                TimelineModel.timestamp <= end_time
            )

        # Order by timestamp descending
        base_query = base_query.order_by(
            desc(TimelineModel.timestamp)
        )

        # Get total count before pagination
        total = base_query.count()

        # Apply pagination using skip/limit
        items = base_query.offset(skip).limit(limit).all()

        # Calculate total pages
        pages = calculate_pages(total, size)

        return TimelineList(
            items=items,
            total=total,
            page=page,
            size=size,
            pages=pages,
        )
