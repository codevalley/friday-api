from functools import lru_cache
from typing import Any, Optional
from pydantic_settings import BaseSettings
from pydantic import SecretStr, ConfigDict
from utils.env import get_env_filename


def get_env(key: str, default: Any = None) -> Any:
    """Get environment variable with default value.

    Args:
        key: Environment variable key
        default: Default value if not found

    Returns:
        Environment variable value or default
    """
    env = get_environment_variables()
    return getattr(env, key, default)


class EnvironmentSettings(BaseSettings):
    # API Configuration
    API_VERSION: str
    APP_NAME: str
    DEBUG_MODE: bool

    # Database Configuration
    DATABASE_DIALECT: str
    DATABASE_DRIVER: str = (
        "+pymysql"  # Default to pymysql for MySQL
    )
    DATABASE_HOSTNAME: str
    DATABASE_NAME: str
    DATABASE_PASSWORD: str
    DATABASE_PORT: int
    DATABASE_USERNAME: str

    # Optional Robo Configuration
    ROBO_API_KEY: SecretStr | None = None
    ROBO_MODEL_NAME: str | None = None
    ROBO_MAX_RETRIES: int = 3
    ROBO_TIMEOUT_SECONDS: int = 30
    ROBO_TEMPERATURE: float = 0.7
    ROBO_MAX_TOKENS: int = 150
    ROBO_NOTE_ENRICHMENT_PROMPT: str = (
        "You are a note formatting assistant. "
        "Your task is to:\n"
        "1. Extract a concise title (<50 chars)\n"
        "2. Format the content in clean markdown\n"
        "3. Use appropriate formatting (bold, italic, lists)\n"
        "4. Keep the content concise but complete"
    )

    # Redis Configuration
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: Optional[str] = None
    REDIS_SSL: bool = False
    REDIS_TIMEOUT: int = 10
    QUEUE_JOB_TIMEOUT: int = 600
    QUEUE_JOB_TTL: int = 3600

    model_config = ConfigDict(
        env_file=get_env_filename(),
        env_file_encoding="utf-8",
        extra="allow",  # Allow extra fields in environment
    )


@lru_cache
def get_environment_variables() -> EnvironmentSettings:
    """Get environment variables."""
    return EnvironmentSettings()
