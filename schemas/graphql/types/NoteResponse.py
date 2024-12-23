from typing import Optional, List
from datetime import datetime
from domain.values import AttachmentType
import strawberry


@strawberry.type
class NoteResponse:
    """Response type for note operations."""

    @strawberry.field
    def id(self) -> int:
        return self._id

    @strawberry.field
    def content(self) -> str:
        return self._content

    @strawberry.field
    def user_id(self) -> str:
        return self._user_id

    @strawberry.field
    def attachment_url(self) -> Optional[str]:
        return self._attachment_url

    @strawberry.field
    def attachment_type(self) -> Optional[AttachmentType]:
        return self._attachment_type

    @strawberry.field
    def activity_id(self) -> int:
        return self._activity_id

    @strawberry.field
    def moment_id(self) -> Optional[int]:
        return self._moment_id

    @strawberry.field
    def created_at(self) -> datetime:
        return self._created_at

    @strawberry.field
    def updated_at(self) -> Optional[datetime]:
        return self._updated_at

    def __init__(
        self,
        id: int,
        content: str,
        user_id: str,
        activity_id: int,
        created_at: datetime,
        attachment_url: Optional[str] = None,
        attachment_type: Optional[AttachmentType] = None,
        moment_id: Optional[int] = None,
        updated_at: Optional[datetime] = None,
    ):
        self._id = id
        self._content = content
        self._user_id = user_id
        self._activity_id = activity_id
        self._attachment_url = attachment_url
        self._attachment_type = attachment_type
        self._moment_id = moment_id
        self._created_at = created_at
        self._updated_at = updated_at


@strawberry.type
class NoteConnection:
    """Type for paginated note lists."""

    @strawberry.field
    def items(self) -> List[NoteResponse]:
        return self._items

    @strawberry.field
    def total(self) -> int:
        return self._total

    @strawberry.field
    def page(self) -> int:
        return self._page

    @strawberry.field
    def size(self) -> int:
        return self._size

    @strawberry.field
    def pages(self) -> int:
        return (self._total + self._size - 1) // self._size

    def __init__(
        self,
        items: List[NoteResponse],
        total: int,
        page: int = 1,
        size: int = 50,
    ):
        self._items = items
        self._total = total
        self._page = page
        self._size = size
