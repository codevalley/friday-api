from typing import Optional, Tuple
from sqlalchemy.orm import Session
from models.UserModel import User
from utils.security import generate_user_secret


class UserRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, username: str) -> Tuple[User, str]:
        """Create a new user with a generated user_secret"""
        user_secret = generate_user_secret()

        user = User(
            username=username,
            user_secret=user_secret,
        )
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)

        return user, user_secret

    def get_by_id(self, user_id: str) -> Optional[User]:
        """Get a user by their ID"""
        return self.db.query(User).filter(User.id == user_id).first()

    def get_by_username(self, username: str) -> Optional[User]:
        """Get a user by their username"""
        return (
            self.db.query(User)
            .filter(User.username == username)
            .first()
        )

    def get_by_user_secret(self, user_secret: str) -> Optional[User]:
        """Get a user by their user_secret"""
        return (
            self.db.query(User)
            .filter(User.user_secret == user_secret)
            .first()
        )
