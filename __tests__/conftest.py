import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timezone

from models.ActivityModel import Activity
from models.MomentModel import Moment
from models.BaseModel import EntityMeta

# Test database URL should be configured in .env.test
from configs.Environment import get_environment_variables


@pytest.fixture(scope="session")
def engine():
    """Create engine for test database"""
    env = get_environment_variables()
    test_engine = create_engine(
        f"{env.DATABASE_DIALECT}://{env.DATABASE_USERNAME}:{env.DATABASE_PASSWORD}@"
        f"{env.DATABASE_HOSTNAME}:{env.DATABASE_PORT}/{env.DATABASE_NAME}"
    )

    # Create all tables
    EntityMeta.metadata.drop_all(
        bind=test_engine
    )  # Clean slate
    EntityMeta.metadata.create_all(bind=test_engine)

    return test_engine


@pytest.fixture(scope="function")
def db_session(engine):
    """Provide a clean database session for each test"""
    connection = engine.connect()
    transaction = connection.begin()
    Session = sessionmaker(bind=connection)
    session = Session()

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def sample_activity():
    """Create a sample activity for testing"""
    return {
        "name": "test_activity",
        "description": "Test activity description",
        "activity_schema": {
            "type": "object",
            "properties": {"notes": {"type": "string"}},
        },
        "icon": "📝",
        "color": "#000000",
    }


@pytest.fixture
def sample_moment(sample_activity):
    """Create a sample moment for testing"""
    return {
        "timestamp": datetime.now(timezone.utc),
        "data": {"notes": "Test moment"},
        "activity_data": sample_activity,
    }
