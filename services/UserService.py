from typing import Tuple
from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session
import re

from configs.Database import get_db_connection
from repositories.UserRepository import UserRepository
from models.UserModel import User
from utils.security import (
    generate_api_key,
    hash_secret,
    parse_api_key,
)


class UserService:
    def __init__(
        self, db: Session = Depends(get_db_connection)
    ):
        self.user_repository = UserRepository(db)

    def _validate_username(self, username: str) -> None:
        """Validate username format"""
        if not re.match("^[a-zA-Z0-9_-]{3,50}$", username):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    "Username must be 3-50 characters long and contain only "
                    "letters, numbers, underscores, and hyphens"
                ),
            )

    def register_user(
        self, username: str
    ) -> Tuple[User, str]:
        """Register a new user and return the user along with their API key"""
        # Validate username format
        self._validate_username(username)

        # Generate API key components
        key_id, secret, full_key = generate_api_key()
        hashed_secret = hash_secret(secret)

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
            if user.user_secret != hash_secret(secret):
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
