"""GraphQL mutations for Task-related operations."""

import strawberry
from strawberry.types import Info
from fastapi import HTTPException

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


@strawberry.type
class TaskMutation:
    """GraphQL mutations for task operations."""

    @strawberry.mutation
    def create_task(
        self, info: Info, task: TaskInput
    ) -> Task:
        """Create a new task.

        Args:
            info: GraphQL request info containing context
            task: Task input data

        Returns:
            Created task

        Raises:
            HTTPException: If user is not authenticated or validation fails
        """
        user = get_user_from_context(info)
        if not user:
            raise HTTPException(
                status_code=401,
                detail="Authentication required to create task",
            )

        service = TaskService(get_db_from_context(info))
        task_data = task.to_domain(str(user.id))

        try:
            result = service.create_task(task_data)
            return Task.from_domain(result)
        except ValueError as e:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid task data: {str(e)}",
            )

    @strawberry.mutation
    def update_task(
        self,
        info: Info,
        task_id: int,
        task: TaskUpdateInput,
    ) -> Task:
        """Update an existing task.

        Args:
            info: GraphQL request info containing context
            task_id: ID of task to update
            task: Updated task data

        Returns:
            Updated task

        Raises:
            HTTPException: If user is not authenticated or validation fails
        """
        user = get_user_from_context(info)
        if not user:
            raise HTTPException(
                status_code=401,
                detail="Authentication required to update task",
            )

        service = TaskService(get_db_from_context(info))
        try:
            # Get existing task to merge with updates
            existing = service.get_task(task_id, user.id)
            task_data = task.to_domain(existing)
            result = service.update_task(
                task_id, user.id, task_data
            )
            return Task.from_domain(result)
        except ValueError as e:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid task data: {str(e)}",
            )

    @strawberry.mutation
    def delete_task(self, info: Info, task_id: int) -> bool:
        """Delete a task.

        Args:
            info: GraphQL request info containing context
            task_id: ID of task to delete

        Returns:
            True if deletion was successful

        Raises:
            HTTPException: If user is not authenticated or task not found
        """
        user = get_user_from_context(info)
        if not user:
            raise HTTPException(
                status_code=401,
                detail="Authentication required to delete task",
            )

        service = TaskService(get_db_from_context(info))
        try:
            return service.delete_task(task_id, user.id)
        except ValueError as e:
            raise HTTPException(
                status_code=404,
                detail=f"Task not found: {str(e)}",
            )
