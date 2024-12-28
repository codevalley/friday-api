# Note Processing service

Below is a **step-by-step** guide on how to integrate **Redis RQ** into your existing architecture so that the **NoteService** can enqueue notes for asynchronous enrichment, and a separate worker process can consume and process those notes using your **RoboService** (LLM integration).

## Key Design Decisions

### Synchronous Processing
- The worker process is synchronous (no async/await needed)
- One job processed at a time per worker
- RQ handles job distribution and queuing
- RoboService calls are synchronous for simplicity and reliability
- Multiple workers can be spawned for parallel processing

### State Management
```python
class ProcessingStatus(str, Enum):
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    ERROR = "error"

    @classmethod
    def valid_transitions(cls) -> Dict[str, List[str]]:
        return {
            cls.QUEUED: [cls.PROCESSING],
            cls.PROCESSING: [cls.COMPLETED, cls.FAILED, cls.ERROR],
            cls.COMPLETED: [],  # Terminal state
            cls.FAILED: [],     # Terminal state
            cls.ERROR: []       # Terminal state
        }
```

---

## 1. Install and Configure Redis + RQ

### 1.1. Install Dependencies

1. **Redis Server**
   You'll need a running Redis instance. Install it locally or use a managed service.

2. **Python Packages**
   - `redis`: for Python Redis connectivity
   - `rq`: for the RQ job queue

```bash
pip install rq redis
```

### 1.2. Redis Configuration

Environment variables needed:
```env
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=  # Optional
REDIS_SSL=false  # Optional
REDIS_TIMEOUT=10  # Connection timeout
QUEUE_JOB_TIMEOUT=600  # Maximum time a job can run (10 minutes)
QUEUE_JOB_TTL=3600  # How long jobs can stay in queue (1 hour)
```

### 1.3. Create Redis Connection Manager

```python
# configs/RedisConnection.py
import os
from redis import Redis
from typing import Optional
from functools import lru_cache

class RedisConfig:
    def __init__(self):
        self.host = os.getenv("REDIS_HOST", "localhost")
        self.port = int(os.getenv("REDIS_PORT", 6379))
        self.db = int(os.getenv("REDIS_DB", 0))
        self.password = os.getenv("REDIS_PASSWORD")
        self.ssl = os.getenv("REDIS_SSL", "false").lower() == "true"
        self.timeout = int(os.getenv("REDIS_TIMEOUT", 10))

@lru_cache()
def get_redis_connection() -> Redis:
    config = RedisConfig()
    return Redis(
        host=config.host,
        port=config.port,
        db=config.db,
        password=config.password,
        ssl=config.ssl,
        socket_timeout=config.timeout,
        decode_responses=True
    )
```

---

## 2. Create a NoteProcessingQueue Wrapper

### 2.1. Queue Wrapper Class

```python
# queues/NoteProcessingQueue.py
from rq import Queue
from datetime import datetime
from configs.RedisConnection import get_redis_connection
from typing import Optional

class NoteProcessingQueue:
    """Wraps RQ queue for note enrichment tasks."""

    def __init__(self):
        self.redis_conn = get_redis_connection()
        self.queue = Queue(
            "note_enrichment",
            connection=self.redis_conn,
            default_timeout=os.getenv("QUEUE_JOB_TIMEOUT", 600)
        )

    def enqueue_process_note(self, note_id: int) -> Optional[str]:
        """Enqueue a job to process a note."""
        try:
            job = self.queue.enqueue(
                "note_worker.process_note_job",
                note_id,
                job_id=f"note_processing_{note_id}",
                meta={
                    'note_id': note_id,
                    'queued_at': datetime.utcnow().isoformat()
                }
            )
            return job.id
        except Exception as e:
            logger.error(f"Failed to enqueue note {note_id}: {str(e)}")
            return None

    def get_queue_health(self) -> dict:
        """Get queue health metrics."""
        return {
            "queue_size": len(self.queue),
            "failed_jobs": len(self.queue.failed_job_registry),
            "scheduled_jobs": len(self.queue.scheduled_job_registry)
        }
```

---

## 3. Worker Implementation

### 3.1. Worker Function

```python
# note_worker.py
import logging
from typing import Optional
from configs.Database import SessionLocal
from repositories.NoteRepository import NoteRepository
from services.RoboService import get_robo_service
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

class NoteProcessingError(Exception): pass
class RoboServiceError(NoteProcessingError): pass

def process_note_job(note_id: int):
    """Worker function that RQ calls to enrich a note."""
    start_time = datetime.now()
    logger.info(f"Starting processing of note {note_id}")

    try:
        with SessionLocal() as db:
            with db.begin():
                note_repo = NoteRepository(db)
                note = note_repo.get(note_id)

                if not note:
                    raise NoteProcessingError(f"Note {note_id} not found")

                # Update status to PROCESSING
                note_repo.update_status(note_id, ProcessingStatus.PROCESSING)

                # Process with RoboService
                robo_service = get_robo_service()
                try:
                    result = robo_service.enrich_note(note.content)
                except Exception as e:
                    raise RoboServiceError(f"RoboService failed: {str(e)}")

                # Update note with results
                note_repo.update(note_id, {
                    "enrichment_data": result,
                    "processing_status": ProcessingStatus.COMPLETED,
                    "processed_at": datetime.now(timezone.utc)
                })

    except Exception as e:
        logger.error(f"Failed to process note {note_id}: {str(e)}")
        with SessionLocal() as db:
            with db.begin():
                NoteRepository(db).update_status(
                    note_id,
                    ProcessingStatus.FAILED
                )
        raise

    finally:
        duration = (datetime.now() - start_time).total_seconds()
        logger.info(f"Note {note_id} processing completed in {duration}s")
```

### 3.2. Worker Process Management

Create a worker management script:

```python
# run_worker.py
import sys
import logging
from rq import Worker, Queue, Connection
from configs.RedisConnection import get_redis_connection
from configs.Logging import setup_logging

def run_worker():
    setup_logging()
    redis_conn = get_redis_connection()

    try:
        with Connection(redis_conn):
            worker = Worker(['note_enrichment'])
            worker.work(with_scheduler=True)
    except KeyboardInterrupt:
        logger.info("Worker shutting down gracefully...")
        sys.exit(0)

if __name__ == '__main__':
    run_worker()
```

---

## 4. Testing Strategy

### 4.1. Unit Tests

```python
# test_note_worker.py
def test_process_note_job_success(mocker):
    # Mock dependencies
    db_mock = mocker.patch('note_worker.SessionLocal')
    note_repo_mock = mocker.patch('note_worker.NoteRepository')
    robo_service_mock = mocker.patch('note_worker.get_robo_service')

    # Setup mocks
    note_mock = mocker.Mock(id=1, content="test content")
    note_repo_mock.return_value.get.return_value = note_mock
    robo_service_mock.return_value.enrich_note.return_value = {"enriched": True}

    # Run job
    process_note_job(1)

    # Verify
    note_repo_mock.return_value.update_status.assert_called_with(
        1, ProcessingStatus.PROCESSING
    )
    note_repo_mock.return_value.update.assert_called()
```

### 4.2. Integration Tests

```python
# test_note_processing_integration.py
import pytest
from rq import Queue
from time import sleep

def test_note_processing_flow(test_db, redis_conn):
    # Create a note
    note = create_test_note(test_db)

    # Enqueue for processing
    queue = Queue('note_enrichment', connection=redis_conn)
    job = queue.enqueue('note_worker.process_note_job', note.id)

    # Wait for processing
    max_wait = 30  # seconds
    while job.get_status() != 'finished' and max_wait > 0:
        sleep(1)
        max_wait -= 1

    # Verify results
    processed_note = get_note(test_db, note.id)
    assert processed_note.processing_status == ProcessingStatus.COMPLETED
    assert processed_note.enrichment_data is not None
```

---

## 5. Monitoring & Observability

### 5.1. Logging Configuration

```python
# configs/Logging.py
import logging
import json
from datetime import datetime

class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_data = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': record.levelname,
            'message': record.getMessage(),
            'module': record.module
        }
        if hasattr(record, 'note_id'):
            log_data['note_id'] = record.note_id
        return json.dumps(log_data)

def setup_logging():
    handler = logging.StreamHandler()
    handler.setFormatter(JSONFormatter())
    logging.getLogger().addHandler(handler)
    logging.getLogger().setLevel(logging.INFO)
```

### 5.2. Health Checks

```python
# monitoring/health.py
from rq import Worker
from configs.RedisConnection import get_redis_connection
from queues.NoteProcessingQueue import NoteProcessingQueue

def get_system_health():
    redis = get_redis_connection()
    queue = NoteProcessingQueue()

    return {
        "redis_connected": redis.ping(),
        "queue_stats": queue.get_queue_health(),
        "workers": {
            "count": len(Worker.all(redis)),
            "active": len([w for w in Worker.all(redis) if w.state == 'busy'])
        }
    }
```

---

## Implementation Order

1. Set up Redis and basic configuration
2. Implement NoteProcessingQueue wrapper
3. Create basic worker with logging
4. Add error handling and state management
5. Implement health checks and monitoring
6. Add comprehensive tests
7. Deploy and scale workers as needed

---

## Notes and Best Practices

1. **Synchronous Processing**
   - Keep worker code synchronous for simplicity
   - Use multiple workers for parallelism instead of async code
   - RQ handles the concurrent job distribution

2. **Error Handling**
   - Always update note status on failure
   - Log errors with context
   - Consider retry strategies for transient failures

3. **Monitoring**
   - Use structured logging
   - Implement health checks
   - Monitor queue size and processing times

4. **Scaling**
   - Run multiple workers for parallel processing
   - Monitor Redis memory usage
   - Consider job prioritization if needed

5. **Development Workflow**
   - Use local Redis for development
   - Run integration tests with temporary Redis instance
   - Monitor worker logs during development

---

## Feature Development Plan

### Epic 1: Core Infrastructure Setup
1. Redis Integration
   - [x] Install and configure Redis locally
   - [x] Set up Redis connection management
     - Created `RedisConfig` for configuration management
     - Implemented `RedisConnection` with health checks
     - Added error handling for connection failures
   - [x] Add Redis health check
   - [ ] Document Redis setup process

2. Queue Management
   - [x] Define queue service interface (`QueueService`)
   - [ ] Create NoteProcessingQueue implementation
   - [ ] Add queue monitoring
   - [ ] Set up queue configuration

### Epic 2: Worker Implementation
1. Basic Worker
   - [ ] Create worker process
   - [ ] Implement job processing logic
   - [ ] Add worker management script
   - [ ] Set up logging

2. Error Handling
   - [ ] Implement error types
   - [ ] Add status updates on failure
   - [ ] Set up error logging
   - [ ] Add transaction management

3. Monitoring
   - [ ] Add structured logging
   - [ ] Implement health checks
   - [ ] Create monitoring dashboard
   - [ ] Set up alerts

### Epic 3: Testing & Validation
1. Unit Tests
   - [ ] Test queue operations
   - [ ] Test worker processing
   - [ ] Test error handling
   - [ ] Test state transitions

2. Integration Tests
   - [ ] Set up test environment
   - [ ] Create end-to-end tests
   - [ ] Test failure scenarios
   - [ ] Validate monitoring

### Epic 4: Documentation & Developer Experience
1. Setup Guide
   - [ ] Write Redis setup instructions
   - [ ] Document worker deployment
   - [ ] Create troubleshooting guide
   - [ ] Add configuration reference

2. Monitoring Guide
   - [ ] Document available commands
   - [ ] Explain monitoring tools
   - [ ] Add debugging tips
   - [ ] Create runbook

---

## Developer Guide

### Getting Started

1. **Install Redis**
   ```bash
   # macOS
   brew install redis
   brew services start redis

   # Ubuntu
   sudo apt-get install redis-server
   sudo systemctl start redis
   ```

2. **Install Python Dependencies**
   ```bash
   pip install rq redis
   ```

3. **Configure Environment**
   ```bash
   # Copy example env file
   cp .env.example .env

   # Edit .env with your settings
   REDIS_HOST=localhost
   REDIS_PORT=6379
   ```

4. **Start Worker**
   ```bash
   # Basic worker
   rq worker note_enrichment

   # With scheduler (for monitoring)
   rq worker --with-scheduler note_enrichment
   ```

### Monitoring Jobs

1. **View Queue Information**
   ```bash
   # Show queue stats
   rq info

   # Show specific queue
   rq info note_enrichment
   ```

2. **Monitor Workers**
   ```bash
   # List workers
   rq workers

   # Watch worker logs
   rq worker note_enrichment --verbose
   ```

3. **Job Management**
   ```bash
   # List failed jobs
   rq list failed

   # List scheduled jobs
   rq list scheduled

   # View job details
   rq job <job_id>
   ```

### Troubleshooting

1. **Common Issues**
   - Redis connection refused
   - Worker not processing jobs
   - Jobs failing silently

2. **Debug Commands**
   ```bash
   # Check Redis connection
   redis-cli ping

   # Monitor Redis in real-time
   redis-cli monitor

   # Clear all queues (development only)
   rq empty note_enrichment
   ```

3. **Logging**
   - Worker logs: `logs/worker.log`
   - Redis logs: System dependent
   - Application logs: `logs/app.log`

### Best Practices

1. **Development**
   - Use local Redis instance
   - Run worker in verbose mode
   - Monitor queue sizes
   - Check failed jobs regularly

2. **Testing**
   - Mock Redis in unit tests
   - Use temporary Redis for integration tests
   - Test failure scenarios
   - Validate state transitions

3. **Deployment**
   - Use separate Redis instance
   - Run multiple workers
   - Monitor memory usage
   - Set up log rotation
