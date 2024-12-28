"""Queue dependencies configuration."""

from functools import lru_cache
from rq import Queue

from configs.redis.RedisConfig import RedisConfig
from configs.redis.RedisConnection import (
    get_redis_connection,
)
from domain.ports.QueueService import QueueService
from infrastructure.queue.RQNoteQueue import RQNoteQueue


@lru_cache()
def get_redis_config() -> RedisConfig:
    """Get Redis configuration."""
    return RedisConfig()


@lru_cache()
def get_queue() -> Queue:
    """Get RQ queue instance."""
    redis_config = get_redis_config()
    redis_conn = get_redis_connection(redis_config)
    return Queue("note_processing", connection=redis_conn)


@lru_cache()
def get_queue_service() -> QueueService:
    """Get queue service instance.

    This function binds the QueueService interface to the
    RQNoteQueue implementation.
    """
    queue = get_queue()
    return RQNoteQueue(queue=queue)
