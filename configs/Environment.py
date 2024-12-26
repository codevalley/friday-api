from functools import lru_cache
from pydantic_settings import BaseSettings
from pydantic import SecretStr, ConfigDict
from utils.env import get_env_filename


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

    model_config = ConfigDict(
        env_file=get_env_filename(),
        env_file_encoding="utf-8",
        extra="allow",  # Allow extra fields in environment
    )


@lru_cache
def get_environment_variables() -> EnvironmentSettings:
    """Get environment variables."""
    return EnvironmentSettings()
