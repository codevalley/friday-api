# Clean Architecture Implementation for Life Moments Logger

## Overview

This project implements the Clean Architecture pattern for a Life Moments logging system. The architecture emphasizes separation of concerns and dependency inversion, organized in concentric circles, with the domain layer at the center and external concerns at the outer layers.

## Architectural Principles

1. **Independence of Frameworks**: The moment logging business logic is isolated from the delivery mechanism (FastAPI) and external frameworks.
2. **Testability**: The architecture makes the system highly testable by isolating moment logging components.
3. **Independence of UI**: The system works with multiple interfaces (REST, GraphQL) for accessing moments.
4. **Independence of Database**: The moment logging rules don't know about storage details.
5. **Independence of External Agency**: Moment logging business rules are separate from external integrations.

## Layer Details

### 1. Domain Layer (Inner Circle)

Located in `models/`, this layer contains:
- Core business entities (Moment, Activity)
- Business rules for moment validation and processing
- Interface definitions for moment logging operations
- No dependencies on outer layers

Example:
```python
# models/MomentModel.py - Core domain entity
class MomentModel(Base):
    __tablename__ = "moments"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime(timezone=True), index=True)
    activity_id = Column(Integer, ForeignKey("activities.id"))
    data = Column(JSON)  # Flexible schema for different activities

    # Relationships
    activity = relationship("ActivityModel", back_populates="moments")
```

### 2. Application Layer

Located in `services/`, this layer:
- Implements moment logging use cases (create moment, query moments, analyze patterns)
- Orchestrates the flow of moment data
- Contains business logic for moment processing and validation
- Depends only on the domain layer

Example:
```python
# services/MomentService.py - Application service
class MomentService:
    def __init__(self, repository: MomentRepository):
        self._repository = repository

    async def create_moment(self, moment_data: dict) -> MomentModel:
        # Validate activity type
        activity = await self._validate_activity(moment_data["activity_id"])

        # Validate moment data against activity schema
        self._validate_moment_data(moment_data["data"], activity.activity_schema)

        # Create and store the moment
        moment = MomentModel(
            timestamp=moment_data["timestamp"],
            activity_id=activity.id,
            data=moment_data["data"]
        )
        return await self._repository.create(moment)

    async def query_moments(self, filters: dict) -> List[MomentModel]:
        # Query moments with time range, activity, etc.
        return await self._repository.query(filters)
```

### 3. Interface Adapters

Located in `repositories/` and `routers/`, this layer:
- Converts moment data between domain and external formats
- Implements repository interfaces for moment storage and retrieval
- Handles HTTP/GraphQL requests for moment logging operations
- Contains controllers and presenters for moment data

### 4. External Interfaces

Located in various outer layer directories:
- REST API endpoints for moments (`routers/v1/moments.py`)
- GraphQL schema for moment queries (`schemas/graphql/`)
- Database configurations for moment storage (`configs/`)
- External service integrations (photo storage, activity tracking)

## Dependency Flow

The dependencies flow from the outer layers inward:
```
External Layer (REST/GraphQL) → Interface Adapters → Application Services → Domain Model
                                                                       ↑
                                                     Core Moment Logging Logic
```

## Benefits of This Architecture

1. **Maintainability**: Changes in external layers don't affect the core moment logging logic
2. **Testability**: Each moment logging component can be tested in isolation
3. **Flexibility**: Easy to add new activity types or change storage systems
4. **Scalability**: Clear boundaries make it easier to scale specific components
