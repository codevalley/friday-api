"""Test UserData domain model."""

import pytest
from datetime import datetime
from unittest.mock import Mock
from domain.user import UserData


@pytest.fixture
def valid_user_data():
    """Create valid user data for testing."""
    return {
        "id": 1,
        "username": "testuser",
        "key_id": ("12345678-1234-5678-1234-567812345678"),
        "user_secret": (
            "$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8"
            "/LewKxcQw8SI9U6vDy"
        ),
        "created_at": datetime(2024, 1, 1, 12, 0),
        "updated_at": datetime(2024, 1, 1, 12, 0),
    }


@pytest.fixture
def valid_user_orm():
    """Create a mock ORM model with valid user data."""
    mock = Mock()
    mock.id = 1
    mock.username = "testuser"
    mock.key_id = "12345678-1234-5678-1234-567812345678"
    mock.user_secret = (
        "$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8"
        "/LewKxcQw8SI9U6vDy"
    )
    mock.created_at = datetime(2024, 1, 1, 12, 0)
    mock.updated_at = datetime(2024, 1, 1, 12, 0)
    return mock


class TestUserData:
    """Test cases for UserData domain model."""

    def test_create_user_with_valid_data(
        self, valid_user_data
    ):
        """Test creating a user with valid data."""
        user = UserData.from_dict(valid_user_data)
        assert user.id == valid_user_data["id"]
        assert user.username == valid_user_data["username"]
        assert user.key_id == valid_user_data["key_id"]
        assert (
            user.user_secret
            == valid_user_data["user_secret"]
        )
        assert (
            user.created_at == valid_user_data["created_at"]
        )
        assert (
            user.updated_at == valid_user_data["updated_at"]
        )

    def test_create_user_with_minimal_data(self):
        """Test creating a user with only required fields."""
        data = {
            "username": "testuser",
            "key_id": "",
            "user_secret": "",
        }
        user = UserData.from_dict(data)
        assert user.username == "testuser"
        assert user.key_id == ""
        assert user.user_secret == ""
        assert user.id is None
        assert user.created_at is None
        assert user.updated_at is None

    def test_to_dict_conversion(self, valid_user_data):
        """Test converting UserData to dictionary."""
        user = UserData.from_dict(valid_user_data)
        data = user.to_dict()
        assert data == valid_user_data

    def test_from_orm_conversion(self, valid_user_orm):
        """Test creating UserData from ORM model."""
        user = UserData.from_orm(valid_user_orm)
        assert user.id == valid_user_orm.id
        assert user.username == valid_user_orm.username
        assert user.key_id == valid_user_orm.key_id
        assert (
            user.user_secret == valid_user_orm.user_secret
        )
        assert user.created_at == valid_user_orm.created_at
        assert user.updated_at == valid_user_orm.updated_at

    @pytest.mark.parametrize(
        "username",
        [
            "ab",  # Too short
            "a" * 51,  # Too long
            "user@name",  # Invalid character
            "user name",  # Space not allowed
            "user+name",  # Plus not allowed
            "",  # Empty string
            None,  # None value
        ],
    )
    def test_invalid_username(
        self, username, valid_user_data
    ):
        """Test validation of invalid usernames."""
        data = dict(valid_user_data)
        data["username"] = username
        with pytest.raises(ValueError) as exc:
            UserData.from_dict(data)
        assert "username" in str(exc.value)

    @pytest.mark.parametrize(
        "key_id",
        [
            "invalid-uuid",  # Wrong format
            "12345",  # Too short
            "a" * 37,  # Too long
            123,  # Wrong type
        ],
    )
    def test_invalid_key_id(self, key_id, valid_user_data):
        """Test validation of invalid key_id values."""
        data = dict(valid_user_data)
        data["key_id"] = key_id
        with pytest.raises(ValueError) as exc:
            UserData.from_dict(data)
        assert "key_id" in str(exc.value)

    @pytest.mark.parametrize(
        "user_secret",
        [
            "invalid-hash",  # Wrong format
            "short",  # Too short
            123,  # Wrong type
            "$3b$12$invalid",  # Wrong prefix
        ],
    )
    def test_invalid_user_secret(
        self, user_secret, valid_user_data
    ):
        """Test validation of invalid user_secret values."""
        data = dict(valid_user_data)
        data["user_secret"] = user_secret
        with pytest.raises(ValueError) as exc:
            UserData.from_dict(data)
        assert "user_secret" in str(exc.value)

    def test_invalid_id(self, valid_user_data):
        """Test validation of invalid id values."""
        data = dict(valid_user_data)
        data["id"] = -1
        with pytest.raises(ValueError) as exc:
            UserData.from_dict(data)
        assert "id must be a positive integer" in str(
            exc.value
        )

    def test_invalid_datetime(self, valid_user_data):
        """Test validation of invalid datetime values."""
        data = dict(valid_user_data)
        data[
            "created_at"
        ] = "2024-01-01"  # String instead of datetime
        with pytest.raises(ValueError) as exc:
            UserData.from_dict(data)
        assert (
            "created_at must be a datetime object"
            in str(exc.value)
        )

    def test_missing_required_fields(self):
        """Test validation of missing required fields."""
        with pytest.raises(KeyError):
            UserData.from_dict({})

    def test_type_mismatches(self, valid_user_data):
        """Test validation of type mismatches."""
        data = dict(valid_user_data)
        data["username"] = 123  # Number instead of string
        with pytest.raises(ValueError) as exc:
            UserData.from_dict(data)
        assert "username must be a non-empty string" in str(
            exc.value
        )

    def test_empty_key_id_and_secret(self):
        """Test that empty key_id and user_secret are allowed."""
        data = {
            "username": "testuser",
            "key_id": "",
            "user_secret": "",
        }
        user = UserData.from_dict(data)
        assert user.key_id == ""
        assert user.user_secret == ""
