"""Pydantic schemas for User-related data."""

from datetime import datetime, UTC
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict

from domain.user import UserData


class UserBase(BaseModel):
    """Base schema for User with common attributes."""

    username: str = Field(
        ...,
        min_length=3,
        max_length=50,
        pattern=r"^[a-zA-Z0-9_-]+$",
        description="Unique username for the user",
    )


class UserCreate(UserBase):
    """Schema for creating a new User."""

    def to_domain(self) -> UserData:
        """Convert to domain model.

        Returns:
            UserData: Domain model instance with validated data
        """
        return UserData(
            username=self.username,
            key_id="",  # Will be generated by service
            user_secret="",  # Will be generated by service
        )


class UserUpdate(BaseModel):
    """Schema for updating an existing User."""

    username: Optional[str] = Field(
        None,
        min_length=3,
        max_length=50,
        pattern=r"^[a-zA-Z0-9_-]+$",
        description="New username for the user",
    )

    def to_domain(self, existing: UserData) -> UserData:
        """Convert to domain model, preserving existing data.

        Args:
            existing: Existing user data to update

        Returns:
            UserData: Updated domain model instance
        """
        update_dict = self.model_dump(exclude_unset=True)
        existing_dict = existing.to_dict()
        existing_dict.update(update_dict)
        return UserData.from_dict(existing_dict)


class UserResponse(UserBase):
    """Response schema for User."""

    id: str = Field(
        ..., description="Unique identifier for the user"
    )
    key_id: str = Field(
        ...,
        description="Public key identifier for API access",
    )
    created_at: datetime = Field(
        ...,
        description="When this user was created",
    )
    updated_at: Optional[datetime] = Field(
        None,
        description="When this user was last updated",
    )

    @classmethod
    def from_domain(
        cls, domain: UserData
    ) -> "UserResponse":
        """Create from domain model.

        Args:
            domain: Domain model instance to convert

        Returns:
            UserResponse: Response model instance
        """
        return cls(
            id=str(domain.id),
            username=domain.username,
            key_id=domain.key_id,
            created_at=domain.created_at
            or datetime.now(UTC),
            updated_at=domain.updated_at,
        )

    model_config = ConfigDict(
        from_attributes=True,
        ser_json_timedelta="iso8601",
        json_encoders=None,  # Use default serializers
    )


class UserRegisterResponse(BaseModel):
    """Response schema for user registration."""

    id: str = Field(
        ..., description="Unique identifier for the user"
    )
    username: str = Field(
        ..., description="User's unique username"
    )
    key_id: str = Field(
        ...,
        description="Public key identifier for API access",
    )
    user_secret: str = Field(
        ..., description="Secret key for authentication"
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        description="When the user was created",
    )
    updated_at: Optional[datetime] = Field(
        None, description="When the user was last updated"
    )

    @classmethod
    def from_domain(
        cls, domain: UserData, user_secret: str
    ) -> "UserRegisterResponse":
        """Create from domain model.

        Args:
            domain: Domain model instance to convert
            user_secret: The generated user secret

        Returns:
            UserRegisterResponse: Response model instance
        """
        return cls(
            id=str(domain.id),
            username=domain.username,
            key_id=domain.key_id,
            user_secret=user_secret,
            created_at=domain.created_at
            or datetime.now(UTC),
            updated_at=domain.updated_at,
        )

    model_config = ConfigDict(
        from_attributes=True,
        ser_json_timedelta="iso8601",
        json_encoders=None,  # Use default serializers
    )


class UserLoginRequest(BaseModel):
    """Request schema for user login."""

    user_secret: str = Field(
        ...,
        description="Secret key for authentication",
    )

    def to_domain(self) -> UserData:
        """Convert to domain model.

        Returns:
            UserData: Domain model instance with validated data
        """
        return UserData(
            username="",  # Will be looked up by service
            key_id="",  # Will be looked up by service
            user_secret=self.user_secret,
        )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "user_secret": (
                    "$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8"
                    "/LewKxcQw8SI9U6vDy"
                ),
            }
        }
    )


class Token(BaseModel):
    """Authentication token response.

    Contains the JWT access token and its type for API authentication.
    """

    access_token: str = Field(
        ..., description="JWT access token"
    )
    token_type: str = Field(
        "bearer",
        description="Token type (always 'bearer')",
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "access_token": (
                    "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9"
                    ".eyJzdWIiOiIxMjM0NTY3ODkwIn0"
                    ".dozjgNryP4J3jVmNHl0w5N_XgL0n1Rg"
                ),
                "token_type": "bearer",
            }
        }
    )


class UserInfoResponse(BaseModel):
    """Response schema for current user information."""

    id: str = Field(
        ..., description="Unique identifier for the user"
    )
    username: str = Field(
        ...,
        min_length=3,
        max_length=50,
        pattern=r"^[a-zA-Z0-9_-]+$",
        description="Unique username for the user",
    )
    created_at: datetime = Field(
        ...,
        description="When this user was created",
    )
    updated_at: Optional[datetime] = Field(
        None,
        description="When this user was last updated",
    )

    @classmethod
    def from_domain(
        cls, domain: UserData
    ) -> "UserInfoResponse":
        """Create from domain model.

        Args:
            domain: Domain model instance to convert

        Returns:
            UserInfoResponse: Response model instance
        """
        return cls(
            id=str(domain.id),
            username=domain.username,
            created_at=domain.created_at
            or datetime.now(UTC),
            updated_at=domain.updated_at,
        )

    model_config = ConfigDict(
        from_attributes=True,
        ser_json_timedelta="iso8601",
        json_encoders=None,  # Use default serializers
    )
