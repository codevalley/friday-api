# Schema Documentation

## Overview

The Friday API uses a layered schema approach with several key components:
- Pydantic schemas for REST API validation and serialization
- GraphQL types for the GraphQL API
- SQLAlchemy models for database interaction
- Domain models for business logic

## Base Schemas

### BaseSchema
The foundation for all Pydantic schemas, providing common validation patterns:
```python
class BaseSchema(BaseModel):
    """Base schema with common validation methods"""
    # ID validation
    # User ID validation
    # Timestamp validation
    # Color code validation
```

### PaginatedResponse
Generic paginated response wrapper:
```python
class PaginatedResponse[T](BaseModel, Generic[T]):
    items: list[T]      # List of items
    total: int          # Total number of items
    page: int          # Current page (1-based)
    size: int          # Items per page
    pages: int         # Total number of pages
```

## Activity Schemas

### ActivityBase
Base schema for activity data:
```python
class ActivityBase(BaseSchema):
    name: str          # Display name (1-255 chars)
    description: str   # Detailed description
    activity_schema: Dict[str, Any]  # JSON Schema
    icon: str         # Display icon
    color: str        # Hex color code
```

### Example
```json
{
    "name": "Daily Mood",
    "description": "Track your daily mood and emotions",
    "activity_schema": {
        "type": "object",
        "properties": {
            "mood": {
                "type": "string",
                "enum": ["Happy", "Sad", "Neutral"]
            },
            "notes": {
                "type": "string"
            }
        }
    },
    "icon": "😊",
    "color": "#4A90E2"
}
```

## Moment Schemas

### MomentBase
Base schema for moment data:
```python
class MomentBase(BaseSchema):
    activity_id: int   # Reference to activity
    data: Dict[str, Any]  # Activity-specific data
    timestamp: datetime   # When it occurred
```

### Example
```json
{
    "activity_id": 1,
    "data": {
        "mood": "Happy",
        "notes": "Had a great day at work!"
    },
    "timestamp": "2023-12-14T12:00:00Z"
}
```

## User Schemas

### UserBase
Base schema for user data:
```python
class UserBase(BaseSchema):
    username: str      # Unique username (3-50 chars)
```

### Example
```json
{
    "username": "john_doe",
    "created_at": "2023-12-14T10:00:00Z",
    "updated_at": null
}
```

## Schema Validation

### Activity Schema Validation
- Name: 1-255 characters
- Description: 1-1000 characters
- Activity Schema: Valid JSON Schema
- Icon: Non-empty string
- Color: Valid hex code (#RRGGBB)

### Moment Schema Validation
- Activity ID: Positive integer
- Data: Must match activity's schema
- Timestamp: Valid UTC datetime

### User Schema Validation
- Username: 3-50 characters
- Username format: letters, numbers, underscores, hyphens

## GraphQL Types

### Activity Type
```graphql
type Activity {
    id: Int!
    name: String!
    description: String!
    activitySchema: String!
    icon: String!
    color: String!
    momentCount: Int!
    moments: [Moment!]!
}
```

### Moment Type
```graphql
type Moment {
    id: Int!
    activityId: Int!
    data: String!
    timestamp: DateTime!
    userId: String
}
```

### User Type
```graphql
type User {
    id: String!
    username: String!
    createdAt: DateTime!
    updatedAt: DateTime
}
```

## Pagination

All list endpoints support pagination with:
- `page`: Page number (1-based)
- `size`: Items per page (max 100)

Response includes:
- `items`: List of items
- `total`: Total number of items
- `pages`: Total number of pages
- `page`: Current page
- `size`: Current page size

## Error Handling

Standard error response:
```json
{
    "detail": "Error message describing what went wrong"
}
```

Common error scenarios:
1. Invalid input data
2. Resource not found
3. Unauthorized access
4. Schema validation failure 