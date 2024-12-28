"""Redis configuration management."""

from dataclasses import dataclass
import os
from configs.Environment import get_env


@dataclass
class RedisConfig:
    """Redis connection configuration."""

    def __init__(self):
        """Initialize Redis configuration from environment."""
        # Allow direct environment variables to override settings
        self.host = os.getenv("REDIS_HOST") or get_env(
            "REDIS_HOST", "localhost"
        )
        self.port = int(
            os.getenv("REDIS_PORT")
            or get_env("REDIS_PORT", "6379")
        )
        self.db = int(
            os.getenv("REDIS_DB")
            or get_env("REDIS_DB", "0")
        )
        self.password = os.getenv(
            "REDIS_PASSWORD"
        ) or get_env("REDIS_PASSWORD", None)
        self.ssl = (
            str(
                os.getenv("REDIS_SSL")
                or get_env("REDIS_SSL", "false")
            ).lower()
            == "true"
        )
        self.timeout = int(
            os.getenv("REDIS_TIMEOUT")
            or get_env("REDIS_TIMEOUT", "10")
        )

        # Queue specific settings
        self.job_timeout = int(
            os.getenv("QUEUE_JOB_TIMEOUT")
            or get_env("QUEUE_JOB_TIMEOUT", "600")
        )
        self.job_ttl = int(
            os.getenv("QUEUE_JOB_TTL")
            or get_env("QUEUE_JOB_TTL", "3600")
        )
        self.queue_name = "note_enrichment"

    def get_connection_params(self) -> dict:
        """Get Redis connection parameters.

        Returns:
            Dict of connection parameters for Redis client

        Raises:
            ValueError: If port or db are invalid
        """
        try:
            return {
                "host": self.host,
                "port": self.port,
                "db": self.db,
                "password": self.password,
                "ssl": self.ssl,
                "socket_timeout": self.timeout,
                "decode_responses": True,
            }
        except ValueError as e:
            raise ValueError(
                f"Invalid Redis configuration: {str(e)}"
            )
