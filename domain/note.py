from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any, List, TypeVar

from domain.exceptions import (
    NoteValidationError,
    NoteContentError,
    NoteAttachmentError,
)
from domain.values import ProcessingStatus

T = TypeVar("T", bound="NoteData")


@dataclass
class NoteData:
    """Domain model for Note.

    This class represents a note that can be attached to moments or tasks.
    It contains all business logic and validation rules.
    """

    content: str
    user_id: str
    attachments: Optional[List[Dict[str, Any]]] = None
    id: Optional[int] = None
    created_at: datetime = field(
        default_factory=datetime.now
    )
    updated_at: datetime = field(
        default_factory=datetime.now
    )
    processing_status: ProcessingStatus = field(
        default_factory=ProcessingStatus.default
    )

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
            "attachments": self.attachments,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "processing_status": self.processing_status,
        }

    def update_content(self, new_content: str) -> None:
        """Update note content and updated_at timestamp."""
        self.content = new_content
        self.updated_at = datetime.now()

    def update_processing_status(
        self, new_status: ProcessingStatus
    ) -> None:
        """Update processing status if transition is valid."""
        if not self.processing_status.can_transition_to(
            new_status
        ):
            raise ValueError(
                f"Invalid transition: {self.processing_status} -> {new_status}"
            )
        self.processing_status = new_status
        self.updated_at = datetime.now()
