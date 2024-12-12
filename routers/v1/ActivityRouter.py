from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from configs.Database import get_db_connection
from schemas.pydantic.ActivitySchema import (
    ActivityResponse,
    ActivityCreate,
    ActivityUpdate,
)
from services.ActivityService import ActivityService
from dependencies import get_current_user
from models.UserModel import UserModel

router = APIRouter(
    prefix="/v1/activities", tags=["activities"]
)


@router.post(
    "", response_model=ActivityResponse, status_code=201
)
async def create_activity(
    activity: ActivityCreate,
    service: ActivityService = Depends(),
    current_user: UserModel = Depends(get_current_user),
):
    """Create a new activity"""
    return service.create_activity(activity)


@router.get("", response_model=List[ActivityResponse])
async def list_activities(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    service: ActivityService = Depends(),
    current_user: UserModel = Depends(get_current_user),
):
    """List all activities with pagination"""
    return service.list_activities(skip=skip, limit=limit)


@router.get(
    "/{activity_id}", response_model=ActivityResponse
)
async def get_activity(
    activity_id: int,
    service: ActivityService = Depends(),
    current_user: UserModel = Depends(get_current_user),
):
    """Get an activity by ID"""
    return service.get_activity(activity_id)


@router.put(
    "/{activity_id}", response_model=ActivityResponse
)
async def update_activity(
    activity_id: int,
    activity: ActivityUpdate,
    service: ActivityService = Depends(),
    current_user: UserModel = Depends(get_current_user),
):
    """Update an activity"""
    return service.update_activity(activity_id, activity)


@router.delete("/{activity_id}", status_code=204)
async def delete_activity(
    activity_id: int,
    service: ActivityService = Depends(),
    current_user: UserModel = Depends(get_current_user),
):
    """Delete an activity"""
    service.delete_activity(activity_id)
    return None
