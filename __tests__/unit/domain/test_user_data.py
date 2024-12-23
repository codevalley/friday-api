"""Test UserData domain model."""

import pytest
from datetime import datetime
from unittest.mock import Mock
from domain.user import UserData
from domain.exceptions import (
    UserValidationError,
    UserKeyValidationError,
    UserIdentifierError,
)


@pytest.fixture
def valid_user_data():
    """Create valid user data for testing."""
    return {
        "username": "testuser",
        "user_secret": (
            "$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8"
            "/LewKxcQw/SKyDC.Oy"  # Valid bcrypt hash
        ),
        "key_id": (
            "123e4567-e89b-12d3-a456-426614174000"  # Valid UUID
        ),
        "id": None,
        "created_at": None,
        "updated_at": None,
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
        assert user.username == valid_user_data["username"]
        assert user.key_id == valid_user_data["key_id"]
        assert (
            user.user_secret
            == valid_user_data["user_secret"]
        )
        assert user.id is None
        assert user.created_at is None
        assert user.updated_at is None

    def test_create_user_with_minimal_data(self):
        """Test creating user with minimal required data."""
        minimal_data = {
            "username": "testuser",
            "user_secret": (
                "$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8"
                "/LewKxcQw/SKyDC.Oy"
            ),
        }
        with pytest.raises(UserKeyValidationError) as exc:
            UserData(**minimal_data)
        assert (
            str(exc.value)
            == "key_id must be empty or a valid UUID format"
        )

    def test_to_dict_conversion(self, valid_user_data):
        """Test converting UserData to dictionary."""
        user = UserData.from_dict(valid_user_data)
        data = user.to_dict()
        # Only compare non-None values
        filtered_data = {
            k: v for k, v in data.items() if v is not None
        }
        expected_data = {
            k: v
            for k, v in valid_user_data.items()
            if v is not None
        }
        assert filtered_data == expected_data

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
            "ab",  # too short
            "a" * 51,  # too long
            "user@name",  # invalid character
            "user name",  # space not allowed
            "user+name",  # plus not allowed
            "",  # empty string
            None,  # None value
        ],
    )
    def test_invalid_username(
        self, username, valid_user_data
    ):
        """Test validation with invalid usernames."""
        valid_user_data["username"] = username
        with pytest.raises(UserIdentifierError):
            UserData(**valid_user_data)

    @pytest.mark.parametrize(
        "key_id",
        [
            "invalid-uuid",  # not UUID format
            12345,  # wrong type
            "a" * 37,  # too long
            123,  # wrong type
        ],
    )
    def test_invalid_key_id(self, key_id, valid_user_data):
        """Test validation with invalid key_ids."""
        valid_user_data["key_id"] = key_id
        with pytest.raises((UserKeyValidationError)):
            UserData(**valid_user_data)

    @pytest.mark.parametrize(
        "user_secret",
        [
            "invalid-hash",  # not bcrypt format
            "short",  # too short
            123,  # wrong type
            "$3b$12$invalid",  # invalid format
        ],
    )
    def test_invalid_user_secret(
        self, user_secret, valid_user_data
    ):
        """Test validation with invalid user_secrets."""
        valid_user_data["user_secret"] = user_secret
        with pytest.raises(UserValidationError):
            UserData(**valid_user_data)

    def test_invalid_id(self, valid_user_data):
        """Test validation with invalid id."""
        valid_user_data["id"] = -1
        with pytest.raises(UserValidationError) as exc:
            UserData(**valid_user_data)
        assert (
            str(exc.value)
            == "id must be a positive integer"
        )

    def test_invalid_datetime(self, valid_user_data):
        """Test validation with invalid datetime."""
        valid_user_data["created_at"] = "not-a-datetime"
        with pytest.raises(UserValidationError) as exc:
            UserData(**valid_user_data)
        assert (
            str(exc.value)
            == "created_at must be a datetime object"
        )

    def test_type_mismatches(self, valid_user_data):
        """Test validation with type mismatches."""
        valid_user_data["username"] = 123  # wrong type
        with pytest.raises(UserIdentifierError) as exc:
            UserData(**valid_user_data)
        assert (
            str(exc.value)
            == "username must be a non-empty string"
        )

    def test_empty_key_id_and_secret(self, valid_user_data):
        """Test validation with empty key_id and secret."""
        valid_user_data["key_id"] = ""
        with pytest.raises(UserKeyValidationError) as exc:
            UserData(**valid_user_data)
        assert (
            str(exc.value)
            == "key_id must be empty or a valid UUID format"
        )

    def test_valid_user_creation(self, valid_user_data):
        """Test creating a valid user."""
        user = UserData(**valid_user_data)
        assert user.username == valid_user_data["username"]
        assert user.key_id == valid_user_data["key_id"]
        assert (
            user.user_secret
            == valid_user_data["user_secret"]
        )

    def test_to_dict(self, valid_user_data):
        """Test conversion to dictionary."""
        user = UserData(**valid_user_data)
        result = user.to_dict()
        assert (
            result["username"]
            == valid_user_data["username"]
        )
        assert result["key_id"] == valid_user_data["key_id"]
        assert (
            result["user_secret"]
            == valid_user_data["user_secret"]
        )

    def test_from_dict(self, valid_user_data):
        """Test creation from dictionary."""
        user = UserData.from_dict(valid_user_data)
        assert user.username == valid_user_data["username"]
        assert user.key_id == valid_user_data["key_id"]
        assert (
            user.user_secret
            == valid_user_data["user_secret"]
        )
