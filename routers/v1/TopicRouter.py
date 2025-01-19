"""Router for Topic-related endpoints."""

from fastapi import APIRouter, Depends, status
from auth.bearer import CustomHTTPBearer

from schemas.pydantic.TopicSchema import (
    TopicCreate,
    TopicUpdate,
    TopicResponse,
)
from schemas.pydantic.PaginationSchema import (
    PaginationParams,
)
from schemas.pydantic.CommonSchema import (
    MessageResponse,
    GenericResponse,
)
from services.TopicService import TopicService
from services.TaskService import TaskService
from dependencies import get_current_user
from orm.UserModel import User
from utils.error_handlers import handle_exceptions

# Use our custom bearer that returns 401 for invalid tokens
auth_scheme = CustomHTTPBearer()

router = APIRouter(
    prefix="/v1/topics",
    tags=["topics"],
    dependencies=[Depends(auth_scheme)],
)


@router.post(
    "",
    response_model=GenericResponse[TopicResponse],
    status_code=status.HTTP_201_CREATED,
)
@handle_exceptions
async def create_topic(
    topic: TopicCreate,
    service: TopicService = Depends(),
    current_user: User = Depends(get_current_user),
) -> GenericResponse[TopicResponse]:
    """Create a new topic."""
    result = service.create_topic(
        user_id=current_user.id,
        data=topic,
    )
    return GenericResponse(
        data=result,
        message="Topic created successfully",
    )


@router.get("", response_model=GenericResponse[dict])
@handle_exceptions
async def list_topics(
    pagination: PaginationParams = Depends(),
    service: TopicService = Depends(),
    current_user: User = Depends(get_current_user),
) -> GenericResponse[dict]:
    """List topics with pagination."""
    result = service.list_topics(
        user_id=current_user.id,
        page=pagination.page,
        size=pagination.size,
    )
    return GenericResponse(
        data=result,
        message=f"Retrieved {result['total']} topics",
    )


@router.get(
    "/{topic_id}",
    response_model=GenericResponse[TopicResponse],
)
@handle_exceptions
async def get_topic(
    topic_id: int,
    service: TopicService = Depends(),
    current_user: User = Depends(get_current_user),
) -> GenericResponse[TopicResponse]:
    """Get a specific topic by ID."""
    result = service.get_topic(topic_id, current_user.id)
    return GenericResponse(data=result)


@router.put(
    "/{topic_id}",
    response_model=GenericResponse[TopicResponse],
)
@handle_exceptions
async def update_topic(
    topic_id: int,
    topic: TopicUpdate,
    service: TopicService = Depends(),
    current_user: User = Depends(get_current_user),
) -> GenericResponse[TopicResponse]:
    """Update a specific topic by ID."""
    result = service.update_topic(
        topic_id=topic_id,
        user_id=current_user.id,
        data=topic,
    )
    return GenericResponse(
        data=result,
        message="Topic updated successfully",
    )


@router.delete(
    "/{topic_id}",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
)
@handle_exceptions
async def delete_topic(
    topic_id: int,
    service: TopicService = Depends(),
    current_user: User = Depends(get_current_user),
) -> MessageResponse:
    """Delete a specific topic by ID."""
    service.delete_topic(topic_id, current_user.id)
    return MessageResponse(
        message="Topic deleted successfully",
    )


@router.get(
    "/{topic_id}/tasks",
    response_model=GenericResponse[dict],
)
@handle_exceptions
async def get_topic_tasks(
    topic_id: int,
    pagination: PaginationParams = Depends(),
    task_service: TaskService = Depends(),
    current_user: User = Depends(get_current_user),
) -> GenericResponse[dict]:
    """Get tasks for a specific topic."""
    result = task_service.get_tasks_by_topic(
        topic_id=topic_id,
        user_id=current_user.id,
        page=pagination.page,
        size=pagination.size,
    )
    return GenericResponse(
        data=result,
        message=f"Retrieved {result['total']} tasks",
    )
