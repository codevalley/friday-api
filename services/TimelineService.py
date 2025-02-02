"""Service for managing timeline events in the system."""

from datetime import datetime
from typing import Dict, Any, Optional, List
from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from configs.Database import get_db_connection
from repositories.TimelineRepository import (
    TimelineRepository,
)
from domain.timeline import TimelineEventType
from domain.exceptions import TimelineValidationError
from utils.validation import validate_pagination
from schemas.pydantic.TimelineSchema import TimelineEvent

import logging

logger = logging.getLogger(__name__)


class TimelineService:
    """Service for managing timeline events.

    This service handles the business logic for retrieving and filtering
    timeline events. It ensures proper validation and authorization.

    Attributes:
        db: Database session
        timeline_repo: Repository for timeline operations
    """

    def __init__(
        self,
        db: Session = Depends(get_db_connection),
    ):
        """Initialize the timeline service.

        Args:
            db: Database session from dependency injection
        """
        self.db = db
        self.timeline_repo = TimelineRepository(db)

    def _handle_timeline_error(
        self, error: Exception
    ) -> None:
        """Map domain exceptions to HTTP exceptions."""
        if isinstance(error, TimelineValidationError):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "message": str(error),
                    "code": error.code,
                },
            )
        raise error

    async def get_recent_events(
        self, user_id: str, limit: int = 5
    ) -> List[TimelineEvent]:
        """Get recent timeline events for a user.

        Args:
            user_id: ID of the user to get events for
            limit: Maximum number of events to return

        Returns:
            List of recent timeline events

        Raises:
            HTTPException: If retrieval fails
        """
        try:
            events = self.timeline_repo.get_recent_by_user(
                user_id=user_id, limit=limit
            )
            return [
                TimelineEvent.model_validate(event)
                for event in events
            ]

        except Exception as e:
            logger.error(
                f"Error getting recent events for user {user_id}: {str(e)}",
                exc_info=True,
            )
            self._handle_timeline_error(e)

    async def list_events(
        self,
        page: int = 1,
        size: int = 50,
        event_type: Optional[TimelineEventType] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        user_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """List timeline events with filtering and pagination.

        Args:
            page: Page number (1-based)
            size: Number of items per page
            event_type: Optional event type to filter by
            start_time: Optional start time to filter by
            end_time: Optional end time to filter by
            user_id: Optional user ID to filter by

        Returns:
            Dict containing:
                - items: List of timeline events
                - total: Total number of events
                - page: Current page number
                - size: Page size
                - pages: Total number of pages

        Raises:
            HTTPException: If validation fails or retrieval fails
        """
        try:
            validate_pagination(page, size)

            result = self.timeline_repo.list_events(
                page=page,
                size=size,
                event_type=event_type,
                start_time=start_time,
                end_time=end_time,
                user_id=user_id,
            )

            return {
                "items": [
                    TimelineEvent.model_validate(event)
                    for event in result.items
                ],
                "total": result.total,
                "page": result.page,
                "size": result.size,
                "pages": result.pages,
            }

        except Exception as e:
            logger.error(
                f"Error listing timeline events: {str(e)}",
                exc_info=True,
            )
            self._handle_timeline_error(e)

    async def get_events_by_type(
        self,
        event_type: TimelineEventType,
        user_id: str,
        page: int = 1,
        size: int = 50,
    ) -> Dict[str, Any]:
        """Get timeline events of a specific type for a user.

        Args:
            event_type: Type of events to retrieve
            user_id: ID of the user to get events for
            page: Page number (1-based)
            size: Number of items per page

        Returns:
            Dict containing paginated events of the specified type

        Raises:
            HTTPException: If validation fails or retrieval fails
        """
        try:
            validate_pagination(page, size)

            result = self.timeline_repo.list_events(
                page=page,
                size=size,
                event_type=event_type,
                user_id=user_id,
            )

            return {
                "items": [
                    TimelineEvent.model_validate(event)
                    for event in result.items
                ],
                "total": result.total,
                "page": result.page,
                "size": result.size,
                "pages": result.pages,
            }

        except Exception as e:
            error_msg = (
                f"Error getting events by type {event_type} "
                f"for user {user_id}: {str(e)}"
            )
            logger.error(error_msg, exc_info=True)
            self._handle_timeline_error(e)

    async def get_events_in_timerange(
        self,
        user_id: str,
        start_time: datetime,
        end_time: datetime,
        page: int = 1,
        size: int = 50,
    ) -> Dict[str, Any]:
        """Get timeline events within a specific time range.

        Args:
            user_id: ID of the user to get events for
            start_time: Start of time range
            end_time: End of time range
            page: Page number (1-based)
            size: Number of items per page

        Returns:
            Dict containing paginated events within the time range

        Raises:
            HTTPException: If validation fails or retrieval fails
        """
        try:
            validate_pagination(page, size)

            if start_time >= end_time:
                raise TimelineValidationError(
                    "Start time must be before end time"
                )

            result = self.timeline_repo.list_events(
                page=page,
                size=size,
                user_id=user_id,
                start_time=start_time,
                end_time=end_time,
            )

            return {
                "items": [
                    TimelineEvent.model_validate(event)
                    for event in result.items
                ],
                "total": result.total,
                "page": result.page,
                "size": result.size,
                "pages": result.pages,
            }

        except Exception as e:
            error_msg = (
                f"Error getting events in timerange for user {user_id}: "
                f"{str(e)}"
            )
            logger.error(error_msg, exc_info=True)
            self._handle_timeline_error(e)
