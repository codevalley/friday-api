from fastapi import APIRouter, Depends, status
from auth.bearer import CustomHTTPBearer

from services.ActivityService import ActivityService
from schemas.pydantic.ActivitySchema import (
    ActivityCreate,
    ActivityUpdate,
    ActivityResponse,
    ActivityList,
    ProcessingStatusResponse,
    RetryResponse,
)
from schemas.pydantic.PaginationSchema import (
    PaginationParams,
)
from schemas.pydantic.CommonSchema import (
    MessageResponse,
    GenericResponse,
)
from dependencies import (
    get_current_user,
    get_activity_service,
)
from orm.UserModel import User
from utils.error_handlers import handle_exceptions

# Use our custom bearer that returns 401 for invalid tokens
auth_scheme = CustomHTTPBearer()

router = APIRouter(
    prefix="/v1/activities",
    tags=["activities"],
    dependencies=[Depends(auth_scheme)],
)


@router.post(
    "",
    response_model=GenericResponse[ActivityResponse],
    status_code=status.HTTP_201_CREATED,
)
@handle_exceptions
async def create_activity(
    activity: ActivityCreate,
    service: ActivityService = Depends(
        get_activity_service
    ),
    current_user: User = Depends(get_current_user),
):
    """Create a new activity"""
    result = service.create_activity(
        activity, current_user.id
    )
    return GenericResponse(
        data=result,
        message="Activity created successfully",
    )


@router.get(
    "", response_model=GenericResponse[ActivityList]
)
@handle_exceptions
async def list_activities(
    pagination: PaginationParams = Depends(),
    service: ActivityService = Depends(
        get_activity_service
    ),
    current_user: User = Depends(get_current_user),
):
    """List all activities with pagination"""
    result = service.list_activities(
        user_id=current_user.id,
        page=pagination.page,
        size=pagination.size,
    )
    return GenericResponse(
        data=result,
        message=f"Retrieved {result.total} activities",
    )


@router.get(
    "/{activity_id}",
    response_model=GenericResponse[ActivityResponse],
)
@handle_exceptions
async def get_activity(
    activity_id: int,
    service: ActivityService = Depends(
        get_activity_service
    ),
    current_user: User = Depends(get_current_user),
):
    """Get an activity by ID"""
    result = service.get_activity(
        activity_id, current_user.id
    )
    return GenericResponse(data=result)


@router.put(
    "/{activity_id}",
    response_model=GenericResponse[ActivityResponse],
)
@handle_exceptions
async def update_activity(
    activity_id: int,
    activity: ActivityUpdate,
    service: ActivityService = Depends(
        get_activity_service
    ),
    current_user: User = Depends(get_current_user),
):
    """Update an activity"""
    result = service.update_activity(
        activity_id,
        activity,
        current_user.id,
    )
    return GenericResponse(
        data=result,
        message="Activity updated successfully",
    )


@router.delete(
    "/{activity_id}",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
)
@handle_exceptions
async def delete_activity(
    activity_id: int,
    service: ActivityService = Depends(
        get_activity_service
    ),
    current_user: User = Depends(get_current_user),
):
    """Delete an activity"""
    service.delete_activity(activity_id, current_user.id)
    return MessageResponse(
        message="Activity deleted successfully"
    )


@router.get(
    "/{activity_id}/processing-status",
    response_model=GenericResponse[
        ProcessingStatusResponse
    ],
)
@handle_exceptions
async def get_processing_status(
    activity_id: int,
    service: ActivityService = Depends(
        get_activity_service
    ),
    current_user: User = Depends(get_current_user),
):
    """Get activity processing status"""
    result = service.get_processing_status(
        activity_id, current_user.id
    )
    return GenericResponse(
        data=result,
        message="Retrieved processing status",
    )


@router.post(
    "/{activity_id}/retry-processing",
    response_model=GenericResponse[RetryResponse],
)
@handle_exceptions
async def retry_processing(
    activity_id: int,
    service: ActivityService = Depends(
        get_activity_service
    ),
    current_user: User = Depends(get_current_user),
):
    """Retry processing for a failed activity"""
    job_id = service.retry_processing(
        activity_id, current_user.id
    )
    return GenericResponse(
        data=RetryResponse(job_id=job_id),
        message="Activity queued for retry processing",
    )
