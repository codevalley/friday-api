# Task GraphQL API Documentation

## Types

### Task
The main Task type representing a user's task.

```graphql
type Task {
  id: Int!                    # Unique identifier
  title: String!              # Task title (1-255 chars)
  description: String!        # Task description
  status: TaskStatus!         # Current status
  priority: TaskPriority!     # Task priority
  userId: String!            # Owner's user ID
  parentId: Int              # Parent task ID (optional)
  createdAt: DateTime!       # Creation timestamp
  updatedAt: DateTime!       # Last update timestamp
  tags: [String!]!          # List of tags
  dueDate: DateTime         # Due date (optional)
}
```

### TaskStatus
Enum representing the possible task statuses.

```graphql
enum TaskStatus {
  TODO         # Initial status
  IN_PROGRESS  # Task is being worked on
  DONE         # Task is completed
}
```

### TaskPriority
Enum representing the task priority levels.

```graphql
enum TaskPriority {
  LOW     # Low priority
  MEDIUM  # Medium priority
  HIGH    # High priority
  URGENT  # Urgent priority
}
```

### TaskInput
Input type for creating a new task.

```graphql
input TaskInput {
  title: String!              # Task title
  description: String!        # Task description
  status: TaskStatus!         # Initial status
  priority: TaskPriority!     # Task priority
  parentId: Int              # Parent task ID (optional)
  tags: [String!]            # List of tags (optional)
  dueDate: DateTime          # Due date (optional)
}
```

### TaskUpdateInput
Input type for updating an existing task.

```graphql
input TaskUpdateInput {
  title: String              # New title (optional)
  description: String        # New description (optional)
  status: TaskStatus         # New status (optional)
  priority: TaskPriority     # New priority (optional)
  parentId: Int             # New parent task ID (optional)
  tags: [String!]           # New tags (optional)
  dueDate: DateTime         # New due date (optional)
}
```

## Queries

### Get Task by ID
Retrieve a single task by its ID.

```graphql
query GetTask($id: Int!) {
  getTask(id: $id) {
    id
    title
    description
    status
    priority
    dueDate
    tags
  }
}
```

### List Tasks
List tasks with pagination and filtering.

```graphql
query ListTasks(
  $page: Int = 1
  $size: Int = 10
  $status: TaskStatus
  $priority: TaskPriority
) {
  listTasks(
    page: $page
    size: $size
    status: $status
    priority: $priority
  ) {
    items {
      id
      title
      status
      priority
      dueDate
    }
    total
    page
    size
    pages
  }
}
```

### Get Subtasks
Get subtasks for a specific task.

```graphql
query GetSubtasks(
  $taskId: Int!
  $page: Int = 1
  $size: Int = 10
) {
  getSubtasks(
    taskId: $taskId
    page: $page
    size: $size
  ) {
    items {
      id
      title
      status
      priority
    }
    total
    page
    size
  }
}
```

## Mutations

### Create Task
Create a new task.

```graphql
mutation CreateTask($input: TaskInput!) {
  createTask(task: $input) {
    id
    title
    description
    status
    priority
    dueDate
    tags
  }
}
```

Example input:
```json
{
  "input": {
    "title": "Complete project documentation",
    "description": "Write comprehensive documentation for the project",
    "status": "TODO",
    "priority": "HIGH",
    "tags": ["documentation", "important"],
    "dueDate": "2024-02-01T00:00:00Z"
  }
}
```

### Update Task
Update an existing task.

```graphql
mutation UpdateTask(
  $id: Int!
  $input: TaskUpdateInput!
) {
  updateTask(taskId: $id, task: $input) {
    id
    title
    description
    status
    priority
    dueDate
    tags
  }
}
```

Example input:
```json
{
  "id": 1,
  "input": {
    "status": "IN_PROGRESS",
    "priority": "URGENT",
    "tags": ["documentation", "urgent"]
  }
}
```

### Delete Task
Delete a task.

```graphql
mutation DeleteTask($id: Int!) {
  deleteTask(taskId: $id)
}
```

## Error Handling

The API uses consistent error codes and messages for different types of errors:

### Authentication Errors
- `UNAUTHORIZED` (401): Authentication required
- `FORBIDDEN` (403): Not authorized to access the task

### Validation Errors
- `TASK_CONTENT_ERROR` (400): Title or description validation failed
- `TASK_INVALID_STATUS` (400): Invalid status transition
- `TASK_PARENT_ERROR` (404): Invalid parent task reference
- `TASK_DATE_ERROR` (400): Invalid date format or value
- `TASK_PRIORITY_ERROR` (400): Invalid priority value
- `TASK_VALIDATION_ERROR` (400): General validation error

### Not Found Errors
- `TASK_NOT_FOUND` (404): Task does not exist

### Server Errors
- `INTERNAL_SERVER_ERROR` (500): Unexpected server error

Example error response:
```json
{
  "errors": [
    {
      "message": "due_date cannot be earlier than created_at",
      "code": "TASK_DATE_ERROR",
      "type": "GraphQLError"
    }
  ]
}
```

## Integration Tests

See `__tests__/integration/graphql/test_task_integration.py` for complete integration test examples.

### Example Test: Create and Update Task
```python
def test_create_and_update_task_flow():
    """Test the complete flow of creating and updating a task."""
    # Create a task
    create_mutation = """
    mutation CreateTask($input: TaskInput!) {
        createTask(task: $input) {
            id
            title
            status
        }
    }
    """
    variables = {
        "input": {
            "title": "Test Task",
            "description": "Test Description",
            "status": "TODO",
            "priority": "MEDIUM"
        }
    }
    result = client.execute(create_mutation, variables)
    task_id = result.data["createTask"]["id"]

    # Update the task
    update_mutation = """
    mutation UpdateTask($id: Int!, $input: TaskUpdateInput!) {
        updateTask(taskId: $id, task: $input) {
            id
            status
        }
    }
    """
    variables = {
        "id": task_id,
        "input": {
            "status": "IN_PROGRESS"
        }
    }
    result = client.execute(update_mutation, variables)
    assert result.data["updateTask"]["status"] == "IN_PROGRESS"
```

## Best Practices

1. Always include error handling in your queries/mutations
2. Use pagination for list operations
3. Request only the fields you need
4. Set appropriate status transitions (TODO → IN_PROGRESS → DONE)
5. Validate dates in UTC timezone
6. Keep task hierarchies shallow (avoid deep nesting)
7. Use meaningful tags for better organization
```
