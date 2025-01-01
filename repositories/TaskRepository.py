"""Repository for managing tasks in the database."""

from typing import List, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import desc, asc

from domain.values import TaskStatus, TaskPriority
from orm.TaskModel import Task
from .BaseRepository import BaseRepository


class TaskRepository(BaseRepository[Task, int]):
    """Repository for managing Task entities.

    This repository extends the BaseRepository to provide CRUD operations
    for Task entities, along with task-specific functionality like filtering
    by status, priority, and due date.
    """

    def __init__(self, db: Session):
        """Initialize repository with database session.

        Args:
            db: SQLAlchemy database session
        """
        super().__init__(db, Task)

    def create(
        self,
        title: str,
        description: str,
        user_id: str,
        status: TaskStatus = TaskStatus.TODO,
        priority: TaskPriority = TaskPriority.MEDIUM,
        due_date: Optional[datetime] = None,
        tags: Optional[List[str]] = None,
        parent_id: Optional[int] = None,
    ) -> Task:
        """Create a new task.

        Args:
            title: Task title
            description: Task description
            user_id: ID of the user creating the task
            status: Task status (default: TODO)
            priority: Task priority (default: MEDIUM)
            due_date: Optional due date
            tags: Optional list of tags
            parent_id: Optional parent task ID

        Returns:
            Task: Created task

        Raises:
            HTTPException: If parent task is invalid / belongs to another user
        """
        # If parent_id is provided, validate it exists and belongs to user
        if parent_id is not None:
            parent_task = self.get_by_user(
                parent_id, user_id
            )
            if parent_task is None:
                raise ValueError(
                    "Parent task not found or "
                    "doesn't belong to user"
                )

        # Create task with original timezone-aware due_date
        task = Task(
            title=title,
            description=description,
            user_id=user_id,
            status=status,
            priority=priority,
            due_date=due_date,
            tags=tags or [],
            parent_id=parent_id,
        )
        return super().create(task)

    def list_tasks(
        self,
        user_id: str,
        status: Optional[TaskStatus] = None,
        priority: Optional[TaskPriority] = None,
        due_before: Optional[datetime] = None,
        due_after: Optional[datetime] = None,
        parent_id: Optional[int] = None,
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
                Task._due_date <= due_before
            )
        if due_after is not None:
            query = query.filter(
                Task._due_date >= due_after
            )
        if parent_id is not None:
            query = query.filter(
                Task.parent_id == parent_id
            )

        # Order by priority (high to low) then due date
        query = query.order_by(
            desc(Task.priority),
            asc(Task._due_date),
        )

        return query.offset(skip).limit(limit).all()

    def count_tasks(
        self,
        user_id: str,
        status: Optional[TaskStatus] = None,
    ) -> int:
        """Count total tasks for a user, optionally filtered by status.

        Args:
            user_id: ID of the user whose tasks to count
            status: Optional status filter

        Returns:
            int: Total number of tasks
        """
        query = self.db.query(Task).filter(
            Task.user_id == user_id
        )
        if status is not None:
            query = query.filter(Task.status == status)
        return query.count()

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
                asc(Task._due_date),
            )
            .offset(skip)
            .limit(limit)
            .all()
        )

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
        task = self.get_by_user(task_id, user_id)
        if task is None:
            return None

        task.status = new_status
        self.db.add(task)
        self.db.flush()
        return task
