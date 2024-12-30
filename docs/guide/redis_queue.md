# Redis Queue (RQ) System Guide

## Overview
Redis Queue (RQ) is a Python library for queueing jobs and processing them in the background with workers. Our system uses RQ for asynchronous note processing.

## Key Components

### 1. Queue
- A list in Redis where jobs are stored
- In our system: `note_enrichment` queue
- Stores jobs waiting to be processed

### 2. Job
- A unit of work to be executed
- Contains:
  - Function to execute
  - Arguments
  - Metadata (timing, status)
- Example: Processing a note's content

### 3. Worker
- Process that executes jobs from the queue
- Can run multiple workers for parallel processing
- Handles job failures and retries

### 4. Redis
- Backend storage
- Stores queues, jobs, and worker information
- Provides persistence and reliability

## Implementation

### Queue Setup
```python
# RQNoteQueue.py
def enqueue_note(self, note_id: int):
    job = self.queue.enqueue(
        "infrastructure.queue.note_worker.process_note_job",  # Function to execute
        args=(note_id,),                                      # Arguments
        job_timeout="10m",                                    # Max execution time
        result_ttl=24 * 60 * 60,                             # Result retention
    )
```

### Job Processing
```python
# note_worker.py
def process_note_job(note_id: int):
    # 1. Get note from database
    # 2. Update status to PROCESSING
    # 3. Process note content
    # 4. Update status to COMPLETED
```

## System Flow
```
[API] ---> [RQNoteQueue] ---> [Redis Queue] ---> [Worker] ---> [Database]
   |           |                   |               |              |
   |           |                   |               |              |
Creates      Adds               Stores          Processes      Updates
Note         Job               Job Data         Note          Status
```

## Redis Data Structure
```
Redis Keys:
- rq:queue:note_enrichment     # List of job IDs
- rq:job:job_id               # Hash with job details
- rq:workers                  # Set of worker IDs
```

## Common Operations

### Monitor Queue
```bash
# Check queue length
redis-cli LLEN rq:queue:note_enrichment

# View all jobs
redis-cli LRANGE rq:queue:note_enrichment 0 -1

# Check active workers
redis-cli SMEMBERS rq:workers
```

### Start Worker
```bash
# Start a worker process
PYTHONPATH=$PYTHONPATH:. rq worker note_enrichment --url redis://localhost:6379
```

## Benefits

1. **Asynchronous Processing**
   - Notes are processed in background
   - API remains responsive

2. **Reliability**
   - Jobs persist in Redis
   - Survive worker crashes
   - Automatic retries

3. **Scalability**
   - Run multiple workers
   - Distribute load

4. **Monitoring**
   - Track job status
   - Queue health metrics
   - Worker status

## Best Practices

1. **Job Timeout**
   - Set appropriate timeouts
   - Handle long-running jobs

2. **Error Handling**
   - Implement retries
   - Log failures
   - Monitor errors

3. **Worker Management**
   - Monitor worker health
   - Scale based on load
   - Regular maintenance
