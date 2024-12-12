from typing import Optional, Tuple
from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from configs.Database import get_db_connection
from repositories.UserRepository import UserRepository
from models.UserModel import User


class UserService:
    def __init__(
        self, db: Session = Depends(get_db_connection)
    ):
        self.user_repository = UserRepository(db)

    async def register_user(
        self, username: str
    ) -> Tuple[User, str]:
        """Register a new user and return the user along with their secret"""
        # Check if username already exists
        if self.user_repository.get_by_username(username):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already registered",
            )

        # Generate a secure user_secret
        user_secret = generate_user_secret()

        # Create the user
        user = self.user_repository.create_user(
            username=username, user_secret=user_secret
        )

        return user, user_secret

    async def authenticate_user(
        self, user_secret: str
    ) -> User:
        """Authenticate a user by their secret and return the user"""
        user = self.user_repository.get_by_user_secret(
            user_secret
        )
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return user
