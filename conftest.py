"""Configure pytest for the project."""

import os
import sys
import pytest

# Add project root to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)


@pytest.fixture(autouse=True)
def setup_test_env():
    """Set up test environment variables."""
    # Store original environment
    original_env = dict(os.environ)

    # Set test environment variables
    os.environ.update(
        {
            "ENV": "test",
            "API_VERSION": "v1",
            "APP_NAME": "friday-api-test",
            "DEBUG_MODE": "true",
            # Database config
            "DATABASE_DIALECT": "sqlite",
            "DATABASE_DRIVER": "",
            "DATABASE_HOSTNAME": ":memory:",
            "DATABASE_NAME": "test_db",
            "DATABASE_PASSWORD": "test",
            "DATABASE_PORT": "0",
            "DATABASE_USERNAME": "test",
            # Robo config
            "ROBO_API_KEY": "test-key",
            "ROBO_MODEL_NAME": "test-model",
            "ROBO_MAX_RETRIES": "3",
            "ROBO_TIMEOUT_SECONDS": "30",
            "ROBO_TEMPERATURE": "0.7",
            "ROBO_MAX_TOKENS": "150",
            "ROBO_NOTE_ENRICHMENT_PROMPT": (
                "You are a note formatting assistant. "
                "Your task is to:\n"
                "1. Extract a concise title (<50 chars)\n"
                "2. Format the content in clean markdown\n"
                "3. Use appropriate formatting (bold, italic, lists)\n"
                "4. Keep the content concise but complete"
            ),
            # Redis config
            "REDIS_HOST": "localhost",
            "REDIS_PORT": "6379",
            "REDIS_DB": "0",
            "REDIS_PASSWORD": "",
            "REDIS_SSL": "false",
            "REDIS_TIMEOUT": "10",
            "QUEUE_JOB_TIMEOUT": "600",
            "QUEUE_JOB_TTL": "3600",
        }
    )

    yield

    # Restore original environment
    os.environ.clear()
    os.environ.update(original_env)
