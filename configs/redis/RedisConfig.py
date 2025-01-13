"""Redis configuration module."""

from pydantic_settings import BaseSettings
from typing import Optional, List


class RedisConfig(BaseSettings):
    """Redis configuration."""

    # Basic Redis connection settings
    host: str = "localhost"
    port: int = 6379
    db: int = 0
    password: Optional[str] = None
    ssl: bool = False
    timeout: int = 10
    decode_responses: bool = False

    # Queue specific settings
    job_timeout: int = 600  # 10 minutes
    job_ttl: int = 3600  # 1 hour
    queue_names: List[str] = [
        "note_enrichment",
        "activity_schema",
    ]

    class Config:
        """Pydantic configuration."""

        env_prefix = "REDIS_"
        env_nested_delimiter = "__"

    def __init__(self, **kwargs):
        """Initialize Redis configuration."""
        super().__init__(**kwargs)
        # Convert empty password to None
        if self.password == "":
            self.password = None

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
