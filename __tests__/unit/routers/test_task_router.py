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
from domain.values import (
    TaskStatus,
    TaskPriority,
    ProcessingStatus,
)
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
    service = mocker.Mock(spec=TaskService)
    service.attach_note = mocker.Mock()
    service.detach_note = mocker.Mock()
    service.get_task_processing_status = mocker.Mock()
    service.reprocess_task = mocker.Mock()
    return service


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
        content="Test task content with details",
        status=TaskStatus.TODO,
        priority=TaskPriority.MEDIUM,
        due_date=current_time,
        user_id=mock_user.id,
        parent_id=None,
        processing_status=ProcessingStatus.PENDING,
        enrichment_data=None,
        processed_at=None,
        created_at=current_time,
        updated_at=current_time,
    )


@pytest.fixture
def mock_processed_task(mock_task):
    """Create a mock processed task response."""
    return TaskResponse(
        **{
            **mock_task.dict(),
            "processing_status": ProcessingStatus.COMPLETED,
            "enrichment_data": {
                "title": "Test task",
                "formatted": "Test task content with details",
                "tokens_used": 10,
                "model_name": "gpt-3.5-turbo",
                "created_at": mock_task.created_at.isoformat(),
                "metadata": {},
            },
            "processed_at": mock_task.created_at
            + timedelta(seconds=5),
        }
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
        "content": "Test task content with details",
        "status": TaskStatus.TODO,
        "priority": TaskPriority.MEDIUM,
        "due_date": now.isoformat(),
        "tags": ["test", "sample"],
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
    ):
        """Test creating a task successfully."""
        mock_service.create_task.return_value = mock_task
        response = client.post(
            "/api/v1/tasks",
            json={
                "content": "Test task content",
                "status": TaskStatus.TODO.value,
                "priority": TaskPriority.MEDIUM.value,
            },
            headers={
                "Authorization": f"Bearer {mock_auth_credentials.credentials}"
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert (
            data["message"]
            == "Task created successfully and queued for processing"
        )
        assert data["data"]["content"] == mock_task.content
        assert (
            data["data"]["processing_status"]
            == ProcessingStatus.PENDING.value
        )

    def test_get_task_processing_status_success(
        self,
        client,
        mock_service,
        mock_user,
        mock_processed_task,
        mock_auth_credentials,
    ):
        """Test getting task processing status successfully."""
        mock_service.get_task_processing_status.return_value = (
            mock_processed_task
        )
        response = client.get(
            "/api/v1/tasks/processing/1",
            headers={
                "Authorization": f"Bearer {mock_auth_credentials.credentials}"
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert (
            data["message"]
            == "Retrieved task processing status"
        )
        assert (
            data["data"]["processing_status"]
            == ProcessingStatus.COMPLETED.value
        )
        assert "enrichment_data" in data["data"]
        assert (
            data["data"]["enrichment_data"]["title"]
            == "Test task"
        )

    def test_reprocess_task_success(
        self,
        client,
        mock_service,
        mock_user,
        mock_auth_credentials,
    ):
        """Test requesting task reprocessing successfully."""
        response = client.post(
            "/api/v1/tasks/1/reprocess",
            headers={
                "Authorization": f"Bearer {mock_auth_credentials.credentials}"
            },
        )
        assert response.status_code == 202
        data = response.json()
        assert (
            data["message"] == "Task reprocessing requested"
        )
        assert (
            data["data"]["message"]
            == "Task queued for reprocessing"
        )
        mock_service.reprocess_task.assert_called_once_with(
            1, mock_user.id
        )

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
            "content": "",  # Empty content should fail validation
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
            "content": "Test task content",
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
            "size": 50,
            "pages": 1,
        }

        response = client.get(
            "/api/v1/tasks",
            params={
                "status": TaskStatus.TODO.value,
                "priority": TaskPriority.HIGH.value,
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
            topic_id=None,
            page=1,
            size=50,
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
            content="Updated task content",
            status=TaskStatus.IN_PROGRESS,
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
        mock_user,
        mock_auth_credentials,
        mock_service,
    ):
        """Test creating a task."""
        # Configure mock service to return a proper task response
        now = datetime.now(timezone.utc)
        mock_response = TaskResponse(
            id=1,
            content=sample_task_data["content"],
            status=sample_task_data["status"],
            priority=sample_task_data["priority"],
            due_date=datetime.fromisoformat(
                sample_task_data["due_date"]
            ),
            user_id=mock_user.id,
            created_at=now,
            updated_at=None,
            parent_id=None,
            processing_status=ProcessingStatus.PENDING,
            enrichment_data=None,
            processed_at=None,
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
            task_response.content
            == sample_task_data["content"]
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

    def test_attach_note_success(
        self,
        client,
        mock_service,
        mock_user,
        mock_task,
        mock_auth_credentials,
    ):
        """Test attaching a note to a task successfully."""
        task_id = 1
        note_id = 1

        mock_service.attach_note.return_value = mock_task

        response = client.put(
            f"/api/v1/tasks/{task_id}/note",
            params={"note_id": note_id},
            headers={
                "Authorization": f"Bearer {mock_auth_credentials.credentials}"
            },
        )

        assert response.status_code == 200
        assert response.json()["data"]["id"] == mock_task.id
        mock_service.attach_note.assert_called_once_with(
            task_id, note_id, mock_user.id
        )

    def test_detach_note_success(
        self,
        client,
        mock_service,
        mock_user,
        mock_task,
        mock_auth_credentials,
    ):
        """Test detaching a note from a task successfully."""
        task_id = 1

        mock_service.detach_note.return_value = mock_task

        response = client.delete(
            f"/api/v1/tasks/{task_id}/note",
            headers={
                "Authorization": f"Bearer {mock_auth_credentials.credentials}"
            },
        )

        assert response.status_code == 200
        assert response.json()["data"]["id"] == mock_task.id
        mock_service.detach_note.assert_called_once_with(
            task_id, mock_user.id
        )

    def test_attach_note_unauthenticated(
        self,
        client,
        mock_service,
    ):
        """Test attaching a note without authentication."""
        task_id = 1
        note_id = 1

        response = client.put(
            f"/api/v1/tasks/{task_id}/note",
            params={"note_id": note_id},
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

    def test_detach_note_unauthenticated(
        self,
        client,
        mock_service,
    ):
        """Test detaching a note without authentication."""
        task_id = 1

        response = client.delete(
            f"/api/v1/tasks/{task_id}/note",
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

    def test_update_task_topic_success(
        self,
        client,
        mock_service,
        mock_user,
        mock_task,
        mock_auth_credentials,
    ):
        """Test updating a task's topic successfully."""
        mock_service.update_task_topic.return_value = (
            mock_task
        )

        response = client.put(
            "/api/v1/tasks/1/topic",
            params={"topic_id": 123},
            headers={
                "Authorization": f"Bearer {mock_auth_credentials.credentials}"
            },
        )

        assert response.status_code == 200
        mock_service.update_task_topic.assert_called_once_with(
            1,
            mock_user.id,
            123,
        )

    def test_update_task_topic_remove(
        self,
        client,
        mock_service,
        mock_user,
        mock_task,
        mock_auth_credentials,
    ):
        """Test removing a task's topic successfully."""
        mock_service.update_task_topic.return_value = (
            mock_task
        )

        response = client.put(
            "/api/v1/tasks/1/topic",
            headers={
                "Authorization": f"Bearer {mock_auth_credentials.credentials}"
            },
        )

        assert response.status_code == 200
        mock_service.update_task_topic.assert_called_once_with(
            1,
            mock_user.id,
            None,
        )

    def test_list_tasks_by_topic_success(
        self,
        client,
        mock_service,
        mock_user,
        mock_task,
        mock_auth_credentials,
    ):
        """Test listing tasks by topic successfully."""
        mock_service.get_tasks_by_topic.return_value = {
            "items": [mock_task.model_dump()],
            "total": 1,
            "page": 1,
            "size": 50,
            "pages": 1,
        }

        response = client.get(
            "/api/v1/tasks/by-topic/123",
            headers={
                "Authorization": f"Bearer {mock_auth_credentials.credentials}"
            },
        )

        assert response.status_code == 200
        mock_service.get_tasks_by_topic.assert_called_once_with(
            123,
            mock_user.id,
            page=1,
            size=50,
        )
