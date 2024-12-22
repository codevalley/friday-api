from typing import Tuple
from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session
import bcrypt
import secrets

from configs.Database import get_db_connection
from repositories.UserRepository import UserRepository
from orm.UserModel import User
from utils.security import (
    generate_api_key,
    parse_api_key,
)
from domain.exceptions import (
    UserValidationError,
    UserKeyValidationError,
    UserIdentifierError
)

import logging

logger = logging.getLogger(__name__)


class UserService:
    def __init__(
        self, db: Session = Depends(get_db_connection)
    ):
        self.user_repository = UserRepository(db)

    def _validate_username(self, username: str) -> None:
        """Validate username format.

        Args:
            username: Username to validate

        Raises:
            HTTPException: If username is invalid
        """
        try:
            if len(username) < 3 or len(username) > 50:
                raise ValueError(
                    "Username must be between 3 and 50 characters long"
                )

            if not username[0].isalpha():
                raise ValueError(
                    "Username must start with a letter"
                )

            if not all(
                c.isalnum() or c in "_-" for c in username
            ):
                raise ValueError(
                    "Username must start with a letter and "
                    "contain only letters, numbers, underscores, "
                    "and hyphens"
                )

            if "__" in username or "--" in username:
                raise ValueError(
                    "Username cannot contain consecutive special characters"
                )

            if any(
                str(i) in username
                for i in range(1000, 10000)
            ):
                raise ValueError(
                    "Username cannot contain more than 3 consecutive numbers"
                )

            if username.lower() in [
                "admin",
                "root",
                "system",
            ]:
                raise ValueError(
                    "This username is reserved"
                )

        except ValueError as e:
            raise HTTPException(
                status_code=400,
                detail=str(e),
            )

    def register_user(
        self, username: str
    ) -> Tuple[User, str]:
        """Register a new user and return the user along with their API key"""
        # Validate username format
        self._validate_username(username)

        # Generate API key components
        key_id, secret, full_key = generate_api_key()
        hashed_secret = self.hash_secret(secret)

        # Create the user with key_id and hashed secret
        try:
            user = self.user_repository.create_user(
                username=username,
                key_id=key_id,
                user_secret=hashed_secret,
            )
            # Return the user and the full API key
            return user, full_key
        except HTTPException as e:
            raise e
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error creating user: {str(e)}",
            )

    def authenticate_user(self, api_key: str) -> User:
        """Authenticate a user by their API key and return the user"""
        try:
            # Parse the API key into key_id and secret
            key_id, secret = parse_api_key(api_key)

            # Get user by key_id (fast lookup)
            user = self.user_repository.get_by_key_id(
                key_id
            )
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid API key",
                    headers={"WWW-Authenticate": "Bearer"},
                )

            # Verify the secret
            if not self.verify_secret(
                secret, user.user_secret
            ):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid API key",
                    headers={"WWW-Authenticate": "Bearer"},
                )

            return user
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid API key format",
                headers={"WWW-Authenticate": "Bearer"},
            )

    def get_user_by_id(self, user_id: str) -> User:
        """Get a user by their ID"""
        try:
            user = self.user_repository.get_by_id(user_id)
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found",
                )
            return user
        except HTTPException as e:
            raise e
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error getting user: {str(e)}",
            )

    def hash_secret(self, secret: str) -> str:
        """Hash a secret using bcrypt with salt.

        Args:
            secret: The secret string to hash

        Returns:
            str: The securely hashed secret
        """
        # Generate a random salt
        salt = bcrypt.gensalt(
            rounds=12
        )  # Work factor of 12

        # Hash the secret with the salt
        hashed = bcrypt.hashpw(secret.encode("utf-8"), salt)

        return hashed.decode("utf-8")

    def verify_secret(
        self, plain_secret: str, hashed_secret: str
    ) -> bool:
        """Verify a plain secret against its hash.

        Args:
            plain_secret: The plain secret to verify
            hashed_secret: The hashed secret to check against

        Returns:
            bool: True if the secret matches, False otherwise
        """
        return bcrypt.checkpw(
            plain_secret.encode("utf-8"),
            hashed_secret.encode("utf-8"),
        )

    def generate_secure_token(
        self, length: int = 32
    ) -> str:
        """Generate a cryptographically secure random token.

        Args:
            length: Length of the token in bytes

        Returns:
            str: A secure random token
        """
        return secrets.token_urlsafe(length)

    def _handle_user_error(self, error: Exception) -> None:
        """Map domain exceptions to HTTP exceptions."""
        if isinstance(error, UserKeyValidationError):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"message": str(error), "code": error.code}
            )
        elif isinstance(error, UserIdentifierError):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"message": str(error), "code": error.code}
            )
        elif isinstance(error, UserValidationError):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"message": str(error), "code": error.code}
            )
        raise error

    # Update other methods to use _handle_user_error
