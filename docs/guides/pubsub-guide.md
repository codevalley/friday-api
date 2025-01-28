# Redis Pub/Sub and Processing Guide

This guide covers the setup, monitoring, and debugging of the note and activity schema processing system using Redis and RQ (Redis Queue).

## Setup Guide

### Prerequisites

1. **Redis Installation**
```bash
# macOS
brew install redis
brew services start redis

# Ubuntu
sudo apt-get install redis-server
sudo systemctl start redis
```

2. **Python Dependencies**
```bash
pip install rq redis
```

### Configuration

1. **Environment Variables**
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

### Worker Setup

1. **Starting Workers**

There are two ways to start the workers:

#### A. Using the run_worker.py script (Recommended for Production)
```bash
# Using the run_worker.py script (includes logging and error handling)
PYTHONPATH=$PYTHONPATH:. python -m infrastructure.queue.run_worker

# For macOS, include OBJC_DISABLE_INITIALIZE_FORK_SAFETY
OBJC_DISABLE_INITIALIZE_FORK_SAFETY=YES PYTHONPATH=$PYTHONPATH:. python -m infrastructure.queue.run_worker
```
This method:
- Automatically configures logging
- Handles all three queues (note_enrichment, activity_schema, task_enrichment)
- Provides better error handling and shutdown management
- Uses settings from your environment configuration

#### B. Using RQ CLI directly (Good for Development)
```bash
# Start a single worker for all queues
PYTHONPATH=$PYTHONPATH:. rq worker note_enrichment activity_schema task_enrichment --url redis://localhost:6379

# for mac include this
export OBJC_DISABLE_INITIALIZE_FORK_SAFETY=YES
# here is the full command to run the worker
OBJC_DISABLE_INITIALIZE_FORK_SAFETY=YES PYTHONPATH=$PYTHONPATH:. rq worker note_enrichment activity_schema task_enrichment --url redis://localhost:6379

# Start dedicated workers for each queue
rq worker note_enrichment --url redis://localhost:6379  # Note processing only
rq worker activity_schema --url redis://localhost:6379  # Activity schema only
rq worker task_enrichment --url redis://localhost:6379  # Task processing only

# Start multiple workers
rq worker note_enrichment activity_schema task_enrichment -c worker_settings --count 3
```

2. **Worker Configuration**
Create `worker_settings.py`:
```python
REDIS_URL = 'redis://localhost:6379/0'
QUEUES = [
    'note_enrichment',
    'activity_schema',
    'task_enrichment'
]  # List all queues
JOB_TIMEOUT = '10m'
RESULT_TTL = 24 * 60 * 60  # 24 hours
```

## Monitoring and Debugging

### Health Checks

The system includes built-in health checks accessible through the monitoring API:

```python
from monitoring.health import get_system_health

health_status = get_system_health()
# Returns:
# {
#     "redis_connected": true,
#     "queue_stats": {
#         "note_enrichment": {
#             "queue_size": 10,
#             "failed_jobs": 0,
#             "scheduled_jobs": 5
#         },
#         "activity_schema": {
#             "queue_size": 5,
#             "failed_jobs": 0,
#             "scheduled_jobs": 2
#         },
#         "task_enrichment": {
#             "queue_size": 8,
#             "failed_jobs": 0,
#             "scheduled_jobs": 3
#         }
#     },
#     "workers": {
#         "count": 3,
#         "active": 2
#     }
# }
```

### Logging

The system uses structured JSON logging for better observability:

```python
# Note processing log
{
    "timestamp": "2024-01-20T10:30:00Z",
    "level": "INFO",
    "message": "Processing note 123",
    "module": "note_worker",
    "note_id": 123
}

# Activity schema processing log
{
    "timestamp": "2024-01-20T10:30:00Z",
    "level": "INFO",
    "message": "Processing activity schema 456",
    "module": "activity_worker",
    "activity_id": 456
}

# Task processing log
{
    "timestamp": "2024-01-20T10:30:00Z",
    "level": "INFO",
    "message": "Processing task 789",
    "module": "task_worker",
    "task_id": 789
}
```

### Queue Monitoring

1. **Queue Statistics**
```python
from infrastructure.queue.RQNoteQueue import RQNoteQueue

queue = RQNoteQueue(redis_queue)
stats = queue.get_queue_health()
```

2. **Job Status Tracking**
```python
# Check status of any job
status = queue.get_job_status(job_id)
# Returns job status, timing, and error information
```

### Error Handling

The system implements a three-tier error handling strategy:

1. **Immediate Retry**: For transient errors
2. **Exponential Backoff**: For resource availability issues
3. **Dead Letter Queue**: For persistent failures

Error states are tracked in the `ProcessingStatus` enum:
- `PENDING`: Initial state
- `PROCESSING`: Currently being processed
- `COMPLETED`: Successfully processed
- `FAILED`: Processing failed after retries
- `ERROR`: System-level error occurred

### Debugging Tips

1. **Check Worker Logs**
```bash
# View logs for all workers
tail -f rq.log

# Filter for specific IDs
grep "note_id=123" rq.log
grep "activity_id=456" rq.log
grep "task_id=789" rq.log
```

2. **Monitor Queue Size**
```bash
# Using redis-cli
redis-cli
> LLEN rq:queue:note_enrichment
> LLEN rq:queue:activity_schema
> LLEN rq:queue:task_enrichment
```

3. **Inspect Failed Jobs**
```bash
# List failed jobs
rq info --only-failures

# Get failure details
rq info -j <job_id>
```

4. **Common Issues and Solutions**

- **Queue Backing Up**
  - Check worker process health
  - Verify Redis connection
  - Monitor system resources

- **Processing Failures**
  - Check RoboService connectivity
  - Verify input data validity
  - Review rate limiting status

- **Worker Crashes**
  - Check memory usage
  - Review error logs
  - Verify environment configuration

## Best Practices

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

3. **Production**
   - Use separate Redis instance
   - Run multiple workers
   - Monitor memory usage
   - Set up log rotation

## Troubleshooting Guide

### Common Error Messages

1. **Redis Connection Errors**
```
Error: Error 111 connecting to localhost:6379. Connection refused.
Solution: Verify Redis is running and accessible
```

2. **Job Timeout Errors**
```
Error: Job exceeded maximum timeout value (600 seconds)
Solution: Adjust QUEUE_JOB_TIMEOUT or optimize processing
```

3. **Worker Memory Issues**
```
Error: Worker exceeded memory limit
Solution: Check for memory leaks, adjust worker count
```

### Performance Optimization

1. **Queue Performance**
   - Monitor queue length for each queue type
   - Adjust worker count based on load
   - Consider dedicated workers for high-volume queues

2. **Worker Performance**
   - Profile memory usage
   - Monitor processing times
   - Optimize batch sizes

3. **System Resources**
   - Monitor Redis memory usage
   - Track CPU utilization
   - Watch network connectivity

## Queue-Specific Guidelines

### Note Enrichment Queue
- Used for processing and enriching notes
- Handles markdown formatting and title extraction
- Typical job duration: 2-5 seconds

### Activity Schema Queue
- Used for analyzing and rendering activity schemas
- Handles schema validation and UI generation
- Typical job duration: 1-3 seconds

### Task Enrichment Queue
- Used for processing and enriching tasks
- Handles content formatting, title extraction, and metadata generation
- Extracts task complexity and estimated time
- Typical job duration: 2-5 seconds

### Common Issues and Solutions

1. **Job Timeouts**
   - Default timeout is 10 minutes
   - Increase for complex tasks:
     ```python
     # In worker_settings.py
     TIMEOUTS = {
         'note_enrichment': '5m',
         'activity_schema': '3m',
         'task_enrichment': '5m'
     }
     ```

2. **Queue Backlog**
   - Monitor queue sizes
   - Add more workers if consistently high
   - Consider dedicated workers per queue

3. **Failed Jobs**
   - Check logs for error patterns
   - Implement retry logic
   - Set up alerts for high failure rates
