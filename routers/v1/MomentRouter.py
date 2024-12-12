from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session

from configs.Database import get_db_connection
from schemas.pydantic.MomentSchema import (
    MomentResponse,
    MomentCreate,
    MomentUpdate,
    MomentList,
)
from services.MomentService import MomentService
from dependencies import get_current_user
from models.UserModel import UserModel

router = APIRouter(prefix="/v1/moments", tags=["moments"])


@router.post(
    "", response_model=MomentResponse, status_code=201
)
async def create_moment(
    moment: MomentCreate,
    service: MomentService = Depends(),
    current_user: UserModel = Depends(get_current_user),
):
    """Create a new moment"""
    return service.create_moment(moment)


@router.get("", response_model=MomentList)
async def list_moments(
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
    activity_id: Optional[int] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    service: MomentService = Depends(),
    current_user: UserModel = Depends(get_current_user),
):
    """
    List moments with filtering and pagination
    - page: Page number (1-based)
    - size: Items per page
    - activity_id: Filter by activity
    - start_date: Filter moments after this time (UTC)
    - end_date: Filter moments before this time (UTC)
    """
    return service.list_moments(
        page, size, activity_id, start_date, end_date
    )


@router.get("/{moment_id}", response_model=MomentResponse)
async def get_moment(
    moment_id: int,
    service: MomentService = Depends(),
    current_user: UserModel = Depends(get_current_user),
):
    """Get a moment by ID"""
    return service.get_moment(moment_id)


@router.put("/{moment_id}", response_model=MomentResponse)
async def update_moment(
    moment_id: int,
    moment: MomentUpdate,
    service: MomentService = Depends(),
    current_user: UserModel = Depends(get_current_user),
):
    """Update a moment"""
    return service.update_moment(moment_id, moment)


@router.delete("/{moment_id}", status_code=204)
async def delete_moment(
    moment_id: int,
    service: MomentService = Depends(),
    current_user: UserModel = Depends(get_current_user),
):
    """Delete a moment"""
    service.delete_moment(moment_id)
    return None


@router.get("/activities/recent", response_model=List[dict])
async def get_recent_activities(
    limit: int = Query(5, ge=1, le=20),
    db: Session = Depends(get_db_connection),
):
    """Get recently used activities"""
    service = MomentService(db)
    return service.get_recent_activities(limit)
