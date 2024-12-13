from datetime import datetime
import strawberry
from typing import Optional
from schemas.base.user_schema import UserData


@strawberry.type
class User:
    """User type for GraphQL queries"""

    id: str = strawberry.field(
        description="Unique identifier for the user"
    )
    username: str = strawberry.field(
        description="User's unique username"
    )
    createdAt: datetime = strawberry.field(
        description="When the user was created"
    )
    updatedAt: Optional[datetime] = strawberry.field(
        description="When the user was last updated"
    )

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
class UserRegisterResponse:
    """Response type for user registration"""

    id: str = strawberry.field(
        description="Unique identifier for the user"
    )
    username: str = strawberry.field(
        description="User's unique username"
    )
    userSecret: str = strawberry.field(
        description="Secret key for authentication (provided in registration)"
    )
    createdAt: datetime = strawberry.field(
        description="When the user was created"
    )
    updatedAt: Optional[datetime] = strawberry.field(
        description="When the user was last updated"
    )

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


@strawberry.type
class Token:
    """Authentication token response"""

    accessToken: str = strawberry.field(
        description="JWT access token"
    )
    tokenType: str = strawberry.field(
        default="bearer",
        description="Token type (always 'bearer')",
    )
