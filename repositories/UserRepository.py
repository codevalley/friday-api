from typing import Optional
from sqlalchemy.orm import Session
from models.UserModel import User
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException, status


class UserRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_user(
        self, username: str, key_id: str, user_secret: str
    ) -> User:
        """Create a new user with the provided username, key_id, user_secret"""
        user = User(
            username=username,
            key_id=key_id,
            user_secret=user_secret,
        )
        self.db.add(user)
        try:
            self.db.commit()
            self.db.refresh(user)
        except IntegrityError as e:
            self.db.rollback()
            if "username" in str(e.orig):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Username already exists",
                )
            if "key_id" in str(e.orig):
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Key ID collision occurred",
                )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Database error occurred",
            )
        return user

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
        """Get a user by their username"""
        return (
            self.db.query(User)
            .filter(User.username == username)
            .first()
        )

    def get_by_key_id(self, key_id: str) -> Optional[User]:
        """Get a user by their key_id (for API key authentication)"""
        return (
            self.db.query(User)
            .filter(User.key_id == key_id)
            .first()
        )
