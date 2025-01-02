"""Unit tests for TaskRouter."""

from datetime import datetime, timezone, timedelta
import pytest
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient
from fastapi.security import HTTPAuthorizationCredentials
from uuid import uuid4

from dependencies import get_current_user
from routers.v1.TaskRouter import router
from services.TaskService import TaskService
from domain.values import TaskStatus, TaskPriority
from domain.exceptions import TaskValidationError
from schemas.pydantic.TaskSchema import (
    TaskUpdate,
    TaskResponse,
)
from orm.UserModel import User


@pytest.fixture
def app(mock_user, mock_service):
    """Create a test FastAPI application."""
    app = FastAPI()

    async def mock_get_current_user():
        return mock_user

    app.dependency_overrides[
        get_current_user
    ] = mock_get_current_user
    app.dependency_overrides[
        TaskService
    ] = lambda: mock_service
    app.include_router(router, prefix="/api")
    return app


@pytest.fixture
def client(app):
    """Create a test client."""
    return TestClient(app)


@pytest.fixture
def mock_service(mocker):
    """Create a mock TaskService."""
    return mocker.Mock(spec=TaskService)


@pytest.fixture
def mock_user():
    """Create a mock user."""
    current_time = datetime.now(timezone.utc)
    return User(
        id=str(uuid4()),
        username="testuser",
        key_id=str(uuid4()),
        user_secret="test-secret-hash",
        created_at=current_time,
        updated_at=current_time,
    )


@pytest.fixture
def mock_task(mock_user):
    """Create a mock task response."""
    current_time = datetime.now(timezone.utc)
    return TaskResponse(
        id=1,
        title="Test Task",
        description="Test Description",
        status=TaskStatus.TODO,
        priority=TaskPriority.MEDIUM,
        due_date=current_time,
        user_id=mock_user.id,  # Use the mock user's ID
        parent_id=None,
        created_at=current_time,
        updated_at=current_time,
    )


@pytest.fixture
def mock_auth_credentials():
    """Create mock auth credentials."""
    return HTTPAuthorizationCredentials(
        scheme="Bearer",
        credentials="test-token",
    )


@pytest.fixture
def sample_task_data():
    """Create sample task data."""
    now = datetime.now(timezone.utc)
    return {
        "title": "Test Task",
        "description": "Test Description",
        "status": "todo",
        "priority": "medium",
        "tags": ["test", "sample"],
        "due_date": (now + timedelta(days=30)).isoformat(),
    }


class TestTaskRouter:
    """Test cases for TaskRouter."""

    def test_create_task_success(
        self,
        client,
        mock_service,
        mock_user,
        mock_task,
        mock_auth_credentials,
        mocker,
    ):
        """Test creating a task successfully."""
        mock_service.create_task.return_value = mock_task

        # Create task data with ISO formatted date
        task_data = {
            "title": "Test Task",
            "description": "Test Description",
            "status": TaskStatus.TODO.value,
            "priority": TaskPriority.MEDIUM.value,
            "due_date": datetime.now(
                timezone.utc
            ).isoformat(),
        }

        response = client.post(
            "/api/v1/tasks",
            json=task_data,
            headers={
                "Authorization": f"Bearer {mock_auth_credentials.credentials}"
            },
        )

        assert response.status_code == 201
        assert (
            response.json()["data"]["title"] == "Test Task"
        )
        mock_service.create_task.assert_called_once()

    def test_create_task_validation_error(
        self,
        client,
        mock_service,
        mock_user,
        mock_auth_credentials,
    ):
        """Test task creation with invalid data."""
        mock_service.create_task.side_effect = (
            TaskValidationError("Invalid task data")
        )

        # Send invalid task data directly as dict
        task_data = {
            "title": "",  # Empty title should fail validation
            "description": "Test Description",
            "status": TaskStatus.TODO.value,
            "priority": TaskPriority.MEDIUM.value,
            "due_date": datetime.now(
                timezone.utc
            ).isoformat(),
        }

        response = client.post(
            "/api/v1/tasks",
            json=task_data,
            headers={
                "Authorization": f"Bearer {mock_auth_credentials.credentials}"
            },
        )

        assert response.status_code == 422

    def test_create_task_unauthenticated(
        self,
        client,
        mock_service,
    ):
        """Test task creation without authentication."""
        # Send task data directly as dict
        task_data = {
            "title": "Test Task",
            "description": "Test Description",
            "status": TaskStatus.TODO.value,
            "priority": TaskPriority.MEDIUM.value,
            "due_date": datetime.now(
                timezone.utc
            ).isoformat(),
        }

        response = client.post(
            "/api/v1/tasks",
            json=task_data,
        )

        assert response.status_code == 401
        response_data = response.json()
        assert (
            response_data["detail"]["code"]
            == "UNAUTHORIZED"
        )
        assert (
            "Invalid or missing authentication token"
            in response_data["detail"]["message"]
        )
        assert (
            response_data["detail"]["type"]
            == "AuthenticationError"
        )

    def test_list_tasks_success(
        self,
        client,
        mock_service,
        mock_user,
        mock_task,
        mock_auth_credentials,
    ):
        """Test listing tasks successfully."""
        mock_service.list_tasks.return_value = {
            "items": [mock_task.model_dump()],
            "total": 1,
            "page": 1,
            "size": 10,
            "pages": 1,
        }

        response = client.get(
            "/api/v1/tasks",
            headers={
                "Authorization": f"Bearer {mock_auth_credentials.credentials}"
            },
        )

        assert response.status_code == 200
        assert response.json()["data"]["total"] == 1
        mock_service.list_tasks.assert_called_once()

    def test_list_tasks_with_filters(
        self,
        client,
        mock_service,
        mock_user,
        mock_task,
        mock_auth_credentials,
    ):
        """Test listing tasks with filters."""
        mock_service.list_tasks.return_value = {
            "items": [mock_task.model_dump()],
            "total": 1,
            "page": 1,
            "size": 10,
            "pages": 1,
        }

        response = client.get(
            "/api/v1/tasks",
            params={
                "status": TaskStatus.TODO.value,
                "priority": TaskPriority.HIGH.value,
                "page": 1,
                "size": 10,
            },
            headers={
                "Authorization": f"Bearer {mock_auth_credentials.credentials}"
            },
        )

        assert response.status_code == 200
        mock_service.list_tasks.assert_called_once_with(
            user_id=mock_user.id,
            status=TaskStatus.TODO,
            priority=TaskPriority.HIGH,
            due_before=None,
            due_after=None,
            parent_id=None,
            page=1,
            size=10,
        )

    def test_get_task_not_found(
        self,
        client,
        mock_service,
        mock_user,
        mock_auth_credentials,
    ):
        """Test getting a non-existent task."""
        mock_service.get_task.side_effect = HTTPException(
            status_code=404,
            detail="Task not found",
        )

        response = client.get(
            "/api/v1/tasks/999",
            headers={
                "Authorization": f"Bearer {mock_auth_credentials.credentials}"
            },
        )

        assert response.status_code == 404
        assert response.json()["detail"] == "Task not found"

    def test_update_task_invalid_status(
        self,
        client,
        mock_service,
        mock_user,
        mock_auth_credentials,
    ):
        """Test updating a task with invalid status transition."""
        mock_service.update_task_status.side_effect = (
            HTTPException(
                status_code=422,
                detail="Invalid status transition",
            )
        )

        response = client.put(
            "/api/v1/tasks/1/status",
            params={"status": TaskStatus.DONE.value},
            headers={
                "Authorization": f"Bearer {mock_auth_credentials.credentials}"
            },
        )

        assert response.status_code == 422
        assert (
            response.json()["detail"]
            == "Invalid status transition"
        )

    def test_get_subtasks_pagination(
        self,
        client,
        mock_service,
        mock_user,
        mock_task,
        mock_auth_credentials,
    ):
        """Test getting subtasks with pagination."""
        mock_service.get_subtasks.return_value = {
            "items": [mock_task.model_dump()],
            "total": 1,
            "page": 2,
            "size": 5,
            "pages": 3,
        }

        response = client.get(
            "/api/v1/tasks/1/subtasks",
            params={"page": 2, "size": 5},
            headers={
                "Authorization": f"Bearer {mock_auth_credentials.credentials}"
            },
        )

        assert response.status_code == 200
        assert response.json()["data"]["page"] == 2
        assert response.json()["data"]["size"] == 5
        mock_service.get_subtasks.assert_called_once_with(
            1,
            mock_user.id,
            page=2,
            size=5,
        )

    def test_update_task_wrong_user(
        self,
        client,
        mock_service,
        mock_user,
        mock_auth_credentials,
    ):
        """Test updating a task belonging to another user."""
        mock_service.update_task.side_effect = (
            HTTPException(
                status_code=403,
                detail="Not authorized to update this task",
            )
        )

        task_data = TaskUpdate(
            title="Updated Task",
            description="Updated Description",
        )

        response = client.put(
            "/api/v1/tasks/1",
            json=task_data.model_dump(exclude_none=True),
            headers={
                "Authorization": f"Bearer {mock_auth_credentials.credentials}"
            },
        )

        assert response.status_code == 403
        assert (
            response.json()["detail"]
            == "Not authorized to update this task"
        )

    def test_delete_task_success(
        self,
        client,
        mock_service,
        mock_user,
        mock_auth_credentials,
    ):
        """Test deleting a task successfully."""
        response = client.delete(
            "/api/v1/tasks/1",
            headers={
                "Authorization": f"Bearer {mock_auth_credentials.credentials}"
            },
        )

        assert response.status_code == 200
        assert (
            response.json()["message"]
            == "Task deleted successfully"
        )
        mock_service.delete_task.assert_called_once_with(
            1,
            mock_user.id,
        )

    def test_delete_task_not_found(
        self,
        client,
        mock_service,
        mock_user,
        mock_auth_credentials,
    ):
        """Test deleting a non-existent task."""
        mock_service.delete_task.side_effect = (
            HTTPException(
                status_code=404,
                detail="Task not found",
            )
        )

        response = client.delete(
            "/api/v1/tasks/999",
            headers={
                "Authorization": f"Bearer {mock_auth_credentials.credentials}"
            },
        )

        assert response.status_code == 404
        assert response.json()["detail"] == "Task not found"

    def test_create_task(
        self,
        client,
        sample_task_data,
        sample_user,
        mock_auth_credentials,
        mock_service,
    ):
        """Test creating a task."""
        # Configure mock service to return a proper task response
        now = datetime.now(timezone.utc)
        mock_response = TaskResponse(
            id=1,
            title=sample_task_data["title"],
            description=sample_task_data["description"],
            status=sample_task_data["status"],
            priority=sample_task_data["priority"],
            tags=sample_task_data["tags"],
            due_date=datetime.fromisoformat(
                sample_task_data["due_date"]
            ),
            user_id=sample_user.id,
            created_at=now,
            updated_at=None,
            parent_id=None,
        )
        mock_service.create_task.return_value = (
            mock_response
        )

        response = client.post(
            "/api/v1/tasks",
            json=sample_task_data,
            headers={
                "Authorization": f"Bearer {mock_auth_credentials.credentials}"
            },
        )
        assert response.status_code == 201

        data = response.json()["data"]
        # Verify response matches TaskResponse schema
        task_response = TaskResponse.model_validate(data)
        assert (
            task_response.title == sample_task_data["title"]
        )
        assert (
            task_response.description
            == sample_task_data["description"]
        )
        assert (
            task_response.status
            == sample_task_data["status"]
        )
        assert (
            task_response.priority
            == sample_task_data["priority"]
        )
        # Verify timestamp fields
        assert task_response.created_at is not None
        assert task_response.created_at.tzinfo is not None
        assert (
            task_response.updated_at is None
        )  # Should be None for new tasks
