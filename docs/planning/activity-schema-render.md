# Activity Schema Render Implementation Plan

## Overview

This document outlines the plan to implement schema rendering for activities, similar to note enrichment. The system will analyze activity schemas using AI to determine optimal rendering strategies.

## Current System Analysis

### Relevant Components
1. **RoboService Interface**
   - Defines abstract methods for AI processing

   - Currently handles note enrichment
   - Implemented by OpenAIService

2. **Worker System**
   - Uses RQ for background processing
   - Currently processes notes
   - Defined in run_worker.py

3. **Activity Domain**
   - Rich domain model with schema validation
   - ORM implementation with comprehensive tests
   - No current async processing capabilities

## Database Changes

### 1. Update Activity Table Schema

```sql
ALTER TABLE activities ADD COLUMN
    processing_status ENUM(
        'NOT_PROCESSED',
        'PENDING',
        'PROCESSING',
        'COMPLETED',
        'FAILED',
        'SKIPPED'
    ) NOT NULL DEFAULT 'NOT_PROCESSED';

ALTER TABLE activities ADD COLUMN
    schema_render JSON NULL,
    processed_at TIMESTAMP NULL;
```

## Implementation Plan

### Epic 1: Database and Model Updates

#### Task 1: Update Database Schema
- [ ] Add migration script for new columns
- [ ] Update init_database.sql
- [ ] Add rollback script

#### Task 2: Update Activity Models
- [ ] Update ActivityModel.py with new fields:
```python:orm/ActivityModel.py
class Activity(EntityMeta):
    # ... existing fields ...

    processing_status: Mapped[str] = Column(
        Enum(
            'NOT_PROCESSED',
            'PENDING',
            'PROCESSING',
            'COMPLETED',
            'FAILED',
            'SKIPPED'
        ),
        nullable=False,
        default='NOT_PROCESSED'
    )
    schema_render: Mapped[Optional[Dict[str, Any]]] = Column(
        JSON,
        nullable=True
    )
    processed_at: Mapped[Optional[datetime]] = Column(
        DateTime,
        nullable=True
    )
```

- [ ] Update domain/activity.py to include new fields
- [ ] Update related schemas and tests

### Epic 2: Queue Integration

#### Task 1: Update Queue Service Interface
```python:domain/ports/QueueService.py
class QueueService(ABC):
    """Interface for queue operations."""

    @abstractmethod
    def enqueue_note(self, note_id: int) -> Optional[str]:
        """Enqueue a note for processing.

        Args:
            note_id: ID of the note to process

        Returns:
            Optional[str]: Job ID if enqueued successfully, None otherwise
        """
        pass

    @abstractmethod
    def enqueue_activity(self, activity_id: int) -> Optional[str]:
        """Enqueue an activity for schema render processing.

        Args:
            activity_id: ID of the activity to process

        Returns:
            Optional[str]: Job ID if enqueued successfully, None otherwise
        """
        pass

    @abstractmethod
    def get_job_status(self, job_id: str) -> Dict[str, Any]:
        """Get status of a job."""
        pass

    @abstractmethod
    def get_queue_health(self) -> Dict[str, Any]:
        """Get health metrics for the queue."""
        pass
```

#### Task 2: Update RQ Queue Implementation
```python:infrastructure/queue/RQNoteQueue.py
class RQNoteQueue(QueueService):
    def __init__(self, queue: Queue):
        self.queue = queue

    def enqueue_note(self, note_id: int) -> Optional[str]:
        """Enqueue a note for processing."""
        try:
            job = self.queue.enqueue(
                "infrastructure.queue.note_worker.process_note_job",
                args=(note_id,),
                job_timeout="10m",
                result_ttl=24 * 60 * 60,  # Keep results for 24 hours
                meta={
                    "note_id": note_id,
                    "queued_at": datetime.now(UTC).isoformat(),
                },
            )
            return job.id if job else None
        except Exception:
            return None

    def enqueue_activity(self, activity_id: int) -> Optional[str]:
        """Enqueue an activity for schema render processing."""
        try:
            job = self.queue.enqueue(
                "infrastructure.queue.activity_worker.process_activity_job",
                args=(activity_id,),
                job_timeout="10m",
                result_ttl=24 * 60 * 60,  # Keep results for 24 hours
                meta={
                    "activity_id": activity_id,
                    "queued_at": datetime.now(UTC).isoformat(),
                },
            )
            return job.id if job else None
        except Exception:
            return None

    # Existing methods remain unchanged
    def get_job_status(self, job_id: str) -> Dict[str, Any]:
        """Get status of a job."""
        try:
            job = Job.fetch(job_id, connection=self.queue.connection)
            return {
                "status": job.get_status(),
                "created_at": job.created_at.isoformat() if job.created_at else None,
                "ended_at": job.ended_at.isoformat() if job.ended_at else None,
                "exc_info": job.exc_info,
                "meta": job.meta,
            }
        except Exception:
            return {"status": "not_found"}

    def get_queue_health(self) -> Dict[str, Any]:
        """Get health metrics for the queue."""
        try:
            return {
                "jobs_total": len(self.queue),
                "workers": len(self.queue.workers),
                "is_empty": self.queue.is_empty,
            }
        except Exception:
            return {
                "jobs_total": 0,
                "workers": 0,
                "is_empty": True,
                "error": "Failed to get queue metrics",
            }
```

Key Changes:
1. Aligned method signatures with existing `RQNoteQueue` implementation
2. Consistent error handling and return types
3. Maintained the same job metadata pattern
4. Kept existing health check and status methods

The rest of the epics remain unchanged.

### Epic 3: RoboService Updates

#### Task 1: Update RoboService Interface
```python:domain/robo.py
class RoboService(ABC):
    # ... existing methods ...

    @abstractmethod
    def analyze_activity_schema(
        self,
        schema: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Analyze activity schema and suggest rendering strategy.

        Args:
            schema: JSON Schema defining activity data structure

        Returns:
            Dict with rendering suggestions
        """
        pass
```

#### Task 2: Update OpenAI Implementation
```python:services/OpenAIService.py
ANALYZE_SCHEMA_FUNCTION = {
    "name": "analyze_schema",
    "description": "Analyze JSON schema and suggest rendering strategy",
    "parameters": {
        "type": "object",
        "properties": {
            "render_type": {
                "type": "string",
                "description": "Suggested rendering type",
                "enum": ["form", "table", "timeline", "cards"]
            },
            "layout": {
                "type": "object",
                "description": "Layout suggestions"
            },
            "field_groups": {
                "type": "array",
                "description": "Suggested field groupings"
            }
        },
        "required": ["render_type", "layout"]
    }
}

class OpenAIService(RoboService):
    # ... existing methods ...

    def analyze_activity_schema(
        self,
        schema: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Analyze schema using OpenAI."""
        try:
            response = self.client.chat.completions.create(
                model=self.config.model_name,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a UI/UX expert. Analyze JSON schemas and suggest optimal rendering strategies.",
                    },
                    {
                        "role": "user",
                        "content": f"Analyze this schema and suggest how to render it: {json.dumps(schema)}",
                    }
                ],
                tools=[{"type": "function", "function": ANALYZE_SCHEMA_FUNCTION}],
                tool_choice={"type": "function", "function": {"name": "analyze_schema"}},
            )

            # Extract and validate response
            tool_call = response.choices[0].message.tool_calls[0]
            result = json.loads(tool_call.function.arguments)

            return result

        except Exception as e:
            logger.error(f"Error analyzing schema: {str(e)}")
            raise RoboAPIError(f"Failed to analyze schema: {str(e)}")
```

### Epic 4: Worker Implementation

#### Task 1: Create Activity Worker
```python:infrastructure/queue/activity_worker.py
"""Worker for processing activity schemas."""

import logging
from datetime import datetime, UTC
from typing import Dict, Any

from sqlalchemy.orm import Session

from configs.Database import get_db_connection
from configs.RoboConfig import get_robo_service
from domain.exceptions import RoboAPIError
from orm.ActivityModel import Activity

logger = logging.getLogger(__name__)

def process_activity(
    activity_id: int,
    user_id: str,
    activity_schema: Dict[str, Any]
) -> None:
    """Process an activity's schema for rendering suggestions.

    Args:
        activity_id: ID of activity to process
        user_id: Owner of the activity
        activity_schema: Schema to analyze
    """
    logger.info(f"Processing activity {activity_id}")

    # Get database session
    db = next(get_db_connection())

    try:
        # Update status to PROCESSING
        activity = db.query(Activity).filter(
            Activity.id == activity_id,
            Activity.user_id == user_id
        ).first()

        if not activity:
            logger.error(f"Activity {activity_id} not found")
            return

        activity.processing_status = 'PROCESSING'
        db.commit()

        # Get RoboService and process
        robo_service = get_robo_service()
        render_suggestion = robo_service.analyze_activity_schema(
            activity_schema
        )

        # Update activity with results
        activity.schema_render = render_suggestion
        activity.processing_status = 'COMPLETED'
        activity.processed_at = datetime.now(UTC)
        db.commit()

        logger.info(f"Successfully processed activity {activity_id}")

    except RoboAPIError as e:
        logger.error(f"RoboAPI error processing activity {activity_id}: {str(e)}")
        activity.processing_status = 'FAILED'
        db.commit()
    except Exception as e:
        logger.error(f"Error processing activity {activity_id}: {str(e)}")
        activity.processing_status = 'FAILED'
        db.commit()
    finally:
        db.close()
```

#### Task 2: Update Worker Runner
- [ ] Modify run_worker.py to handle both note and activity processing
- [ ] Add proper error handling and logging

### Epic 5: Service Layer Integration

#### Task 1: Update ActivityService
```python:services/ActivityService.py
class ActivityService:
    def __init__(
        self,
        repository: ActivityRepository,
        queue_service: ActivityQueueService
    ):
        self.repository = repository
        self.queue_service = queue_service

    def create_activity(self, data: ActivityData) -> ActivityData:
        """Create activity and queue for processing."""
        activity = self.repository.create(data)

        # Queue for processing
        self.queue_service.queue_activity_processing(
            activity_id=activity.id,
            user_id=activity.user_id,
            activity_schema=activity.activity_schema
        )

        return activity
```

### Epic 6: Testing

#### Task 1: Unit Tests
- [ ] Test new activity model fields
- [ ] Test queue service
- [ ] Test worker processing
- [ ] Test RoboService schema analysis

#### Task 2: Integration Tests
- [ ] Test end-to-end activity creation and processing
- [ ] Test error handling and status updates
- [ ] Test concurrent processing

### Testing Activity Schema Rendering

#### Unit Tests
- Test the new fields in the `Activity` model.
- Test the `enqueue_activity` method in the `RQNoteQueue` class.
- Test the `analyze_activity_schema` method in the `OpenAIService` class.

#### Integration Tests
- Add integration tests for end-to-end activity creation and processing.
- Test error handling and status updates.
- Test concurrent processing.

## Timeline

1. **Week 1**: Database and Model Updates
   - Database migration
   - Model updates
   - Basic tests

2. **Week 2**: Queue and RoboService
   - Queue service implementation
   - RoboService updates
   - OpenAI integration

3. **Week 3**: Worker Implementation
   - Activity worker
   - Worker runner updates
   - Service integration

4. **Week 4**: Testing and Documentation
   - Unit tests
   - Integration tests
   - Documentation updates

## Notes

1. **Reuse Existing Infrastructure**:
   - Use existing worker infrastructure
   - Leverage RoboService pattern
   - Follow note enrichment patterns

2. **Error Handling**:
   - Implement proper retries
   - Handle API rate limits
   - Log failures appropriately

3. **Performance Considerations**:
   - Monitor queue length
   - Track processing times
   - Consider batch processing

4. **Future Improvements**:
   - Cache common rendering patterns
   - Implement schema versioning
   - Add rendering preview capability
