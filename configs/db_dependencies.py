from configs.Database import SessionLocal


def get_db_connection():
    """FastAPI dependency for database connection.

    This is used as a dependency in FastAPI route handlers.
    It yields a database session that will be closed after
    the request is complete.
    """
    print("\nCreating new database session")  # Debug log
    db = SessionLocal()
    try:
        print("Yielding database session")  # Debug log
        yield db
    finally:
        print("Closing database session")  # Debug log
        db.close()
