"""Redis connection module."""

from redis import Redis

from configs.redis.RedisConfig import RedisConfig


def get_redis_connection(config: RedisConfig) -> Redis:
    """Get Redis connection.

    Args:
        config: Redis configuration

    Returns:
        Redis: Redis connection instance
    """
    return Redis(
        host=config.host,
        port=config.port,
        db=config.db,
        password=config.password,
        ssl=config.ssl,
        socket_timeout=config.timeout,
        decode_responses=True,
    )
