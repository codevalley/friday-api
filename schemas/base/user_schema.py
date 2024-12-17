from typing import Optional, Dict
from datetime import datetime
from dataclasses import dataclass
import re


@dataclass
class UserData:
    """Base data structure for user data"""

    username: str
    id: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    user_secret: Optional[
        str
    ] = None  # Only used during registration

    def __post_init__(self):
        """Validate data after initialization"""
        self.validate()

    def validate(self) -> None:
        """Validate the user data"""
        # Username validation
        if not isinstance(self.username, str):
            raise ValueError("username must be a string")

        if not re.match(r"^[a-zA-Z0-9_-]+$", self.username):
            raise ValueError(
                "username can only have letters, numbers, underscores, hyphens"
            )

        if (
            len(self.username) < 3
            or len(self.username) > 50
        ):
            raise ValueError(
                "username must be between 3 and 50 characters"
            )

        # ID validation
        if self.id is not None:
            if not isinstance(self.id, str):
                raise ValueError("id must be a string")
            if not self.id.strip():
                raise ValueError(
                    "id cannot be empty if provided"
                )

        # Timestamp validation
        if self.created_at is not None:
            if not isinstance(self.created_at, datetime):
                raise ValueError(
                    "created_at must be a datetime object"
                )

        if self.updated_at is not None:
            if not isinstance(self.updated_at, datetime):
                raise ValueError(
                    "updated_at must be a datetime object"
                )
            if (
                self.created_at
                and self.updated_at < self.created_at
            ):
                raise ValueError(
                    "updated_at cannot be earlier than created_at"
                )

        # User secret validation
        if self.user_secret is not None:
            if not isinstance(self.user_secret, str):
                raise ValueError(
                    "user_secret must be a string"
                )
            if len(self.user_secret) < 32:
                raise ValueError(
                    "user_secret must be at least 32 characters"
                )

    @classmethod
    def from_dict(cls, data: Dict) -> "UserData":
        """Create from a dictionary (used by both Pydantic and GraphQL)"""
        if not isinstance(data, dict):
            raise ValueError("Input must be a dictionary")

        if "username" not in data:
            raise ValueError("username is required")

        return cls(
            username=data["username"],
            id=data.get("id"),
            created_at=data.get("created_at")
            or data.get("createdAt"),
            updated_at=data.get("updated_at")
            or data.get("updatedAt"),
            user_secret=data.get("user_secret")
            or data.get("userSecret"),
        )

    def to_dict(
        self,
        graphql: bool = False,
        include_secret: bool = False,
    ) -> Dict:
        """
        Convert to dictionary, optionally using GraphQL field naming

        Args:
            graphql: Whether to use GraphQL field naming
            include_secret: Whether to include the user_secret (registration)
        """
        if graphql:
            base = {
                "username": self.username,
                "createdAt": self.created_at,
                "updatedAt": self.updated_at,
            }
            if include_secret and self.user_secret:
                base["userSecret"] = self.user_secret
        else:
            base = {
                "username": self.username,
                "created_at": self.created_at,
                "updated_at": self.updated_at,
            }
            if include_secret and self.user_secret:
                base["user_secret"] = self.user_secret

        if self.id is not None:
            base["id"] = self.id

        return base

    def to_auth_dict(self) -> Dict:
        """Convert to dictionary for authentication purposes"""
        if not self.id:
            raise ValueError(
                "Cannot create auth dict without user id"
            )

        return {"id": self.id, "username": self.username}
