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
    TopicList,
)
from utils.validation import validate_pagination

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
            # Convert schema to domain and validate
            domain_data = data.to_domain(user_id)

            # Create via repository
            topic_orm = self.topic_repo.create_from_domain(
                domain_data
            )
            self.db.commit()
            self.db.refresh(topic_orm)

            return TopicResponse.model_validate(topic_orm)
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
        self, user_id: str, topic_id: int
    ) -> TopicResponse:
        """Get a topic by ID.

        Args:
            user_id: Owner's user ID
            topic_id: Topic ID

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

            # Ensure topic has required fields
            if topic.id is None:
                raise ValueError("Topic missing ID")

            return TopicResponse.model_validate(topic)
        except ValueError as e:
            logger.error(f"Invalid topic data: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Invalid topic data",
            )
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
        user_id: str,
        topic_id: int,
        data: TopicUpdate,
    ) -> TopicResponse:
        """Update a topic.

        Args:
            user_id: Owner's user ID
            topic_id: Topic ID to update
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

            # Ensure topic has required fields
            if updated.id is None:
                raise ValueError("Updated topic missing ID")

            return TopicResponse.model_validate(updated)
        except (
            TopicValidationError,
            TopicNameError,
            TopicIconError,
        ) as e:
            self._handle_topic_error(e)
        except ValueError as e:
            logger.error(f"Invalid topic data: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Invalid topic data",
            )
        except Exception as e:
            logger.error(
                f"Unexpected error updating topic: {str(e)}"
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update topic",
            )

    def delete_topic(
        self, user_id: str, topic_id: int
    ) -> bool:
        """Delete a topic.

        Args:
            user_id: Owner's user ID
            topic_id: Topic ID to delete

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
        size: int = 50,
    ) -> TopicList:
        """List all topics for a user with pagination.

        Args:
            user_id: Owner's user ID
            page: Page number (default: 1)
            size: Page size (default: 50)

        Returns:
            TopicList: Paginated list of topics

        Raises:
            HTTPException: If pagination parameters are invalid
        """
        try:
            validate_pagination(page, size)
            skip = (page - 1) * size

            topics = self.topic_repo.list_by_user(
                user_id, skip=skip, limit=size
            )
            total = self.topic_repo.count_user_topics(user_id)

            return TopicList(
                items=[
                    TopicResponse.model_validate(t)
                    for t in topics
                ],
                total=total,
                page=page,
                size=size,
                pages=(total + size - 1) // size,
            )
        except ValueError as e:
            logger.error(
                f"Invalid pagination parameters: {str(e)}"
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e),
            )
        except Exception as e:
            logger.error(
                f"Unexpected error listing topics: {str(e)}"
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to list topics",
            )
