from typing import (
    Generic,
    List,
    Optional,
    Type,
    TypeVar,
    Any,
)
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from fastapi import HTTPException, status

from .RepositoryMeta import RepositoryMeta

# Type variables with better constraints
ModelType = TypeVar("ModelType")
KeyType = TypeVar(
    "KeyType", int, str
)  # Limit key types to int and str


class BaseRepository(
    RepositoryMeta[ModelType, KeyType],
    Generic[ModelType, KeyType],
):
    """Base repository implementing common CRUD operations
    with error handling"""

    def __init__(self, db: Session, model: Type[ModelType]):
        """Initialize repository with database session and model class

        Args:
            db: SQLAlchemy database session
            model: SQLAlchemy model class
        """
        self.db = db
        self.model = model

    def create(self, instance: ModelType) -> ModelType:
        """Create a new instance in the database

        Args:
            instance: Model instance to create

        Returns:
            Created model instance

        Raises:
            HTTPException: If database constraints are violated
            or other errors occur
        """
        try:
            self.db.add(instance)
            self.db.commit()
            self.db.refresh(instance)
            return instance
        except IntegrityError as e:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Resource already exists: {str(e)}",
            )
        except SQLAlchemyError as e:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Database error: {str(e)}",
            )

    def get(self, id: KeyType) -> Optional[ModelType]:
        """Get a single instance by ID

        Args:
            id: Primary key value

        Returns:
            Model instance if found, None otherwise
        """
        return (
            self.db.query(self.model)
            .filter(self.model.id == id)
            .first()
        )

    def get_by_id(
        self, id: KeyType, user_id: str
    ) -> Optional[ModelType]:
        """Get a single instance by ID and user_id for authorization

        Args:
            id: Primary key value
            user_id: User ID for authorization

        Returns:
            Model instance if found and authorized, None otherwise

        Raises:
            HTTPException: If database error occurs
        """
        try:
            return (
                self.db.query(self.model)
                .filter(
                    self.model.id == id,
                    self.model.user_id == user_id,
                )
                .first()
            )
        except SQLAlchemyError as e:
            raise HTTPException(
                status_code=500,
                detail=f"Database error: {str(e)}",
            )

    def list(
        self, skip: int = 0, limit: int = 100
    ) -> List[ModelType]:
        """List instances with pagination

        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of model instances
        """
        return (
            self.db.query(self.model)
            .offset(skip)
            .limit(limit)
            .all()
        )

    def update(
        self, id: KeyType, data: dict[str, Any]
    ) -> Optional[ModelType]:
        """Update an instance by ID

        Args:
            id: Primary key value
            data: Dictionary of fields to update

        Returns:
            Updated model instance if found, None otherwise

        Raises:
            HTTPException: If database constraints are violated
            or other errors occur
        """
        try:
            instance = self.get(id)
            if not instance:
                return None

            for key, value in data.items():
                setattr(instance, key, value)

            self.db.commit()
            self.db.refresh(instance)
            return instance
        except IntegrityError as e:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Update violates constraints: {str(e)}",
            )
        except SQLAlchemyError as e:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Database error: {str(e)}",
            )

    def delete(self, id: KeyType) -> bool:
        """Delete an instance by ID

        Args:
            id: Primary key value

        Returns:
            True if instance was deleted, False if not found

        Raises:
            HTTPException: If database error occurs
        """
        try:
            instance = self.get(id)
            if not instance:
                return False

            self.db.delete(instance)
            self.db.commit()
            return True
        except SQLAlchemyError as e:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Database error: {str(e)}",
            )

    def validate_existence(
        self,
        id: KeyType,
        error_message: str = "Resource not found",
    ) -> ModelType:
        """Validate that a resource exists and raise HTTPException if not

        Args:
            id: Primary key value
            error_message: Custom error message to use

        Returns:
            Model instance if found

        Raises:
            HTTPException: If resource not found
        """
        instance = self.get(id)
        if not instance:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=error_message,
            )
        return instance
