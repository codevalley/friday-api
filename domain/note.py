from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from enum import Enum


class AttachmentType(str, Enum):
    """Type of attachment that can be associated with a note.

    Inherits from str to allow case-insensitive comparison and
    automatic string serialization.
    """

    VOICE = "voice"
    PHOTO = "photo"
    FILE = "file"

    @classmethod
    def _missing_(
        cls, value: str
    ) -> Optional["AttachmentType"]:
        """Handle case-insensitive lookup of enum values.

        Args:
            value: The value to look up

        Returns:
            Matching enum member or None
        """
        for member in cls:
            if member.value.upper() == value.upper():
                return member
        return None


@dataclass
class NoteData:
    """Domain model for a note.

    This class represents a note in the system, with optional attachments.
    It includes validation rules to ensure data consistency.

    Attributes:
        content: The text content of the note
        user_id: ID of the user who owns this note
        id: Optional unique identifier
        attachment_url: Optional URL to an attachment
        attachment_type: Optional type of the attachment
        created_at: When the note was created
        updated_at: When the note was last updated
    """

    content: str
    user_id: str
    id: Optional[int] = None
    attachment_url: Optional[str] = None
    attachment_type: Optional[AttachmentType] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def __post_init__(self):
        self.validate()

    def validate(self):
        """Validate the note data.

        Raises:
            ValueError: If any validation rules are violated
        """
        if not self.content or not isinstance(
            self.content, str
        ):
            raise ValueError(
                "Note content must be a non-empty string"
            )
        if len(self.content) < 1:
            raise ValueError("Note content cannot be empty")
        if not self.user_id or not isinstance(
            self.user_id, str
        ):
            raise ValueError(
                "user_id must be a non-empty string"
            )
        if self.attachment_url and not self.attachment_type:
            raise ValueError(
                "attachment_type is required when attachment_url is provided"
            )
        if self.attachment_type and not self.attachment_url:
            raise ValueError(
                "attachment_url is required when attachment_type is provided"
            )

    def to_dict(self):
        """Convert the note to a dictionary.

        Returns:
            Dictionary representation of the note
        """
        return {
            "id": self.id,
            "content": self.content,
            "user_id": self.user_id,
            "attachment_url": self.attachment_url,
            "attachment_type": (
                self.attachment_type.value
                if self.attachment_type
                else None
            ),
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, data: dict):
        """Create a note from a dictionary.

        Args:
            data: Dictionary containing note data

        Returns:
            NoteData instance
        """
        if data.get("attachment_type"):
            data["attachment_type"] = AttachmentType(
                data["attachment_type"]
            )
        return cls(**data)
