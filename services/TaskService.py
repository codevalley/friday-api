"""Service for managing tasks in the system."""

from typing import Dict, Any, Optional
from datetime import datetime
from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from configs.Database import get_db_connection
from repositories.TaskRepository import TaskRepository
from repositories.TopicRepository import TopicRepository
from domain.values import TaskStatus, TaskPriority
from domain.exceptions import (
    TaskValidationError,
    TaskStatusError,
    TaskReferenceError,
)
from utils.validation import validate_pagination
from schemas.pydantic.TaskSchema import (
    TaskCreate,
    TaskUpdate,
    TaskResponse,
)

import logging

logger = logging.getLogger(__name__)


class TaskService:
    """Service for managing tasks in the system.

    This service handles the business logic for creating, reading, updating,
    and deleting tasks. It ensures proper validation and authorization.

    Attributes:
        db: Database session
        task_repo: Repository for task operations
        topic_repo: Repository for topic operations
    """

    def __init__(
        self,
        db: Session = Depends(get_db_connection),
    ):
        """Initialize the task service.

        Args:
            db: Database session from dependency injection
        """
        self.db = db
        self.task_repo = TaskRepository(db)
        self.topic_repo = TopicRepository(db)

    def _validate_topic(
        self, topic_id: Optional[int], user_id: str
    ) -> None:
        """Validate that a topic exists and belongs to the user.

        Args:
            topic_id: ID of the topic to validate
            user_id: ID of the user who should own the topic

        Raises:
            TaskReferenceError: If topic doesn't exist or wrong user
        """
        if topic_id is not None:
            topic = self.topic_repo.get_by_user(
                topic_id, user_id
            )
            if topic is None:
                raise TaskReferenceError(
                    "Topic not found or belongs to "
                    "another user"
                )

    def _handle_task_error(self, error: Exception) -> None:
        """Map domain exceptions to HTTP exceptions."""
        if isinstance(error, TaskStatusError):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "message": str(error),
                    "code": error.code,
                },
            )
        elif isinstance(error, TaskReferenceError):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "message": str(error),
                    "code": error.code,
                },
            )
        elif isinstance(error, TaskValidationError):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "message": str(error),
                    "code": error.code,
                },
            )
        raise error

    def create_task(
        self,
        task_data: TaskCreate,
        user_id: str,
    ) -> TaskResponse:
        """Create a new task.

        Args:
            task_data: Task creation data
            user_id: ID of the user creating the task

        Returns:
            TaskResponse: Created task data

        Raises:
            HTTPException: If task creation fails
        """
        try:
            # Convert to domain model
            domain_data = task_data.to_domain(user_id)

            # Validate topic if provided
            self._validate_topic(
                domain_data.topic_id, user_id
            )

            # Validate before saving
            domain_data.validate_for_save()

            # Create task - only pass fields that repository expects
            task = self.task_repo.create(
                title=domain_data.title,
                description=domain_data.description,
                user_id=domain_data.user_id,
                status=domain_data.status,
                priority=domain_data.priority,
                due_date=domain_data.due_date,
                tags=domain_data.tags,
                parent_id=domain_data.parent_id,
                topic_id=domain_data.topic_id,
            )
            self.db.commit()

            # Ensure task was created successfully
            if task.id is None:
                raise ValueError(
                    "Task creation failed - no ID returned"
                )

            return TaskResponse.model_validate(
                task.to_dict()
            )

        except (
            TaskValidationError,
            TaskStatusError,
            TaskReferenceError,
        ) as e:
            self._handle_task_error(e)
            raise
        except Exception as e:
            logger.error(
                f"Unexpected error creating task: {str(e)}"
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create task",
            )

    def get_task(
        self, task_id: int, user_id: str
    ) -> TaskResponse:
        """Get a specific task by ID.

        Args:
            task_id: ID of the task to retrieve
            user_id: ID of the user requesting the task

        Returns:
            TaskResponse: Task data

        Raises:
            HTTPException: If task not found or access denied
        """
        task = self.task_repo.get_by_user(task_id, user_id)
        if not task:
            raise HTTPException(
                status_code=404, detail="Task not found"
            )

        # Ensure task has an ID
        if task.id is None:
            raise ValueError("Task missing ID")

        return TaskResponse.model_validate(task.to_dict())

    def list_tasks(
        self,
        user_id: str,
        status: Optional[TaskStatus] = None,
        priority: Optional[TaskPriority] = None,
        due_before: Optional[datetime] = None,
        due_after: Optional[datetime] = None,
        parent_id: Optional[int] = None,
        topic_id: Optional[int] = None,
        page: int = 1,
        size: int = 50,
    ) -> Dict[str, Any]:
        """List tasks for a user with filtering and pagination.

        Args:
            user_id: ID of the user whose tasks to list
            status: Optional status filter
            priority: Optional priority filter
            due_before: Optional due date upper bound
            due_after: Optional due date lower bound
            parent_id: Optional parent task ID filter
            topic_id: Optional topic ID filter
            page: Page number (default: 1)
            size: Page size (default: 50)

        Returns:
            Dict[str, Any]: Paginated list of tasks

        Raises:
            HTTPException: If pagination parameters are invalid
        """
        validate_pagination(page, size)
        skip = (page - 1) * size

        # Validate topic if provided
        self._validate_topic(topic_id, user_id)

        tasks = self.task_repo.list_tasks(
            user_id=user_id,
            status=status,
            priority=priority,
            due_before=due_before,
            due_after=due_after,
            parent_id=parent_id,
            topic_id=topic_id,
            skip=skip,
            limit=size,
        )

        total = self.task_repo.count_tasks(
            user_id=user_id,
            status=status,
            topic_id=topic_id,
        )

        return {
            "items": [
                TaskResponse.model_validate(task.to_dict())
                for task in tasks
            ],
            "total": total,
            "page": page,
            "size": size,
            "pages": (total + size - 1) // size,
        }

    def update_task(
        self,
        task_id: int,
        user_id: str,
        update_data: TaskUpdate,
    ) -> TaskResponse:
        """Update a specific task.

        Args:
            task_id: ID of the task to update
            user_id: ID of the user requesting the update
            update_data: Data to update

        Returns:
            TaskResponse: Updated task data

        Raises:
            HTTPException: If task not found or update fails
        """
        task = self.task_repo.get_by_user(task_id, user_id)
        if not task:
            raise HTTPException(
                status_code=404, detail="Task not found"
            )

        try:
            # Validate topic if being updated
            if update_data.topic_id is not None:
                self._validate_topic(
                    update_data.topic_id, user_id
                )

            # Update task
            update_dict = update_data.model_dump(
                exclude_unset=True
            )
            updated_task = self.task_repo.update(
                task_id, update_dict
            )
            if not updated_task:
                raise HTTPException(
                    status_code=404,
                    detail="Failed to update task",
                )

            self.db.commit()
            return TaskResponse.model_validate(
                updated_task.to_dict()
            )

        except TaskReferenceError as e:
            self._handle_task_error(e)
            raise
        except Exception as e:
            logger.error(
                f"Unexpected error updating task: {str(e)}"
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update task",
            )

    def update_task_topic(
        self,
        task_id: int,
        user_id: str,
        topic_id: Optional[int],
    ) -> TaskResponse:
        """Update a task's topic.

        Args:
            task_id: ID of the task to update
            user_id: ID of the user requesting the update
            topic_id: New topic ID, or None to remove topic

        Returns:
            TaskResponse: Updated task data

        Raises:
            HTTPException: If task not found or update fails
        """
        try:
            # Validate topic if being set
            self._validate_topic(topic_id, user_id)

            # Update task's topic
            updated_task = self.task_repo.update_topic(
                task_id, user_id, topic_id
            )
            if not updated_task:
                raise HTTPException(
                    status_code=404,
                    detail="Task not found",
                )

            self.db.commit()
            return TaskResponse.model_validate(
                updated_task.to_dict()
            )

        except TaskReferenceError as e:
            self._handle_task_error(e)
            raise
        except Exception as e:
            logger.error(
                f"Unexpected error updating task topic: {str(e)}"
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update task topic",
            )

    def get_tasks_by_topic(
        self,
        topic_id: int,
        user_id: str,
        page: int = 1,
        size: int = 50,
    ) -> Dict[str, Any]:
        """Get all tasks for a specific topic.

        Args:
            topic_id: ID of the topic
            user_id: ID of the user requesting the tasks
            page: Page number (default: 1)
            size: Page size (default: 50)

        Returns:
            Dict[str, Any]: Paginated list of tasks

        Raises:
            HTTPException: If topic not found or pagination parameters invalid
        """
        validate_pagination(page, size)
        skip = (page - 1) * size

        # Validate topic exists and belongs to user
        self._validate_topic(topic_id, user_id)

        tasks = self.task_repo.get_tasks_by_topic(
            topic_id=topic_id,
            user_id=user_id,
            skip=skip,
            limit=size,
        )

        total = self.task_repo.count_tasks(
            user_id=user_id,
            topic_id=topic_id,
        )

        return {
            "items": [
                TaskResponse.model_validate(task.to_dict())
                for task in tasks
            ],
            "total": total,
            "page": page,
            "size": size,
            "pages": (total + size - 1) // size,
        }

    def delete_task(
        self, task_id: int, user_id: str
    ) -> bool:
        """Delete a specific task.

        Args:
            task_id: ID of the task to delete
            user_id: ID of the user requesting deletion

        Returns:
            bool: True if task was deleted

        Raises:
            HTTPException: If task not found or deletion fails
        """
        task = self.task_repo.get_by_user(task_id, user_id)
        if not task:
            raise HTTPException(
                status_code=404, detail="Task not found"
            )

        try:
            self.task_repo.delete(task_id)
            self.db.commit()
            return True

        except Exception as e:
            logger.error(
                f"Unexpected error deleting task: {str(e)}"
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete task",
            )

    def update_task_status(
        self,
        task_id: int,
        user_id: str,
        new_status: TaskStatus,
    ) -> TaskResponse:
        """Update a task's status.

        Args:
            task_id: ID of the task to update
            user_id: ID of the user requesting the update
            new_status: New status to set

        Returns:
            TaskResponse: Updated task data

        Raises:
            HTTPException: If task not found or status update fails
        """
        try:
            task = self.task_repo.update_status(
                task_id=task_id,
                user_id=user_id,
                new_status=new_status,
            )
            if not task:
                raise HTTPException(
                    status_code=404,
                    detail="Task not found",
                )

            self.db.commit()

            # Ensure task has an ID
            if task.id is None:
                raise ValueError("Updated task missing ID")

            return TaskResponse.model_validate(
                task.to_dict()
            )

        except TaskStatusError as e:
            self._handle_task_error(e)
        except Exception as e:
            logger.error(
                f"Unexpected error updating task status: {str(e)}"
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update task status",
            )

    def get_subtasks(
        self,
        task_id: int,
        user_id: str,
        page: int = 1,
        size: int = 50,
    ) -> Dict[str, Any]:
        """Get subtasks for a specific task.

        Args:
            task_id: ID of the parent task
            user_id: ID of the user requesting subtasks
            page: Page number (default: 1)
            size: Page size (default: 50)

        Returns:
            Dict[str, Any]: Paginated list of subtasks

        Raises:
            HTTPException: If parent task not found or access denied
        """
        # First verify parent task exists and belongs to user
        parent = self.task_repo.get_by_user(
            task_id, user_id
        )
        if not parent:
            raise HTTPException(
                status_code=404,
                detail="Parent task not found",
            )

        validate_pagination(page, size)
        skip = (page - 1) * size

        subtasks = self.task_repo.get_subtasks(
            task_id=task_id,
            user_id=user_id,
            skip=skip,
            limit=size,
        )

        return {
            "items": [
                TaskResponse.model_validate(task.to_dict())
                for task in subtasks
            ],
            "total": len(
                subtasks
            ),  # Simple count since filtered
            "page": page,
            "size": size,
            "pages": (len(subtasks) + size - 1) // size,
        }
