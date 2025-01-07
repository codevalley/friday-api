"""Worker process runner script."""

import sys
import logging
from rq import Worker, Queue, Connection

from configs.Logging import configure_logging
from configs.queue_dependencies import (
    get_redis_connection,
    get_redis_config,
)


def run_worker():
    """Run the worker process.

    This function:
    1. Sets up logging
    2. Creates Redis connection
    3. Starts RQ worker process
    4. Handles graceful shutdown
    """
    # Configure logging
    configure_logging()
    logger = logging.getLogger(__name__)
    logger.info("Starting note and activity processing worker")

    try:
        # Get Redis connection and config
        redis_conn = get_redis_connection()
        redis_config = get_redis_config()

        # Start worker
        with Connection(redis_conn):
            note_queue = Queue(redis_config.queue_name)
            activity_queue = Queue("activity_processing")
            worker = Worker([note_queue, activity_queue])
            logger.info(
                f"Worker listening on queues: {note_queue.name}, {activity_queue.name}"
            )
            worker.work(with_scheduler=True)

    except KeyboardInterrupt:
        logger.info(
            "Received shutdown signal, stopping worker..."
        )
        sys.exit(0)
    except Exception as e:
        logger.error(f"Worker failed: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    run_worker()
