from typing import (
    Generic,
    List,
    Optional,
    Type,
    TypeVar,
    Any,
)
import logging
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from fastapi import HTTPException, status
from sqlalchemy import select

from .RepositoryMeta import RepositoryMeta
from utils.validation.validation import validate_existence

# Set up repository logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

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
        logger.debug(
            f"Initializing {self.__class__.__name__}"
            f" with model {model.__name__}"
        )
        self.db = db
        self.model = model

    def create(self, instance: ModelType) -> ModelType:
        """Create a new instance in the database"""
        logger.debug(
            f"Creating new {self.model.__name__} instance: {instance}"
        )
        try:
            self.db.add(instance)
            logger.debug("Added instance to session")
            self.db.commit()
            logger.debug("Committed transaction")

            # Refresh with the relationships we know we'll need
            self.db.refresh(instance)
            logger.debug("Refreshed instance")

            # Execute any pending loads within the same session
            self.db.execute(
                select(self.model).filter(
                    self.model.id == instance.id
                )
            )
            logger.debug("Loaded relationships")
            return instance
        except IntegrityError as e:
            logger.error(
                f"Integrity error during create: {str(e)}"
            )
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Resource already exists: {str(e)}",
            )
        except SQLAlchemyError as e:
            logger.error(
                f"Database error during create: {str(e)}"
            )
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Database error: {str(e)}",
            )

    def get(self, id: KeyType) -> Optional[ModelType]:
        """Get a single instance by ID"""
        logger.debug(
            f"Getting {self.model.__name__} instance with id: {id}"
        )
        try:
            instance = (
                self.db.query(self.model)
                .filter(self.model.id == id)
                .first()
            )
            logger.debug(
                f"Found instance: {instance is not None}"
            )
            return instance
        except SQLAlchemyError as e:
            logger.error(
                f"Database error during get: {str(e)}"
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Database error: {str(e)}",
            )

    def list(
        self, skip: int = 0, limit: int = 100
    ) -> List[ModelType]:
        """List instances with pagination"""
        logger.debug(
            f"Listing {self.model.__name__} instances with "
            f"skip: {skip}, limit: {limit}"
        )
        try:
            instances = (
                self.db.query(self.model)
                .offset(skip)
                .limit(limit)
                .all()
            )
            logger.debug(
                f"Found {len(instances)} instances"
            )
            return instances
        except SQLAlchemyError as e:
            logger.error(
                f"Database error during list: {str(e)}"
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Database error: {str(e)}",
            )

    def get_by_id(
        self, id: KeyType, user_id: str
    ) -> Optional[ModelType]:
        """Get a single instance by ID and verify ownership
           (alias for get_by_owner)

        Args:
            id: Instance ID
            user_id: Owner's user ID

        Returns:
            Instance if found and owned by user, None otherwise
        """
        return self.get_by_owner(id, user_id)

    def get_by_user(
        self, id: KeyType, user_id: str
    ) -> Optional[ModelType]:
        """Get a single instance by ID and verify ownership
           (alias for get_by_owner)

        Args:
            id: Instance ID
            user_id: Owner's user ID

        Returns:
            Instance if found and owned by user, None otherwise
        """
        return self.get_by_owner(id, user_id)

    def validate_existence(
        self,
        id: KeyType,
        error_message: str = None,
    ) -> ModelType:
        """Validate that a resource exists

        Args:
            id: Resource ID
            error_message: Optional custom error message

        Returns:
            Instance if found

        Raises:
            HTTPException: If resource not found
        """
        if error_message is None:
            error_message = (
                f"{self.model.__name__} not found"
            )
        return validate_existence(
            self.db, self.model, id, error_message
        )

    def update(
        self, id: KeyType, data: dict[str, Any]
    ) -> Optional[ModelType]:
        """Update an instance by ID"""
        logger.debug(
            f"Updating {self.model.__name__} instance with "
            f"id: {id}, data: {data}"
        )
        try:
            instance = self.get(id)
            if not instance:
                return None

            for key, value in data.items():
                setattr(instance, key, value)

            self.db.commit()
            logger.debug("Committed update")
            self.db.refresh(instance)
            logger.debug("Refreshed instance")
            return instance
        except IntegrityError as e:
            logger.error(
                f"Integrity error during update: {str(e)}"
            )
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Update violates constraints: {str(e)}",
            )
        except SQLAlchemyError as e:
            logger.error(
                f"Database error during update: {str(e)}"
            )
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Database error: {str(e)}",
            )

    def delete(self, id: KeyType) -> bool:
        """Delete an instance by ID"""
        logger.debug(
            f"Deleting {self.model.__name__} instance with id: {id}"
        )
        try:
            instance = self.get(id)
            if not instance:
                return False

            self.db.delete(instance)
            self.db.commit()
            logger.debug("Deleted instance")
            return True
        except SQLAlchemyError as e:
            logger.error(
                f"Database error during delete: {str(e)}"
            )
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Database error: {str(e)}",
            )

    def get_by_owner(
        self, id: KeyType, user_id: str
    ) -> Optional[ModelType]:
        """Get a single instance by ID and verify ownership

        Args:
            id: Instance ID
            user_id: Owner's user ID

        Returns:
            Instance if found and owned by user, None otherwise
        """
        logger.debug(
            f"Getting {self.model.__name__} instance with "
            f"id: {id} for user: {user_id}"
        )
        try:
            instance = (
                self.db.query(self.model)
                .filter(
                    self.model.id == id,
                    self.model.user_id == user_id,
                )
                .first()
            )
            logger.debug(
                f"Found instance: {instance is not None}"
            )
            return instance
        except SQLAlchemyError as e:
            logger.error(
                f"Database error during get_by_owner: {str(e)}"
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Database error: {str(e)}",
            )
