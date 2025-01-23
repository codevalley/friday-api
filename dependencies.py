"""FastAPI dependency providers."""

from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional
from configs.Database import get_db_connection
from configs.OpenAPI import security
from configs.queue_dependencies import get_queue_service
from repositories.UserRepository import UserRepository
from repositories.ActivityRepository import (
    ActivityRepository,
)
from services.ActivityService import ActivityService
from utils.security import verify_token
from orm.UserModel import User
from domain.ports.QueueService import QueueService
from fastapi.security import HTTPAuthorizationCredentials


def get_current_user(
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


def get_optional_user(
    db: Session = Depends(get_db_connection),
    credentials: Optional[
        HTTPAuthorizationCredentials
    ] = Depends(security),
) -> Optional[User]:
    """Get the current user if authenticated, otherwise return None."""
    try:
        if not credentials:
            return None

        # Get the token from credentials
        token = credentials.credentials

        # Verify the JWT token and get user_id
        user_id = verify_token(token)
        if not user_id:
            return None

        # Get user from database
        repository = UserRepository(db)
        user = repository.get_by_id(user_id)
        return user
    except Exception:
        return None


def get_queue() -> QueueService:
    """Get queue service instance."""
    return get_queue_service()


def get_activity_service(
    db: Session = Depends(get_db_connection),
    queue: QueueService = Depends(get_queue),
) -> ActivityService:
    """Get activity service instance."""
    repository = ActivityRepository(db)
    return ActivityService(
        repository=repository, queue_service=queue
    )
