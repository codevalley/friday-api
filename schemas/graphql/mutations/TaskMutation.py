"""GraphQL mutations for Task-related operations."""

import strawberry
from strawberry.types import Info
from fastapi import HTTPException
from typing import Dict, Any

from domain.exceptions import (
    TaskValidationError,
    TaskContentError,
    TaskStatusError,
    TaskParentError,
    TaskReferenceError,
    TaskDateError,
    TaskPriorityError,
)
from schemas.graphql.types.Task import (
    Task,
    TaskInput,
    TaskUpdateInput,
)
from services.TaskService import TaskService
from configs.GraphQL import (
    get_user_from_context,
    get_db_from_context,
)


def create_error_response(
    message: str, code: str, status_code: int = 400
) -> HTTPException:
    """Create a standardized error response.

    Args:
        message: The error message.
        code: The error code.
        status_code: The HTTP status code (default: 400).

    Returns:
        HTTPException with standardized format.
    """
    return HTTPException(
        status_code=status_code,
        detail={
            "message": message,
            "code": code,
            "type": "GraphQLError",
        },
    )


def handle_task_error(error: Exception) -> None:
    """Handle task-related errors and raise appropriate HTTP exceptions.

    Args:
        error: The error to handle.

    Raises:
        HTTPException: With appropriate status code and message.
    """
    if isinstance(error, TaskContentError):
        raise create_error_response(
            str(error), "TASK_CONTENT_ERROR"
        )
    elif isinstance(error, TaskStatusError):
        raise create_error_response(
            str(error), "TASK_INVALID_STATUS"
        )
    elif isinstance(error, TaskParentError):
        raise create_error_response(
            str(error), "TASK_PARENT_ERROR", 404
        )
    elif isinstance(error, TaskReferenceError):
        raise create_error_response(
            str(error), "TASK_NOT_FOUND", 404
        )
    elif isinstance(error, TaskDateError):
        raise create_error_response(
            str(error), "TASK_DATE_ERROR"
        )
    elif isinstance(error, TaskPriorityError):
        raise create_error_response(
            str(error), "TASK_PRIORITY_ERROR"
        )
    elif isinstance(error, TaskValidationError):
        raise create_error_response(
            str(error), "TASK_VALIDATION_ERROR"
        )
    elif isinstance(error, HTTPException):
        # Pass through HTTP exceptions
        raise error
    else:
        raise create_error_response(
            "Internal server error",
            "INTERNAL_SERVER_ERROR",
            500,
        )


def check_authentication(info: Info) -> Dict[str, Any]:
    """Check authentication and return context.

    Args:
        info: The GraphQL info object.

    Returns:
        Dict containing db and user.

    Raises:
        HTTPException: If authentication fails.
    """
    db = get_db_from_context(info)
    user = get_user_from_context(info)

    if not user:
        raise create_error_response(
            "Authentication required",
            "UNAUTHORIZED",
            401,
        )

    return {"db": db, "user": user}


def check_task_ownership(
    task_user_id: str, current_user_id: str
) -> None:
    """Check if the current user owns the task.

    Args:
        task_user_id: The task's user ID.
        current_user_id: The current user's ID.

    Raises:
        HTTPException: If the user doesn't own the task.
    """
    if str(task_user_id) != str(current_user_id):
        raise create_error_response(
            "Not authorized to access this task",
            "FORBIDDEN",
            403,
        )


@strawberry.type
class TaskMutation:
    """GraphQL mutations for task operations."""

    @strawberry.mutation
    def create_task(
        self, info: Info, task: TaskInput
    ) -> Task:
        """Create a new task.

        Args:
            info: The GraphQL info object.
            task: The task input data.

        Returns:
            The created task.

        Raises:
            HTTPException: If authentication fails or task creation is invalid.
        """
        context = check_authentication(info)
        db, user = context["db"], context["user"]

        try:
            task_data = task.to_domain(str(user.id))
            task_service = TaskService(db)
            created_task = task_service.create_task(
                task_data
            )
            return Task.from_domain(created_task)
        except Exception as e:
            handle_task_error(e)

    @strawberry.mutation
    def update_task(
        self,
        info: Info,
        task_id: int,
        task: TaskUpdateInput,
    ) -> Task:
        """Update an existing task.

        Args:
            info: The GraphQL info object.
            task_id: The ID of the task to update.
            task: The task update data.

        Returns:
            The updated task.

        Raises:
            HTTPException: If authentication fails or task update is invalid.
        """
        context = check_authentication(info)
        db, user = context["db"], context["user"]

        try:
            task_service = TaskService(db)
            existing_task = task_service.get_task(task_id)
            check_task_ownership(
                existing_task.user_id, user.id
            )

            task_data = task.to_domain(existing_task)
            updated_task = task_service.update_task(
                task_id, task_data
            )
            return Task.from_domain(updated_task)
        except Exception as e:
            handle_task_error(e)

    @strawberry.mutation
    def delete_task(self, info: Info, task_id: int) -> bool:
        """Delete a task.

        Args:
            info: The GraphQL info object.
            task_id: The ID of the task to delete.

        Returns:
            True if the task was deleted successfully.

        Raises:
            HTTPException: If authentication fails or task deletion is invalid.
        """
        context = check_authentication(info)
        db, user = context["db"], context["user"]

        try:
            task_service = TaskService(db)
            existing_task = task_service.get_task(task_id)
            check_task_ownership(
                existing_task.user_id, user.id
            )

            task_service.delete_task(task_id)
            return True
        except Exception as e:
            handle_task_error(e)
