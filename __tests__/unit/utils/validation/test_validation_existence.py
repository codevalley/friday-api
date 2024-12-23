"""Test existence validation utilities."""

import pytest
from unittest.mock import Mock
from fastapi import HTTPException
from sqlalchemy import Column, Integer
from orm.BaseModel import EntityMeta
from utils.validation.validation import validate_existence


class MockModel(EntityMeta):
    """Mock model for testing."""

    __tablename__ = "mock_model"
    id = Column(Integer, primary_key=True)


@pytest.fixture
def mock_db():
    """Create mock database session."""
    return Mock()


def test_validate_existence_found(mock_db):
    """Test validation when resource exists."""
    # Arrange
    mock_instance = MockModel()
    mock_db.query.return_value.filter.return_value.first.return_value = (
        mock_instance
    )

    # Act
    result = validate_existence(mock_db, MockModel, 1)

    # Assert
    assert result == mock_instance


def test_validate_existence_not_found(mock_db):
    """Test validation when resource doesn't exist."""
    # Arrange
    mock_db.query.return_value.filter.return_value.first.return_value = (
        None
    )

    # Act & Assert
    with pytest.raises(HTTPException) as exc:
        validate_existence(mock_db, MockModel, 1)

    assert exc.value.status_code == 404
    assert "not found" in str(exc.value.detail)
