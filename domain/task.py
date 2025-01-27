"""Domain model for Task."""

from dataclasses import dataclass, field
from datetime import datetime, timezone as tz
from typing import Optional, List, Dict, Any, TypeVar, Type

from domain.exceptions import (
    TaskValidationError,
    TaskContentError,
    TaskDateError,
    TaskPriorityError,
    TaskStatusError,
    TaskParentError,
)
from domain.values import (
    TaskStatus,
    TaskPriority,
    ProcessingStatus,
)


T = TypeVar("T", bound="TaskData")


@dataclass
class TaskData:
    """Domain model for Task.

    This class represents a user task in the system and contains
    all business logic and validation rules for tasks.
    A task can optionally reference a note for additional context
    and can be organized under a topic.

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
        content: Task content in markdown format (max 512 chars)
        user_id: ID of the user who owns this task
        status: Current status of the task (todo/in_progress/done)
        priority: Priority level of the task
        due_date: When this task is due
        tags: List of tags associated with this task
        parent_id: ID of the parent task if this is a subtask
        note_id: Optional ID of an associated note
        topic_id: Optional ID of the associated topic
        processing_status: Status of content processing
        enrichment_data: Data from content processing
        processed_at: When the content was processed
        id: Unique identifier for this task (optional)
        created_at: When this task was created
        updated_at: When this task was last updated
    """

    content: str
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
    note_id: Optional[int] = None
    topic_id: Optional[int] = None
    processing_status: ProcessingStatus = field(
        default_factory=lambda: ProcessingStatus.PENDING
    )
    enrichment_data: Optional[Dict[str, Any]] = None
    processed_at: Optional[datetime] = None
    id: Optional[int] = None
    created_at: datetime = field(
        default_factory=lambda: datetime.now(tz.utc)
    )
    updated_at: datetime = field(
        default_factory=lambda: datetime.now(tz.utc)
    )

    def __post_init__(self) -> None:
        """Validate task data after initialization."""
        self.validate()

    def validate(
        self, require_user_id: bool = True
    ) -> None:
        """Validate task data.

        Args:
            require_user_id: Whether to require user_id to be set

        Raises:
            TaskValidationError: If validation fails
            TaskContentError: If content validation fails
            TaskDateError: If date validation fails
            TaskPriorityError: If priority validation fails
            TaskStatusError: If status validation fails
            TaskParentError: If parent task validation fails
        """
        # Basic field validations
        if not isinstance(self.content, str):
            raise TaskContentError(
                "content must be a string"
            )

        if not self.content.strip():
            raise TaskContentError(
                "content cannot be empty"
            )

        if len(self.content) > 512:
            raise TaskContentError(
                "content cannot exceed 512 characters"
            )

        if require_user_id and (
            not isinstance(self.user_id, str)
            or not self.user_id
        ):
            raise TaskValidationError(
                "user_id must be a non-empty string"
            )

        if not isinstance(self.status, TaskStatus):
            raise TaskStatusError("Invalid task status")

        if not isinstance(self.priority, TaskPriority):
            raise TaskPriorityError("Invalid task priority")

        if not isinstance(
            self.processing_status, ProcessingStatus
        ):
            raise TaskValidationError(
                "Invalid processing status"
            )

        # Optional field validations
        if self.tags is not None:
            if not isinstance(self.tags, list):
                raise TaskValidationError(
                    "tags must be a list"
                )
            for tag in self.tags:
                if not isinstance(tag, str):
                    raise TaskValidationError(
                        "tags must be strings"
                    )

        if self.parent_id is not None:
            if (
                not isinstance(self.parent_id, int)
                or self.parent_id <= 0
            ):
                raise TaskParentError(
                    "parent_id must be a positive integer"
                )
            if self.parent_id == self.id:
                raise TaskParentError(
                    "task cannot be its own parent"
                )

        if self.note_id is not None:
            if (
                not isinstance(self.note_id, int)
                or self.note_id <= 0
            ):
                raise TaskValidationError(
                    "note_id must be a positive integer"
                )

        if self.topic_id is not None:
            if (
                not isinstance(self.topic_id, int)
                or self.topic_id <= 0
            ):
                raise TaskValidationError(
                    "topic_id must be a positive integer"
                )

        if self.id is not None and (
            not isinstance(self.id, int) or self.id <= 0
        ):
            raise TaskValidationError(
                "id must be a positive integer"
            )

        # Datetime validations
        if not isinstance(self.created_at, datetime):
            raise TaskValidationError(
                "created_at must be a datetime object"
            )

        if not isinstance(self.updated_at, datetime):
            raise TaskValidationError(
                "updated_at must be a datetime object"
            )

        # Due date validations (after all other fields are validated)
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

        # Processing validations
        if (
            self.enrichment_data is not None
            and self.processed_at is None
        ):
            raise TaskValidationError(
                "processed_at required with enrichment_data"
            )

        if (
            self.processed_at is not None
            and self.enrichment_data is None
        ):
            raise TaskValidationError(
                "enrichment_data required with processed_at"
            )

        if self.processed_at is not None:
            if not isinstance(self.processed_at, datetime):
                raise TaskValidationError(
                    "processed_at must be a datetime object"
                )
            if self.processed_at.tzinfo is None:
                raise TaskValidationError(
                    "processed_at must be timezone-aware"
                )

        if self.enrichment_data is not None:
            if not isinstance(self.enrichment_data, dict):
                raise TaskValidationError(
                    "enrichment_data must be a dictionary"
                )
            required_keys = {
                "title",
                "formatted",
                "tokens_used",
                "model_name",
                "created_at",
                "metadata",
            }
            if not all(
                key in self.enrichment_data
                for key in required_keys
            ):
                raise TaskValidationError(
                    "Invalid enrichment data structure"
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
            "content": self.content,
            "user_id": self.user_id,
            "status": self.status.value,
            "priority": self.priority.value,
            "due_date": self.due_date,
            "tags": self.tags,
            "parent_id": self.parent_id,
            "note_id": self.note_id,
            "topic_id": self.topic_id,
            "processing_status": self.processing_status.value,
            "enrichment_data": self.enrichment_data,
            "processed_at": self.processed_at,
            "id": self.id,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

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

        processing_status = data.get("processing_status")
        if isinstance(processing_status, str):
            processing_status = ProcessingStatus(
                processing_status
            )
        elif processing_status is None:
            processing_status = ProcessingStatus.default()

        # Handle both snake_case and camelCase keys
        user_id = data.get("user_id") or data.get("userId")
        note_id = data.get("note_id") or data.get("noteId")
        parent_id = data.get("parent_id") or data.get(
            "parentId"
        )
        topic_id = data.get("topic_id") or data.get(
            "topicId"
        )
        due_date = data.get("due_date") or data.get(
            "dueDate"
        )
        enrichment_data = data.get(
            "enrichment_data"
        ) or data.get("enrichmentData")
        processed_at = data.get("processed_at") or data.get(
            "processedAt"
        )
        created_at = (
            data.get("created_at")
            or data.get("createdAt")
            or datetime.now(tz.utc)
        )
        updated_at = (
            data.get("updated_at")
            or data.get("updatedAt")
            or datetime.now(tz.utc)
        )

        return cls(
            id=data.get("id"),
            content=data["content"],
            user_id=user_id,
            status=status,
            priority=priority,
            due_date=due_date,
            tags=data.get("tags"),
            parent_id=parent_id,
            note_id=note_id,
            topic_id=topic_id,
            processing_status=processing_status,
            enrichment_data=enrichment_data,
            processed_at=processed_at,
            created_at=created_at,
            updated_at=updated_at,
        )

    def update_status(self, new_status: TaskStatus) -> None:
        """Update task status if transition is valid."""
        if not self.status.can_transition_to(new_status):
            raise TaskStatusError(
                f"Invalid transition: {self.status} -> {new_status}"
            )
        self.status = new_status
        self.updated_at = datetime.now(tz.utc)

    def update_priority(
        self, new_priority: TaskPriority
    ) -> None:
        """Update task priority."""
        if not isinstance(new_priority, TaskPriority):
            raise TaskPriorityError(
                f"priority must be one of: {[p.value for p in TaskPriority]}"
            )
        self.priority = new_priority
        self.updated_at = datetime.now(tz.utc)

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
        self.updated_at = datetime.now(tz.utc)

    def update_processing_status(
        self,
        new_status: ProcessingStatus,
        enrichment_data: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Update processing status if transition is valid.

        Args:
            new_status: New processing status
            enrichment_data: Optional enrichment data to
            set when status is completed

        Raises:
            TaskValidationError: If transition is invalid or
            enrichment data is invalid
        """
        # Validate enrichment data structure first if provided
        if enrichment_data is not None:
            required_keys = {
                "title",
                "formatted",
                "tokens_used",
                "model_name",
                "created_at",
                "metadata",
            }
            if not all(
                key in enrichment_data
                for key in required_keys
            ):
                raise TaskValidationError(
                    "Invalid enrichment data structure"
                )

        if not self.processing_status.can_transition_to(
            new_status
        ):
            raise TaskValidationError(
                f"Invalid transition: {self.processing_status} -> {new_status}"
            )

        # Set enrichment data if status is completed
        if new_status == ProcessingStatus.COMPLETED:
            if enrichment_data is None:
                raise TaskValidationError(
                    "Enrichment data is required when status is completed"
                )
            self.enrichment_data = enrichment_data
            self.processed_at = datetime.now(tz.utc)

        self.processing_status = new_status
        self.updated_at = datetime.now(tz.utc)
        self.validate()

    def validate_topic_ownership(
        self, topic_user_id: str
    ) -> None:
        """Validate that the topic belongs to the same user as the task.

        Args:
            topic_user_id: User ID of the topic owner

        Raises:
            TaskValidationError: If topic belongs to a different user
        """
        if (
            self.topic_id is not None
            and topic_user_id != self.user_id
        ):
            raise TaskValidationError(
                "Topic must belong to the same user as the task"
            )

    def handle_topic_deletion(self) -> None:
        """Handle topic deletion by removing the topic reference.

        This method is called when the associated topic is deleted
        to ensure the task remains valid.
        """
        self.topic_id = None
        self.updated_at = datetime.now(tz.utc)
