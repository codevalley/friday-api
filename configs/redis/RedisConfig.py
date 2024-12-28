"""Redis configuration module."""

from pydantic_settings import BaseSettings


class RedisConfig(BaseSettings):
    """Redis configuration settings."""

    host: str = "localhost"
    port: int = 6379
    db: int = 0
    password: str | None = None
    ssl: bool = False
    timeout: int = 5

    class Config:
        """Pydantic configuration."""

        env_prefix = "REDIS_"
