"""Validation utilities for common operations"""

from typing import TypeVar, Type
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from orm.BaseModel import EntityMeta

M = TypeVar("M", bound=EntityMeta)


def validate_existence(
    db: Session,
    model: Type[M],
    id: any,
    error_message: str = "Resource not found",
) -> M:
    """Validate that a resource exists in the database

    Args:
        db: SQLAlchemy database session
        model: Model class to query
        id: Resource ID
        error_message: Custom error message if not found

    Returns:
        Instance if found

    Raises:
        HTTPException: If resource not found
    """
    instance = (
        db.query(model).filter(model.id == id).first()
    )
    if not instance:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=error_message,
        )
    return instance
