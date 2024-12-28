"""Test database dependencies."""

import pytest
from sqlalchemy import text
from sqlalchemy.orm import Session
from configs.Database import get_db_connection


@pytest.fixture
def db_session():
    """Get a database session for testing."""
    # Get the generator
    db_gen = get_db_connection()

    # Get the session
    db = next(db_gen)

    yield db

    # Clean up
    try:
        next(db_gen)
    except StopIteration:
        pass


def test_get_db_connection(db_session):
    """Test database connection dependency."""
    # Verify we got a session
    assert isinstance(db_session, Session)

    # Test that session works
    result = db_session.execute(text("SELECT 1"))
    assert result.scalar() == 1

    # Test that session can be committed
    db_session.commit()

    # Test that session can be rolled back
    db_session.rollback()


def test_session_cleanup():
    """Test that session is properly cleaned up."""
    # Get a new session
    db_gen = get_db_connection()
    db = next(db_gen)

    # Store the session id for comparison
    session_id = id(db)

    # Use the session
    result = db.execute(text("SELECT 1"))
    assert result.scalar() == 1

    # Trigger cleanup
    try:
        next(db_gen)
    except StopIteration:
        pass

    # Try to get a new session
    new_db_gen = get_db_connection()
    new_db = next(new_db_gen)

    # Verify we got a different session
    assert id(new_db) != session_id

    try:
        next(new_db_gen)
    except StopIteration:
        pass
