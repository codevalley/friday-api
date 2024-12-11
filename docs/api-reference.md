# Friday API Reference

This document provides detailed information about the Friday API endpoints, their usage, and examples.

## REST API Endpoints

### Activities

#### List Activities
```http
GET /v1/activities
```
Returns a list of all activities.

**Response**
```json
{
  "items": [
    {
      "id": 1,
      "name": "Reading",
      "description": "Track reading sessions",
      "activity_schema": {
        "type": "object",
        "properties": {
          "book": { "type": "string" },
          "pages": { "type": "number" },
          "notes": { "type": "string" }
        }
      },
      "icon": "📚",
      "color": "#4A90E2"
    }
  ]
}
```

#### Get Activity
```http
GET /v1/activities/{id}
```
Returns a specific activity by ID.

**Parameters**
- `id` (path) - Activity ID

#### Create Activity
```http
POST /v1/activities
```
Creates a new activity.

**Request Body**
```json
{
  "name": "Exercise",
  "description": "Track workout sessions",
  "activity_schema": {
    "type": "object",
    "properties": {
      "type": { "type": "string", "enum": ["cardio", "strength"] },
      "duration": { "type": "number" },
      "intensity": { "type": "string", "enum": ["low", "medium", "high"] }
    },
    "required": ["type", "duration"]
  },
  "icon": "💪",
  "color": "#E24A90"
}
```

#### Update Activity
```http
PATCH /v1/activities/{id}
```
Updates an existing activity.

**Parameters**
- `id` (path) - Activity ID

#### Delete Activity
```http
DELETE /v1/activities/{id}
```
Deletes an activity.

**Parameters**
- `id` (path) - Activity ID

### Moments

#### List Moments
```http
GET /v1/moments
```
Returns a paginated list of moments with optional filtering.

**Query Parameters**
- `page` (optional) - Page number (default: 1)
- `size` (optional) - Items per page (default: 10, max: 100)
- `activity_id` (optional) - Filter by activity
- `start_date` (optional) - Filter moments after this date (UTC)
- `end_date` (optional) - Filter moments before this date (UTC)

**Response**
```json
{
  "items": [
    {
      "id": 1,
      "activity_id": 1,
      "timestamp": "2024-12-11T05:30:00Z",
      "data": {
        "book": "The Pragmatic Programmer",
        "pages": 50,
        "notes": "Great chapter on code quality"
      },
      "activity": {
        "id": 1,
        "name": "Reading",
        "icon": "📚",
        "color": "#4A90E2"
      }
    }
  ],
  "total": 42,
  "page": 1,
  "size": 10,
  "pages": 5
}
```

#### Get Moment
```http
GET /v1/moments/{id}
```
Returns a specific moment by ID.

**Parameters**
- `id` (path) - Moment ID

#### Create Moment
```http
POST /v1/moments
```
Creates a new moment.

**Request Body**
```json
{
  "activity_id": 1,
  "timestamp": "2024-12-11T05:30:00Z",
  "data": {
    "book": "The Pragmatic Programmer",
    "pages": 50,
    "notes": "Great chapter on code quality"
  }
}
```

#### Update Moment
```http
PATCH /v1/moments/{id}
```
Updates an existing moment.

**Parameters**
- `id` (path) - Moment ID

#### Delete Moment
```http
DELETE /v1/moments/{id}
```
Deletes a moment.

**Parameters**
- `id` (path) - Moment ID

## GraphQL API

### Queries

#### List Activities
```graphql
query {
  activities {
    id
    name
    description
    activitySchema
    icon
    color
    moments {
      id
      timestamp
      data
    }
  }
}
```

#### Get Activity
```graphql
query ($id: Int!) {
  activity(id: $id) {
    id
    name
    description
    activitySchema
    icon
    color
    moments {
      id
      timestamp
      data
    }
  }
}
```

#### List Moments
```graphql
query ($page: Int, $size: Int, $activityId: Int, $startDate: DateTime, $endDate: DateTime) {
  moments(page: $page, size: $size, activityId: $activityId, startDate: $startDate, endDate: $endDate) {
    items {
      id
      timestamp
      data
      activity {
        id
        name
        icon
        color
      }
    }
    total
    page
    size
    pages
  }
}
```

### Mutations

#### Create Activity
```graphql
mutation ($input: ActivityInput!) {
  createActivity(input: $input) {
    id
    name
    description
    activitySchema
    icon
    color
  }
}
```

#### Update Activity
```graphql
mutation ($id: Int!, $input: ActivityUpdateInput!) {
  updateActivity(id: $id, input: $input) {
    id
    name
    description
    activitySchema
    icon
    color
  }
}
```

#### Create Moment
```graphql
mutation ($input: MomentInput!) {
  createMoment(input: $input) {
    id
    timestamp
    data
    activity {
      id
      name
      icon
      color
    }
  }
}
```

#### Update Moment
```graphql
mutation ($id: Int!, $input: MomentUpdateInput!) {
  updateMoment(id: $id, input: $input) {
    id
    timestamp
    data
    activity {
      id
      name
      icon
      color
    }
  }
}
```
