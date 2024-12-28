"""Redis connection management."""

from functools import lru_cache
from redis import Redis
from .RedisConfig import RedisConfig


class RedisConnectionError(Exception):
    """Raised when Redis connection fails."""

    pass


@lru_cache()
def get_redis_connection() -> Redis:
    """Get Redis connection with caching.

    Returns:
        Redis client instance

    Raises:
        RedisConnectionError: If connection fails
    """
    config = RedisConfig()
    try:
        params = config.get_connection_params()
        client = Redis(**params)
        # Test connection
        if not client.ping():
            raise RedisConnectionError("Redis ping failed")
        return client
    except Exception as e:
        raise RedisConnectionError(
            f"Failed to connect to Redis: {str(e)}"
        )


def check_redis_health() -> dict:
    """Check Redis connection health.

    Returns:
        Dict containing health check results
    """
    try:
        client = get_redis_connection()
        if not client.ping():
            return {
                "status": "unhealthy",
                "error": "Redis ping failed",
            }
        return {"status": "healthy", "error": None}
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}
