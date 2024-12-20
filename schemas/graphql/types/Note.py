import strawberry
from datetime import datetime
from typing import Optional
from domain.note import AttachmentType


@strawberry.type
class Note:
    id: int
    content: str
    user_id: str
    attachment_url: Optional[str] = None
    attachment_type: Optional[AttachmentType] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
