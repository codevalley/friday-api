"""Test TopicRepository class."""

import pytest

from repositories.TopicRepository import TopicRepository
from orm.TopicModel import Topic


@pytest.fixture
def topic_repository(test_db_session):
    """Create TopicRepository instance with test database session."""
    return TopicRepository(db=test_db_session)


@pytest.fixture
def sample_topic(test_db_session, sample_user) -> Topic:
    """Create a sample topic for testing."""
    topic = Topic(
        name="Test Topic",
        icon="📝",
        user_id=sample_user.id,
    )
    test_db_session.add(topic)
    test_db_session.commit()
    test_db_session.refresh(topic)
    return topic


class TestTopicRepository:
    """Test suite for TopicRepository."""

    def test_create_topic(
        self, topic_repository, sample_user
    ):
        """Test creating a topic."""
        topic = topic_repository.create(
            name="Work",
            icon="💼",
            user_id=sample_user.id,
        )

        assert topic.id is not None
        assert topic.name == "Work"
        assert topic.icon == "💼"
        assert topic.user_id == sample_user.id
        assert topic.created_at is not None
        assert topic.updated_at is None

    def test_get_topic_by_id(
        self, topic_repository, sample_topic
    ):
        """Test retrieving a topic by ID."""
        topic = topic_repository.get(sample_topic.id)
        assert topic is not None
        assert topic.id == sample_topic.id
        assert topic.name == sample_topic.name
        assert topic.icon == sample_topic.icon
        assert topic.user_id == sample_topic.user_id

    def test_get_topic_by_user(
        self, topic_repository, sample_topic, sample_user
    ):
        """Test retrieving a topic by user ID."""
        topic = topic_repository.get_by_user(
            sample_topic.id, sample_user.id
        )
        assert topic is not None
        assert topic.id == sample_topic.id
        assert topic.user_id == sample_user.id

    def test_get_topic_by_name(
        self, topic_repository, sample_topic, sample_user
    ):
        """Test retrieving a topic by name."""
        topic = topic_repository.get_by_name(
            sample_user.id, sample_topic.name
        )
        assert topic is not None
        assert topic.id == sample_topic.id
        assert topic.name == sample_topic.name
        assert topic.user_id == sample_user.id

    def test_list_topics(
        self, topic_repository, sample_topic, sample_user
    ):
        """Test listing topics for a user."""
        # Create another topic for the same user
        topic_repository.create(
            name="Personal",
            icon="🏠",
            user_id=sample_user.id,
        )

        # List topics
        topics = topic_repository.list_topics(
            user_id=sample_user.id,
            skip=0,
            limit=10,
        )

        assert len(topics) == 2
        assert all(
            t.user_id == sample_user.id for t in topics
        )

    def test_update_topic(
        self, topic_repository, sample_topic
    ):
        """Test updating a topic."""
        # Update the topic
        updated = topic_repository.update_topic(
            sample_topic.id,
            sample_topic.user_id,
            name="Updated Topic",
            icon="🔄",
        )

        assert updated is not None
        assert updated.id == sample_topic.id
        assert updated.name == "Updated Topic"
        assert updated.icon == "🔄"
        assert updated.updated_at is not None

    def test_delete_topic(
        self, topic_repository, sample_topic
    ):
        """Test deleting a topic."""
        # Delete the topic
        result = topic_repository.delete(sample_topic.id)
        assert result is True

        # Verify it's gone
        topic = topic_repository.get(sample_topic.id)
        assert topic is None

    def test_get_nonexistent_topic(self, topic_repository):
        """Test retrieving a nonexistent topic."""
        topic = topic_repository.get(999)
        assert topic is None

    def test_update_nonexistent_topic(
        self, topic_repository
    ):
        """Test updating a nonexistent topic."""
        updated = topic_repository.update_topic(
            999, "test-user", name="Updated Topic"
        )
        assert updated is None

    def test_delete_nonexistent_topic(
        self, topic_repository
    ):
        """Test deleting a nonexistent topic."""
        result = topic_repository.delete(999)
        assert result is False

    def test_user_isolation(
        self,
        topic_repository,
        sample_topic,
        another_user,
    ):
        """Test that users can't access each other's topics."""
        # Try to get another user's topic
        topic = topic_repository.get_by_user(
            sample_topic.id, another_user.id
        )
        assert topic is None

        # List topics for another user
        topics = topic_repository.list_topics(
            user_id=another_user.id,
            skip=0,
            limit=10,
        )
        assert len(topics) == 0
