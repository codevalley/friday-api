from typing import Optional
from sqlalchemy.orm import Session
from models.UserModel import UserModel


class UserRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_user(
        self, username: str, user_secret: str
    ) -> UserModel:
        """Create a new user with the given username and user_secret"""
        user = UserModel(
            username=username, user_secret=user_secret
        )
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    def get_by_user_secret(
        self, user_secret: str
    ) -> Optional[UserModel]:
        """Get a user by their user_secret"""
        return (
            self.db.query(UserModel)
            .filter(UserModel.user_secret == user_secret)
            .first()
        )

    def get_by_id(
        self, user_id: str
    ) -> Optional[UserModel]:
        """Get a user by their ID"""
        return (
            self.db.query(UserModel)
            .filter(UserModel.id == user_id)
            .first()
        )

    def get_by_username(
        self, username: str
    ) -> Optional[UserModel]:
        """Get a user by their username"""
        return (
            self.db.query(UserModel)
            .filter(UserModel.username == username)
            .first()
        )
