# Application Services

## Overview

The application services layer implements the business logic of the application. It acts as a mediator between the domain models and the external interfaces (REST API). Services handle data validation, business rules, and coordinate operations between repositories.

## Service Implementation

### Activity Service

```python
# services/ActivityService.py
class ActivityService:
    def __init__(self, db: Session = Depends(get_db_connection)):
        self.db = db
        self.activity_repository = ActivityRepository(db)

    def create_activity(self, activity_data: ActivityCreate) -> ActivityResponse:
        """Create a new activity with schema validation"""
        activity = self.activity_repository.create(
            name=activity_data.name,
            description=activity_data.description,
            activity_schema=activity_data.activity_schema,
            icon=activity_data.icon,
            color=activity_data.color
        )
        return ActivityResponse.model_validate(activity)

    def get_activity(self, activity_id: int) -> Optional[ActivityResponse]:
        """Get an activity by ID"""
        activity = self.activity_repository.validate_existence(activity_id)
        return ActivityResponse.model_validate(activity)
```

### Moment Service

```python
# services/MomentService.py
class MomentService:
    def __init__(self, db: Session = Depends(get_db_connection)):
        self.db = db
        self.moment_repository = MomentRepository(db)
        self.activity_repository = ActivityRepository(db)

    def create_moment(self, moment_data: MomentCreate) -> MomentResponse:
        """Create a new moment with data validation"""
        # Get activity to validate data against schema
        activity = self.activity_repository.validate_existence(moment_data.activity_id)

        try:
            # Validate moment data against activity schema
            jsonschema.validate(instance=moment_data.data, schema=activity.activity_schema)
        except ValidationError as e:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid moment data: {str(e)}"
            )

        moment = self.moment_repository.create(
            activity_id=moment_data.activity_id,
            data=moment_data.data,
            timestamp=moment_data.timestamp
        )

        return MomentResponse.model_validate(moment)

    def list_moments(
        self,
        page: int = 1,
        size: int = 50,
        activity_id: Optional[int] = None,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None
    ) -> PaginationResponse:
        """List moments with filtering and pagination"""
        moments_list = self.moment_repository.list_moments(
            page=page,
            size=size,
            activity_id=activity_id,
            start_time=start_time,
            end_time=end_time
        )

        return PaginationResponse(
            items=[MomentResponse.model_validate(moment) for moment in moments_list.items],
            total=moments_list.total,
            page=moments_list.page,
            size=moments_list.size,
            pages=moments_list.pages
        )
```

## Key Features

1. **Data Validation**
   - Input validation using Pydantic models
   - JSON Schema validation for activity-specific data
   - Error handling with meaningful messages

2. **Business Logic**
   - Coordinates operations between repositories
   - Implements business rules and validations
   - Handles data transformations

3. **Type Safety**
   - Strong typing with Pydantic models
   - Runtime type checking
   - Comprehensive type hints

## Service Layer Responsibilities

1. **Input Processing**
   - Validates incoming data
   - Converts between DTOs and domain models
   - Handles data type conversions

2. **Business Rules**
   - Enforces domain constraints
   - Validates relationships
   - Ensures data consistency

3. **Error Handling**
   - Provides meaningful error messages
   - Handles business rule violations
   - Manages transaction boundaries

## Best Practices

1. **Dependency Injection**
   - Services receive dependencies through constructor
   - Facilitates testing and mocking
   - Loose coupling between components

2. **Single Responsibility**
   - Each service handles one domain concept
   - Clear separation of concerns
   - Focused business logic

3. **Error Management**
   - Consistent error handling
   - Proper exception hierarchy
   - Informative error messages

## API Integration

1. **Response Formatting**
   - Converts between database models and API responses
   - Handles nested relationships
   - Manages field serialization

2. **Query Handling**
   - Efficient data loading
   - Proper pagination
   - Field-level permissions

3. **Request Processing**
   - Input validation
   - Transaction management
   - Response formatting
