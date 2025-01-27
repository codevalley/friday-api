# Task Enrichment Implementation Plan

This document outlines the plan to restructure the task model to align with the note model structure, introducing content enrichment and processing capabilities.

## Current Structure
Currently, tasks have:
- `title`: Required field for task name
- `description`: Required field for task details
- `status`: TaskStatus enum (TODO, IN_PROGRESS, DONE) for task progress tracking
- Other metadata fields (priority, due_date, etc.)

## Target Structure
We will move to a structure where:
- `content`: Main field containing the task content (replaces title + description)
- `status`: TaskStatus enum (TODO, IN_PROGRESS, DONE) for task progress tracking
- `enrichment_data`: JSON field containing processed data including:
  - `title`: Extracted/generated title
  - `formatted`: Formatted content in markdown
  - `tokens_used`: Number of tokens used in processing
  - `model_name`: Name of the model used for processing
  - `created_at`: Timestamp of when enrichment was performed
  - `metadata`: Additional metadata from processing
- `processing_status`: ProcessingStatus enum (reusing from domain/values.py) for content processing state
- `processed_at`: Timestamp of last processing

## Implementation Steps

### 1. Database Changes

Create tables with new structure (no migration needed as we'll recreate from scratch):
```sql
-- tasks table structure
CREATE TABLE tasks (
    id SERIAL PRIMARY KEY,
    content TEXT NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'todo',
    priority VARCHAR(20) NOT NULL DEFAULT 'medium',
    processing_status VARCHAR(20) NOT NULL DEFAULT 'pending',
    enrichment_data JSON,
    processed_at TIMESTAMP,
    due_date TIMESTAMP,
    tags TEXT[],
    parent_id INTEGER REFERENCES tasks(id),
    topic_id INTEGER REFERENCES topics(id),
    user_id VARCHAR(36) NOT NULL REFERENCES users(id),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP
);
```

### 2. Domain Layer Changes

1. Reuse existing enums from `domain/values.py`:
- Use existing `ProcessingStatus` enum for content processing states
- Keep existing `TaskStatus` enum for task progress tracking (TODO, IN_PROGRESS, DONE)

2. Update `TaskData` in `domain/task.py`:
- Replace title/description with content field
- Add enrichment_data, processing_status, processed_at
- Update validation logic

### 3. ORM Layer Changes

1. Update `TaskModel.py`:
```python
class Task(EntityMeta):
    """Task Model represents a single task or todo item.

    Each task belongs to a user and contains content that is processed
    to extract a title and format the description. Tasks maintain their
    state through status and priority flags.

    Attributes:
        id: Unique identifier
        content: Task content in markdown format
        status: Task progress status (TODO, IN_PROGRESS, DONE)
        user_id: ID of the task owner
        priority: Task priority level (LOW, MEDIUM, HIGH)
        due_date: Optional deadline for the task
        tags: List of tags for categorization
        parent_id: Optional ID of parent task
        note_id: Optional ID of associated note
        topic_id: Optional ID of associated topic
        processing_status: Status of content processing (from ProcessingStatus enum)
        enrichment_data: Data from content processing
        processed_at: When the content was processed
        created_at: When the task was created
        updated_at: When the task was last updated
    """
    __tablename__ = "tasks"

    content: Mapped[str] = Column(
        String(4096), nullable=False
    )
    status: Mapped[TaskStatus] = Column(
        SQLEnum(TaskStatus),
        nullable=False,
        default=TaskStatus.TODO,
        server_default=TaskStatus.TODO.value,
    )
    processing_status: Mapped[ProcessingStatus] = Column(
        SQLEnum(ProcessingStatus),
        nullable=False,
        default=ProcessingStatus.PENDING,
        server_default=ProcessingStatus.PENDING.value,
    )
    enrichment_data: Mapped[Optional[Dict[str, Any]]] = Column(
        JSON, nullable=True, default=None
    )
    processed_at: Mapped[Optional[datetime]] = Column(
        DateTime, nullable=True
    )
    # ... existing fields ...

    def __init__(self, **kwargs):
        """Initialize task with defaults if not provided."""
        if "status" not in kwargs:
            kwargs["status"] = TaskStatus.TODO
        if "processing_status" not in kwargs:
            kwargs["processing_status"] = ProcessingStatus.PENDING
        super().__init__(**kwargs)
```

### 4. Schema Layer Changes

1. Update `TaskSchema.py`:
```python
class TaskBase(BaseModel):
    """Base schema for task data."""
    content: str = Field(
        ...,
        min_length=1,
        description="Task content in markdown format"
    )
    status: TaskStatus = Field(default=TaskStatus.TODO)
    priority: TaskPriority = Field(default=TaskPriority.MEDIUM)
    due_date: Optional[datetime] = None
    tags: List[str] = Field(default_factory=list)
    parent_id: Optional[int] = None
    topic_id: Optional[int] = Field(None, gt=0)

class TaskResponse(TaskBase):
    """Schema for task responses."""
    id: int
    user_id: str
    enrichment_data: Optional[Dict[str, Any]] = None
    processing_status: ProcessingStatus
    processed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    topic: Optional[TopicResponse] = None
```

### 5. Service Layer Changes

1. Create new `TaskEnrichmentService`:
```python
class TaskEnrichmentService:
    """Service for enriching task content."""

    def __init__(self, robo_service: RoboService):
        self.robo_service = robo_service

    async def enrich_task(self, content: str) -> Dict[str, Any]:
        """Process task content to extract title and format content."""
        result = await self.robo_service.process_text(
            content,
            context={"type": "task_enrichment"}
        )
        return {
            "title": result.metadata["title"],
            "formatted": result.content,
            "tokens_used": result.tokens_used,
            "model_name": result.model_name,
            "created_at": result.created_at.isoformat(),
            "metadata": result.metadata
        }
```

2. Update `TaskService`:
- Add TaskEnrichmentService dependency
- Add method to trigger task enrichment
- Update create/update methods to handle new structure

### 6. Queue Layer Changes

1. Create new task worker in `infrastructure/queue/task_worker.py`:
```python
def process_task_job(
    task_id: int,
    session: Optional[Session] = None,
    robo_service: Optional[RoboService] = None,
    task_repository: Optional[TaskRepository] = None,
    max_retries: int = 3,
) -> None:
    """Process a task using RoboService.

    Args:
        task_id: ID of task to process
        session: Optional database session
        robo_service: Optional RoboService instance
        task_repository: Optional task repository
        max_retries: Maximum number of retries

    Raises:
        ValueError: If task not found
        RoboServiceError: If processing fails
    """
    session_provided = session is not None
    start_time = datetime.now(timezone.utc)
    logger = logging.getLogger(__name__)

    try:
        logger.info(f"Starting to process task {task_id}")

        # Create session if not provided
        if not session:
            logger.debug("Creating new database session")
            session = SessionLocal()

        # Create repository if not provided
        if not task_repository:
            logger.debug("Creating new task repository")
            task_repository = TaskRepository(session)

        # Get task
        logger.debug(f"Fetching task {task_id}")
        task = task_repository.get_by_id(task_id)
        if not task:
            raise ValueError(f"Task {task_id} not found")

        # Update to PROCESSING
        logger.debug(f"Updating task {task_id} status to PROCESSING")
        task.processing_status = ProcessingStatus.PROCESSING
        task.updated_at = datetime.now(timezone.utc)
        session.add(task)
        session.commit()

        # Create RoboService if not provided
        if not robo_service:
            logger.debug("Creating new RoboService instance")
            robo_service = get_robo_service()

        for attempt in range(max_retries + 1):
            try:
                logger.info(
                    f"Attempt {attempt + 1}/{max_retries + 1} "
                    f"to process task {task_id}"
                )
                result = robo_service.process_text(
                    task.content,
                    context={"type": "task_enrichment"},
                )
                logger.info(f"Successfully processed task {task_id}")

                task.enrichment_data = {
                    "title": result.metadata["title"],
                    "formatted": result.content,
                    "tokens_used": result.tokens_used,
                    "model_name": result.model_name,
                    "created_at": result.created_at.isoformat(),
                    "metadata": result.metadata,
                }

                # Update to COMPLETED
                task.processing_status = ProcessingStatus.COMPLETED
                task.processed_at = datetime.now(timezone.utc)
                task.updated_at = datetime.now(timezone.utc)
                session.add(task)
                session.commit()
                logger.info(f"Successfully completed processing task {task_id}")
                return

            except Exception as e:
                logger.error(
                    f"Failed to process task {task_id} "
                    f"(attempt {attempt + 1}/{max_retries + 1}): {str(e)}"
                )

                if attempt == max_retries:
                    logger.error(f"All attempts failed for task {task_id}")
                    task.processing_status = ProcessingStatus.FAILED
                    task.updated_at = datetime.now(timezone.utc)
                    session.add(task)
                    session.commit()
                    raise RoboServiceError(
                        f"Failed to process task {task_id}: {str(e)}"
                    )

                delay = calculate_backoff(attempt + 1)
                logger.info(f"Waiting {delay}s before retry")
                time.sleep(delay)

    except Exception as e:
        if not isinstance(e, (ValueError, RoboServiceError)):
            logger.error(
                f"Error in process_task_job for task {task_id}: {str(e)}",
                exc_info=True,
            )
        raise

    finally:
        if not session_provided and session:
            logger.debug("Closing database session")
            session.close()

        duration = (
            datetime.now(timezone.utc) - start_time
        ).total_seconds()
        logger.info(f"Task {task_id} processing completed in {duration}s")
```

### 7. Configuration Changes

1. Add new environment variables:
```
ROBO_TASK_ENRICHMENT_PROMPT="You are a task formatting assistant. Your task is to:\n1. Extract a concise title (<50 chars)\n2. Format the content in clean markdown\n3. Use appropriate formatting (bold, italic, lists)\n4. Keep the content concise but complete"
```

### 8. Test Updates

1. Update existing tests to handle new structure
2. Add new tests for:
- Task enrichment process
- Processing status transitions
- Content formatting
- Error handling and retries
- Logging coverage

### 9. Planning & Tracking

### Completed Work
1. Core Layer Updates
   - [x] Update domain layer (TaskData model, validation, etc.)
   - [x] Update ORM layer (Task model, new fields)
   - [x] Update schema layer (TaskCreate, TaskUpdate, TaskResponse schemas)
   - [x] Update service layer (TaskService, enrichment methods)
   - [x] Update repository layer and tests

### Current Epics (In Priority Order)

1. Router Layer Updates
   - [x] Update TaskRouter.py with new structure
   - [x] Fix unit tests in test_task_router.py
   - [x] Fix integration tests in test_task_topic_integration.py
   - [x] Update API documentation
   - [x] Add new endpoints for processing status if needed

2. Database Structure
   - [x] Update init_database.sql with new table structure
   - [x] Add necessary indexes
   - [x] Add foreign key constraints
   - [x] Test database initialization script

3. Worker Implementation
   - [x] Create TaskWorker
   - [x] Add OpenAI function definition
   - [x] Add error handling and retries
   - [x] Add logging
   - [x] Add worker tests

4. Configuration Updates
   - [x] Add task enrichment environment variables
   - [x] Set up task processing queue
   - [ ] Update test_flow.sh with new task schema
   - [ ] Update API documentation with new task format

## Success Criteria

1. All router tests passing with new structure
2. Database initialization script working correctly
3. Task enrichment working reliably with proper error handling
4. No degradation in API performance
5. Error rates within acceptable thresholds
6. Processing times within expected ranges
7. Logging provides clear visibility into processing status
