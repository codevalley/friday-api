"""Repository for managing Topic entities."""

from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from repositories.BaseRepository import BaseRepository
from orm.TopicModel import Topic
from domain.exceptions import (
    TopicValidationError,
    TopicNameError,
)


class TopicRepository(BaseRepository[Topic, int]):
    """Repository for managing Topic entities.

    This repository extends the BaseRepository to provide CRUD operations
    for Topic entities, along with topic-specific functionality like
    filtering by user and name.
    """

    def __init__(self, db: Session):
        """Initialize repository with database session.

        Args:
            db: SQLAlchemy database session
        """
        super().__init__(db, Topic)

    def create(
        self,
        name: str,
        icon: str,
        user_id: str,
    ) -> Topic:
        """Create a new topic.

        Args:
            name: Topic name (unique per user)
            icon: Topic icon (emoji or URI)
            user_id: ID of the user creating the topic

        Returns:
            Topic: Created topic

        Raises:
            TopicNameError: If topic name already exists for user
            TopicValidationError: If topic creation fails
        """
        try:
            topic = Topic(
                name=name,
                icon=icon,
                user_id=user_id,
            )
            return super().create(topic)
        except IntegrityError as e:
            if "uq_topic_name_per_user" in str(e):
                raise TopicNameError(
                    f"Topic name '{name}' already exists for user"
                )
            raise TopicValidationError(str(e))

    def list_topics(
        self,
        user_id: str,
        skip: int = 0,
        limit: int = 50,
    ) -> List[Topic]:
        """List all topics for a specific user.

        Args:
            user_id: Owner's user ID
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of topics owned by the user
        """
        return (
            self.db.query(Topic)
            .filter(Topic.user_id == user_id)
            .offset(skip)
            .limit(limit)
            .all()
        )

    def count_topics(self, user_id: str) -> int:
        """Count total topics for a user.

        Args:
            user_id: ID of the user whose topics to count

        Returns:
            int: Total number of topics
        """
        return (
            self.db.query(Topic)
            .filter(Topic.user_id == user_id)
            .count()
        )

    def get_by_name(
        self, user_id: str, name: str
    ) -> Optional[Topic]:
        """Get a topic by its name for a specific user.

        Args:
            user_id: Owner's user ID
            name: Topic name to search for

        Returns:
            Topic if found, None otherwise
        """
        return (
            self.db.query(Topic)
            .filter(
                Topic.user_id == user_id, Topic.name == name
            )
            .first()
        )

    def update_topic(
        self,
        topic_id: int,
        user_id: str,
        name: Optional[str] = None,
        icon: Optional[str] = None,
    ) -> Optional[Topic]:
        """Update a topic's fields.

        Args:
            topic_id: ID of the topic to update
            user_id: ID of the user who owns the topic
            name: Optional new name
            icon: Optional new icon

        Returns:
            Topic: Updated topic if found and owned by user, None otherwise

        Raises:
            TopicNameError: If new name already exists for user
            TopicValidationError: If update fails
        """
        topic = self.get_by_owner(topic_id, user_id)
        if topic is None:
            return None

        try:
            if name is not None:
                topic.name = name
            if icon is not None:
                topic.icon = icon

            self.db.add(topic)
            self.db.flush()
            return topic
        except IntegrityError as e:
            if "uq_topic_name_per_user" in str(e):
                raise TopicNameError(
                    f"Topic name '{name}' already exists for user"
                )
            raise TopicValidationError(str(e))

    def count_by_user(self, user_id: str) -> int:
        """Count topics for a user.

        Args:
            user_id: Owner's user ID

        Returns:
            int: Number of topics
        """
        return (
            self.db.query(Topic)
            .filter(Topic.user_id == user_id)
            .count()
        )
