"""Test BaseModel class."""

import pytest
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.exc import IntegrityError

from orm.BaseModel import EntityMeta, to_dict


class TestTableModel(EntityMeta):
    """Test model for validating BaseModel functionality."""

    __tablename__ = "test_table"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=False)
    description = Column(String(200))
    created_at = Column(
        DateTime, nullable=False, default=datetime.utcnow
    )


def test_table_definition():
    """Test that table is properly defined with columns."""
    assert TestTableModel.__tablename__ == "test_table"
    assert hasattr(TestTableModel, "id")
    assert hasattr(TestTableModel, "name")
    assert hasattr(TestTableModel, "description")
    assert hasattr(TestTableModel, "created_at")


def test_column_validation(test_db_session):
    """Test column constraints and validation."""
    # Test valid model creation
    model = TestTableModel(
        name="Test Name", description="Test Description"
    )
    test_db_session.add(model)
    test_db_session.commit()

    assert model.id is not None
    assert model.name == "Test Name"
    assert model.description == "Test Description"
    assert isinstance(model.created_at, datetime)

    # Test nullable constraint
    with pytest.raises(IntegrityError):
        invalid_model = TestTableModel(
            description="No Name"
        )
        test_db_session.add(invalid_model)
        test_db_session.commit()


def test_to_dict_conversion():
    """Test conversion of model instance to dictionary."""
    now = datetime.utcnow()
    model = TestTableModel(
        id=1,
        name="Test Name",
        description="Test Description",
        created_at=now,
    )

    result = to_dict(model)

    assert isinstance(result, dict)
    assert result["id"] == 1
    assert result["name"] == "Test Name"
    assert result["description"] == "Test Description"
    assert result["created_at"] == now.isoformat()


def test_to_dict_with_none_values():
    """Test to_dict handles None values correctly."""
    model = TestTableModel(name="Test Name")
    result = to_dict(model)

    assert result["name"] == "Test Name"
    assert "description" in result
    assert result["description"] is None


def test_table_reuse(test_db_session):
    """Test that table can be reused across multiple tests."""
    # First insertion
    model1 = TestTableModel(name="First Test")
    test_db_session.add(model1)
    test_db_session.commit()

    # Second insertion
    model2 = TestTableModel(name="Second Test")
    test_db_session.add(model2)
    test_db_session.commit()

    # Verify both records exist
    results = test_db_session.query(TestTableModel).all()
    assert len(results) == 2
    assert results[0].name == "First Test"
    assert results[1].name == "Second Test"
