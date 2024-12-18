"""Domain model for User.

This module defines the core User entity and its business rules.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Any, Optional, Type, TypeVar
import re

T = TypeVar("T", bound="UserData")


@dataclass
class UserData:
    """Domain model for User.

    This class represents a user in the system and contains all business
    logic and validation rules for users.

    Data Flow and Conversions:
    1. API Layer: Incoming data is validated by Pydantic schemas
       (UserCreate/UserUpdate)
    2. Domain Layer: Data is converted to UserData using to_domain()
       methods
    3. Database Layer: UserData is converted to ORM models
       using from_dict()
    4. Response: ORM models are converted back to UserData using from_orm()
    5. API Response: UserData is converted to response schemas
       using from_domain()

    Attributes:
        username: Unique username for the user
        key_id: Public key identifier for API access
        user_secret: Hashed secret for API authentication
        id: Unique identifier for the user (optional)
        created_at: When this record was created (optional)
        updated_at: When this record was last updated (optional)
    """

    username: str
    key_id: str
    user_secret: str
    id: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def __post_init__(self):
        """Validate the user data after initialization."""
        self.validate()

    def validate(self) -> None:
        """Validate the user data.

        This method performs comprehensive validation of all fields
        to ensure data integrity and consistency.

        Raises:
            ValueError: If any validation fails
        """
        if not self.username or not isinstance(
            self.username, str
        ):
            raise ValueError(
                "username must be a non-empty string"
            )

        # Username format validation
        if not re.match(
            r"^[a-zA-Z0-9_-]{3,50}$", self.username
        ):
            raise ValueError(
                "username must be 3-50 characters and contain only "
                "letters, numbers, underscores, and hyphens"
            )

        if not isinstance(self.key_id, str):
            raise ValueError("key_id must be a string")

        # Key ID format validation (if not empty)
        if self.key_id and not re.match(
            r"^[a-zA-Z0-9-]{36}$", self.key_id
        ):
            raise ValueError(
                "key_id must be empty or a valid UUID format"
            )

        if not isinstance(self.user_secret, str):
            raise ValueError("user_secret must be a string")

        # User secret format validation (if not empty)
        if self.user_secret and not re.match(
            r"^\$2[ayb]\$.{56}$", self.user_secret
        ):
            raise ValueError(
                "user_secret must be empty or a valid bcrypt hash"
            )

        if self.id is not None and (
            not isinstance(self.id, int) or self.id <= 0
        ):
            raise ValueError(
                "id must be a positive integer"
            )

        if self.created_at is not None and not isinstance(
            self.created_at, datetime
        ):
            raise ValueError(
                "created_at must be a datetime object"
            )

        if self.updated_at is not None and not isinstance(
            self.updated_at, datetime
        ):
            raise ValueError(
                "updated_at must be a datetime object"
            )

    def to_dict(self) -> Dict[str, Any]:
        """Convert the user data to a dictionary.

        This method is used when we need to serialize the domain model,
        typically for API responses or database operations.

        Returns:
            Dict[str, Any]: Dictionary representation of the user,
                           with all fields properly serialized
        """
        return {
            "id": self.id,
            "username": self.username,
            "key_id": self.key_id,
            "user_secret": self.user_secret,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls: Type[T], data: Dict[str, Any]) -> T:
        """Create a UserData instance from a dictionary.

        This method is used when we receive data from an API request
        or need to reconstruct the domain model from stored data.

        Args:
            data: Dictionary containing user data with the following fields:
                - username: Unique username (required)
                - key_id: Public key identifier (required)
                - user_secret: Hashed secret (required)
                - id: Unique identifier (optional)
                - created_at: Creation timestamp (optional)
                - updated_at: Last update timestamp (optional)

        Returns:
            UserData: New instance with validated data

        Raises:
            ValueError: If required fields are missing or invalid
        """
        return cls(
            id=data.get("id"),
            username=data["username"],
            key_id=data.get("key_id", ""),
            user_secret=data.get("user_secret", ""),
            created_at=data.get("created_at"),
            updated_at=data.get("updated_at"),
        )

    @classmethod
    def from_orm(cls: Type[T], orm_model: Any) -> T:
        """Create a UserData instance from an ORM model.

        This method bridges the database and domain layers,
        ensuring that data from the database is properly validated.

        Args:
            orm_model: SQLAlchemy model instance

        Returns:
            UserData: New instance with validated data from the database
        """
        return cls(
            id=orm_model.id,
            username=orm_model.username,
            key_id=orm_model.key_id,
            user_secret=orm_model.user_secret,
            created_at=orm_model.created_at,
            updated_at=orm_model.updated_at,
        )
