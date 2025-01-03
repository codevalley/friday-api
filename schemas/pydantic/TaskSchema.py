"""Pydantic schemas for task-related operations."""

from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field

from domain.task import TaskData
from domain.values import TaskStatus, TaskPriority


class TaskBase(BaseModel):
    """Base schema for task data.

    Attributes:
        title: Task title
        description: Task description
        status: Task status (default: TODO)
        priority: Task priority (default: MEDIUM)
        due_date: Optional due date
        tags: Optional list of tags
        parent_id: Optional parent task ID
        note_id: Optional ID of an associated note
    """

    title: str = Field(..., min_length=1)
    description: str = Field(..., min_length=1)
    status: TaskStatus = Field(default=TaskStatus.TODO)
    priority: TaskPriority = Field(
        default=TaskPriority.MEDIUM
    )
    due_date: Optional[datetime] = None
    tags: Optional[List[str]] = Field(default_factory=list)
    parent_id: Optional[int] = None
    note_id: Optional[int] = Field(
        None,
        gt=0,
        description="Optional ID of an associated note",
    )


class TaskCreate(TaskBase):
    """Schema for task creation."""

    def to_domain(self, user_id: str) -> "TaskData":
        """Convert to domain model data."""
        from domain.task import TaskData

        return TaskData(
            **self.model_dump(),
            user_id=user_id,
        )


class TaskUpdate(BaseModel):
    """Schema for task updates."""

    title: Optional[str] = Field(None, min_length=1)
    description: Optional[str] = Field(None, min_length=1)
    status: Optional[TaskStatus] = None
    priority: Optional[TaskPriority] = None
    due_date: Optional[datetime] = None
    tags: Optional[List[str]] = None
    parent_id: Optional[int] = None


class TaskResponse(TaskBase):
    """Schema for task responses."""

    id: int
    user_id: str
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        """Pydantic config."""

        from_attributes = True
