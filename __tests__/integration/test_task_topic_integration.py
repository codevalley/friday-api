"""Integration tests for Task-Topic relationships."""

import pytest
from datetime import datetime, timezone
from uuid import uuid4

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from dependencies import get_current_user, get_queue
from routers.v1 import TaskRouter, TopicRouter
from services.TaskService import TaskService
from services.TopicService import TopicService
from domain.values import TaskStatus, TaskPriority
from orm.UserModel import User
from orm.BaseModel import Base
from schemas.pydantic.TopicSchema import TopicCreate
from schemas.pydantic.TaskSchema import (
    TaskCreate,
    TaskUpdate,
)
from typing import Dict, Any, Optional


@pytest.fixture(scope="session")
def test_db():
    """Create a test database."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    return engine


@pytest.fixture
def test_db_session(test_db):
    """Create a test database session."""
    Session = sessionmaker(bind=test_db)
    session = Session()
    try:
        yield session
    finally:
        session.rollback()
        session.close()


@pytest.fixture
def queue_service():
    """Mock queue service for testing."""

    class MockQueueService:
        def enqueue_task(
            self, task_type: str, task_data: Dict[str, Any]
        ) -> Optional[str]:
            return "mock-job-id"

        def enqueue_note(
            self, note_id: int
        ) -> Optional[str]:
            return "mock-job-id"

        def enqueue_activity(
            self, activity_id: int
        ) -> Optional[str]:
            return "mock-job-id"

        def get_job_status(
            self, job_id: str
        ) -> Dict[str, Any]:
            return {"status": "completed"}

        def get_queue_health(self) -> Dict[str, Any]:
            return {"status": "healthy"}

    return MockQueueService()


@pytest.fixture
def app(test_db_session, queue_service):
    """Create a test FastAPI application with real services."""
    app = FastAPI()

    # Use real services with test database and mock queue
    app.dependency_overrides[
        get_queue
    ] = lambda: queue_service
    app.dependency_overrides[
        TaskService
    ] = lambda: TaskService(test_db_session, queue_service)
    app.dependency_overrides[
        TopicService
    ] = lambda: TopicService(test_db_session)

    app.include_router(TaskRouter.router)
    app.include_router(TopicRouter.router)
    return app


@pytest.fixture
def test_user(test_db_session):
    """Create a test user."""
    user = User(
        id=str(uuid4()),
        username=f"testuser_{uuid4().hex[:8]}",
        key_id=str(uuid4()),
        user_secret="test-secret-hash",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    test_db_session.add(user)
    test_db_session.commit()
    return user


@pytest.fixture
def client(app, test_user):
    """Create a test client with authenticated user."""

    async def mock_get_current_user():
        return test_user

    app.dependency_overrides[
        get_current_user
    ] = mock_get_current_user
    client = TestClient(app)
    client.headers["Authorization"] = "Bearer test-token"
    return client


def test_task_topic_lifecycle(client, test_user):
    """Test complete lifecycle of task-topic relationship."""
    # 1. Create a topic
    topic_data = TopicCreate(name="Work", icon="💼")
    topic_response = client.post(
        "/v1/topics", json=topic_data.model_dump()
    )
    assert topic_response.status_code == 201
    topic_id = topic_response.json()["data"]["id"]

    # 2. Create a task with the topic
    task_data = TaskCreate(
        content="Complete Project: Finish the integration tests",
        status=TaskStatus.TODO,
        priority=TaskPriority.HIGH,
        topic_id=topic_id,
    )
    task_response = client.post(
        "/v1/tasks", json=task_data.model_dump()
    )
    assert task_response.status_code == 201
    task_id = task_response.json()["data"]["id"]
    assert (
        task_response.json()["data"]["topic_id"] == topic_id
    )

    # 3. Verify task appears in topic's task list
    topic_tasks = client.get(f"/v1/topics/{topic_id}/tasks")
    assert topic_tasks.status_code == 200
    assert any(
        task["id"] == task_id
        for task in topic_tasks.json()["data"]["items"]
    )

    # 4. Update task's topic
    new_topic_data = TopicCreate(name="Testing", icon="🧪")
    new_topic_response = client.post(
        "/v1/topics", json=new_topic_data.model_dump()
    )
    assert new_topic_response.status_code == 201
    new_topic_id = new_topic_response.json()["data"]["id"]

    task_update = TaskUpdate(topic_id=new_topic_id)
    task_update_response = client.put(
        f"/v1/tasks/{task_id}",
        json=task_update.model_dump(),
    )
    assert task_update_response.status_code == 200
    assert (
        task_update_response.json()["data"]["topic_id"]
        == new_topic_id
    )

    # 5. Verify task moved to new topic
    old_topic_tasks = client.get(
        f"/v1/topics/{topic_id}/tasks"
    )
    assert not any(
        task["id"] == task_id
        for task in old_topic_tasks.json()["data"]["items"]
    )

    new_topic_tasks = client.get(
        f"/v1/topics/{new_topic_id}/tasks"
    )
    assert any(
        task["id"] == task_id
        for task in new_topic_tasks.json()["data"]["items"]
    )


def test_topic_deletion_impact(client, test_user):
    """Test impact of topic deletion on associated tasks."""
    # 1. Create a topic
    topic_data = TopicCreate(name="Temporary", icon="⏳")
    topic_response = client.post(
        "/v1/topics", json=topic_data.model_dump()
    )
    assert topic_response.status_code == 201
    topic_id = topic_response.json()["data"]["id"]

    # 2. Create multiple tasks with the topic
    tasks = []
    for i in range(3):
        task_data = TaskCreate(
            content=f"Test task {i}: This is a test task",
            status=TaskStatus.TODO,
            priority=TaskPriority.MEDIUM,
            topic_id=topic_id,
        )
        response = client.post(
            "/v1/tasks", json=task_data.model_dump()
        )
        assert response.status_code == 201
        tasks.append(response.json()["data"]["id"])

    # 3. Delete the topic
    delete_response = client.delete(
        f"/v1/topics/{topic_id}"
    )
    assert delete_response.status_code == 200

    # 4. Verify tasks still exist but without topic
    for task_id in tasks:
        task_response = client.get(f"/v1/tasks/{task_id}")
        assert task_response.status_code == 200
        assert (
            task_response.json()["data"]["topic_id"] is None
        )


def test_task_topic_filtering(client, test_user):
    """Test task filtering and pagination with topics."""
    # 1. Create two topics
    topic1_data = TopicCreate(name="Work", icon="💼")
    topic2_data = TopicCreate(name="Personal", icon="🏠")

    topic1_response = client.post(
        "/v1/topics", json=topic1_data.model_dump()
    )
    topic2_response = client.post(
        "/v1/topics", json=topic2_data.model_dump()
    )

    topic1_id = topic1_response.json()["data"]["id"]
    topic2_id = topic2_response.json()["data"]["id"]

    # 2. Create tasks for each topic
    for i in range(5):
        task_data = TaskCreate(
            content=f"Work Task {i}: Work related task",
            status=TaskStatus.TODO,
            priority=TaskPriority.HIGH,
            topic_id=topic1_id,
        )
        client.post(
            "/v1/tasks", json=task_data.model_dump()
        )

        task_data = TaskCreate(
            content=f"Personal Task {i}: Personal stuff",
            status=TaskStatus.TODO,
            priority=TaskPriority.LOW,
            topic_id=topic2_id,
        )
        client.post(
            "/v1/tasks", json=task_data.model_dump()
        )

    # 3. Test filtering by topic
    work_tasks = client.get(
        f"/v1/tasks?topic_id={topic1_id}"
    )
    assert work_tasks.status_code == 200
    assert len(work_tasks.json()["data"]["items"]) == 5
    assert all(
        task["topic_id"] == topic1_id
        for task in work_tasks.json()["data"]["items"]
    )

    # 4. Test pagination
    paginated = client.get(
        f"/v1/tasks?topic_id={topic2_id}&page=1&size=3"
    )
    assert paginated.status_code == 200
    assert len(paginated.json()["data"]["items"]) == 3
    assert paginated.json()["data"]["total"] == 5


def test_task_topic_error_handling(client, test_user):
    """Test error handling in task-topic operations."""
    # 1. Try to create task with non-existent topic
    task_data = TaskCreate(
        content="Invalid Topic Task: This should fail",
        status=TaskStatus.TODO,
        priority=TaskPriority.MEDIUM,
        topic_id=99999,  # Non-existent topic ID
    )
    response = client.post(
        "/v1/tasks", json=task_data.model_dump()
    )
    assert response.status_code == 404
    assert (
        "topic not found"
        in response.json()["detail"]["message"].lower()
    )

    # 2. Create valid topic and task
    topic_data = TopicCreate(name="Valid Topic", icon="✅")
    topic_response = client.post(
        "/v1/topics", json=topic_data.model_dump()
    )
    topic_id = topic_response.json()["data"]["id"]

    task_data.topic_id = topic_id
    task_response = client.post(
        "/v1/tasks", json=task_data.model_dump()
    )
    task_id = task_response.json()["data"]["id"]

    # 3. Try to update task with non-existent topic
    task_update = TaskUpdate(topic_id=99999)
    task_update_response = client.put(
        f"/v1/tasks/{task_id}",
        json=task_update.model_dump(),
    )
    assert task_update_response.status_code == 404
    assert (
        "topic not found"
        in task_update_response.json()["detail"][
            "message"
        ].lower()
    )

    # 4. Try to get tasks for non-existent topic
    invalid_topic = client.get("/v1/topics/99999/tasks")
    assert invalid_topic.status_code == 404
    assert (
        "topic not found"
        in invalid_topic.json()["detail"]["message"].lower()
    )
