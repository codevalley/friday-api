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
from models.UserModel import User

router = APIRouter(
    prefix="/v1/activities", tags=["activities"]
)


@router.post(
    "", response_model=ActivityResponse, status_code=201
)
async def create_activity(
    activity: ActivityCreate,
    service: ActivityService = Depends(),
    current_user: User = Depends(get_current_user),
):
    """Create a new activity"""
    # Add user_id to activity data
    activity.user_id = current_user.id
    return service.create_activity(activity)


@router.get("", response_model=List[ActivityResponse])
async def list_activities(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    service: ActivityService = Depends(),
    current_user: User = Depends(get_current_user),
):
    """List all activities with pagination"""
    return service.list_activities(skip=skip, limit=limit)


@router.get(
    "/{activity_id}", response_model=ActivityResponse
)
async def get_activity(
    activity_id: int,
    service: ActivityService = Depends(),
    current_user: User = Depends(get_current_user),
):
    """Get an activity by ID"""
    activity = service.get_activity(activity_id)
    if not activity:
        raise HTTPException(
            status_code=404, detail="Activity not found"
        )
    return activity


@router.put(
    "/{activity_id}", response_model=ActivityResponse
)
async def update_activity(
    activity_id: int,
    activity: ActivityUpdate,
    service: ActivityService = Depends(),
    current_user: User = Depends(get_current_user),
):
    """Update an activity"""
    updated = service.update_activity(activity_id, activity)
    if not updated:
        raise HTTPException(
            status_code=404, detail="Activity not found"
        )
    return updated


@router.delete("/{activity_id}")
async def delete_activity(
    activity_id: int,
    service: ActivityService = Depends(),
    current_user: User = Depends(get_current_user),
):
    """Delete an activity"""
    deleted = service.delete_activity(activity_id)
    if not deleted:
        raise HTTPException(
            status_code=404, detail="Activity not found"
        )
    return {"message": "Activity deleted successfully"}
