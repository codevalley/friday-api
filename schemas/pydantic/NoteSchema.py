from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from typing import Optional, List, Dict, Any
from domain.note import NoteData
from domain.values import AttachmentType, ProcessingStatus


class NoteBase(BaseModel):
    """Base schema for note data validation."""

    content: str = Field(
        ...,
        min_length=1,
        max_length=2000,
        description="Content of the note",
    )
    attachment_url: Optional[str] = Field(
        None,
        max_length=500,
        description="URL of the attachment if any",
    )
    attachment_type: Optional[AttachmentType] = Field(
        None, description="Type of the attachment"
    )
    processing_status: ProcessingStatus = Field(
        default_factory=ProcessingStatus.default,
        description="Processing status of the note",
    )


class NoteCreate(BaseModel):
    """Schema for creating a new note."""

    content: str = Field(
        ..., min_length=1, max_length=10000
    )
    activity_id: Optional[int] = None
    moment_id: Optional[int] = None
    attachments: Optional[List[Dict[str, Any]]] = None

    def to_domain(self, user_id: str) -> NoteData:
        """Convert to domain model.

        Args:
            user_id: ID of the user creating the note

        Returns:
            NoteData instance with validated data
        """
        return NoteData(
            content=self.content,
            user_id=user_id,
            activity_id=self.activity_id,
            moment_id=self.moment_id,
            attachments=self.attachments,
        )


class NoteUpdate(BaseModel):
    """Schema for updating an existing note."""

    content: Optional[str] = Field(
        None, min_length=1, max_length=2000
    )
    attachment_url: Optional[str] = Field(
        None, max_length=500
    )
    attachment_type: Optional[AttachmentType] = None
    processing_status: Optional[ProcessingStatus] = Field(
        None, description="New processing status"
    )


class NoteResponse(BaseModel):
    """Schema for note responses."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    content: str
    user_id: str
    activity_id: Optional[int] = None
    moment_id: Optional[int] = None
    attachments: Optional[List[Dict[str, Any]]] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    @classmethod
    def from_domain(
        cls, domain: NoteData
    ) -> "NoteResponse":
        """Create response from domain model.

        Args:
            domain: NoteData instance

        Returns:
            NoteResponse instance
        """
        return cls(
            id=domain.id,
            content=domain.content,
            user_id=domain.user_id,
            activity_id=domain.activity_id,
            moment_id=domain.moment_id,
            attachments=domain.attachments,
            created_at=domain.created_at,
            updated_at=domain.updated_at,
        )


class NoteList(BaseModel):
    """Schema for list of notes."""

    items: List[NoteResponse]
    total: int
    page: Optional[int] = 1
    size: Optional[int] = 10
    pages: Optional[int] = 1
