"""Domain model for Task."""

from dataclasses import dataclass, field
from datetime import datetime, UTC
from typing import Optional, List, Dict, Any, TypeVar, Type

from domain.exceptions import (
    TaskValidationError,
    TaskContentError,
    TaskDateError,
    TaskPriorityError,
    TaskStatusError,
    TaskParentError,
)
from domain.values import TaskStatus, TaskPriority

T = TypeVar("T", bound="TaskData")


@dataclass
class TaskData:
    """Domain model for Task.

    This class represents a user task in the system and contains
    all business logic and validation rules for tasks.

    Data Flow and Conversions:
    1. API Layer: Incoming data is validated by Pydantic schemas
       (TaskCreate/TaskUpdate)
    2. Domain Layer: Data is converted to TaskData using to_domain()
       methods
    3. Database Layer: TaskData is converted to ORM models
       using from_dict()
    4. Response: ORM models are converted back to TaskData using from_orm()
    5. API Response: TaskData is converted to response schemas
       using from_domain()

    Attributes:
        title: Title of the task
        description: Detailed description of the task
        user_id: ID of the user who owns this task
        status: Current status of the task (todo/in_progress/done)
        priority: Priority level of the task
        due_date: When this task is due
        tags: List of tags/topics associated with this task
        parent_id: ID of the parent task if this is a subtask
        id: Unique identifier for this task (optional)
        created_at: When this task was created
        updated_at: When this task was last updated
    """

    title: str
    description: str
    user_id: Optional[str] = None
    status: TaskStatus = field(
        default_factory=TaskStatus.default
    )
    priority: TaskPriority = field(
        default_factory=TaskPriority.default
    )
    due_date: Optional[datetime] = None
    tags: Optional[List[str]] = None
    parent_id: Optional[int] = None
    id: Optional[int] = None
    created_at: datetime = field(
        default_factory=lambda: datetime.now(UTC)
    )
    updated_at: datetime = field(
        default_factory=lambda: datetime.now(UTC)
    )

    def __post_init__(self) -> None:
        """Validate task data after initialization.

        For backward compatibility, we validate with require_user_id=True
        by default. The GraphQL layer will create tasks with
        require_user_id=False and then set the user_id before saving.
        """
        self.validate()

    def validate(
        self, require_user_id: bool = True
    ) -> None:
        """Validate the task data.

        Args:
            require_user_id: Whether to require user_id to be set.
                           Defaults to True for backward
                           compatibility.

        Raises:
            TaskValidationError: If validation fails
        """
        if not isinstance(self.title, str):
            raise TaskContentError("title must be a string")

        if not self.title.strip():
            raise TaskContentError("title cannot be empty")

        if len(self.title) > 255:
            raise TaskContentError(
                "title cannot exceed 255 characters"
            )

        if not isinstance(self.description, str):
            raise TaskContentError(
                "description must be a string"
            )

        if require_user_id and (
            not isinstance(self.user_id, str)
            or not self.user_id
        ):
            raise TaskValidationError(
                "user_id must be a non-empty string"
            )

        if not isinstance(self.status, TaskStatus):
            raise TaskStatusError(
                f"status must be one of: {[s.value for s in TaskStatus]}"
            )

        if not isinstance(self.priority, TaskPriority):
            raise TaskPriorityError(
                f"priority must be one of: {[p.value for p in TaskPriority]}"
            )

        if self.due_date is not None:
            if not isinstance(self.due_date, datetime):
                raise TaskDateError(
                    "due_date must be a datetime object"
                )
            if self.due_date.tzinfo is None:
                raise TaskDateError(
                    "due_date must be timezone-aware"
                )
            if self.due_date < self.created_at:
                raise TaskDateError(
                    "due_date cannot be earlier than created_at"
                )

        if self.tags is not None:
            if not isinstance(self.tags, list):
                raise TaskValidationError(
                    "tags must be a list"
                )
            for tag in self.tags:
                if not isinstance(tag, str):
                    raise TaskValidationError(
                        "each tag must be a string"
                    )
                if not tag.strip():
                    raise TaskValidationError(
                        "tags cannot be empty strings"
                    )

        if self.parent_id is not None:
            if not isinstance(self.parent_id, int):
                raise TaskParentError(
                    "parent_id must be an integer"
                )
            if self.parent_id <= 0:
                raise TaskParentError(
                    "parent_id must be a positive integer"
                )
            if self.parent_id == self.id:
                raise TaskParentError(
                    "task cannot be its own parent"
                )

        if self.id is not None and (
            not isinstance(self.id, int) or self.id <= 0
        ):
            raise TaskValidationError(
                "id must be a positive integer"
            )

    def validate_for_save(self) -> None:
        """Validate task data before saving."""
        self.validate(require_user_id=True)

    def to_dict(self) -> dict:
        """Convert to dictionary for repository operations.

        Returns:
            dict: Dictionary representation of the task
        """
        return {
            "title": self.title,
            "description": self.description,
            "user_id": self.user_id,
            "status": self.status.value,
            "priority": self.priority.value,
            "due_date": self.due_date,
            "tags": self.tags,
            "parent_id": self.parent_id,
            "id": self.id,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    def update_status(self, new_status: TaskStatus) -> None:
        """Update task status if transition is valid."""
        if not self.status.can_transition_to(new_status):
            raise TaskStatusError(
                f"Invalid transition: {self.status} -> {new_status}"
            )
        self.status = new_status
        self.updated_at = datetime.now(UTC)

    def update_priority(
        self, new_priority: TaskPriority
    ) -> None:
        """Update task priority."""
        if not isinstance(new_priority, TaskPriority):
            raise TaskPriorityError(
                f"priority must be one of: {[p.value for p in TaskPriority]}"
            )
        self.priority = new_priority
        self.updated_at = datetime.now(UTC)

    def update_due_date(
        self, new_due_date: Optional[datetime]
    ) -> None:
        """Update task due date."""
        if new_due_date is not None:
            if not isinstance(new_due_date, datetime):
                raise TaskDateError(
                    "due_date must be a datetime object"
                )
            if new_due_date.tzinfo is None:
                raise TaskDateError(
                    "due_date must be timezone-aware"
                )
            if new_due_date < self.created_at:
                raise TaskDateError(
                    "due_date cannot be earlier than created_at"
                )
        self.due_date = new_due_date
        self.updated_at = datetime.now(UTC)

    @classmethod
    def from_dict(cls: Type[T], data: Dict[str, Any]) -> T:
        """Create TaskData from dictionary data.

        Args:
            data: Dictionary containing task data

        Returns:
            TaskData instance
        """
        # Convert string status/priority to enum if needed
        status = data.get("status")
        if isinstance(status, str):
            status = TaskStatus(status)
        elif status is None:
            status = TaskStatus.default()

        priority = data.get("priority")
        if isinstance(priority, str):
            priority = TaskPriority(priority)
        elif priority is None:
            priority = TaskPriority.default()

        return cls(
            id=data.get("id"),
            title=data["title"],
            description=data["description"],
            user_id=data["user_id"],
            status=status,
            priority=priority,
            due_date=data.get("due_date"),
            tags=data.get("tags"),
            parent_id=data.get("parent_id"),
            created_at=data.get(
                "created_at", datetime.now(UTC)
            ),
            updated_at=data.get(
                "updated_at", datetime.now(UTC)
            ),
        )
