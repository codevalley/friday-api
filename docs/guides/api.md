# API Documentation

## Authentication

### Register User
```http
POST /v1/auth/register
Content-Type: application/json

{
    "username": "john_doe"
}
```

Response:
```json
{
    "id": "uuid",
    "username": "john_doe",
    "user_secret": "secret_key_for_api_auth"
}
```

### Login
```http
POST /v1/auth/login
Content-Type: application/json

{
    "user_secret": "secret_key_for_api_auth"
}
```

Response:
```json
{
    "access_token": "jwt_token",
    "token_type": "bearer"
}
```

## Activities

### Create Activity
```http
POST /v1/activities
Authorization: Bearer <token>
Content-Type: application/json

{
    "name": "Daily Mood",
    "description": "Track your daily mood",
    "activity_schema": {
        "type": "object",
        "properties": {
            "mood": {
                "type": "string",
                "enum": ["Happy", "Sad", "Neutral"]
            }
        }
    },
    "icon": "😊",
    "color": "#4A90E2"
}
```

### List Activities
```http
GET /v1/activities?page=1&size=10
Authorization: Bearer <token>
```

### Get Activity
```http
GET /v1/activities/{activity_id}
Authorization: Bearer <token>
```

### Update Activity
```http
PUT /v1/activities/{activity_id}
Authorization: Bearer <token>
Content-Type: application/json

{
    "name": "Updated Name",
    "description": "Updated description"
}
```

### Delete Activity
```http
DELETE /v1/activities/{activity_id}
Authorization: Bearer <token>
```

## Moments

### Create Moment
```http
POST /v1/moments
Authorization: Bearer <token>
Content-Type: application/json

{
    "activity_id": 1,
    "data": {
        "mood": "Happy",
        "notes": "Great day!"
    },
    "timestamp": "2023-12-14T12:00:00Z"
}
```

### List Moments
```http
GET /v1/moments?page=1&size=10
Authorization: Bearer <token>
```

### Get Moment
```http
GET /v1/moments/{moment_id}
Authorization: Bearer <token>
```

### Update Moment
```http
PUT /v1/moments/{moment_id}
Authorization: Bearer <token>
Content-Type: application/json

{
    "data": {
        "mood": "Neutral",
        "notes": "Updated notes"
    }
}
```

### Delete Moment
```http
DELETE /v1/moments/{moment_id}
Authorization: Bearer <token>
```

## GraphQL API

### Endpoint
```http
POST /graphql
Authorization: Bearer <token>
Content-Type: application/json
```

### Queries

List Activities:
```graphql
query {
    activities(page: 1, size: 10) {
        items {
            id
            name
            description
            activitySchema
            icon
            color
            momentCount
        }
        total
        page
        size
        pages
    }
}
```

Get Activity:
```graphql
query {
    activity(id: 1) {
        id
        name
        description
        moments {
            id
            data
            timestamp
        }
    }
}
```

List Moments:
```graphql
query {
    moments(page: 1, size: 10) {
        items {
            id
            activityId
            data
            timestamp
        }
        total
        page
        size
        pages
    }
}
```

### Mutations

Create Activity:
```graphql
mutation {
    createActivity(input: {
        name: "Daily Mood"
        description: "Track your mood"
        activitySchema: "{\"type\":\"object\"}"
        icon: "😊"
        color: "#4A90E2"
    }) {
        id
        name
    }
}
```

Create Moment:
```graphql
mutation {
    createMoment(input: {
        activityId: 1
        data: "{\"mood\":\"Happy\"}"
        timestamp: "2023-12-14T12:00:00Z"
    }) {
        id
        data
    }
}
```

## Error Responses

### 400 Bad Request
```json
{
    "detail": "Invalid input data"
}
```

### 401 Unauthorized
```json
{
    "detail": "Invalid authentication credentials"
}
```

### 403 Forbidden
```json
{
    "detail": "Not authorized to access this resource"
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
    "detail": [
        {
            "loc": ["body", "name"],
            "msg": "field required",
            "type": "value_error.missing"
        }
    ]
}
```

## Rate Limiting

- 100 requests per minute per IP
- 1000 requests per hour per user
- Headers:
  - `X-RateLimit-Limit`: Rate limit ceiling
  - `X-RateLimit-Remaining`: Remaining requests
  - `X-RateLimit-Reset`: Time until reset
