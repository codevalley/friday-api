from functools import lru_cache
import os

from pydantic_settings import BaseSettings


@lru_cache
def get_env_filename():
    runtime_env = os.getenv("ENV")
    return f".env.{runtime_env}" if runtime_env else ".env"


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
    ROBO_API_KEY: str | None = None
    ROBO_MODEL_NAME: str | None = None
    ROBO_MAX_RETRIES: int = 3
    ROBO_TIMEOUT_SECONDS: int = 30
    ROBO_TEMPERATURE: float = 0.7

    class Config:
        env_file = get_env_filename()
        env_file_encoding = "utf-8"
        extra = "allow"  # Allow extra fields in environment


@lru_cache
def get_environment_variables():
    return EnvironmentSettings()
