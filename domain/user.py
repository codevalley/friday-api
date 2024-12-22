"""Domain model for User.

This module defines the core User entity and its business rules.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Any, Optional, Type, TypeVar
import re

from domain.exceptions import (
    UserValidationError,
    UserKeyValidationError,
    UserIdentifierError
)

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
    user_secret: str
    key_id: Optional[str] = None
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
            UserValidationError: If validation fails
        """
        if not self.username or not isinstance(
            self.username, str
        ):
            raise UserIdentifierError(
                "username must be a non-empty string"
            )

        # Username format validation
        if not re.match(
            r"^[a-zA-Z][a-zA-Z0-9_-]*$", self.username
        ):
            raise UserIdentifierError(
                "username must start with a letter and contain only "
                "letters, numbers, underscores, and hyphens"
            )

        # Length check
        if not 3 <= len(self.username) <= 50:
            raise UserIdentifierError(
                "username must be between 3 and 50 characters long"
            )

        # Check for consecutive special characters
        if re.search(r"[_-]{2,}", self.username):
            raise UserIdentifierError(
                "username cannot contain consecutive special characters"
            )

        # Check for reserved words
        reserved_words = {
            "admin",
            "root",
            "system",
            "anonymous",
            "user",
            "moderator",
            "support",
            "help",
            "info",
            "test",
        }
        if self.username.lower() in reserved_words:
            raise UserIdentifierError(
                "this username is reserved and cannot be used"
            )

        # Check for too many consecutive numbers
        if re.search(r"\d{4,}", self.username):
            raise UserIdentifierError(
                "username cannot contain more than 3 consecutive numbers"
            )

        # key_id is required but can be None during initialization
        if self.key_id is None:
            raise UserKeyValidationError(
                "key_id must be empty or a valid UUID format"
            )
        elif not isinstance(self.key_id, str):
            raise UserKeyValidationError("key_id must be a string")
        elif not re.match(r"^[a-zA-Z0-9-]{36}$", self.key_id):
            raise UserKeyValidationError(
                "key_id must be empty or a valid UUID format"
            )

        if not isinstance(self.user_secret, str):
            raise UserValidationError("user_secret must be a string")

        # User secret format validation
        if self.user_secret and not re.match(
            r"^\$2[ayb]\$.{56}$", self.user_secret
        ):
            raise UserValidationError(
                "user_secret must be empty or a valid bcrypt hash"
            )

        if self.id is not None and (
            not isinstance(self.id, int) or self.id <= 0
        ):
            raise UserValidationError(
                "id must be a positive integer"
            )

        if self.created_at is not None and not isinstance(
            self.created_at, datetime
        ):
            raise UserValidationError(
                "created_at must be a datetime object"
            )

        if self.updated_at is not None and not isinstance(
            self.updated_at, datetime
        ):
            raise UserValidationError(
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
