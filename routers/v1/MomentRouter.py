from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, Query

from schemas.pydantic.MomentSchema import (
    MomentResponse,
    MomentCreate,
    MomentUpdate,
    MomentList,
)
from schemas.pydantic.PaginationSchema import (
    PaginationParams,
)
from services.MomentService import MomentService
from dependencies import get_current_user
from models.UserModel import User

router = APIRouter(prefix="/v1/moments", tags=["moments"])


@router.post(
    "", response_model=MomentResponse, status_code=201
)
async def create_moment(
    moment: MomentCreate,
    service: MomentService = Depends(),
    current_user: User = Depends(get_current_user),
):
    """Create a new moment"""
    return service.create_moment(moment, current_user.id)


@router.get("", response_model=MomentList)
async def list_moments(
    pagination: PaginationParams = Depends(),
    activity_id: Optional[int] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    service: MomentService = Depends(),
    current_user: User = Depends(get_current_user),
):
    """
    List moments with filtering and pagination
    - activity_id: Filter by activity
    - start_date: Filter moments after this time (UTC)
    - end_date: Filter moments before this time (UTC)
    """
    return service.list_moments(
        page=pagination.page,
        size=pagination.size,
        activity_id=activity_id,
        start_date=start_date,
        end_date=end_date,
        user_id=current_user.id,
    )


@router.get("/{moment_id}", response_model=MomentResponse)
async def get_moment(
    moment_id: int,
    service: MomentService = Depends(),
    current_user: User = Depends(get_current_user),
):
    """Get a moment by ID"""
    return service.get_moment(moment_id, current_user.id)


@router.put("/{moment_id}", response_model=MomentResponse)
async def update_moment(
    moment_id: int,
    moment: MomentUpdate,
    service: MomentService = Depends(),
    current_user: User = Depends(get_current_user),
):
    """Update a moment"""
    return service.update_moment(
        moment_id, moment, current_user.id
    )


@router.delete("/{moment_id}", status_code=204)
async def delete_moment(
    moment_id: int,
    service: MomentService = Depends(),
    current_user: User = Depends(get_current_user),
):
    """Delete a moment"""
    service.delete_moment(moment_id, current_user.id)
    return None


@router.get("/activities/recent", response_model=List[dict])
async def get_recent_activities(
    limit: int = Query(5, ge=1, le=20),
    service: MomentService = Depends(),
    current_user: User = Depends(get_current_user),
):
    """Get recently used activities"""
    return service.list_recent_activities(
        str(current_user.id), limit
    )
