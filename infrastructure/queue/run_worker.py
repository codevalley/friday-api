"""Worker process runner script."""

import sys
import logging
from rq import Worker, Queue

from configs.Logging import configure_logging
from configs.queue_dependencies import get_redis_connection


def run_worker():
    """Run the worker process.

    This function:
    1. Sets up logging
    2. Creates Redis connection
    3. Starts RQ worker process listening to multiple queues
    4. Handles graceful shutdown
    """
    # Configure logging
    configure_logging()
    logger = logging.getLogger(__name__)
    logger.info("Starting worker process")

    try:
        # Get Redis connection and config
        redis_conn = get_redis_connection()

        # Start worker with multiple queues
        queues = [
            Queue("note_enrichment", connection=redis_conn),
            Queue("activity_schema", connection=redis_conn),
        ]
        worker = Worker(queues, connection=redis_conn)
        logger.info(
            f"Worker listening on queues: {[q.name for q in queues]}"
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
