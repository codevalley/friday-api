from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from typing import Optional
from domain.note import NoteData, AttachmentType


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


class NoteCreate(NoteBase):
    """Schema for creating a new note."""

    def to_domain(self, user_id: str) -> NoteData:
        """Convert to domain model.

        Args:
            user_id: ID of the user creating the note

        Returns:
            NoteData instance
        """
        return NoteData(
            content=self.content,
            user_id=user_id,
            attachment_url=self.attachment_url,
            attachment_type=self.attachment_type,
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


class NoteResponse(BaseModel):
    """Schema for note responses."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    content: str
    user_id: str
    attachment_url: Optional[str] = None
    attachment_type: Optional[AttachmentType] = None
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
        return cls(**domain.to_dict())
