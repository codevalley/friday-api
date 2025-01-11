"""Queue dependencies configuration."""

from functools import lru_cache
from rq import Queue
from typing import Dict

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
def get_queues() -> Dict[str, Queue]:
    """Get RQ queue instances.

    Returns:
        Dict mapping queue names to Queue instances
    """
    redis_config = get_redis_config()
    redis_conn = get_redis_connection()
    return {
        name: Queue(name, connection=redis_conn)
        for name in redis_config.queue_names
    }


@lru_cache()
def get_queue_service() -> QueueService:
    """Get queue service instance.

    This function binds the QueueService interface to the
    RQNoteQueue implementation.
    """
    queues = get_queues()
    # Use note_enrichment queue as primary for backward compatibility
    return RQNoteQueue(queue=queues["note_enrichment"])
