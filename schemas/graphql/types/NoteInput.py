from typing import Optional
from domain.values import AttachmentType
import strawberry


@strawberry.input
class NoteInput:
    """Input type for creating a new note."""

    content: str = strawberry.field(
        description="Content of the note"
    )
    attachment_url: Optional[str] = strawberry.field(
        default=None,
        description="URL of the attachment if any",
    )
    attachment_type: Optional[
        AttachmentType
    ] = strawberry.field(
        default=None,
        description="Type of the attachment",
    )
    activity_id: int = strawberry.field(
        description="ID of the associated activity"
    )
    moment_id: Optional[int] = strawberry.field(
        default=None,
        description="ID of the associated moment",
    )
