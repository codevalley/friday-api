"""Router for Timeline-related endpoints."""

from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, Query

from services.TimelineService import TimelineService
from schemas.pydantic.TimelineSchema import TimelineEvent
from schemas.pydantic.PaginationSchema import (
    PaginationParams,
)
from schemas.pydantic.CommonSchema import GenericResponse
from domain.timeline import TimelineEventType
from dependencies import get_current_user
from orm.UserModel import User
from utils.error_handlers import handle_exceptions
from auth.bearer import CustomHTTPBearer

# Use our custom bearer that returns 401 for invalid tokens
auth_scheme = CustomHTTPBearer()

router = APIRouter(
    prefix="/v1/timeline",
    tags=["timeline"],
    dependencies=[Depends(auth_scheme)],
)


@router.get(
    "",
    response_model=GenericResponse[dict],
)
@handle_exceptions
async def list_timeline_events(
    pagination: PaginationParams = Depends(),
    event_type: Optional[TimelineEventType] = Query(None),
    start_time: Optional[datetime] = Query(None),
    end_time: Optional[datetime] = Query(None),
    service: TimelineService = Depends(),
    current_user: User = Depends(get_current_user),
) -> GenericResponse[dict]:
    """List timeline events with optional filtering.

    Args:
        pagination: Pagination parameters
        event_type: Optional event type to filter by
        start_time: Optional start time to filter by
        end_time: Optional end time to filter by
        service: Timeline service instance
        current_user: Current authenticated user

    Returns:
        Dictionary containing:
            - items: List of timeline events
            - total: Total number of events
            - page: Current page number
            - size: Page size
            - pages: Total number of pages
    """
    result = await service.list_events(
        page=pagination.page,
        size=pagination.size,
        event_type=event_type,
        start_time=start_time,
        end_time=end_time,
        user_id=current_user.id,
    )

    return GenericResponse(
        data=result,
        message="Timeline events retrieved successfully",
    )


@router.get(
    "/recent",
    response_model=GenericResponse[list[TimelineEvent]],
)
@handle_exceptions
async def get_recent_events(
    limit: int = Query(5, ge=1, le=50),
    service: TimelineService = Depends(),
    current_user: User = Depends(get_current_user),
) -> GenericResponse[list[TimelineEvent]]:
    """Get recent timeline events for the current user.

    Args:
        limit: Maximum number of events to return (1-50)
        service: Timeline service instance
        current_user: Current authenticated user

    Returns:
        List of recent timeline events
    """
    events = await service.get_recent_events(
        user_id=current_user.id,
        limit=limit,
    )

    return GenericResponse(
        data=events,
        message="Recent timeline events retrieved successfully",
    )


@router.get(
    "/by-type/{event_type}",
    response_model=GenericResponse[dict],
)
@handle_exceptions
async def get_events_by_type(
    event_type: TimelineEventType,
    pagination: PaginationParams = Depends(),
    service: TimelineService = Depends(),
    current_user: User = Depends(get_current_user),
) -> GenericResponse[dict]:
    """Get timeline events of a specific type.

    Args:
        event_type: Type of events to retrieve
        pagination: Pagination parameters
        service: Timeline service instance
        current_user: Current authenticated user

    Returns:
        Dictionary containing:
            - items: List of timeline events
            - total: Total number of events
            - page: Current page number
            - size: Page size
            - pages: Total number of pages
    """
    result = await service.get_events_by_type(
        event_type=event_type,
        user_id=current_user.id,
        page=pagination.page,
        size=pagination.size,
    )

    return GenericResponse(
        data=result,
        message=f"Timeline events of type {event_type} retrieved successfully",
    )


@router.get(
    "/in-timerange",
    response_model=GenericResponse[dict],
)
@handle_exceptions
async def get_events_in_timerange(
    start_time: datetime = Query(...),
    end_time: datetime = Query(...),
    pagination: PaginationParams = Depends(),
    service: TimelineService = Depends(),
    current_user: User = Depends(get_current_user),
) -> GenericResponse[dict]:
    """Get timeline events within a specific time range.

    Args:
        start_time: Start of time range
        end_time: End of time range
        pagination: Pagination parameters
        service: Timeline service instance
        current_user: Current authenticated user

    Returns:
        Dictionary containing:
            - items: List of timeline events
            - total: Total number of events
            - page: Current page number
            - size: Page size
            - pages: Total number of pages
    """
    result = await service.get_events_in_timerange(
        user_id=current_user.id,
        start_time=start_time,
        end_time=end_time,
        page=pagination.page,
        size=pagination.size,
    )

    return GenericResponse(
        data=result,
        message="Timeline events in timerange retrieved successfully",
    )
