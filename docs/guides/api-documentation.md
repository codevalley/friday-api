Below is a comprehensive API guide extracted from the **Friday API** codebase and the test script you provided. It covers routes for **User Auth**, **Activities**, **Moments**, **Notes**, and **Tasks**, including the request and response formats. This document is intended for your frontend developer so they can integrate with each endpoint effectively.

---

## Table of Contents

1. [Authentication](#authentication)
   - [Register User](#register-user)
   - [Obtain Token](#obtain-token)
   - [Get Current User Info](#get-current-user-info)

2. [Activities](#activities)
   - [Create Activity](#create-activity)
   - [List Activities](#list-activities)
   - [Get Activity by ID](#get-activity-by-id)
   - [Update Activity](#update-activity)
   - [Delete Activity](#delete-activity)

3. [Moments](#moments)
   - [Create Moment](#create-moment)
   - [List Moments](#list-moments)
   - [Get Moment by ID](#get-moment-by-id)
   - [Update Moment](#update-moment)
   - [Delete Moment](#delete-moment)
   - [Attach / Detach Note from Moment](#attach--detach-note-from-moment)
     *(Optional if exposed in your code—some references exist)*

4. [Notes](#notes)
   - [Create Note](#create-note)
   - [List Notes](#list-notes)
   - [Get Note by ID](#get-note-by-id)
   - [Update Note](#update-note)
   - [Delete Note](#delete-note)

5. [Tasks](#tasks)
   - [Create Task](#create-task)
   - [List Tasks](#list-tasks)
   - [Get Task by ID](#get-task-by-id)
   - [Update Task](#update-task)
   - [Delete Task](#delete-task)
   - [Update Task Status](#update-task-status)
   - [Get Subtasks](#get-subtasks)
   - [Attach / Detach Note from Task](#attach--detach-note-from-task)

6. [Common Response Formats](#common-response-formats)

---

## 1. Authentication

### Register User
**Endpoint**: `POST /v1/auth/register`
**Description**: Creates a new user with a minimal `username` and returns an API key (`user_secret`).

**Request Body**:
```json
{
  "username": "string (3-50 chars)"
}
```

**Response** (usually wrapped in `GenericResponse`):
```json
{
  "data": {
    "id": "string (UUID)",
    "username": "string",
    "key_id": "string (UUID)",
    "user_secret": "string (the secret part of the API key)",
    "created_at": "ISO datetime",
    "updated_at": "ISO datetime or null"
  },
  "message": "User registered successfully"
}
```
- `user_secret` is used in the next step to obtain a bearer token.
- **Note**: You can store `user_secret` on the client side for further actions.

---

### Obtain Token
**Endpoint**: `POST /v1/auth/token`
**Description**: Exchanges the user’s `user_secret` for a JWT `access_token`.

**Request Body**:
```json
{
  "user_secret": "string (the user_secret from registration)"
}
```

**Response**:
```json
{
  "data": {
    "access_token": "string (JWT token)",
    "token_type": "bearer"
  },
  "message": "Login successful"
}
```
- **Bearer Token** needs to be sent in the `Authorization` header for all subsequent requests:
  ```
  Authorization: Bearer <access_token>
  ```

---

### Get Current User Info
**Endpoint**: `GET /v1/auth/me`
*(This route exists in `AuthRouter.py` but the test script might not show it. If you have it enabled, here’s the pattern.)*

**Description**: Returns info about the currently authenticated user.

**Request Header**:
```
Authorization: Bearer <access_token>
```

**Response**:
```json
{
  "data": {
    "id": "string (UUID)",
    "username": "string",
    "created_at": "ISO datetime",
    "updated_at": "ISO datetime or null"
  },
  "message": "Current user retrieved successfully"
}
```
- If the user/token is invalid, returns a `401 Unauthorized`.

---

## 2. Activities

### Create Activity
**Endpoint**: `POST /v1/activities`
**Description**: Creates a new activity for the authenticated user.

**Request Header**:
```
Authorization: Bearer <access_token>
Content-Type: application/json
```

**Request Body**:
```json
{
  "name": "string (required)",
  "description": "string (required)",
  "activity_schema": { ... },  // JSON schema for moment data
  "icon": "string (emoji or text)",
  "color": "#RRGGBB"
}
```

**Sample**:
```json
{
  "name": "Reading",
  "description": "Track reading sessions",
  "activity_schema": {
    "type": "object",
    "properties": { "book": { "type": "string" }, "pages": { "type": "number" } },
    "required": ["book", "pages"]
  },
  "icon": "📚",
  "color": "#4A90E2"
}
```

**Response**:
```json
{
  "data": {
    "id": 123,  // Activity's numeric ID
    "name": "Reading",
    "description": "Track reading sessions",
    "activity_schema": { ... },
    "icon": "📚",
    "color": "#4A90E2",
    "user_id": "string (the user's UUID)",
    "moment_count": 0,
    "created_at": "ISO datetime",
    "updated_at": null,
    "moments": null
  },
  "message": "Activity created successfully"
}
```

---

### List Activities
**Endpoint**: `GET /v1/activities?page={page}&size={size}`
**Description**: Lists all activities belonging to the current user. Supports pagination.

**Query Parameters**:
- `page` (optional, default=1)
- `size` (optional, default=100)

**Response**:
```json
{
  "data": {
    "items": [
      {
        "id": 123,
        "name": "...",
        "description": "...",
        "activity_schema": { ... },
        "icon": "...",
        "color": "#RRGGBB",
        "user_id": "UUID",
        "moment_count": 0,
        "created_at": "ISO datetime",
        "updated_at": null
      },
      ...
    ],
    "total": 2,
    "page": 1,
    "size": 100,
    "pages": 1
  },
  "message": "Retrieved 2 activities"
}
```

---

### Get Activity by ID
**Endpoint**: `GET /v1/activities/{activity_id}`
**Description**: Retrieves a single activity by its numeric ID, if it belongs to the current user.

**Response**:
```json
{
  "data": {
    "id": 123,
    "name": "...",
    "description": "...",
    "activity_schema": { ... },
    "icon": "...",
    "color": "#RRGGBB",
    "user_id": "UUID",
    "moment_count": 5,
    "created_at": "ISO datetime",
    "updated_at": "ISO datetime or null",
    "moments": [
      // Optionally includes moment details if you want them in the same response
      // Typically it might be null or an array of moments
    ]
  }
}
```
- If `activity_id` does not exist or is owned by another user, returns `404 {"detail":"Activity not found"}`.

---

### Update Activity
**Endpoint**: `PUT /v1/activities/{activity_id}`
**Description**: Updates an existing activity (color, schema, etc.).

**Request Body** (any subset of fields):
```json
{
  "name": "Updated name",
  "description": "Updated desc",
  "activity_schema": { ... },
  "icon": "🔄",
  "color": "#FF5733"
}
```

**Response**:
```json
{
  "data": {
    "id": 123,
    "name": "Updated name",
    "description": "Updated desc",
    "activity_schema": { ... },
    "icon": "🔄",
    "color": "#FF5733",
    "user_id": "UUID",
    "moment_count": 5,
    "created_at": "ISO datetime",
    "updated_at": "ISO datetime"
  },
  "message": "Activity updated successfully"
}
```

---

### Delete Activity
**Endpoint**: `DELETE /v1/activities/{activity_id}`
**Description**: Deletes the specified activity if owned by the current user.

**Response**:
```json
{
  "message": "Activity deleted successfully"
}
```
- If not found, returns `404 {"detail":"Activity not found"}`.

---

## 3. Moments

### Create Moment
**Endpoint**: `POST /v1/moments`
**Description**: Creates a new moment for a given activity.

**Request Body**:
```json
{
  "activity_id": 123,        // numeric ID of activity
  "data": { "book": "Book 1","pages": 50 },
  "timestamp": "2024-12-12T12:30:00Z",
  "note_id": int (optional)  // link to note if you want
}
```
- `data` must conform to the `activity_schema` of the associated activity.

**Response**:
```json
{
  "data": {
    "id": 1,
    "activity_id": 123,
    "data": { "book": "Book 1","pages":50 },
    "timestamp": "2024-12-12T12:30:00Z",
    "user_id": "UUID",
    "created_at": "ISO datetime",
    "updated_at": null
  },
  "message": "Moment created successfully"
}
```

---

### List Moments
**Endpoint**: `GET /v1/moments?page={page}&size={size}&activity_id={?}&start_date={?}&end_date={?}`
**Description**: Lists all moments for the current user with optional filtering by activity, date range, etc.

**Sample Request**:
```
GET /v1/moments?page=1&size=50&activity_id=123
Authorization: Bearer <token>
```

**Response** (paginated):
```json
{
  "data": {
    "items": [
      {
        "id": 1,
        "activity_id": 123,
        "data": { "book": "Book 1", "pages": 50 },
        "timestamp": "2024-12-12T12:30:00Z",
        "note_id": null,
        "created_at": "ISO datetime",
        "updated_at": null
      },
      ...
    ],
    "total": 2,
    "page": 1,
    "size": 50,
    "pages": 1
  },
  "message": "Retrieved 2 moments"
}
```

---

### Get Moment by ID
**Endpoint**: `GET /v1/moments/{moment_id}`
**Description**: Retrieves a single moment by numeric ID, if owned by the current user.

**Response**:
```json
{
  "data": {
    "id": 1,
    "activity_id": 123,
    "data": { ... },
    "timestamp": "2024-12-12T12:30:00Z",
    "user_id": "UUID",
    "created_at": "ISO datetime",
    "updated_at": "ISO datetime or null"
  }
}
```

---

### Update Moment
**Endpoint**: `PUT /v1/moments/{moment_id}`
**Description**: Updates a moment’s data or timestamp.

**Request Body** (partial or full):
```json
{
  "data": { "book":"New Title","pages":99 },
  "timestamp": "2024-12-25T09:00:00Z"
}
```

**Response**:
```json
{
  "data": {
    "id": 1,
    "activity_id": 123,
    "data": { "book":"New Title","pages":99 },
    "timestamp": "2024-12-25T09:00:00Z",
    "user_id": "UUID",
    "created_at": "ISO datetime",
    "updated_at": "ISO datetime"
  },
  "message": "Moment updated successfully"
}
```

---

### Delete Moment
**Endpoint**: `DELETE /v1/moments/{moment_id}`
**Description**: Deletes the specified moment if owned by the current user.

**Response**:
```json
{
  "message": "Moment deleted successfully"
}
```

---

### Attach / Detach Note from Moment
*(Only if you have these in `MomentRouter.py`—some references exist; your code might or might not use them.)*

- **Attach**: `PUT /v1/moments/{moment_id}/note`
  ```json
  {
    "note_id": 45
  }
  ```
- **Detach**: `DELETE /v1/moments/{moment_id}/note`

They return updated Moment data upon success.

---

## 4. Notes

### Create Note
**Endpoint**: `POST /v1/notes`
**Description**: Creates a new note. A note can include text content and optional attachments.

**Request Body** (simple):
```json
{
  "content": "string",
  "attachments": [
    {
      "type": "image|document|link",
      "url": "https://..."
    },
    ...
  ]
}
```

**Sample**:
```json
{
  "content": "My second note - with photo",
  "attachments": [
    {
      "type": "image",
      "url": "https://example.com/photo.jpg"
    }
  ]
}
```

**Response**:
```json
{
  "data": {
    "id": 10,
    "content": "My second note - with photo",
    "user_id": "UUID",
    "attachments": [
      {
        "type": "image",
        "url": "https://example.com/photo.jpg"
      }
    ],
    "processing_status": "NOT_PROCESSED" | "PENDING" | ...
    "enrichment_data": null,
    "processed_at": null,
    "created_at": "ISO datetime",
    "updated_at": null
  },
  "message": "Note created successfully"
}
```

*(Your test script shows a variant with `"attachment_url"` and `"attachment_type"` - your code in `NoteService.py` might unify them into an array of attachments. Just confirm your final structure. The domain expects `attachments: List[Dict[str, Any]]`.)*

---

### List Notes
**Endpoint**: `GET /v1/notes?page={page}&size={size}`
**Description**: Lists user’s notes with pagination.

**Response** (example):
```json
{
  "data": {
    "items": [
      {
        "id": 10,
        "content": "...",
        "user_id": "UUID",
        "attachments": [],
        "processing_status": "NOT_PROCESSED",
        "enrichment_data": null,
        "processed_at": null,
        "created_at": "2025-01-01T10:00:00Z",
        "updated_at": null
      },
      ...
    ],
    "total": 5,
    "page": 1,
    "size": 50,
    "pages": 1
  },
  "message": "Retrieved 5 notes"
}
```

---

### Get Note by ID
**Endpoint**: `GET /v1/notes/{note_id}`
**Description**: Retrieves a single note by numeric ID if owned by the current user.

**Response**:
```json
{
  "data": {
    "id": 10,
    "content": "...",
    "user_id": "UUID",
    "attachments": [...],
    "processing_status": "NOT_PROCESSED" | "...",
    "enrichment_data": null,
    "processed_at": null,
    "created_at": "ISO datetime",
    "updated_at": null
  }
}
```

---

### Update Note
**Endpoint**: `PUT /v1/notes/{note_id}`
**Description**: Updates note’s content, attachments, or processing status.

**Request Body** (partial or full):
```json
{
  "content": "Updated content",
  "attachments": [
    {
      "type": "document",
      "url": "https://example.com/updated.pdf"
    }
  ],
  "processing_status": "COMPLETED"
}
```

**Response**:
```json
{
  "data": {
    "id": 10,
    "content": "Updated content",
    "user_id": "UUID",
    "attachments": [
      {
        "type": "document",
        "url": "https://example.com/updated.pdf"
      }
    ],
    "processing_status": "COMPLETED",
    "enrichment_data": ...,
    "processed_at": "ISO datetime or null",
    "created_at": "ISO datetime",
    "updated_at": "ISO datetime"
  },
  "message": "Note updated successfully"
}
```

---

### Delete Note
**Endpoint**: `DELETE /v1/notes/{note_id}`
**Description**: Deletes the note if owned by the current user.

**Response**:
```json
{
  "message": "Note deleted successfully"
}
```

---

## 5. Tasks

### Create Task
**Endpoint**: `POST /v1/tasks`
**Description**: Creates a new task. A task can optionally reference a parent task or a note.

**Request Body**:
```json
{
  "title": "string (required)",
  "description": "string (required)",
  "status": "todo|in_progress|done",    // default 'todo'
  "priority": "low|medium|high|urgent", // default 'medium'
  "due_date": "ISO datetime (timezone-aware)",
  "tags": ["string", ...],
  "parent_id": 1,   // optional link to parent task
  "note_id": 10     // optional link to note
}
```

**Response**:
```json
{
  "data": {
    "id": 5,
    "title": "Task Title",
    "description": "Task details",
    "user_id": "UUID",
    "status": "todo",
    "priority": "medium",
    "due_date": "2025-01-30T12:00:00Z",
    "tags": ["test"],
    "parent_id": null,
    "note_id": null,
    "created_at": "ISO datetime",
    "updated_at": null
  },
  "message": "Task created successfully"
}
```

---

### List Tasks
**Endpoint**: `GET /v1/tasks?page={page}&size={size}&status=&priority=&due_before=&due_after=&parent_id=`
**Description**: Lists all tasks for the current user with optional filters (status, priority, date, etc.).

**Response** (paginated):
```json
{
  "data": {
    "items": [
      {
        "id": 5,
        "title": "Task Title",
        "description": "Task details",
        "user_id": "UUID",
        "status": "in_progress",
        "priority": "high",
        "due_date": "2025-01-30T12:00:00Z",
        "tags": ["test"],
        "parent_id": null,
        "note_id": null,
        "created_at": "ISO datetime",
        "updated_at": "ISO datetime or null"
      },
      ...
    ],
    "total": 2,
    "page": 1,
    "size": 50,
    "pages": 1
  },
  "message": "Retrieved 2 tasks"
}
```

---

### Get Task by ID
**Endpoint**: `GET /v1/tasks/{task_id}`
**Description**: Retrieves a specific task by numeric ID if owned by the current user.

**Response**:
```json
{
  "data": {
    "id": 5,
    "title": "Task Title",
    "description": "Task details",
    "user_id": "UUID",
    "status": "in_progress",
    "priority": "high",
    "due_date": "2025-01-30T12:00:00Z",
    "tags": ["test"],
    "parent_id": null,
    "note_id": null,
    "created_at": "ISO datetime",
    "updated_at": null
  }
}
```

---

### Update Task
**Endpoint**: `PUT /v1/tasks/{task_id}`
**Description**: Updates any fields of the task (title, description, status, etc.).

**Request Body** (partial or full):
```json
{
  "title": "Updated Title",
  "status": "in_progress",
  "priority": "high"
}
```

**Response**:
```json
{
  "data": {
    "id": 5,
    "title": "Updated Title",
    "description": "Task details",
    "user_id": "UUID",
    "status": "in_progress",
    "priority": "high",
    "due_date": "2025-01-30T12:00:00Z",
    "tags": ["test"],
    "parent_id": null,
    "note_id": null,
    "created_at": "ISO datetime",
    "updated_at": "ISO datetime"
  },
  "message": "Task updated successfully"
}
```

---

### Delete Task
**Endpoint**: `DELETE /v1/tasks/{task_id}`
**Description**: Deletes the specified task if owned by the current user.

**Response**:
```json
{
  "message": "Task deleted successfully"
}
```

---

### Update Task Status
**Endpoint**: `PUT /v1/tasks/{task_id}/status`
**Description**: Convenience endpoint to change status only.

**Request Body**:
```json
{
  "status": "todo|in_progress|done"
}
```
**Response**: Returns the updated Task data, same shape as a normal update.

---

### Get Subtasks
**Endpoint**: `GET /v1/tasks/{task_id}/subtasks?page={page}&size={size}`
**Description**: Lists all subtasks of a particular parent task, if the parent is owned by the current user.

**Response**:
```json
{
  "data": {
    "items": [ { "id": 6, "...": "..." }, ... ],
    "total": 1,
    "page": 1,
    "size": 50,
    "pages": 1
  },
  "message": "Retrieved 1 subtasks"
}
```

---

### Attach / Detach Note from Task
**Endpoints**:
- **Attach**: `PUT /v1/tasks/{task_id}/note`
  ```json
  {
    "note_id": 10
  }
  ```
  Returns the updated task object with `note_id` set.

- **Detach**: `DELETE /v1/tasks/{task_id}/note`
  Returns the updated task object with `note_id` = null.

---

## 6. Common Response Formats

You may notice three main response patterns:

1. **`GenericResponse<T>`**
   ```json
   {
     "data": { ... },  // Type T
     "message": "Some message"
   }
   ```
   e.g., creating an Activity returns `data: ActivityResponse`

2. **`MessageResponse`** (For success operations like delete)
   ```json
   {
     "message": "Resource deleted successfully"
   }
   ```

3. **`Error Response`**
   ```json
   {
     "detail": "Error message or object"
   }
   ```
   or
   ```json
   {
     "status": 400,
     "message": "Validation error",
     "errors": [...],
     ...
   }
   ```
   depending on the exception.

---

## Additional Notes

- **Authorization**: All protected endpoints require an `Authorization: Bearer <token>` header.
- **Pagination**: Many listing endpoints (activities, moments, notes, tasks) accept `page` and `size` query parameters.
- **Ownership**: Each entity (activity, moment, note, task) is tied to a single user. Attempting to access or modify another user’s entity will result in a `404 Not Found` or `401/403` depending on the code path.
- **Data Validation**:
  - Activities hold a `activity_schema` used to validate `moments.data`.
  - Tasks, notes, etc. have their own constraints.

---

**That should cover the end-to-end overview of the Friday API**. Your frontend developer can reference these endpoints, payloads, and response formats to implement the UI. The attached test script provides real-world usage examples that map to these documented endpoints. If you have any questions or need clarifications on an endpoint or data field, feel free to let me know!
