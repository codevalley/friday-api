"""Service for managing Topic entities."""

from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from configs.Database import get_db_connection
from repositories.TopicRepository import TopicRepository
from domain.exceptions import (
    TopicValidationError,
    TopicNameError,
    TopicIconError,
)
from schemas.pydantic.TopicSchema import (
    TopicCreate,
    TopicUpdate,
    TopicResponse,
)

import logging

logger = logging.getLogger(__name__)


class TopicService:
    """Service for managing Topic entities.

    This service handles the business logic for topics, including
    validation, creation, updates, and deletion.

    Attributes:
        db: Database session
        topic_repo: Repository for topic operations
    """

    def __init__(
        self, db: Session = Depends(get_db_connection)
    ):
        """Initialize service with database session.

        Args:
            db: SQLAlchemy database session
        """
        self.db = db
        self.topic_repo = TopicRepository(db)

    def _handle_topic_error(self, error: Exception) -> None:
        """Map domain exceptions to HTTP exceptions."""
        if isinstance(error, TopicNameError):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "message": str(error),
                    "code": error.code,
                },
            )
        elif isinstance(error, TopicIconError):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "message": str(error),
                    "code": error.code,
                },
            )
        elif isinstance(error, TopicValidationError):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "message": str(error),
                    "code": error.code,
                },
            )
        raise error

    def create_topic(
        self, user_id: str, data: TopicCreate
    ) -> TopicResponse:
        """Create a new topic.

        Args:
            user_id: Owner's user ID
            data: Topic creation data

        Returns:
            TopicResponse: Created topic

        Raises:
            HTTPException: If topic creation fails
        """
        try:
            # Check for duplicate name
            existing = self.topic_repo.get_by_name(
                user_id, data.name
            )
            if existing:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Topic with this name already exists",
                )

            # Create via repository
            topic_orm = self.topic_repo.create(
                name=data.name,
                icon=data.icon,
                user_id=user_id,
            )
            self.db.commit()
            self.db.refresh(topic_orm)

            return TopicResponse.model_validate(topic_orm)
        except HTTPException:
            raise
        except (
            TopicValidationError,
            TopicNameError,
            TopicIconError,
        ) as e:
            self._handle_topic_error(e)
        except Exception as e:
            logger.error(
                f"Unexpected error creating topic: {str(e)}"
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create topic",
            )

    def get_topic(
        self, topic_id: str, user_id: str
    ) -> TopicResponse:
        """Get a topic by ID.

        Args:
            topic_id: Topic ID
            user_id: Owner's user ID

        Returns:
            TopicResponse: Found topic

        Raises:
            HTTPException: If topic not found
        """
        try:
            topic = self.topic_repo.get_by_owner(
                topic_id, user_id
            )
            if not topic:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Topic not found",
                )

            return TopicResponse.model_validate(topic)
        except HTTPException:
            raise
        except Exception as e:
            logger.error(
                f"Unexpected error getting topic: {str(e)}"
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to get topic",
            )

    def update_topic(
        self,
        topic_id: str,
        user_id: str,
        data: TopicUpdate,
    ) -> TopicResponse:
        """Update a topic.

        Args:
            topic_id: Topic ID to update
            user_id: Owner's user ID
            data: Update data

        Returns:
            TopicResponse: Updated topic

        Raises:
            HTTPException: If topic not found or update fails
        """
        try:
            # Verify ownership
            topic = self.topic_repo.get_by_owner(
                topic_id, user_id
            )
            if not topic:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Topic not found",
                )

            # Update via repository
            data_to_update = data.model_dump(
                exclude_unset=True
            )
            updated = self.topic_repo.update(
                topic_id, data_to_update
            )
            self.db.commit()

            return TopicResponse.model_validate(updated)
        except HTTPException:
            raise
        except (
            TopicValidationError,
            TopicNameError,
            TopicIconError,
        ) as e:
            self._handle_topic_error(e)
        except Exception as e:
            logger.error(
                f"Unexpected error updating topic: {str(e)}"
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update topic",
            )

    def delete_topic(
        self, topic_id: str, user_id: str
    ) -> bool:
        """Delete a topic.

        Args:
            topic_id: Topic ID to delete
            user_id: Owner's user ID

        Returns:
            bool: True if deleted

        Raises:
            HTTPException: If topic not found or deletion fails
        """
        try:
            # Verify ownership
            topic = self.topic_repo.get_by_owner(
                topic_id, user_id
            )
            if not topic:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Topic not found",
                )

            # Delete via repository
            deleted = self.topic_repo.delete(topic_id)
            self.db.commit()
            return deleted
        except HTTPException:
            raise
        except Exception as e:
            logger.error(
                f"Unexpected error deleting topic: {str(e)}"
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete topic",
            )

    def list_topics(
        self,
        user_id: str,
        page: int = 1,
        size: int = 10,
    ) -> dict:
        """List topics for a user.

        Args:
            user_id: Owner's user ID
            page: Page number (1-based)
            size: Page size

        Returns:
            dict: Dictionary containing:
                - items: List of topics
                - total: Total number of topics
                - page: Current page number
                - size: Page size
                - pages: Total number of pages
        """
        try:
            # Calculate offset
            skip = (page - 1) * size

            # Get topics via repository
            topics = self.topic_repo.list_topics(
                user_id=user_id,
                skip=skip,
                limit=size,
            )
            total = self.topic_repo.count_by_user(user_id)

            # Calculate total pages
            pages = (total + size - 1) // size

            return {
                "items": [
                    TopicResponse.model_validate(t)
                    for t in topics
                ],
                "total": total,
                "page": page,
                "size": size,
                "pages": pages,
            }
        except Exception as e:
            logger.error(
                f"Unexpected error listing topics: {str(e)}"
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to list topics",
            )
