import logging
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.engine import Engine
from configs.Environment import get_environment_variables
import time

# Configure SQLAlchemy logging
logging.basicConfig()
# Log all SQL statements
logging.getLogger("sqlalchemy.engine").setLevel(
    logging.INFO
)
# For even more detailed logging including parameters:
logging.getLogger("sqlalchemy.engine").setLevel(
    logging.DEBUG
)

env = get_environment_variables()

# Construct Database URL from environment variables
DATABASE_URL = (
    f"{env.DATABASE_DIALECT}://"
    f"{env.DATABASE_USERNAME}:{env.DATABASE_PASSWORD}"
    f"@{env.DATABASE_HOSTNAME}:{env.DATABASE_PORT}"
    f"/{env.DATABASE_NAME}"
)

# Create engine with echo=True to enable SQL logging
engine = create_engine(
    DATABASE_URL,
    echo=True,  # Enable SQL echoing
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=10,
)


# Add timing logging for queries
@event.listens_for(Engine, "before_cursor_execute")
def before_cursor_execute(
    conn,
    cursor,
    statement,
    parameters,
    context,
    executemany,
):
    conn.info.setdefault("query_start_time", []).append(
        time.time()
    )
    logging.getLogger("sqlalchemy.engine").debug(
        "Start Query: %s", statement
    )


@event.listens_for(Engine, "after_cursor_execute")
def after_cursor_execute(
    conn,
    cursor,
    statement,
    parameters,
    context,
    executemany,
):
    total = time.time() - conn.info["query_start_time"].pop(
        -1
    )
    logging.getLogger("sqlalchemy.engine").debug(
        "Query Complete!"
    )
    logging.getLogger("sqlalchemy.engine").debug(
        "Total Time: %f", total
    )


SessionLocal = sessionmaker(
    autocommit=False, autoflush=False, bind=engine
)


def get_db_connection():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
