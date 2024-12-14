from datetime import datetime
import strawberry
from typing import Optional
from schemas.base.user_schema import UserData


@strawberry.type
class User:
    """User type for GraphQL queries"""

    @strawberry.field(
        description="Unique identifier for the user"
    )
    def id(self) -> str:
        return self._id

    @strawberry.field(description="User's unique username")
    def username(self) -> str:
        return self._username

    @strawberry.field(
        description="When the user was created"
    )
    def createdAt(self) -> datetime:
        return self._created_at

    @strawberry.field(
        description="When the user was last updated"
    )
    def updatedAt(self) -> Optional[datetime]:
        return self._updated_at

    def __init__(
        self,
        id: str,
        username: str,
        createdAt: datetime,
        updatedAt: Optional[datetime] = None,
    ):
        self._id = id
        self._username = username
        self._created_at = createdAt
        self._updated_at = updatedAt

    @classmethod
    def from_domain(cls, user: UserData) -> "User":
        """Create from domain model"""
        user_dict = user.to_dict(graphql=True)
        return cls(
            id=user_dict["id"],
            username=user_dict["username"],
            createdAt=user_dict["createdAt"],
            updatedAt=user_dict["updatedAt"],
        )


@strawberry.type
class UserRegisterResponse:
    """Response type for user registration"""

    @strawberry.field(
        description="Unique identifier for the user"
    )
    def id(self) -> str:
        return self._id

    @strawberry.field(description="User's unique username")
    def username(self) -> str:
        return self._username

    @strawberry.field(
        description="Secret key for authentication (provided in registration)"
    )
    def userSecret(self) -> str:
        return self._user_secret

    @strawberry.field(
        description="When the user was created"
    )
    def createdAt(self) -> datetime:
        return self._created_at

    @strawberry.field(
        description="When the user was last updated"
    )
    def updatedAt(self) -> Optional[datetime]:
        return self._updated_at

    def __init__(
        self,
        id: str,
        username: str,
        userSecret: str,
        createdAt: datetime,
        updatedAt: Optional[datetime] = None,
    ):
        self._id = id
        self._username = username
        self._user_secret = userSecret
        self._created_at = createdAt
        self._updated_at = updatedAt

    @classmethod
    def from_domain(
        cls, user: UserData
    ) -> "UserRegisterResponse":
        """Create from domain model"""
        user_dict = user.to_dict(
            graphql=True, include_secret=True
        )
        return cls(
            id=user_dict["id"],
            username=user_dict["username"],
            userSecret=user_dict["userSecret"],
            createdAt=user_dict["createdAt"],
            updatedAt=user_dict["updatedAt"],
        )


@strawberry.input
class UserCreateInput:
    """Input type for creating a new user"""

    username: str = strawberry.field(
        description="Username must be 3-50 characters and contain only "
        "letters, numbers, underscores, and hyphens"
    )

    def to_domain(self) -> UserData:
        """Convert to domain model"""
        return UserData.from_dict(
            {"username": self.username}
        )


@strawberry.input
class UserLoginInput:
    """Input type for user login"""

    userSecret: str = strawberry.field(
        description="User's secret key for authentication"
    )


@strawberry.type
class Token:
    """Authentication token response"""

    @strawberry.field(description="JWT access token")
    def accessToken(self) -> str:
        return self._access_token

    @strawberry.field(
        description="Token type (always 'bearer')"
    )
    def tokenType(self) -> str:
        return self._token_type

    def __init__(
        self,
        accessToken: str,
        tokenType: str = "bearer",
    ):
        self._access_token = accessToken
        self._token_type = tokenType
