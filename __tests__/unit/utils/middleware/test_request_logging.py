"""Tests for the request logging middleware."""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from utils.middleware.request_logging import (
    RequestLoggingMiddleware,
)


@pytest.fixture
def test_app():
    """Create a test FastAPI application with the RequestLoggingMiddleware."""
    app = FastAPI()
    app.add_middleware(RequestLoggingMiddleware)

    @app.get("/test")
    async def test_endpoint():
        """Simple test endpoint that returns a message."""
        return {"message": "test"}

    return app


@pytest.fixture
def client(test_app):
    """Create a TestClient instance for the test app."""
    return TestClient(test_app)


def test_request_logging_middleware(
    client, caplog, setup_logging
):
    """Test that the middleware logs requests and responses correctly."""
    response = client.get("/test")
    assert response.status_code == 200

    logs = (
        caplog.text.lower()
    )  # lowercase for case-insensitive comparison

    # Check request log
    assert "request started" in logs
    assert "path=/test" in logs or "path = /test" in logs
    assert "method=get" in logs or "method = get" in logs

    # Check response log
    assert "request completed" in logs
    assert (
        "status_code=200" in logs
        or "status_code = 200" in logs
    )
    assert "duration_ms" in logs
