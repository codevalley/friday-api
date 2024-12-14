from fastapi import APIRouter, Depends, HTTPException

from services.ActivityService import ActivityService
from schemas.pydantic.ActivitySchema import (
    ActivityCreate,
    ActivityUpdate,
    ActivityResponse,
    ActivityList,
)
from schemas.pydantic.PaginationSchema import (
    PaginationParams,
)
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
    try:
        return service.create_activity(
            activity, current_user.id
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("", response_model=ActivityList)
async def list_activities(
    pagination: PaginationParams = Depends(),
    service: ActivityService = Depends(),
    current_user: User = Depends(get_current_user),
):
    """List all activities with pagination"""
    return service.list_activities(
        user_id=current_user.id,
        page=pagination.page,
        size=pagination.size,
    )


@router.get(
    "/{activity_id}", response_model=ActivityResponse
)
async def get_activity(
    activity_id: int,
    service: ActivityService = Depends(),
    current_user: User = Depends(get_current_user),
):
    """Get an activity by ID"""
    activity = service.get_activity(
        activity_id, current_user.id
    )
    if not activity:
        raise HTTPException(
            status_code=404,
            detail="Activity not found",
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
    updated = service.update_activity(
        activity_id,
        activity,
        current_user.id,
    )
    if not updated:
        raise HTTPException(
            status_code=404,
            detail="Activity not found",
        )
    return updated


@router.delete("/{activity_id}")
async def delete_activity(
    activity_id: int,
    service: ActivityService = Depends(),
    current_user: User = Depends(get_current_user),
):
    """Delete an activity"""
    if not service.delete_activity(
        activity_id, current_user.id
    ):
        raise HTTPException(
            status_code=404,
            detail="Activity not found",
        )
    return {"message": "Activity deleted successfully"}
