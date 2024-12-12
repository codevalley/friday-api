from fastapi import Depends, HTTPException, status
from fastapi.security import (
    HTTPBearer,
    HTTPAuthorizationCredentials,
)
from sqlalchemy.orm import Session
from configs.Database import get_db_connection
from repositories.UserRepository import UserRepository
from utils.security import verify_token
from models.UserModel import UserModel

# OAuth2 bearer token scheme
security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(
        security
    ),
    db: Session = Depends(get_db_connection),
) -> UserModel:
    """Dependency to get the current authenticated user"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    # Verify the JWT token
    user_id = verify_token(credentials.credentials)
    if user_id is None:
        raise credentials_exception

    # Get the user from database
    user_repository = UserRepository(db)
    user = user_repository.get_by_id(user_id)
    if user is None:
        raise credentials_exception

    return user
