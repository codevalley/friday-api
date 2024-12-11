# API Layer Documentation

## Overview

The API layer provides RESTful endpoints for managing moments and activities in the life logging system. It follows REST principles and uses FastAPI for implementation.

## Base URL

```
/api/v1
```

## Endpoints

### Moments

#### List Moments
```
GET /moments
```

Query Parameters:
- `start_time`: ISO 8601 timestamp (UTC)
- `end_time`: ISO 8601 timestamp (UTC)
- `activity_id`: Integer
- `limit`: Integer (default: 50)
- `offset`: Integer (default: 0)

Response:
```json
{
    "items": [
        {
            "id": 1,
            "timestamp": "2024-01-01T12:00:00Z",
            "activity_id": 1,
            "data": {
                "location": {"lat": 37.7749, "lng": -122.4194},
                "notes": "Beautiful day at the park"
            }
        }
    ],
    "total": 100,
    "limit": 50,
    "offset": 0
}
```

#### Create Moment
```
POST /moments
```

Request Body:
```json
{
    "timestamp": "2024-01-01T12:00:00Z",
    "activity_id": 1,
    "data": {
        "location": {"lat": 37.7749, "lng": -122.4194},
        "notes": "Beautiful day at the park"
    }
}
```

#### Get Moment
```
GET /moments/{moment_id}
```

Response:
```json
{
    "id": 1,
    "timestamp": "2024-01-01T12:00:00Z",
    "activity_id": 1,
    "data": {
        "location": {"lat": 37.7749, "lng": -122.4194},
        "notes": "Beautiful day at the park"
    }
}
```

#### Update Moment
```
PUT /moments/{moment_id}
```

Request Body:
```json
{
    "data": {
        "location": {"lat": 37.7749, "lng": -122.4194},
        "notes": "Updated notes about the day"
    }
}
```

#### Delete Moment
```
DELETE /moments/{moment_id}
```

### Activities

#### List Activities
```
GET /activities
```

Response:
```json
{
    "items": [
        {
            "id": 1,
            "name": "outdoor_activity",
            "description": "Outdoor activities and adventures",
            "activity_schema": {
                "type": "object",
                "properties": {
                    "location": {
                        "type": "object",
                        "properties": {
                            "lat": {"type": "number"},
                            "lng": {"type": "number"}
                        }
                    },
                    "notes": {"type": "string"}
                }
            },
            "icon": "hiking",
            "color": "#4CAF50"
        }
    ]
}
```

#### Create Activity
```
POST /activities
```

Request Body:
```json
{
    "name": "outdoor_activity",
    "description": "Outdoor activities and adventures",
    "activity_schema": {
        "type": "object",
        "properties": {
            "location": {
                "type": "object",
                "properties": {
                    "lat": {"type": "number"},
                    "lng": {"type": "number"}
                }
            },
            "notes": {"type": "string"}
        }
    },
    "icon": "hiking",
    "color": "#4CAF50"
}
```

#### Get Activity
```
GET /activities/{activity_id}
```

#### Update Activity
```
PUT /activities/{activity_id}
```

Request Body:
```json
{
    "description": "Updated description",
    "activity_schema": {
        "type": "object",
        "properties": {
            "location": {
                "type": "object",
                "properties": {
                    "lat": {"type": "number"},
                    "lng": {"type": "number"}
                }
            },
            "notes": {"type": "string"},
            "weather": {"type": "string"}
        }
    },
    "icon": "mountain",
    "color": "#2196F3"
}
```

#### Delete Activity
```
DELETE /activities/{activity_id}
```

## Error Responses

All endpoints may return the following error responses:

### 400 Bad Request
```json
{
    "detail": "Invalid request data",
    "errors": [
        {
            "field": "timestamp",
            "message": "Invalid timestamp format"
        }
    ]
}
```

### 404 Not Found
```json
{
    "detail": "Resource not found"
}
```

### 422 Validation Error
```json
{
    "detail": "Data validation error",
    "errors": [
        {
            "field": "data",
            "message": "Does not match activity schema"
        }
    ]
}
```

### 500 Internal Server Error
```json
{
    "detail": "Internal server error"
}
```

## Authentication

All endpoints require authentication using JWT tokens:

```
Authorization: Bearer <token>
```

## Rate Limiting

- 1000 requests per hour per API key
- Rate limit headers included in responses:
  ```
  X-RateLimit-Limit: 1000
  X-RateLimit-Remaining: 999
  X-RateLimit-Reset: 1640995200
  ```