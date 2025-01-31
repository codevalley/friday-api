"""Unit tests for custom SQLAlchemy types."""

import pytest
from sqlalchemy import (
    Column,
    Integer,
    create_engine,
)
from sqlalchemy.orm import (
    declarative_base,
    sessionmaker,
    Session,
)

from orm.types import JSONType

Base = declarative_base()


class TestModel(Base):
    """Test model using custom types."""

    __tablename__ = "test_json_type"

    id = Column(Integer, primary_key=True)
    data = Column(JSONType)


@pytest.fixture
def db_session() -> Session:
    """Create test database session."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    TestingSessionLocal = sessionmaker(
        bind=engine, autocommit=False, autoflush=False
    )
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(engine)


def test_json_type_with_dict(db_session):
    """Test storing and retrieving dictionary values."""
    test_data = {"key": "value", "nested": {"foo": "bar"}}
    model = TestModel(data=test_data)
    db_session.add(model)
    db_session.commit()

    saved = db_session.get(TestModel, model.id)
    assert saved.data == test_data
    assert isinstance(saved.data, dict)
    assert saved.data["key"] == "value"
    assert saved.data["nested"]["foo"] == "bar"


def test_json_type_with_list(db_session):
    """Test storing and retrieving list values."""
    test_data = [1, "two", {"three": 3}]
    model = TestModel(data=test_data)
    db_session.add(model)
    db_session.commit()

    saved = db_session.get(TestModel, model.id)
    assert saved.data == test_data
    assert isinstance(saved.data, list)
    assert saved.data[0] == 1
    assert saved.data[1] == "two"
    assert saved.data[2]["three"] == 3


def test_json_type_with_none(db_session):
    """Test storing and retrieving None values."""
    model = TestModel(data=None)
    db_session.add(model)
    db_session.commit()

    saved = db_session.get(TestModel, model.id)
    assert saved.data is None


def test_json_type_with_scalar_values(db_session):
    """Test storing and retrieving scalar values."""
    test_cases = [
        (42, int),
        ("string", str),
        (True, bool),
        (3.14, float),
    ]

    for value, expected_type in test_cases:
        model = TestModel(data=value)
        db_session.add(model)
        db_session.commit()

        saved = db_session.get(TestModel, model.id)
        assert saved.data == value
        assert isinstance(saved.data, expected_type)


def test_json_type_dialect_impl():
    """Test dialect implementation selection."""
    json_type = JSONType()

    # Test PostgreSQL dialect
    class MockPostgresDialect:
        name = "postgresql"

        def type_descriptor(self, type_):
            return f"postgresql-{type_.__class__.__name__}"

    pg_impl = json_type.load_dialect_impl(
        MockPostgresDialect()
    )
    assert "postgresql-JSONB" in pg_impl

    # Test SQLite dialect
    class MockSQLiteDialect:
        name = "sqlite"

        def type_descriptor(self, type_):
            return f"sqlite-{type_.__class__.__name__}"

    sqlite_impl = json_type.load_dialect_impl(
        MockSQLiteDialect()
    )
    assert "sqlite-JSON" in sqlite_impl


def test_json_type_complex_nested_structure(db_session):
    """Test storing and retrieving complex nested structures."""
    test_data = {
        "string": "value",
        "integer": 42,
        "float": 3.14,
        "boolean": True,
        "null": None,
        "list": [1, 2, 3],
        "nested_dict": {
            "a": 1,
            "b": [4, 5, 6],
            "c": {
                "d": "nested",
                "e": [7, 8, 9],
            },
        },
        "list_of_dicts": [
            {"id": 1, "name": "first"},
            {"id": 2, "name": "second"},
        ],
    }

    model = TestModel(data=test_data)
    db_session.add(model)
    db_session.commit()

    saved = db_session.get(TestModel, model.id)
    assert saved.data == test_data
    assert isinstance(saved.data, dict)
    assert saved.data["string"] == "value"
    assert saved.data["integer"] == 42
    assert saved.data["float"] == 3.14
    assert saved.data["boolean"] is True
    assert saved.data["null"] is None
    assert saved.data["list"] == [1, 2, 3]
    assert saved.data["nested_dict"]["a"] == 1
    assert saved.data["nested_dict"]["b"] == [4, 5, 6]
    assert saved.data["nested_dict"]["c"]["d"] == "nested"
    assert saved.data["nested_dict"]["c"]["e"] == [7, 8, 9]
    assert saved.data["list_of_dicts"][0]["id"] == 1
    assert (
        saved.data["list_of_dicts"][1]["name"] == "second"
    )
