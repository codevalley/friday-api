"""Pydantic schemas for task-related operations."""

from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict

from domain.task import TaskData
from domain.values import (
    TaskStatus,
    TaskPriority,
    ProcessingStatus,
)
from .TopicSchema import TopicResponse
from .PaginationSchema import PaginationResponse


class TaskBase(BaseModel):
    """Base schema for task data.

    Attributes:
        content: Task content in markdown format (max 512 chars)
        status: Task status (default: TODO)
        priority: Task priority (default: MEDIUM)
        due_date: Optional due date
        tags: Optional list of tags
        parent_id: Optional parent task ID
        note_id: Optional ID of an associated note
        topic_id: Optional ID of an associated topic
    """

    content: str = Field(
        ...,
        min_length=1,
        max_length=512,
        description="Task content in markdown format (max 512 chars)",
    )
    status: TaskStatus = Field(
        default_factory=TaskStatus.default,
        description="Current status of the task",
    )
    priority: TaskPriority = Field(
        default_factory=TaskPriority.default,
        description="Priority level of the task",
    )
    due_date: Optional[datetime] = Field(
        None,
        description="When this task is due",
    )
    tags: Optional[List[str]] = Field(
        default_factory=list,
        description="List of tags for categorization",
    )
    parent_id: Optional[int] = Field(
        None,
        description="ID of parent task if this is a subtask",
    )
    note_id: Optional[int] = Field(
        None,
        gt=0,
        description="Optional ID of an associated note",
    )
    topic_id: Optional[int] = Field(
        None,
        gt=0,
        description="Optional ID of an associated topic",
    )

    model_config = ConfigDict(from_attributes=True)


class TaskCreate(TaskBase):
    """Schema for task creation."""

    def to_domain(self, user_id: str) -> "TaskData":
        """Convert to domain model data.

        Args:
            user_id: ID of the user creating the task

        Returns:
            TaskData instance with validated data
        """
        return TaskData(
            **self.model_dump(),
            user_id=user_id,
            processing_status=ProcessingStatus.PENDING,
        )


class TaskUpdate(BaseModel):
    """Schema for task updates."""

    content: Optional[str] = Field(
        None,
        min_length=1,
        max_length=512,
        description="Task content in markdown format (max 512 chars)",
    )
    status: Optional[TaskStatus] = Field(
        None,
        description="New task status",
    )
    priority: Optional[TaskPriority] = Field(
        None,
        description="New priority level",
    )
    due_date: Optional[datetime] = None
    tags: Optional[List[str]] = None
    parent_id: Optional[int] = None
    topic_id: Optional[int] = Field(
        None,
        gt=0,
        description="Optional ID of an associated topic",
    )
    processing_status: Optional[ProcessingStatus] = Field(
        None,
        description="New processing status",
    )

    model_config = ConfigDict(from_attributes=True)


class TaskEnrichmentResult(BaseModel):
    """Schema for task enrichment results."""

    title: str = Field(
        ...,
        max_length=50,
        description="Extracted title",
    )
    formatted: str = Field(
        ...,
        description="Markdown formatted content",
    )
    tokens_used: int = Field(
        ...,
        gt=0,
        description="Number of tokens used",
    )
    model_name: str = Field(
        ...,
        description="Name of model used",
    )
    created_at: datetime = Field(
        ...,
        description="When enrichment was performed",
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional task-specific metadata",
    )

    model_config = ConfigDict(from_attributes=True)


class TaskResponse(TaskBase):
    """Schema for task responses."""

    id: int
    user_id: str
    processing_status: ProcessingStatus = Field(
        default_factory=ProcessingStatus.default,
        description="Processing status of the task",
    )
    enrichment_data: Optional[TaskEnrichmentResult] = Field(
        None,
        description="Enrichment processing results",
    )
    processed_at: Optional[datetime] = Field(
        None,
        description="When content was processed",
    )
    created_at: datetime
    updated_at: Optional[datetime] = None
    topic: Optional[TopicResponse] = None

    model_config = ConfigDict(from_attributes=True)

    @classmethod
    def from_domain(
        cls, domain: TaskData
    ) -> "TaskResponse":
        """Create response from domain model.

        Args:
            domain: TaskData instance

        Returns:
            TaskResponse instance with all fields populated
        """
        data = domain.to_dict()
        return cls(**data)


class TaskProcessingResponse(BaseModel):
    """Schema for task processing status responses.

    This schema is used for endpoints that return the processing status
    and enrichment data for a task.
    """

    id: int
    user_id: str
    content: str
    processing_status: ProcessingStatus = Field(
        ...,
        description="Current processing status of the task",
    )
    enrichment_data: Optional[TaskEnrichmentResult] = Field(
        None,
        description="Enrichment processing results if available",
    )
    processed_at: Optional[datetime] = Field(
        None,
        description="When content was last processed",
    )

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": 1,
                "user_id": "123e4567-e89b-12d3-a456-426614174000",
                "content": "Complete Q1 planning document",
                "processing_status": "COMPLETED",
                "enrichment_data": {
                    "title": "Q1 Planning",
                    "formatted": "Complete Q1 planning document",
                    "tokens_used": 10,
                    "model_name": "gpt-3.5-turbo",
                    "created_at": "2024-01-27T10:00:00Z",
                    "metadata": {},
                },
                "processed_at": "2024-01-27T10:00:05Z",
            }
        },
    )

    @classmethod
    def from_domain(
        cls, domain: "TaskData"
    ) -> "TaskProcessingResponse":
        """Create response from domain model.

        Args:
            domain: TaskData instance

        Returns:
            TaskProcessingResponse instance with processing fields
        """
        return cls(
            id=domain.id,
            user_id=domain.user_id,
            content=domain.content,
            processing_status=domain.processing_status,
            enrichment_data=domain.enrichment_data,
            processed_at=domain.processed_at,
        )


class TaskList(PaginationResponse):
    """Response schema for list of Tasks.

    This schema is used for paginated responses when listing tasks.
    It includes pagination metadata along with the list of tasks.

    Attributes:
        items: List of tasks
        total: Total number of items
        page: Current page number
        size: Items per page
        pages: Total number of pages
    """

    items: List[TaskResponse] = Field(
        description="List of tasks on this page"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "items": [
                    {
                        "id": 1,
                        "user_id": "123e4567-e89b-12d3-a456-426614174000",
                        "content": "Complete Q1 planning document",
                        "status": "TODO",
                        "priority": "HIGH",
                        "due_date": "2024-02-01T17:00:00Z",
                        "tags": ["planning", "q1"],
                        "processing_status": "NOT_PROCESSED",
                        "enrichment_data": None,
                        "processed_at": None,
                        "created_at": "2024-01-27T10:00:00Z",
                        "updated_at": "2024-01-27T10:00:00Z",
                    }
                ],
                "total": 1,
                "page": 1,
                "size": 10,
                "pages": 1,
            }
        }
    )
