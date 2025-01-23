"""Test authentication dependencies."""

import pytest
from fastapi import HTTPException
from unittest.mock import Mock, patch  # noqa: F401
from dependencies import (  # noqa: F401
    get_current_user,
    get_optional_user,
)


@pytest.fixture
def mock_credentials():
    """Create mock credentials."""
    credentials = Mock()
    credentials.credentials = "valid_token"
    return credentials


@pytest.fixture
def mock_user():
    """Create mock user."""
    user = Mock()
    user.id = "test_user_id"
    return user


def test_get_current_user_valid(
    mock_credentials, mock_user, mock_db
):
    """Test getting current user with valid token."""
    with patch("dependencies.verify_token") as mock_verify:
        with patch(
            "dependencies.UserRepository"
        ) as mock_repo:
            mock_verify.return_value = "test_user_id"
            mock_repo.return_value.get_by_id.return_value = (
                mock_user
            )

            user = get_current_user(
                mock_credentials, mock_db
            )

            assert user == mock_user
            mock_verify.assert_called_once_with(
                "valid_token"
            )
            mock_repo.return_value.get_by_id.assert_called_once_with(
                "test_user_id"
            )


def test_get_current_user_invalid_token(
    mock_credentials, mock_db
):
    """Test getting current user with invalid token."""
    with patch("dependencies.verify_token") as mock_verify:
        mock_verify.return_value = None

        with pytest.raises(HTTPException) as exc:
            get_current_user(mock_credentials, mock_db)

        assert exc.value.status_code == 401
        assert "Invalid token" in str(exc.value.detail)


def test_get_current_user_user_not_found(
    mock_credentials, mock_db
):
    """Test getting current user when user not found in DB."""
    with patch("dependencies.verify_token") as mock_verify:
        with patch(
            "dependencies.UserRepository"
        ) as mock_repo:
            mock_verify.return_value = "test_user_id"
            mock_repo.return_value.get_by_id.return_value = (
                None
            )

            with pytest.raises(HTTPException) as exc:
                get_current_user(mock_credentials, mock_db)

            assert exc.value.status_code == 401
            assert "User not found" in str(exc.value.detail)


def test_get_optional_user_valid(
    mock_credentials, mock_user, mock_db
):
    """Test getting optional user with valid token."""
    with patch("dependencies.verify_token") as mock_verify:
        with patch(
            "dependencies.UserRepository"
        ) as mock_repo:
            mock_verify.return_value = "test_user_id"
            mock_repo.return_value.get_by_id.return_value = (
                mock_user
            )

            user = get_optional_user(
                mock_db, mock_credentials
            )

            assert user == mock_user
            mock_verify.assert_called_once_with(
                "valid_token"
            )
            mock_repo.return_value.get_by_id.assert_called_once_with(
                "test_user_id"
            )


def test_get_optional_user_no_credentials(mock_db):
    """Test getting optional user with no credentials."""
    user = get_optional_user(mock_db, None)
    assert user is None


def test_get_optional_user_invalid_token(
    mock_credentials, mock_db
):
    """Test getting optional user with invalid token."""
    with patch("dependencies.verify_token") as mock_verify:
        mock_verify.return_value = None

        user = get_optional_user(mock_db, mock_credentials)

        assert user is None
        mock_verify.assert_called_once_with("valid_token")


def test_get_current_user_verify_token_error(
    mock_credentials, mock_db
):
    """Test getting current user when token verification fails."""
    with patch("dependencies.verify_token") as mock_verify:
        mock_verify.side_effect = Exception(
            "Token verification failed"
        )

        with pytest.raises(HTTPException) as exc:
            get_current_user(mock_credentials, mock_db)

        assert exc.value.status_code == 401
        assert "Token verification failed" in str(
            exc.value.detail
        )


def test_get_optional_user_verify_token_error(
    mock_credentials, mock_db
):
    """Test getting optional user when token verification fails."""
    with patch("dependencies.verify_token") as mock_verify:
        mock_verify.side_effect = Exception(
            "Token verification failed"
        )

        user = get_optional_user(mock_db, mock_credentials)

        assert user is None


def test_get_optional_user_db_error(
    mock_credentials, mock_db
):
    """Test getting optional user when database query fails."""
    with patch("dependencies.verify_token") as mock_verify:
        with patch(
            "dependencies.UserRepository"
        ) as mock_repo:
            mock_verify.return_value = "test_user_id"
            mock_repo.return_value.get_by_id.side_effect = (
                Exception("DB error")
            )

            user = get_optional_user(
                mock_db, mock_credentials
            )

            assert user is None
