"""Repository for managing tasks in the database."""

from typing import List, Optional, Union, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import desc, asc
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException

from domain.values import TaskStatus, TaskPriority
from orm.TaskModel import Task
from repositories.BaseRepository import BaseRepository
from domain.exceptions import (
    TaskReferenceError,
    TaskValidationError,
)
from domain.task import TaskData


class TaskRepository(BaseRepository[Task, int]):
    """Repository for managing Task entities.

    This repository extends the BaseRepository to provide CRUD operations
    for Task entities, along with task-specific functionality like filtering
    by status, priority, due date, and topics.
    """

    def __init__(self, db: Session):
        """Initialize repository with database session.

        Args:
            db: SQLAlchemy database session
        """
        super().__init__(db, Task)

    def create(
        self,
        task_or_kwargs: Union[TaskData, Dict[str, Any]],
    ) -> TaskData:
        """Create a new task.

        Args:
            task_or_kwargs: Either a TaskData instance
            or a dict of task attributes

        Returns:
            TaskData instance with database ID populated

        Raises:
            TaskValidationError: If validation fails
        """
        try:
            # Convert TaskData to dict if needed
            if isinstance(task_or_kwargs, TaskData):
                task_dict = task_or_kwargs.__dict__
            else:
                task_dict = task_or_kwargs

            # Create ORM instance
            task = Task(**task_dict)
            return super().create(task)
        except HTTPException as e:
            if e.status_code == 409:
                raise TaskValidationError(
                    f"Invalid topic: {e.detail}"
                )
            raise

    def list_tasks(
        self,
        user_id: str,
        status: Optional[TaskStatus] = None,
        priority: Optional[TaskPriority] = None,
        due_before: Optional[datetime] = None,
        due_after: Optional[datetime] = None,
        parent_id: Optional[int] = None,
        topic_id: Optional[int] = None,
        skip: int = 0,
        limit: int = 50,
    ) -> List[Task]:
        """List tasks for a user with filtering and pagination.

        Args:
            user_id: ID of the user whose tasks to list
            status: Optional status filter
            priority: Optional priority filter
            due_before: Optional due date upper bound
            due_after: Optional due date lower bound
            parent_id: Optional parent task ID filter
            topic_id: Optional topic ID filter
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List[Task]: List of tasks matching the criteria
        """
        query = self.db.query(Task).filter(
            Task.user_id == user_id
        )

        # Apply filters if provided
        if status is not None:
            query = query.filter(Task.status == status)
        if priority is not None:
            query = query.filter(Task.priority == priority)
        if due_before is not None:
            query = query.filter(
                Task.due_date <= due_before
            )
        if due_after is not None:
            query = query.filter(Task.due_date >= due_after)
        if parent_id is not None:
            query = query.filter(
                Task.parent_id == parent_id
            )
        if topic_id is not None:
            query = query.filter(Task.topic_id == topic_id)

        # Order by priority (high to low) then due date
        query = query.order_by(
            desc(Task.priority),
            asc(Task.due_date),
        )

        return query.offset(skip).limit(limit).all()

    def count_tasks(
        self,
        user_id: str,
        status: Optional[TaskStatus] = None,
        topic_id: Optional[int] = None,
    ) -> int:
        """Count total tasks for a user, optionally filtered by status
        and topic.

        Args:
            user_id: ID of the user whose tasks to count
            status: Optional status filter
            topic_id: Optional topic filter

        Returns:
            int: Total number of tasks
        """
        query = self.db.query(Task).filter(
            Task.user_id == user_id
        )
        if status is not None:
            query = query.filter(Task.status == status)
        if topic_id is not None:
            query = query.filter(Task.topic_id == topic_id)
        return query.count()

    def get_tasks_by_topic(
        self,
        topic_id: int,
        user_id: str,
        skip: int = 0,
        limit: int = 50,
    ) -> List[Task]:
        """Get all tasks for a given topic.

        Args:
            topic_id: ID of the topic
            user_id: ID of the user who owns the tasks
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List[Task]: List of tasks for the topic
        """
        return (
            self.db.query(Task)
            .filter(
                Task.topic_id == topic_id,
                Task.user_id == user_id,
            )
            .order_by(
                desc(Task.priority),
                asc(Task.due_date),
            )
            .offset(skip)
            .limit(limit)
            .all()
        )

    def update_topic(
        self,
        task_id: int,
        user_id: str,
        topic_id: Optional[int] = None,
    ) -> Task:
        """Update a task's topic.

        Args:
            task_id: ID of the task to update
            user_id: ID of the user who owns the task
            topic_id: New topic ID to set, or None to remove topic

        Returns:
            Task: Updated task

        Raises:
            TaskReferenceError: If task not found or doesn't belong to user
            TaskValidationError: If topic_id is invalid
        """
        task = self.get_by_user(user_id, task_id)
        if task is None:
            raise TaskReferenceError(
                f"Task {task_id} not found or doesn't belong to user"
            )

        task.topic_id = topic_id
        try:
            self.db.add(task)
            self.db.commit()
            self.db.refresh(task)
            return task
        except IntegrityError as e:
            self.db.rollback()
            raise TaskValidationError(
                f"Invalid topic: {str(e)}"
            )

    def get_subtasks(
        self,
        task_id: int,
        user_id: str,
        skip: int = 0,
        limit: int = 50,
    ) -> List[Task]:
        """Get subtasks for a given task.

        Args:
            task_id: ID of the parent task
            user_id: ID of the user who owns the task
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List[Task]: List of subtasks
        """
        return (
            self.db.query(Task)
            .filter(
                Task.parent_id == task_id,
                Task.user_id == user_id,
            )
            .order_by(
                desc(Task.priority),
                asc(Task.due_date),
            )
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_by_user(
        self, user_id: str, task_id: int
    ) -> Optional[Task]:
        """Get a task by ID for a specific user.

        Args:
            user_id: User ID
            task_id: Task ID

        Returns:
            Task if found and belongs to user, None otherwise
        """
        return self.get_by_owner(task_id, user_id)

    def update_status(
        self,
        task_id: int,
        user_id: str,
        new_status: TaskStatus,
    ) -> Optional[Task]:
        """Update a task's status.

        This is a convenience method that ensures the status transition
        is valid according to the TaskStatus rules.

        Args:
            task_id: ID of the task to update
            user_id: ID of the user who owns the task
            new_status: New status to set

        Returns:
            Task: Updated task if found and owned by user, None otherwise

        Raises:
            ValueError: If the status transition is invalid
        """
        task = self.get_by_user(user_id, task_id)
        if task is None:
            return None

        task.status = new_status
        self.db.add(task)
        self.db.flush()
        return task
