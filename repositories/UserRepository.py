from typing import Optional
from sqlalchemy.orm import Session
from orm.UserModel import User
from fastapi import HTTPException, status

from .BaseRepository import BaseRepository


class UserRepository(BaseRepository[User, str]):
    """Repository for managing User entities"""

    def __init__(self, db: Session):
        """Initialize with database session

        Args:
            db: SQLAlchemy database session
        """
        super().__init__(db, User)

    def create_user(
        self, username: str, key_id: str, user_secret: str
    ) -> User:
        """Create a new user

        Args:
            username: Unique username
            key_id: Unique API key ID
            user_secret: Hashed user secret

        Returns:
            Created User instance

        Raises:
            HTTPException: If username exists or key_id collision
        """
        user = User(
            username=username,
            key_id=key_id,
            user_secret=user_secret,
        )
        try:
            return self.create(user)
        except HTTPException as e:
            if e.status_code == status.HTTP_409_CONFLICT:
                # Check specific constraint violation
                if "username" in str(e.detail):
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Username already exists",
                    )
                if "key_id" in str(e.detail):
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail="Key ID collision occurred",
                    )
            raise e

    def get_by_id(self, user_id: str) -> Optional[User]:
        """Get a user by their ID"""
        return (
            self.db.query(User)
            .filter(User.id == user_id)
            .first()
        )

    def get_by_username(
        self, username: str
    ) -> Optional[User]:
        """Get a user by their username

        Args:
            username: Username to lookup

        Returns:
            User if found, None otherwise
        """
        return (
            self.db.query(User)
            .filter(User.username == username)
            .first()
        )

    def get_by_key_id(self, key_id: str) -> Optional[User]:
        """Get a user by their key_id (for API key authentication)

        Args:
            key_id: API key ID to lookup

        Returns:
            User if found, None otherwise
        """
        return (
            self.db.query(User)
            .filter(User.key_id == key_id)
            .first()
        )
