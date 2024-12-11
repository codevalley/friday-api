# Application Services Layer

## Overview

The application services layer implements the core business logic for the life moments logging system. It orchestrates the flow of data between the API layer and the domain layer, ensuring that all business rules are properly enforced.

## Service Components

### MomentService

The `MomentService` handles all operations related to moments.

```python
class MomentService:
    def __init__(
        self,
        moment_repository: MomentRepository,
        activity_service: ActivityService
    ):
        self._repository = moment_repository
        self._activity_service = activity_service

    async def create_moment(self, data: MomentCreate) -> MomentModel:
        """Create a new moment."""
        # Validate activity exists
        activity = await self._activity_service.get_activity(data.activity_id)
        if not activity:
            raise ActivityNotFoundError(data.activity_id)

        # Validate moment data against activity schema
        self._validate_moment_data(data.data, activity.activity_schema)

        # Create moment
        moment = MomentModel(
            timestamp=data.timestamp,
            activity_id=activity.id,
            data=data.data
        )
        return await self._repository.create(moment)

    async def get_moment(self, moment_id: int) -> Optional[MomentModel]:
        """Retrieve a specific moment."""
        return await self._repository.get(moment_id)

    async def list_moments(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        activity_id: Optional[int] = None,
        limit: int = 50,
        offset: int = 0
    ) -> Tuple[List[MomentModel], int]:
        """List moments with optional filtering."""
        return await self._repository.list_moments(
            start_time=start_time,
            end_time=end_time,
            activity_id=activity_id,
            limit=limit,
            offset=offset
        )

    async def update_moment(
        self,
        moment_id: int,
        data: MomentUpdate
    ) -> Optional[MomentModel]:
        """Update an existing moment."""
        moment = await self.get_moment(moment_id)
        if not moment:
            raise MomentNotFoundError(moment_id)

        # Validate updated data against activity schema
        activity = await self._activity_service.get_activity(moment.activity_id)
        self._validate_moment_data(data.data, activity.activity_schema)

        return await self._repository.update(
            moment_id,
            {"data": data.data}
        )

    async def delete_moment(self, moment_id: int) -> bool:
        """Delete a moment."""
        return await self._repository.delete(moment_id)

    def _validate_moment_data(self, data: dict, schema: dict) -> None:
        """Validate moment data against activity schema."""
        try:
            jsonschema.validate(data, schema)
        except jsonschema.exceptions.ValidationError as e:
            raise InvalidMomentDataError(str(e))
```

### ActivityService

The `ActivityService` manages activity types and their schemas.

```python
class ActivityService:
    def __init__(self, activity_repository: ActivityRepository):
        self._repository = activity_repository

    async def create_activity(self, data: ActivityCreate) -> ActivityModel:
        """Create a new activity type."""
        # Validate schema structure
        self._validate_activity_schema(data.activity_schema)
        
        # Validate color format
        self._validate_color(data.color)
        
        activity = ActivityModel(
            name=data.name,
            description=data.description,
            activity_schema=data.activity_schema,
            icon=data.icon,
            color=data.color
        )
        return await self._repository.create(activity)

    async def get_activity(self, activity_id: int) -> Optional[ActivityModel]:
        """Retrieve a specific activity."""
        return await self._repository.get(activity_id)

    async def list_activities(
        self,
        limit: int = 50,
        offset: int = 0
    ) -> Tuple[List[ActivityModel], int]:
        """List all activities."""
        return await self._repository.list_activities(limit=limit, offset=offset)

    async def update_activity(
        self,
        activity_id: int,
        data: ActivityUpdate
    ) -> Optional[ActivityModel]:
        """Update an existing activity."""
        activity = await self.get_activity(activity_id)
        if not activity:
            raise ActivityNotFoundError(activity_id)

        if data.activity_schema:
            self._validate_activity_schema(data.activity_schema)
        
        if data.color:
            self._validate_color(data.color)

        return await self._repository.update(activity_id, data.dict(exclude_unset=True))

    async def delete_activity(self, activity_id: int) -> bool:
        """Delete an activity and all associated moments."""
        return await self._repository.delete(activity_id)

    def _validate_activity_schema(self, schema: dict) -> None:
        """Validate that the activity schema is valid JSON Schema."""
        try:
            # Validate schema is valid JSON Schema
            jsonschema.Draft7Validator.check_schema(schema)
        except jsonschema.exceptions.SchemaError as e:
            raise InvalidActivitySchemaError(str(e))

    def _validate_color(self, color: str) -> None:
        """Validate color format (hex or named color)."""
        if not re.match(r'^#(?:[0-9a-fA-F]{3}){1,2}$', color) and \
           color not in VALID_COLOR_NAMES:
            raise InvalidColorError(f"Invalid color format: {color}")
```

## Service Layer Features

1. **Data Validation**
   - JSON Schema validation for moment data
   - Activity schema validation
   - Color format validation
   - Timestamp validation

2. **Business Rules**
   - Moments must have valid activities
   - Activity schemas must be valid JSON Schema
   - Colors must be valid formats
   - Proper UTC timestamp handling

3. **Error Handling**
   - Custom exception types for different error cases
   - Detailed error messages
   - Proper error propagation

4. **Transaction Management**
   - Atomic operations where needed
   - Proper cleanup on failures
   - Consistent state maintenance

## Dependencies

The service layer depends on:
- Repository interfaces (not implementations)
- Domain models
- Pydantic schemas for data validation
- JSON Schema for dynamic schema validation

## Error Types

```python
class MomentError(Exception):
    """Base class for moment-related errors."""
    pass

class ActivityError(Exception):
    """Base class for activity-related errors."""
    pass

class MomentNotFoundError(MomentError):
    """Raised when a moment is not found."""
    pass

class ActivityNotFoundError(ActivityError):
    """Raised when an activity is not found."""
    pass

class InvalidMomentDataError(MomentError):
    """Raised when moment data doesn't match activity schema."""
    pass

class InvalidActivitySchemaError(ActivityError):
    """Raised when activity schema is invalid."""
    pass

class InvalidColorError(ActivityError):
    """Raised when color format is invalid."""
    pass