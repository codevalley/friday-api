from typing import TypeVar, Any, Dict
from sqlalchemy.orm import DeclarativeBase, declared_attr
from datetime import datetime

from configs.Database import Engine


class Base(DeclarativeBase):
    """Base class for all ORM models."""

    @declared_attr
    def __tablename__(cls) -> str:
        """Generate table name automatically from class name."""
        return cls.__name__.lower()

    def to_domain(self) -> Any:
        """Convert ORM model to domain model.

        This method should be implemented by subclasses to convert
        ORM models to their corresponding domain models.
        """
        raise NotImplementedError(
            f"to_domain() not implemented for {self.__class__.__name__}"
        )

    @classmethod
    def from_domain(cls, domain: Any) -> "Base":
        """Create ORM model from domain model.

        This method should be implemented by subclasses to convert
        domain models to their corresponding ORM models.
        """
        raise NotImplementedError(
            f"from_domain() not implemented for {cls.__name__}"
        )


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
    # Import all models to ensure they're registered with SQLAlchemy
    # These imports are required for table creation even if unused
    from orm.UserModel import User  # noqa: F401
    from orm.ActivityModel import Activity  # noqa: F401
    from orm.MomentModel import Moment  # noqa: F401
    from orm.NoteModel import Note  # noqa: F401
    from orm.TaskModel import Task  # noqa: F401
    from orm.DocumentModel import Document  # noqa: F401
    from orm.TopicModel import Topic  # noqa: F401

    EntityMeta.metadata.create_all(bind=Engine)
