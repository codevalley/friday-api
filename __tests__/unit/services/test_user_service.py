import pytest
from fastapi import HTTPException
from sqlalchemy.orm import Session

from services.UserService import UserService
from orm.UserModel import User
from utils.security import hash_secret, parse_api_key


@pytest.fixture
def user_service(test_db_session: Session) -> UserService:
    """Create a UserService instance with test database"""
    return UserService(test_db_session)


class TestUserService:
    def test_register_user_success(
        self, user_service: UserService
    ):
        """Test successful user registration"""
        username = "testuser123"
        user, api_key = user_service.register_user(username)

        assert isinstance(user, User)
        assert user.username == username
        assert user.id is not None
        assert user.key_id is not None
        assert user.user_secret is not None

        # Verify API key format and components
        key_id, secret = parse_api_key(api_key)
        assert user.key_id == key_id
        assert user.user_secret == hash_secret(secret)

    @pytest.mark.parametrize(
        "invalid_username,expected_error",
        [
            (
                "ab",
                "Username must be between 3 and 50 characters long",
            ),
            (
                "a" * 51,
                "Username must be between 3 and 50 characters long",
            ),
            (
                "123user",
                "Username must start with a letter",
            ),
            (
                "user__name",
                "Username cannot contain consecutive special characters",
            ),
            ("admin", "This username is reserved"),
            (
                "test1234567",
                "Username cannot contain more than 3 consecutive numbers",
            ),
            (
                "user@name",
                "Username must start with a letter and contain only letters",
            ),
        ],
    )
    def test_validate_username_invalid(
        self,
        user_service: UserService,
        invalid_username: str,
        expected_error: str,
    ):
        """Test username validation with invalid usernames"""
        with pytest.raises(HTTPException) as exc_info:
            user_service._validate_username(
                invalid_username
            )
        assert expected_error in str(exc_info.value.detail)

    def test_register_duplicate_username(
        self, user_service: UserService
    ):
        """Test registration with duplicate username"""
        username = "uniqueuser"
        user_service.register_user(username)

        with pytest.raises(HTTPException) as exc_info:
            user_service.register_user(username)
        assert "already exists" in str(
            exc_info.value.detail
        )

    def test_authenticate_user_success(
        self, user_service: UserService
    ):
        """Test successful user authentication"""
        # Register a user first
        username = "authuser"
        user, api_key = user_service.register_user(username)

        # Authenticate with the API key
        authenticated_user = user_service.authenticate_user(
            api_key
        )
        assert authenticated_user.id == user.id
        assert authenticated_user.username == username

    @pytest.mark.parametrize(
        "invalid_key",
        [
            "invalid_key",
            "invalid.key.format",
            "toolong.key.thisisnotvalidbase64",
            "",
            None,
        ],
    )
    def test_authenticate_user_invalid_key(
        self, user_service: UserService, invalid_key: str
    ):
        """Test authentication with invalid API keys"""
        with pytest.raises(HTTPException) as exc_info:
            user_service.authenticate_user(invalid_key)
        assert exc_info.value.status_code == 401

    def test_authenticate_user_wrong_secret(
        self, user_service: UserService
    ):
        """Test authentication with wrong API key secret"""
        # Register a user
        username = "secretuser"
        user, _ = user_service.register_user(username)

        # Create an API key with wrong secret
        wrong_key = f"{user.key_id}.wrongsecret"

        with pytest.raises(HTTPException) as exc_info:
            user_service.authenticate_user(wrong_key)
        assert exc_info.value.status_code == 401

    def test_get_user_by_id_success(
        self, user_service: UserService
    ):
        """Test successful user retrieval by ID"""
        # Register a user first
        username = "getuser"
        created_user, _ = user_service.register_user(
            username
        )

        # Get user by ID
        retrieved_user = user_service.get_user_by_id(
            created_user.id
        )
        assert retrieved_user.id == created_user.id
        assert retrieved_user.username == username

    def test_get_user_by_id_not_found(
        self, user_service: UserService
    ):
        """Test get user with non-existent ID"""
        with pytest.raises(HTTPException) as exc_info:
            user_service.get_user_by_id("nonexistent_id")
        assert exc_info.value.status_code == 404
        assert "User not found" in str(
            exc_info.value.detail
        )
