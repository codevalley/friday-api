from typing import Generic, List, Optional, Type, TypeVar
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from fastapi import HTTPException, status

from .RepositoryMeta import RepositoryMeta

# Type variable for SQLAlchemy model
M = TypeVar("M")
# Type variable for primary key
K = TypeVar("K")


class BaseRepository(RepositoryMeta[M, K], Generic[M, K]):
    """Base repository implementing common CRUD operations with error handling"""

    def __init__(self, db: Session, model: Type[M]):
        """Initialize repository with database session and model class

        Args:
            db: SQLAlchemy database session
            model: SQLAlchemy model class
        """
        self.db = db
        self.model = model

    def create(self, instance: M) -> M:
        """Create a new instance in the database

        Args:
            instance: Model instance to create

        Returns:
            Created model instance

        Raises:
            HTTPException: If database constraints are violated
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
                detail=f"Database error occurred: {str(e)}",
            )

    def get(self, id: K) -> Optional[M]:
        """Get an instance by ID

        Args:
            id: Primary key value

        Returns:
            Model instance if found, None otherwise
        """
        try:
            return (
                self.db.query(self.model)
                .filter(self.model.id == id)
                .first()
            )
        except SQLAlchemyError as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Database error occurred: {str(e)}",
            )

    def list(
        self, limit: int = 100, start: int = 0
    ) -> List[M]:
        """List instances with pagination

        Args:
            limit: Maximum number of instances to return
            start: Number of instances to skip

        Returns:
            List of model instances

        Raises:
            HTTPException: If database error occurs
        """
        try:
            return (
                self.db.query(self.model)
                .offset(start)
                .limit(limit)
                .all()
            )
        except SQLAlchemyError as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Database error occurred: {str(e)}",
            )

    def update(self, id: K, data: dict) -> Optional[M]:
        """Update an instance by ID

        Args:
            id: Primary key value
            data: Dictionary of attributes to update

        Returns:
            Updated model instance if found, None otherwise

        Raises:
            HTTPException: If database constraints are violated
        """
        try:
            instance = self.get(id)
            if not instance:
                return None

            for key, value in data.items():
                if (
                    hasattr(instance, key)
                    and value is not None
                ):
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
                detail=f"Database error occurred: {str(e)}",
            )

    def delete(self, id: K) -> bool:
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
                detail=f"Database error occurred: {str(e)}",
            )

    def exists(self, id: K) -> bool:
        """Check if an instance exists

        Args:
            id: Primary key value

        Returns:
            True if instance exists, False otherwise
        """
        return self.get(id) is not None
