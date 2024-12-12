from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from repositories.UserRepository import UserRepository
from models.UserModel import UserModel
from utils.security import generate_user_secret


class UserService:
    def __init__(self, db: Session):
        self.user_repository = UserRepository(db)

    def register_user(
        self, username: str
    ) -> tuple[UserModel, str]:
        """Register a new user and return the user model along with their secret"""
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

    def authenticate_user(
        self, user_secret: str
    ) -> UserModel:
        """Authenticate a user by their secret and return the user model"""
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
