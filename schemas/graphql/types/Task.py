"""Task GraphQL types."""

from datetime import datetime
from typing import List, Optional, Any
import strawberry

from domain.task import TaskData
from domain.values import TaskStatus, TaskPriority


@strawberry.type
class Task:
    """GraphQL type for Task."""

    @strawberry.field(
        description="Unique identifier for the task"
    )
    def id(self) -> int:
        """Task ID."""
        return self._domain.id

    @strawberry.field(description="Title of the task")
    def title(self) -> str:
        """Task title."""
        return self._domain.title

    @strawberry.field(
        description="Detailed description of the task"
    )
    def description(self) -> str:
        """Task description."""
        return self._domain.description

    @strawberry.field(
        description="Current status of the task"
    )
    def status(self) -> TaskStatus:
        """Task status."""
        return self._domain.status

    @strawberry.field(
        description="Priority level of the task"
    )
    def priority(self) -> TaskPriority:
        """Task priority."""
        return self._domain.priority

    @strawberry.field(description="Due date for the task")
    def due_date(self) -> Optional[datetime]:
        """Task due date."""
        return self._domain.due_date

    @strawberry.field(
        description="ID of the user who owns the task"
    )
    def user_id(self) -> str:
        """ID of the user who owns the task."""
        return self._domain.user_id

    @strawberry.field(
        description="ID of the parent task if this is a subtask"
    )
    def parent_id(self) -> Optional[int]:
        """ID of the parent task."""
        return self._domain.parent_id

    @strawberry.field(
        description="When the task was created"
    )
    def created_at(self) -> datetime:
        """Task creation timestamp."""
        return self._domain.created_at

    @strawberry.field(
        description="When the task was last updated"
    )
    def updated_at(self) -> Optional[datetime]:
        """Task update timestamp."""
        return self._domain.updated_at

    def __init__(self, domain: TaskData):
        """Initialize with domain model."""
        self._domain = domain

    @classmethod
    def from_domain(cls, domain: TaskData) -> "Task":
        """Create from domain model."""
        return cls(domain)

    @classmethod
    def from_db(cls, db_model: Any) -> "Task":
        """Create from database model."""
        return cls(TaskData.from_orm(db_model))


@strawberry.type
class TaskConnection:
    """Type for paginated task lists."""

    @strawberry.field(description="List of tasks")
    def items(self) -> List[Task]:
        """Get list of tasks."""
        return self._items

    @strawberry.field(description="Total number of items")
    def total(self) -> int:
        """Get total number of items."""
        return self._total

    @strawberry.field(description="Current page number")
    def page(self) -> int:
        """Get current page number."""
        return self._page

    @strawberry.field(
        description="Number of items per page"
    )
    def size(self) -> int:
        """Get number of items per page."""
        return self._size

    @strawberry.field(description="Total number of pages")
    def pages(self) -> int:
        """Get total number of pages."""
        return (self._total + self._size - 1) // self._size

    def __init__(
        self,
        items: List[Task],
        total: int,
        page: int = 1,
        size: int = 50,
    ):
        """Initialize TaskConnection.

        Args:
            items: List of tasks for current page
            total: Total number of tasks
            page: Current page number (1-based)
            size: Number of items per page
        """
        self._items = items
        self._total = total
        self._page = page
        self._size = size

    @classmethod
    def from_domain(
        cls, items: List[TaskData], page: int, size: int
    ) -> "TaskConnection":
        """Create from domain models."""
        return cls(
            items=[
                Task.from_domain(item) for item in items
            ],
            total=len(items),
            page=page,
            size=size,
        )


@strawberry.input
class TaskInput:
    """GraphQL input type for creating a Task."""

    title: str = strawberry.field(
        description="Title of the task"
    )
    description: str = strawberry.field(
        description="Detailed description"
    )
    status: TaskStatus = strawberry.field(
        description="Initial task status"
    )
    priority: TaskPriority = strawberry.field(
        description="Task priority level"
    )
    due_date: Optional[datetime] = strawberry.field(
        default=None,
        description="When the task is due",
    )
    parent_id: Optional[int] = strawberry.field(
        default=None,
        description="ID of parent task if this is a subtask",
    )

    def to_domain(self, user_id: str) -> TaskData:
        """Convert to domain model.

        Args:
            user_id: ID of the user creating the task
        """
        return TaskData(
            title=self.title,
            description=self.description,
            status=self.status,
            priority=self.priority,
            due_date=self.due_date,
            parent_id=self.parent_id,
            user_id=user_id,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )


@strawberry.input
class TaskUpdateInput:
    """GraphQL input type for updating a Task."""

    title: Optional[str] = strawberry.field(
        default=None,
        description="New title for the task",
    )
    description: Optional[str] = strawberry.field(
        default=None,
        description="New description for the task",
    )
    status: Optional[TaskStatus] = strawberry.field(
        default=None,
        description="New task status",
    )
    priority: Optional[TaskPriority] = strawberry.field(
        default=None,
        description="New task priority",
    )
    due_date: Optional[datetime] = strawberry.field(
        default=None,
        description="New due date for the task",
    )

    def to_domain(self, existing: TaskData) -> TaskData:
        """Convert to domain model, using existing data for missing fields."""
        return TaskData(
            id=existing.id,
            title=self.title or existing.title,
            description=self.description
            or existing.description,
            status=self.status or existing.status,
            priority=self.priority or existing.priority,
            due_date=self.due_date or existing.due_date,
            parent_id=existing.parent_id,
            user_id=existing.user_id,
            created_at=existing.created_at,
            updated_at=datetime.now(),
        )
