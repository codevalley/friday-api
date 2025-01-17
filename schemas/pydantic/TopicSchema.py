"""Topic schemas for request/response validation."""

from datetime import datetime, UTC
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict

from domain.topic import TopicData
from schemas.pydantic.PaginationSchema import PaginationResponse

# Common model configuration
model_config = ConfigDict(
    from_attributes=True,  # Enable ORM mode
    json_encoders={
        datetime: lambda v: v.isoformat()  # Format datetime as ISO string
    },
)


class TopicBase(BaseModel):
    """Base schema for Topic with common attributes.

    Attributes:
        name: Unique name for the topic (per user)
        icon: Emoji character or URI for the icon
    """

    name: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Unique name for the topic (per user)",
        examples=["Work", "Personal", "Shopping", "Health"],
    )
    icon: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Emoji character or URI for the icon",
        examples=[
            "📝",
            "🏠",
            "🛒",
            "💪",
            "https://example.com/icons/work.png",
        ],
    )

    model_config = model_config


class TopicCreate(TopicBase):
    """Schema for creating a new Topic.

    This schema is used when creating a new topic. It inherits the base fields
    and adds the ability to convert to a domain model.
    """

    def to_domain(self, user_id: str) -> TopicData:
        """Convert schema to domain model.

        Args:
            user_id: Owner's user ID

        Returns:
            TopicData: Domain model instance with validated data
        """
        data = self.model_dump()
        data["user_id"] = user_id
        return TopicData.from_dict(data)


class TopicUpdate(BaseModel):
    """Schema for updating an existing Topic.

    All fields are optional since this is used for partial updates.
    """

    name: Optional[str] = Field(
        None,
        min_length=1,
        max_length=255,
        description="New name for the topic",
        examples=["Updated Work", "New Personal"],
    )
    icon: Optional[str] = Field(
        None,
        min_length=1,
        max_length=255,
        description="New emoji or URI for the icon",
        examples=["📊", "🎯"],
    )

    model_config = model_config

    def to_domain(self, existing: TopicData) -> TopicData:
        """Convert schema to domain model.

        Args:
            existing: Existing topic domain model

        Returns:
            TopicData: Updated domain model instance with validated data
        """
        update_dict = self.model_dump(exclude_unset=True)
        existing_dict = existing.to_dict()
        existing_dict.update(update_dict)
        existing_dict["updated_at"] = datetime.now(UTC)
        return TopicData.from_dict(existing_dict)


class TopicResponse(TopicBase):
    """Schema for Topic response data.

    This schema is used for API responses. It includes all base fields
    plus system fields like ID and timestamps.

    Attributes:
        id: Unique identifier
        user_id: Owner's user ID
        created_at: Creation timestamp
        updated_at: Last update timestamp
    """

    id: int = Field(
        description="Unique identifier", examples=[1, 42]
    )
    user_id: str = Field(
        description="Owner's user ID",
        examples=["123e4567-e89b-12d3-a456-426614174000"],
    )
    created_at: datetime = Field(
        description="When this topic was created",
        examples=["2024-01-11T12:00:00Z"],
    )
    updated_at: Optional[datetime] = Field(
        None,
        description="When this topic was last updated",
        examples=["2024-01-12T15:30:00Z"],
    )

    model_config = model_config

    @classmethod
    def from_domain(
        cls, domain: TopicData
    ) -> "TopicResponse":
        """Create response schema from domain model.

        Args:
            domain: Topic domain model

        Returns:
            TopicResponse: Response schema instance with all fields
        """
        return cls(**domain.to_dict())


class TopicList(PaginationResponse):
    """Response schema for list of Topics.

    This schema is used for paginated responses when listing topics.
    It includes pagination metadata along with the list of topics.

    Attributes:
        items: List of topics
        total: Total number of items
        page: Current page number
        size: Items per page
        pages: Total number of pages
    """

    items: List[TopicResponse] = Field(
        description="List of topics on this page"
    )

    model_config = model_config | ConfigDict(
        json_schema_extra={
            "example": {
                "items": [
                    {
                        "id": 1,
                        "user_id": "123e4567-e89b-12d3-a456-426614174000",
                        "name": "Work",
                        "icon": "💼",
                        "created_at": "2024-01-11T12:00:00Z",
                        "updated_at": "2024-01-12T15:30:00Z",
                    },
                    {
                        "id": 2,
                        "user_id": "123e4567-e89b-12d3-a456-426614174000",
                        "name": "Personal",
                        "icon": "🏠",
                        "created_at": "2024-01-11T12:00:00Z",
                        "updated_at": None,
                    },
                ],
                "total": 10,
                "page": 1,
                "size": 2,
                "pages": 5,
            }
        }
    )

    @classmethod
    def from_domain(
        cls, items: List[TopicData], page: int, size: int, total: int
    ) -> "TopicList":
        """Create paginated response from domain models.

        Args:
            items: List of topic domain models
            page: Current page number
            size: Items per page
            total: Total number of items

        Returns:
            TopicList: Paginated response with topics and metadata
        """
        return cls(
            items=[
                TopicResponse.from_domain(item)
                for item in items
            ],
            total=total,
            page=page,
            size=size,
            pages=(total + size - 1) // size,
        )
