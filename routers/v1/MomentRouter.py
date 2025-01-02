from typing import List
from datetime import datetime
from fastapi import APIRouter, Depends, Query, status
from auth.bearer import CustomHTTPBearer

from schemas.pydantic.MomentSchema import (
    MomentResponse,
    MomentCreate,
    MomentUpdate,
    MomentList,
)
from schemas.pydantic.ActivitySchema import ActivityResponse
from schemas.pydantic.PaginationSchema import (
    PaginationParams,
)
from schemas.pydantic.CommonSchema import (
    MessageResponse,
    GenericResponse,
)
from services.MomentService import MomentService
from dependencies import get_current_user
from orm.UserModel import User
from utils.error_handlers import handle_exceptions

# Use our custom bearer that returns 401 for invalid tokens
auth_scheme = CustomHTTPBearer()

router = APIRouter(
    prefix="/v1/moments",
    tags=["moments"],
    dependencies=[Depends(auth_scheme)],
)


@router.post(
    "",
    response_model=GenericResponse[MomentResponse],
    status_code=status.HTTP_201_CREATED,
)
@handle_exceptions
async def create_moment(
    moment: MomentCreate,
    service: MomentService = Depends(),
    current_user: User = Depends(get_current_user),
):
    """Create a new moment"""
    result = service.create_moment(moment, current_user.id)
    return GenericResponse(
        data=result,
        message="Moment created successfully",
    )


@router.get("", response_model=GenericResponse[MomentList])
@handle_exceptions
async def list_moments(
    pagination: PaginationParams = Depends(),
    activity_id: int | None = None,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
    service: MomentService = Depends(),
    current_user: User = Depends(get_current_user),
):
    """
    List moments with filtering and pagination
    - activity_id: Filter by activity
    - start_date: Filter moments after this time (UTC)
    - end_date: Filter moments before this time (UTC)
    """
    result = service.list_moments(
        page=pagination.page,
        size=pagination.size,
        activity_id=activity_id,
        start_date=start_date,
        end_date=end_date,
        user_id=current_user.id,
    )
    return GenericResponse(
        data=result,
        message=f"Retrieved {result.total} moments",
    )


@router.get(
    "/{moment_id}",
    response_model=GenericResponse[MomentResponse],
)
@handle_exceptions
async def get_moment(
    moment_id: int,
    service: MomentService = Depends(),
    current_user: User = Depends(get_current_user),
):
    """Get a moment by ID"""
    result = service.get_moment(moment_id, current_user.id)
    return GenericResponse(data=result)


@router.put(
    "/{moment_id}",
    response_model=GenericResponse[MomentResponse],
)
@handle_exceptions
async def update_moment(
    moment_id: int,
    moment: MomentUpdate,
    service: MomentService = Depends(),
    current_user: User = Depends(get_current_user),
):
    """Update a moment"""
    result = service.update_moment(
        moment_id, moment, current_user.id
    )
    return GenericResponse(
        data=result,
        message="Moment updated successfully",
    )


@router.delete(
    "/{moment_id}",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
)
@handle_exceptions
async def delete_moment(
    moment_id: int,
    service: MomentService = Depends(),
    current_user: User = Depends(get_current_user),
):
    """Delete a moment"""
    service.delete_moment(moment_id, current_user.id)
    return MessageResponse(
        message="Moment deleted successfully"
    )


@router.get(
    "/activities/recent",
    response_model=GenericResponse[List[ActivityResponse]],
)
@handle_exceptions
async def get_recent_activities(
    limit: int = Query(5, ge=1, le=20),
    service: MomentService = Depends(),
    current_user: User = Depends(get_current_user),
):
    """Get recently used activities"""
    activities = service.list_recent_activities(
        str(current_user.id), limit
    )
    return GenericResponse(
        data=activities,
        message=f"Retrieved {len(activities)} recent activities",
    )
