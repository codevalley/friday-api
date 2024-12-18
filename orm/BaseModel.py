from typing import TypeVar, Any, Dict
from sqlalchemy.orm import DeclarativeBase
from datetime import datetime

from configs.Database import Engine


# Create base class with type information
class Base(DeclarativeBase):
    """Base class for all ORM models."""

    pass


EntityMeta = Base

# Type variable for model instances
ModelType = TypeVar("ModelType", bound=Base)


def to_dict(model: ModelType) -> Dict[str, Any]:
    """Convert model instance to dictionary.

    Includes all columns and relationships that are loaded.
    Handles datetime objects by converting them to ISO format.

    Args:
        model: SQLAlchemy model instance

    Returns:
        Dictionary representation of the model
    """
    from sqlalchemy import inspect

    result = {}
    for c in inspect(model).mapper.column_attrs:
        value = getattr(model, c.key)
        # Convert datetime to ISO format
        if isinstance(value, datetime):
            value = value.isoformat()
        result[c.key] = value
    return result


def init() -> None:
    """Initialize database tables.

    Creates all tables defined in the models if they don't exist.
    """
    EntityMeta.metadata.create_all(bind=Engine)
