from datetime import datetime
from typing import Optional
from domain.values import AttachmentType, ProcessingStatus
import strawberry


@strawberry.type
class Note:
    """GraphQL type for Note."""

    @strawberry.field
    def id(self) -> int:
        """Note ID."""
        return self._id

    @strawberry.field
    def content(self) -> str:
        """Note content."""
        return self._content

    @strawberry.field
    def user_id(self) -> str:
        """ID of the user who created the note."""
        return self._user_id

    @strawberry.field
    def attachment_url(self) -> Optional[str]:
        """URL of the attachment if any."""
        return self._attachment_url

    @strawberry.field
    def attachment_type(self) -> Optional[AttachmentType]:
        """Type of the attachment."""
        return self._attachment_type

    @strawberry.field
    def created_at(self) -> datetime:
        """When the note was created."""
        return self._created_at

    @strawberry.field
    def updated_at(self) -> Optional[datetime]:
        """When the note was last updated."""
        return self._updated_at

    @strawberry.field
    def processing_status(self) -> ProcessingStatus:
        """Status of Robo processing for the note."""
        return self._processing_status

    def __init__(
        self,
        id: int,
        content: str,
        user_id: str,
        created_at: datetime,
        attachment_url: Optional[str] = None,
        attachment_type: Optional[AttachmentType] = None,
        updated_at: Optional[datetime] = None,
        processing_status: ProcessingStatus = ProcessingStatus.default(),
    ):
        self._id = id
        self._content = content
        self._user_id = user_id
        self._attachment_url = attachment_url
        self._attachment_type = attachment_type
        self._created_at = created_at
        self._updated_at = updated_at
        self._processing_status = processing_status
