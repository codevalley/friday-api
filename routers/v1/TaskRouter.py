"""Router for Task-related endpoints."""

from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from services.TaskService import TaskService
from schemas.pydantic.TaskSchema import (
    TaskCreate,
    TaskUpdate,
    TaskResponse,
)
from schemas.pydantic.PaginationSchema import (
    PaginationParams,
)
from schemas.pydantic.CommonSchema import (
    MessageResponse,
    GenericResponse,
)
from domain.values import TaskStatus, TaskPriority
from dependencies import get_current_user
from orm.UserModel import User
from utils.error_handlers import handle_exceptions
from auth.bearer import CustomHTTPBearer

# Use our custom bearer that returns 401 for invalid tokens
auth_scheme = CustomHTTPBearer()

router = APIRouter(
    prefix="/v1/tasks",
    tags=["tasks"],
    dependencies=[Depends(auth_scheme)],
)


@router.post(
    "",
    response_model=GenericResponse[TaskResponse],
    status_code=status.HTTP_201_CREATED,
)
@handle_exceptions
async def create_task(
    task: TaskCreate,
    service: TaskService = Depends(),
    current_user: User = Depends(get_current_user),
) -> GenericResponse[TaskResponse]:
    """Create a new task."""
    result = service.create_task(task, current_user.id)
    return GenericResponse(
        data=result,
        message="Task created successfully",
    )


@router.get("", response_model=GenericResponse[dict])
@handle_exceptions
async def list_tasks(
    pagination: PaginationParams = Depends(),
    status: Optional[TaskStatus] = None,
    priority: Optional[TaskPriority] = None,
    due_before: Optional[datetime] = None,
    due_after: Optional[datetime] = None,
    parent_id: Optional[int] = Query(None),
    topic_id: Optional[int] = Query(None),
    service: TaskService = Depends(),
    current_user: User = Depends(get_current_user),
) -> GenericResponse[dict]:
    """
    List tasks with filtering and pagination.
    - status: Filter by task status
    - priority: Filter by task priority
    - due_before: Filter tasks due before this time (UTC)
    - due_after: Filter tasks due after this time (UTC)
    - parent_id: Filter subtasks of a specific parent task
    - topic_id: Filter tasks by topic
    """
    result = service.list_tasks(
        user_id=current_user.id,
        status=status,
        priority=priority,
        due_before=due_before,
        due_after=due_after,
        parent_id=parent_id,
        topic_id=topic_id,
        page=pagination.page,
        size=pagination.size,
    )
    return GenericResponse(
        data=result,
        message=f"Retrieved {result['total']} tasks",
    )


@router.get(
    "/{task_id}",
    response_model=GenericResponse[TaskResponse],
)
@handle_exceptions
async def get_task(
    task_id: int,
    service: TaskService = Depends(),
    current_user: User = Depends(get_current_user),
) -> GenericResponse[TaskResponse]:
    """Get a specific task by ID."""
    result = service.get_task(task_id, current_user.id)
    return GenericResponse(data=result)


@router.put(
    "/{task_id}",
    response_model=GenericResponse[TaskResponse],
)
@handle_exceptions
async def update_task(
    task_id: int,
    task: TaskUpdate,
    service: TaskService = Depends(),
    current_user: User = Depends(get_current_user),
) -> GenericResponse[TaskResponse]:
    """Update a specific task by ID."""
    result = service.update_task(
        task_id,
        current_user.id,
        task,
    )
    return GenericResponse(
        data=result,
        message="Task updated successfully",
    )


@router.delete(
    "/{task_id}",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
)
@handle_exceptions
async def delete_task(
    task_id: int,
    service: TaskService = Depends(),
    current_user: User = Depends(get_current_user),
) -> MessageResponse:
    """Delete a specific task by ID."""
    service.delete_task(task_id, current_user.id)
    return MessageResponse(
        message="Task deleted successfully",
    )


@router.put(
    "/{task_id}/status",
    response_model=GenericResponse[TaskResponse],
)
@handle_exceptions
async def update_task_status(
    task_id: int,
    status: TaskStatus,
    service: TaskService = Depends(),
    current_user: User = Depends(get_current_user),
) -> GenericResponse[TaskResponse]:
    """Update a task's status."""
    result = service.update_task_status(
        task_id,
        current_user.id,
        status,
    )
    return GenericResponse(
        data=result,
        message="Task status updated successfully",
    )


@router.get(
    "/{task_id}/subtasks",
    response_model=GenericResponse[dict],
)
@handle_exceptions
async def get_subtasks(
    task_id: int,
    pagination: PaginationParams = Depends(),
    service: TaskService = Depends(),
    current_user: User = Depends(get_current_user),
) -> GenericResponse[dict]:
    """Get subtasks for a specific task."""
    result = service.get_subtasks(
        task_id,
        current_user.id,
        page=pagination.page,
        size=pagination.size,
    )
    return GenericResponse(
        data=result,
        message=f"Retrieved {result['total']} subtasks",
    )


@router.put(
    "/{task_id}/note",
    response_model=GenericResponse[TaskResponse],
)
@handle_exceptions
async def attach_note(
    task_id: int,
    note_id: int,
    service: TaskService = Depends(),
    current_user: User = Depends(get_current_user),
) -> GenericResponse[TaskResponse]:
    """Attach a note to a task.

    Args:
        task_id: ID of the task to update
        note_id: ID of the note to attach
    """
    result = service.attach_note(
        task_id, note_id, current_user.id
    )
    return GenericResponse(
        data=result,
        message="Note attached to task successfully",
    )


@router.delete(
    "/{task_id}/note",
    response_model=GenericResponse[TaskResponse],
)
@handle_exceptions
async def detach_note(
    task_id: int,
    service: TaskService = Depends(),
    current_user: User = Depends(get_current_user),
) -> GenericResponse[TaskResponse]:
    """Detach the note from a task."""
    result = service.detach_note(task_id, current_user.id)
    return GenericResponse(
        data=result,
        message="Note detached from task successfully",
    )


@router.put(
    "/{task_id}/topic",
    response_model=GenericResponse[TaskResponse],
)
@handle_exceptions
async def update_task_topic(
    task_id: int,
    topic_id: Optional[int] = None,
    service: TaskService = Depends(),
    current_user: User = Depends(get_current_user),
) -> GenericResponse[TaskResponse]:
    """Update a task's topic.

    Args:
        task_id: ID of the task to update
        topic_id: ID of the topic to assign, or None to remove topic
    """
    result = service.update_task_topic(
        task_id,
        current_user.id,
        topic_id,
    )
    return GenericResponse(
        data=result,
        message="Task topic updated successfully",
    )


@router.get(
    "/by-topic/{topic_id}",
    response_model=GenericResponse[dict],
)
@handle_exceptions
async def list_tasks_by_topic(
    topic_id: int,
    pagination: PaginationParams = Depends(),
    service: TaskService = Depends(),
    current_user: User = Depends(get_current_user),
) -> GenericResponse[dict]:
    """Get all tasks for a specific topic.

    Args:
        topic_id: ID of the topic to get tasks for
    """
    result = service.get_tasks_by_topic(
        topic_id,
        current_user.id,
        page=pagination.page,
        size=pagination.size,
    )
    return GenericResponse(
        data=result,
        message=f"Retrieved {result['total']} tasks for topic",
    )
