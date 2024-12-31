"""Redis configuration module."""

from pydantic_settings import BaseSettings
from typing import Optional


class RedisConfig(BaseSettings):
    """Redis configuration settings."""

    # Basic Redis connection settings
    host: str = "localhost"
    port: int = 6379
    db: int = 0
    password: Optional[str] = None
    ssl: bool = False
    timeout: int = 10
    decode_responses: bool = True

    # Queue specific settings
    job_timeout: int = 600  # 10 minutes
    job_ttl: int = 3600  # 1 hour
    queue_name: str = "note_enrichment"

    class Config:
        """Pydantic configuration."""

        env_prefix = "REDIS_"
        env_nested_delimiter = "__"

    def get_connection_params(self) -> dict:
        """Get Redis connection parameters.

        Returns:
            Dict of connection parameters for Redis client

        Raises:
            ValueError: If configuration is invalid
        """
        return {
            "host": self.host,
            "port": self.port,
            "db": self.db,
            "password": self.password,
            "ssl": self.ssl,
            "socket_timeout": self.timeout,
            "decode_responses": self.decode_responses,
        }