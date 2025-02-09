Below is a **project plan** for creating a new **"timeline"** API endpoint in your system. This plan covers the **functional requirements**, **high-level design**, and a **detailed breakdown of tasks** (epics, tasks, subtasks) following a clean architecture / DDD approach.

---

## 1. **Overview & Requirements**

### 1.1 Purpose of the Timeline API
We want an API that:
1. Retrieves a reverse-chronological feed of different entity types: **Tasks**, **Notes**, **Moments**, (and possibly more in the future).
2. Supports **filters**:
   - By entity type (e.g., only tasks, only notes, only moments, or any combination).
   - By **keyword** search across the entities (content, title, description, etc.).
3. Provides a **unified view** so front-end can display a timeline or activity feed.

### 1.2 Desired Features
1. **Reverse Chronological Sorting**: The timeline should list entities (tasks/notes/moments) from newest to oldest.
2. **Filter by Entity Type**: For example, `entity_type=task` or `entity_type=notes,moments` etc.
3. **Keyword Search**: If a `keyword` is passed, only entities whose content/title/description matches that keyword should be returned. (Exact search logic can vary—like partial match, full-text, etc.)
4. **Paginated**: Typically, we will want page/size (just like the rest of the endpoints).
5. **Extensibility**: Easy to add new entity types in the future.

### 1.3 Endpoint Specification (Draft)
- **Path**: `GET /v1/timeline`
- **Query Params**:
  - `page`: Page number (default = 1)
  - `size`: Items per page (default = 50)
  - `entity_types`: Comma-separated list of types to include (`tasks,notes,moments`). If omitted, show all.
  - `keyword`: Optional search term across relevant fields.
- **Response**:
  ```json
  {
    "items": [
      {
        "type": "task",          // or "note", "moment"
        "id": 123,
        "title": "...",
        "description": "...",
        "content": "...",
        "timestamp": "2024-12-12T14:30:00Z",
        // Additional fields depending on type
      },
      ...
    ],
    "page": 1,
    "size": 50,
    "total": 123,
    "pages": 3
  }
  ```
  (We may unify the fields, or use sub-objects depending on how we want to structure it.)

---

## 2. **High-Level Design (DDD / Clean Architecture)**

```
┌───────────────────────────────────┐
│           Presentation            │  (FastAPI Routers / Controllers)
└───────────────────────────────────┘
                ▼
┌───────────────────────────────────┐
│        Application/Service        │  (TimelineService, aggregator logic)
└───────────────────────────────────┘
                ▼
┌───────────────────────────────────┐
│        Domain / Entities          │   (Domain Models for Task, Note, Moment)
│  + New: A "TimelineEvent" Value   │
└───────────────────────────────────┘
                ▼
┌───────────────────────────────────┐
│        Infrastructure/ORM         │  (TaskRepository, NoteRepository,
│         Repositories, etc.)       │   MomentRepository)
└───────────────────────────────────┘
```

### 2.1 Domain Layer
- We might define a **Value Object** or a small Domain Model named **`TimelineEventData`** containing fields:
  ```python
  class TimelineEventData:
      entity_type: str       # "task", "note", "moment"
      entity_id: int
      timestamp: datetime
      title: Optional[str]
      description: Optional[str]
      content: Optional[str]
      ...
  ```
- This domain model is ephemeral: it’s built by aggregating data from Tasks, Notes, Moments to present them in a unified list.

### 2.2 Application Layer (Service)
1. **TimelineService**:
   - **Aggregates** tasks, notes, and moments from the DB (via repositories).
   - **Merges** them into a single list of `TimelineEventData`.
   - **Applies** sorting, pagination, and filtering (keyword, entity types).
   - **Returns** a uniform domain list to the router.

### 2.3 Infrastructure Layer
- We **reuse** existing Repositories:
  - `TaskRepository` might add a new `list_recent_tasks(...)` method.
  - `NoteRepository` might add `list_recent_notes(...)`.
  - `MomentRepository` already has `list_moments`, but we can add a specialized method.
- Or we can just reuse the existing `.list()` or `.list_*` methods, passing in filters for date ordering, etc.

### 2.4 Presentation Layer (API Router)
- A new router method: `GET /v1/timeline` in something like `TimelineRouter.py`.
- We parse query params (`page`, `size`, `entity_types`, `keyword`).
- We call `TimelineService.get_timeline(...)`.
- We return a consistent JSON structure (like the other endpoints).

---

## 3. **Implementation Plan**

Below is a recommended breakdown into **Epics** → **User Stories / Tasks** → **Subtasks**. Adapt as needed.

### **Epic 1**: **Add Timeline Domain & Aggregation Logic**

#### Task 1: Define Domain Model / Value Object
- **Subtask 1.1**: Create a `TimelineEventData` class in the **domain layer**:
  ```python
  @dataclass
  class TimelineEventData:
      entity_type: str  # "task", "note", "moment"
      entity_id: int
      timestamp: datetime
      title: Optional[str]
      description: Optional[str]
      # Maybe content for notes, or partial content, etc.
  ```
- **Subtask 1.2**: Decide how to store minimal info about the entity (title, description, etc.). Possibly store it in a single `summary` field or in separate fields.

#### Task 2: Create Timeline Aggregation in Application/Service
- **Subtask 2.1**: In `services/TimelineService.py` (new file):
  - A `TimelineService` class with a method like:
    ```python
    def get_timeline(
        self,
        user_id: str,
        page: int,
        size: int,
        entity_types: List[str],
        keyword: Optional[str]
    ) -> List[TimelineEventData]:
        ...
    ```
- **Subtask 2.2**: Inside `get_timeline`, call each repository method (Tasks, Notes, Moments) to retrieve data that belongs to the user. Possibly retrieving all in a certain date range or just everything.
- **Subtask 2.3**: Convert them to `TimelineEventData` objects.
- **Subtask 2.4**: Merge them into a single list. Sort by `timestamp` descending.
- **Subtask 2.5**: Filter out by `entity_type` if requested.
- **Subtask 2.6**: Perform a simple **keyword** match if needed:
  - Could be naive (lowercase content includes `keyword`).
  - Or skip if no `keyword`.
- **Subtask 2.7**: Apply pagination, returning the final subset.

#### Task 3: Possibly add specialized Repository Methods
- If needed, define e.g. `list_recent_for_timeline(...)` in each repository. Or just reuse `.list_*(...)` with ordering by `updated_at` or `created_at`.
  - **Subtask 3.1**: Add a `list_tasks_for_timeline(user_id: str, keyword: Optional[str]) -> List[Task]` that returns tasks in descending order of `updated_at` or `created_at`.
  - **Subtask 3.2**: Similarly for `NoteRepository` and `MomentRepository`.

---

### **Epic 2**: **Add Timeline Router**

#### Task 4: Implement the Controller/Router
- **Subtask 4.1**: Create a `TimelineRouter.py` under `routers/v1/`. Something like:
  ```python
  from fastapi import APIRouter, Depends
  from services.TimelineService import TimelineService
  @router.get("/timeline")
  async def get_timeline(
      page: int = 1,
      size: int = 50,
      entity_types: str = "",
      keyword: str = None,
      current_user: User = Depends(get_current_user),
      service: TimelineService = Depends()
  ):
      ...
  ```
- **Subtask 4.2**: Parse the `entity_types` param (comma-separated) into a list.
- **Subtask 4.3**: Call `service.get_timeline(...)`.
- **Subtask 4.4**: Wrap the returned list in a standard response format (like `GenericResponse` with pagination).

#### Task 5: Ensure JSON Schema for the “TimelineEvent” in the Response
- Decide on the shape of each “item” in the timeline. Possibly:
  ```json
  {
    "items": [
      {
        "type": "task",
        "id": 101,
        "title": "Meeting notes",
        "description": "...",
        "timestamp": "2025-01-10T09:00:00Z"
      },
      {
        "type": "note",
        "id": 12,
        "content": "This is a note",
        "timestamp": "2025-01-09T18:30:00Z"
      }
    ],
    "page": 1,
    "size": 50,
    "total": 2,
    "pages": 1
  }
  ```
- We can unify them or conditionally include fields. For consistent front-end usage, we might always return a few standard fields and then an optional “details” object for type-specific data.

---

### **Epic 3**: **Filtering & Search**

#### Task 6: Implement Keyword Filtering
- **Subtask 6.1**: In the domain service, if `keyword` is present, we filter results. We could:
  - Either do a naive in-memory filter after retrieving them.
  - Or push the filter into the DB queries with a `LIKE '%keyword%'` if columns are text-based.
- **Subtask 6.2**: For a more advanced approach, consider a full-text index or a separate search engine. But that might be scope for the future.

---

### **Epic 4**: **Testing & Documentation**

#### Task 7: Unit Tests in Domain / Service
- **Subtask 7.1**: Test `TimelineService.get_timeline()` with various data sets.
- **Subtask 7.2**: Test filtering by entity type and keyword.
- **Subtask 7.3**: Test pagination logic.

#### Task 8: Integration Tests / End-to-End
- **Subtask 8.1**: Add an integration test hitting the `GET /v1/timeline` endpoint, verifying JSON structure, sorting, filtering, etc.

#### Task 9: Document the New Endpoint
- **Subtask 9.1**: Update the API docs (OpenAPI or external doc) with the new route, describing query params, response schema, examples, etc.
- **Subtask 9.2**: Possibly update your test script (like the one you shared) to do at least one timeline test call.

---

## 4. **Example Timeline API Flow**

1. **User calls** `GET /v1/timeline?entity_types=task,note&keyword=running&page=1&size=20`.
2. **Auth** is done via bearer token in headers.
3. **TimelineService**:
   1. Pull tasks that belong to the user and contain “running” in `title`, `description` (in DB or in memory).
   2. Pull notes that contain “running” in `content`.
   3. Convert each to `TimelineEventData` with proper `timestamp`.
   4. Merge/sort by descending timestamp.
   5. Slice page 1 of size 20, return in the correct format.
4. **Output**: JSON with `items`, `page`, `size`, etc.

---

## 5. **Summary**

By following the **epics** and **tasks** above, you’ll have:
- A unified **Timeline** domain approach (aggregating data from tasks/notes/moments).
- A new **TimelineService** to handle filtering, sorting, merging.
- A **TimelineRouter** to expose `GET /v1/timeline`.
- **Tests** verifying correctness, security, and performance.
- **Documentation** so your front-end team can build a “timeline” or “activity feed” UI easily.

This plan should be flexible enough to add more entity types in the future (e.g., new “events” or “messages”) by hooking them into the aggregator.
