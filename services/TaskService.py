"""Service for managing tasks in the system."""

from typing import Dict, Any, Optional
from datetime import datetime
from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from configs.Database import get_db_connection
from repositories.TaskRepository import TaskRepository
from repositories.TopicRepository import TopicRepository
from domain.values import (
    TaskStatus,
    TaskPriority,
    ProcessingStatus,
)
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
from domain.ports.QueueService import QueueService
from dependencies import get_queue

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
        queue_service: Queue service for task processing
    """

    def __init__(
        self,
        db: Session = Depends(get_db_connection),
        queue_service: QueueService = Depends(get_queue),
    ):
        """Initialize the task service.

        Args:
            db: Database session from dependency injection
            queue_service: Queue service for task processing
        """
        self.db = db
        self.task_repo = TaskRepository(db)
        self.topic_repo = TopicRepository(db)
        self.queue_service = queue_service

    def _validate_topic(
        self, topic_id: int, user_id: str
    ) -> None:
        """Validate that a topic exists and belongs to user.

        Args:
            topic_id: Topic ID to validate
            user_id: Owner's user ID

        Raises:
            TaskReferenceError: If topic not found or doesn't belong to user
        """
        topic = self.topic_repo.get_by_owner(
            topic_id, user_id
        )
        if topic is None:
            raise TaskReferenceError("Topic not found")

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
                status_code=status.HTTP_404_NOT_FOUND,
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
        self, user_id: str, task_data: TaskCreate
    ) -> TaskResponse:
        """Create a new task and enqueue it for processing.

        Args:
            user_id: ID of the user creating the task
            task_data: Task creation data

        Returns:
            TaskResponse: Created task data

        Raises:
            HTTPException: If validation fails
        """
        try:
            # Convert to domain model
            task = task_data.to_domain(user_id)

            # Validate topic if provided
            if task.topic_id is not None:
                self._validate_topic(task.topic_id, user_id)

            # Save to database
            task = self.task_repo.create(task)

            # Enqueue for processing
            self.queue_service.enqueue_task(
                "process_task",
                {"task_id": task.id},
            )

            # Return response
            return TaskResponse.from_domain(task)

        except Exception as e:
            logger.error(
                f"Error creating task: {str(e)}",
                exc_info=True,
            )
            self._handle_task_error(e)

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
        task = self.task_repo.get_by_user(user_id, task_id)
        if not task:
            raise HTTPException(
                status_code=404, detail="Task not found"
            )

        # Ensure task has an ID
        if task.id is None:
            raise ValueError("Task missing ID")

        return TaskResponse.from_domain(task)

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
        if topic_id is not None:
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
                TaskResponse.from_domain(task)
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
        task_update: TaskUpdate,
        user_id: str,
    ) -> TaskResponse:
        """Update an existing task.

        Args:
            task_id: ID of task to update
            task_update: Update data
            user_id: ID of user making update

        Returns:
            TaskResponse: Updated task data

        Raises:
            HTTPException: If task not found or validation fails
        """
        try:
            # Get existing task
            task = self.task_repo.get_by_user(
                user_id, task_id
            )
            if task is None:
                raise TaskReferenceError("Task not found")

            # Validate topic if being updated
            if task_update.topic_id is not None:
                self._validate_topic(
                    task_update.topic_id, user_id
                )

            # Update task with only non-None fields
            update_dict = {}
            for field, value in task_update.model_dump(
                exclude_unset=True
            ).items():
                if value is not None:
                    update_dict[field] = value

            # If content changed, reset processing
            if "content" in update_dict:
                update_dict[
                    "processing_status"
                ] = ProcessingStatus.PENDING
                update_dict["enrichment_data"] = None
                update_dict["processed_at"] = None

                # Re-enqueue for processing
                self.queue_service.enqueue_task(
                    "process_task",
                    {"task_id": task_id},
                )

            task = self.task_repo.update(
                task_id, update_dict
            )

            self.db.commit()
            return TaskResponse.from_domain(task)

        except Exception as e:
            logger.error(
                f"Error updating task {task_id}: {str(e)}",
                exc_info=True,
            )
            self._handle_task_error(e)

    def update_task_topic(
        self,
        task_id: int,
        user_id: str,
        topic_id: Optional[int] = None,
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
            if topic_id is not None:
                self._validate_topic(topic_id, user_id)

            # Update task's topic
            updated_task = self.task_repo.update_topic(
                task_id=task_id,
                user_id=user_id,
                topic_id=topic_id,
            )
            if not updated_task:
                raise HTTPException(
                    status_code=404,
                    detail="Task not found",
                )

            self.db.commit()
            self.db.refresh(updated_task)
            return TaskResponse.from_domain(updated_task)

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
        try:
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
                    TaskResponse.from_domain(task)
                    for task in tasks
                ],
                "total": total,
                "page": page,
                "size": size,
                "pages": (total + size - 1) // size,
            }
        except TaskReferenceError as e:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"message": str(e)},
            )
        except Exception as e:
            logger.error(
                f"Unexpected error getting tasks by topic: {str(e)}"
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    "message": "Failed to get tasks by topic"
                },
            )

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
        task = self.task_repo.get_by_user(user_id, task_id)
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

            return TaskResponse.from_domain(task)

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
            user_id, task_id
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
                TaskResponse.from_domain(task)
                for task in subtasks
            ],
            "total": len(
                subtasks
            ),  # Simple count since filtered
            "page": page,
            "size": size,
            "pages": (len(subtasks) + size - 1) // size,
        }
