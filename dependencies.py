from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session
from configs.Database import get_db_connection
from configs.OpenAPI import security
from repositories.UserRepository import UserRepository
from utils.security import verify_token
from models.UserModel import User
from fastapi.security import HTTPAuthorizationCredentials


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(
        security
    ),
    db: Session = Depends(get_db_connection),
) -> User:
    """Get the current authenticated user from the bearer token"""
    try:
        # Get the token from credentials
        token = credentials.credentials

        # Verify the JWT token and get user_id
        user_id = verify_token(token)
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token",
            )

        # Get user from database
        repository = UserRepository(db)
        user = repository.get_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
            )

        return user
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
        )
