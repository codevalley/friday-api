from datetime import datetime
from typing import Optional

from pydantic import Field, ConfigDict

from schemas.base.user_schema import UserData
from schemas.pydantic.CommonSchema import BaseSchema


# Common model configuration
model_config = ConfigDict(
    from_attributes=True,  # Enable ORM mode
    json_encoders={
        datetime: lambda v: v.isoformat()  # Format datetime as ISO string
    },
)


class UserBase(BaseSchema):
    """Base schema for User with common attributes.

    Attributes:
        username: User's unique username (3-50 characters)
    """

    username: str = Field(
        ...,
        min_length=3,
        max_length=50,
        description="User's unique username",
    )

    model_config = model_config

    def to_domain(self) -> UserData:
        """Convert to domain model.

        Returns:
            UserData: Domain model instance with validated data
        """
        return UserData.from_dict(self.model_dump())


class UserCreate(UserBase):
    """Schema for creating a new user.

    Inherits all fields from UserBase.
    """

    pass


class UserRegisterResponse(BaseSchema):
    """Response model for user registration.

    Attributes:
        id: Unique identifier for the user
        username: User's unique username
        user_secret: Secret key for API authentication
    """

    id: str = Field(
        ...,
        description="Unique identifier for the user",
    )
    username: str = Field(
        ...,
        description="User's unique username",
    )
    user_secret: str = Field(
        ...,
        description="Secret key for API authentication",
    )

    model_config = model_config

    @classmethod
    def from_domain(
        cls, user: UserData
    ) -> "UserRegisterResponse":
        """Create from domain model.

        Args:
            user: Domain model instance to convert

        Returns:
            UserRegisterResponse: Response model instance
        """
        return cls(**user.to_dict(include_secret=True))


class UserResponse(BaseSchema):
    """Full user response model with all fields.

    Attributes:
        id: Unique identifier for the user
        username: User's unique username
        created_at: When the user was created
        updated_at: When the user was last updated
    """

    id: str = Field(
        ...,
        description="Unique identifier for the user",
    )
    username: str = Field(
        ...,
        description="User's unique username",
    )
    created_at: datetime = Field(
        ...,
        description="When the user was created",
    )
    updated_at: Optional[datetime] = Field(
        None,
        description="When the user was last updated",
    )

    model_config = model_config

    @classmethod
    def from_domain(cls, user: UserData) -> "UserResponse":
        """Create from domain model.

        Args:
            user: Domain model instance to convert

        Returns:
            UserResponse: Response model instance
        """
        return cls(**user.to_dict())


class UserLoginRequest(BaseSchema):
    """Request model for user login.

    Attributes:
        user_secret: User's secret key for authentication
    """

    user_secret: str = Field(
        ...,
        description="User's secret key for authentication",
    )

    model_config = model_config


class Token(BaseSchema):
    """Token response model.

    Attributes:
        access_token: JWT access token
        token_type: Token type (always 'bearer')
    """

    access_token: str = Field(
        ...,
        description="JWT access token",
        example="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    )
    token_type: str = Field(
        "bearer",
        description="Token type (always 'bearer')",
    )

    model_config = model_config
