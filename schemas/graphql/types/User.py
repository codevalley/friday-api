"""GraphQL types for User-related data."""

from datetime import datetime
from typing import Any, Optional
import strawberry

from domain.user import UserData


@strawberry.type
class User:
    """GraphQL type for User."""

    @strawberry.field
    def id(self) -> int:
        """User ID."""
        return self._domain.id

    @strawberry.field
    def username(self) -> str:
        """User's username."""
        return self._domain.username

    @strawberry.field
    def key_id(self) -> str:
        """User's public key identifier."""
        return self._domain.key_id

    @strawberry.field
    def created_at(self) -> Optional[datetime]:
        """When the user was created."""
        return self._domain.created_at

    @strawberry.field
    def updated_at(self) -> Optional[datetime]:
        """When the user was last updated."""
        return self._domain.updated_at

    def __init__(self, domain: UserData):
        """Initialize with domain model."""
        self._domain = domain

    @classmethod
    def from_domain(cls, domain: UserData) -> "User":
        """Create from domain model."""
        return cls(domain)

    @classmethod
    def from_db(cls, db_model: Any) -> "User":
        """Create from database model."""
        return cls(UserData.from_orm(db_model))


@strawberry.input
class UserCreateInput:
    """GraphQL input type for creating a User."""

    username: str = strawberry.field(
        description="Unique username for the user"
    )
    key_id: str = strawberry.field(
        description="Public key identifier for API access"
    )
    user_secret: str = strawberry.field(
        description="Hashed secret for API authentication"
    )

    def to_domain(self) -> UserData:
        """Convert to domain model."""
        return UserData(
            username=self.username,
            key_id=self.key_id,
            user_secret=self.user_secret,
        )


@strawberry.input
class UserUpdateInput:
    """GraphQL input type for updating a User."""

    username: Optional[str] = strawberry.field(
        default=None,
        description="New username for the user",
    )
    key_id: Optional[str] = strawberry.field(
        default=None,
        description="New public key identifier",
    )
    user_secret: Optional[str] = strawberry.field(
        default=None,
        description="New hashed secret",
    )

    def to_domain(self, existing: UserData) -> UserData:
        """Convert to domain model, using existing data for missing fields."""
        return UserData(
            id=existing.id,
            username=self.username or existing.username,
            key_id=self.key_id or existing.key_id,
            user_secret=self.user_secret
            or existing.user_secret,
            created_at=existing.created_at,
            updated_at=datetime.now(),
        )


@strawberry.input
class UserLoginInput:
    """GraphQL input type for user login."""

    username: str = strawberry.field(
        description="Username to login with"
    )
    key_id: str = strawberry.field(
        description="Public key identifier for API access"
    )
    user_secret: str = strawberry.field(
        description="Hashed secret for authentication"
    )

    def to_domain(self) -> UserData:
        """Convert to domain model."""
        return UserData(
            username=self.username,
            key_id=self.key_id,
            user_secret=self.user_secret,
        )


@strawberry.type
class UserRegisterResponse:
    """Response type for user registration.

    Contains user information and authentication details
    returned after successful registration.
    """

    @strawberry.field(
        description="Unique identifier for the user"
    )
    def id(self) -> int:
        """Get user ID."""
        return self._domain.id

    @strawberry.field(description="User's unique username")
    def username(self) -> str:
        """Get username."""
        return self._domain.username

    @strawberry.field(
        description="Public key identifier for API access"
    )
    def key_id(self) -> str:
        """Get key ID."""
        return self._domain.key_id

    @strawberry.field(
        description="Secret key for authentication"
    )
    def user_secret(self) -> str:
        """Get user secret."""
        return self._domain.user_secret

    @strawberry.field(
        description="When the user was created"
    )
    def created_at(self) -> datetime:
        """Get creation timestamp."""
        return self._domain.created_at

    @strawberry.field(
        description="When the user was last updated"
    )
    def updated_at(self) -> Optional[datetime]:
        """Get update timestamp."""
        return self._domain.updated_at

    def __init__(self, domain: UserData):
        """Initialize with domain model."""
        self._domain = domain

    @classmethod
    def from_domain(
        cls, domain: UserData
    ) -> "UserRegisterResponse":
        """Create from domain model."""
        return cls(domain)


@strawberry.type
class Token:
    """Authentication token response.

    Contains the JWT access token and its type for API authentication.
    """

    @strawberry.field(description="JWT access token")
    def access_token(self) -> str:
        """Get access token."""
        return self._access_token

    @strawberry.field(
        description="Token type (always 'bearer')"
    )
    def token_type(self) -> str:
        """Get token type."""
        return self._token_type

    def __init__(
        self,
        access_token: str,
        token_type: str = "bearer",
    ):
        """Initialize Token type.

        Args:
            access_token: JWT access token string
            token_type: Token type (defaults to 'bearer')
        """
        self._access_token = access_token
        self._token_type = token_type
