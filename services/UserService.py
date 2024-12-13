from typing import Tuple
from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session
import re

from configs.Database import get_db_connection
from repositories.UserRepository import UserRepository
from models.UserModel import User
from utils.security import (
    generate_user_secret,
    hash_user_secret,
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
        """Register a new user and return the user along with their secret"""
        # Validate username format
        self._validate_username(username)

        # Generate a secure user_secret and hash it for storage
        user_secret = generate_user_secret()
        hashed_secret = hash_user_secret(user_secret)

        # Create the user with hashed secret
        try:
            user = self.user_repository.create_user(
                username=username,
                user_secret=hashed_secret,
            )
            # Return the user and the ORIGINAL user_secret (not the hash)
            return user, user_secret
        except HTTPException as e:
            raise e
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error creating user: {str(e)}",
            )

    def authenticate_user(
        self, user_secret: str
    ) -> User:
        """Authenticate a user by their secret and return the user"""
        # Hash the provided secret
        hashed_secret = hash_user_secret(user_secret)
        
        # Find user by hashed secret
        user = self.user_repository.get_by_secret_hash(hashed_secret)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return user
