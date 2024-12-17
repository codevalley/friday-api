from fixtures.test_model import TestModel
import pytest
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException
from repositories.BaseRepository import BaseRepository
import sys
import os

sys.path.append(
    os.path.join(os.path.dirname(__file__), "../..")
)


@pytest.fixture
def base_repository(test_db_session):
    """Create a BaseRepository instance for testing"""
    return BaseRepository(
        db=test_db_session, model=TestModel
    )


@pytest.fixture
def sample_data():
    """Create sample data for testing"""
    return {
        "name": "Test Item",
        "description": "Test Description",
    }


def test_create_success(base_repository, sample_data):
    """Test successful creation of a new instance"""
    instance = TestModel(**sample_data)
    created = base_repository.create(instance)

    assert created.id is not None
    assert created.name == sample_data["name"]
    assert created.description == sample_data["description"]


def test_create_duplicate_error(
    base_repository, sample_data
):
    """Test error handling when creating duplicate entries"""
    instance1 = TestModel(**sample_data)
    instance2 = TestModel(**sample_data)

    base_repository.create(instance1)

    with pytest.raises(HTTPException) as exc_info:
        base_repository.create(instance2)
    assert exc_info.value.status_code == 409


def test_get_existing(base_repository, sample_data):
    """Test retrieving an existing instance"""
    instance = TestModel(**sample_data)
    created = base_repository.create(instance)

    retrieved = base_repository.get(created.id)
    assert retrieved is not None
    assert retrieved.id == created.id
    assert retrieved.name == created.name


def test_get_nonexistent(base_repository):
    """Test retrieving a non-existent instance"""
    retrieved = base_repository.get(999)
    assert retrieved is None


def test_list_pagination(base_repository):
    """Test listing instances with pagination"""
    # Create multiple instances
    for i in range(5):
        instance = TestModel(
            name=f"Item {i}", description=f"Description {i}"
        )
        base_repository.create(instance)

    # Test different pagination scenarios
    all_items = base_repository.list(skip=0, limit=10)
    assert len(all_items) == 5

    first_page = base_repository.list(skip=0, limit=2)
    assert len(first_page) == 2

    second_page = base_repository.list(skip=2, limit=2)
    assert len(second_page) == 2
    assert first_page[0].id != second_page[0].id


def test_update_success(base_repository, sample_data):
    """Test successful update of an instance"""
    instance = TestModel(**sample_data)
    created = base_repository.create(instance)

    updated = base_repository.update(
        created.id, {"name": "Updated Name"}
    )
    assert updated is not None
    assert updated.name == "Updated Name"
    assert (
        updated.description == sample_data["description"]
    )  # Other fields unchanged


def test_update_nonexistent(base_repository):
    """Test updating a non-existent instance"""
    updated = base_repository.update(
        999, {"name": "Updated Name"}
    )
    assert updated is None


def test_update_integrity_error(
    base_repository, sample_data, mocker
):
    """Test error handling when integrity error occurs during update"""
    instance = TestModel(**sample_data)
    created = base_repository.create(instance)

    # Mock SQLAlchemy IntegrityError
    mock_session = mocker.patch.object(
        base_repository, "db"
    )
    mock_session.commit.side_effect = IntegrityError(
        "statement", "params", "orig"
    )

    with pytest.raises(HTTPException) as exc_info:
        base_repository.update(
            created.id, {"name": "Updated Name"}
        )
    assert exc_info.value.status_code == 409
    assert "Update violates constraints" in str(
        exc_info.value.detail
    )


def test_delete_success(base_repository, sample_data):
    """Test successful deletion of an instance"""
    instance = TestModel(**sample_data)
    created = base_repository.create(instance)

    result = base_repository.delete(created.id)
    assert result is True

    # Verify instance is deleted
    retrieved = base_repository.get(created.id)
    assert retrieved is None


def test_delete_nonexistent(base_repository):
    """Test deleting a non-existent instance"""
    result = base_repository.delete(999)
    assert result is False


def test_validate_existence_success(
    base_repository, sample_data
):
    """Test validation of existing instance"""
    instance = TestModel(**sample_data)
    created = base_repository.create(instance)

    validated = base_repository.validate_existence(
        created.id
    )
    assert validated is not None
    assert validated.id == created.id


def test_validate_existence_error(base_repository):
    """Test validation of non-existent instance"""
    with pytest.raises(HTTPException) as exc_info:
        base_repository.validate_existence(999)
    assert exc_info.value.status_code == 404


def test_create_database_error(
    base_repository, sample_data, mocker
):
    """Test error handling when database error occurs during create"""
    instance = TestModel(**sample_data)

    # Mock SQLAlchemy error
    mock_session = mocker.patch.object(
        base_repository, "db"
    )
    mock_session.commit.side_effect = SQLAlchemyError(
        "Database error"
    )

    with pytest.raises(HTTPException) as exc_info:
        base_repository.create(instance)
    assert exc_info.value.status_code == 500
    assert "Database error" in str(exc_info.value.detail)


def test_update_database_error(
    base_repository, sample_data, mocker
):
    """Test error handling when database error occurs during update"""
    instance = TestModel(**sample_data)
    created = base_repository.create(instance)

    # Mock SQLAlchemy error
    mock_session = mocker.patch.object(
        base_repository, "db"
    )
    mock_session.commit.side_effect = SQLAlchemyError(
        "Database error"
    )

    with pytest.raises(HTTPException) as exc_info:
        base_repository.update(
            created.id, {"name": "Updated Name"}
        )
    assert exc_info.value.status_code == 500
    assert "Database error" in str(exc_info.value.detail)


def test_delete_database_error(
    base_repository, sample_data, mocker
):
    """Test error handling when database error occurs during delete"""
    instance = TestModel(**sample_data)
    created = base_repository.create(instance)

    # Mock SQLAlchemy error
    mock_session = mocker.patch.object(
        base_repository, "db"
    )
    mock_session.commit.side_effect = SQLAlchemyError(
        "Database error"
    )

    with pytest.raises(HTTPException) as exc_info:
        base_repository.delete(created.id)
    assert exc_info.value.status_code == 500
    assert "Database error" in str(exc_info.value.detail)


def test_get_by_id_database_error(base_repository, mocker):
    """Test error handling when database error occurs during get_by_id"""
    # Mock SQLAlchemy error
    mock_session = mocker.patch.object(
        base_repository, "db"
    )
    mock_session.query.side_effect = SQLAlchemyError(
        "Database error"
    )

    with pytest.raises(HTTPException) as exc_info:
        base_repository.get_by_id(1, 1)  # user_id=1, id=1
    assert exc_info.value.status_code == 500
    assert "Database error" in str(exc_info.value.detail)
