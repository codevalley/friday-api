import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from main import app
from models.UserModel import User
from services.UserService import UserService
from configs.Database import (
    get_db_connection,
    SessionLocal,
    Engine,
)


# Create a test database session
def override_get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Override the database dependency
app.dependency_overrides[get_db_connection] = (
    override_get_db
)

client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_database():
    # Set up - create tables
    User.__table__.create(bind=Engine, checkfirst=True)

    # Run the test
    yield

    # Tear down - drop tables
    User.__table__.drop(bind=Engine, checkfirst=True)


def test_register_user():
    response = client.post(
        "/v1/auth/register", json={"username": "testuser"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "id" in data
    assert data["username"] == "testuser"
    assert "user_secret" in data


def test_register_duplicate_username():
    # First registration
    response1 = client.post(
        "/v1/auth/register",
        json={"username": "duplicate_user"},
    )
    assert response1.status_code == 200

    # Second registration with same username
    response2 = client.post(
        "/v1/auth/register",
        json={"username": "duplicate_user"},
    )
    assert response2.status_code == 400
    assert (
        "Username already registered"
        in response2.json()["detail"]
    )


def test_login_with_valid_secret():
    # First register a user
    register_response = client.post(
        "/v1/auth/register", json={"username": "loginuser"}
    )
    user_secret = register_response.json()["user_secret"]

    # Then try to login
    login_response = client.post(
        "/v1/auth/token", json={"user_secret": user_secret}
    )
    assert login_response.status_code == 200
    data = login_response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_login_with_invalid_secret():
    login_response = client.post(
        "/v1/auth/token",
        json={"user_secret": "invalid_secret"},
    )
    assert login_response.status_code == 401
    assert (
        "Invalid credentials"
        in login_response.json()["detail"]
    )


def test_protected_endpoint_with_valid_token():
    # First register and get a token
    register_response = client.post(
        "/v1/auth/register",
        json={"username": "protecteduser"},
    )
    user_secret = register_response.json()["user_secret"]

    login_response = client.post(
        "/v1/auth/token", json={"user_secret": user_secret}
    )
    token = login_response.json()["access_token"]

    # Then try to access protected endpoint
    response = client.get(
        "/v1/activities",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200


def test_protected_endpoint_without_token():
    response = client.get("/v1/activities")
    assert response.status_code == 401
    assert "Not authenticated" in response.json()["detail"]


def test_protected_endpoint_with_invalid_token():
    response = client.get(
        "/v1/activities",
        headers={"Authorization": "Bearer invalid_token"},
    )
    assert response.status_code == 401
    assert (
        "Could not validate credentials"
        in response.json()["detail"]
    )
