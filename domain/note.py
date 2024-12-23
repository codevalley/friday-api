from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Dict, Any, List, TypeVar

from domain.exceptions import (
    NoteValidationError,
    NoteContentError,
    NoteAttachmentError,
    NoteReferenceError,
)

T = TypeVar("T", bound="NoteData")


@dataclass
class NoteData:
    """Domain model for Note.

    This class represents a note attached to an activity or moment
    and contains all business logic and validation rules.
    """

    content: str
    user_id: str
    activity_id: Optional[int] = None
    attachments: Optional[List[Dict[str, Any]]] = None
    moment_id: Optional[int] = None
    id: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def __post_init__(self) -> None:
        """Validate note data after initialization."""
        self.validate()

    def validate(self) -> None:
        """Validate the note data.

        Raises:
            NoteValidationError: If validation fails
        """
        if not isinstance(self.content, str):
            raise NoteContentError(
                "content must be a string"
            )

        if not self.content.strip():
            raise NoteContentError(
                "content cannot be empty"
            )

        if len(self.content) > 10000:
            raise NoteContentError(
                "content cannot exceed 10000 characters"
            )

        if (
            not isinstance(self.user_id, str)
            or not self.user_id
        ):
            raise NoteValidationError(
                "user_id must be a non-empty string"
            )

        if self.activity_id is not None:
            if (
                not isinstance(self.activity_id, int)
                or self.activity_id <= 0
            ):
                raise NoteReferenceError(
                    "activity_id must be a positive integer"
                )

        if self.moment_id is not None:
            if (
                not isinstance(self.moment_id, int)
                or self.moment_id <= 0
            ):
                raise NoteReferenceError(
                    "moment_id must be a positive integer"
                )

        if self.attachments is not None:
            if not isinstance(self.attachments, list):
                raise NoteAttachmentError(
                    "attachments must be a list"
                )

            for attachment in self.attachments:
                self._validate_attachment(attachment)

        if self.id is not None and (
            not isinstance(self.id, int) or self.id <= 0
        ):
            raise NoteValidationError(
                "id must be a positive integer"
            )

    def _validate_attachment(
        self, attachment: Dict[str, Any]
    ) -> None:
        """Validate a single attachment.

        Args:
            attachment: Attachment data to validate

        Raises:
            NoteAttachmentError: If validation fails
        """
        if not isinstance(attachment, dict):
            raise NoteAttachmentError(
                "attachment must be a dictionary"
            )

        required_fields = {"type", "url"}
        if not all(
            field in attachment for field in required_fields
        ):
            raise NoteAttachmentError(
                f"attachment must contain fields: {required_fields}"
            )

        if not isinstance(attachment["type"], str):
            raise NoteAttachmentError(
                "attachment type must be a string"
            )

        if not isinstance(attachment["url"], str):
            raise NoteAttachmentError(
                "attachment url must be a string"
            )

        # Validate attachment type
        valid_types = {"image", "document", "link"}
        if attachment["type"] not in valid_types:
            raise NoteAttachmentError(
                f"attachment type must be one of: {valid_types}"
            )

    def to_dict(self) -> Dict[str, Any]:
        """Convert note to dictionary."""
        return {
            "id": self.id,
            "content": self.content,
            "user_id": self.user_id,
            "activity_id": self.activity_id,
            "moment_id": self.moment_id,
            "attachments": self.attachments,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }
