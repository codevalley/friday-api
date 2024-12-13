# OpenAPI Request Examples

## Activities

### Create Activity (POST /v1/activities)

```json
{
  "name": "New Activity",
  "description": "Activity description",
  "activity_schema": {
    "type": "object",
    "properties": {
      "value": {
        "type": "string"
      }
    }
  },
  "icon": "activity-icon",
  "color": "#00FF00"
}
```

### Update Activity (PUT /v1/activities/{id})

```json
{
  "name": "Updated Activity",
  "description": "Updated description",
  "activity_schema": {
    "type": "object",
    "properties": {
      "value": {
        "type": "string"
      }
    }
  },
  "icon": "new-icon",
  "color": "#FF0000"
}
```

## Moments

### Create Moment (POST /v1/moments)

```json
{
  "activity_id": 1,
  "data": {
    "value": "Sample value"
  },
  "timestamp": "2024-12-12T16:30:00Z"
}
```

### Update Moment (PUT /v1/moments/{id})

```json
{
  "data": {
    "value": "Updated value"
  },
  "timestamp": "2024-12-12T16:30:00Z"
}
```

## Query Parameters

### List Activities (GET /v1/activities)

- `skip` (optional): Number of records to skip (default: 0)
- `limit` (optional): Maximum number of records to return (default: 100)

### List Moments (GET /v1/moments)

- `page` (optional): Page number (default: 1)
- `size` (optional): Page size (default: 50)
- `activity_id` (optional): Filter by activity ID
- `start_time` (optional): Filter moments after this timestamp (ISO 8601 format)
- `end_time` (optional): Filter moments before this timestamp (ISO 8601 format)
