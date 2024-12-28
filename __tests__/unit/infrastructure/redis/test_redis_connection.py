"""Tests for Redis connection management."""

import pytest
from unittest.mock import MagicMock, patch
from redis import Redis
from configs.redis.RedisConnection import (
    get_redis_connection,
    check_redis_health,
    RedisConnectionError,
)


@pytest.fixture(autouse=True)
def clear_lru_cache():
    """Clear LRU cache between tests."""
    get_redis_connection.cache_clear()


@pytest.fixture
def mock_redis(monkeypatch):
    """Mock Redis client."""
    mock = MagicMock(spec=Redis)
    mock.ping.return_value = True
    with patch(
        "configs.redis.RedisConnection.Redis",
        return_value=mock,
    ):
        yield mock


def test_get_redis_connection_success(mock_redis):
    """Test successful Redis connection."""
    connection = get_redis_connection()
    assert mock_redis.ping.called
    assert connection is mock_redis


def test_get_redis_connection_failure(mock_redis):
    """Test Redis connection failure."""
    mock_redis.ping.side_effect = Exception(
        "Connection failed"
    )
    with pytest.raises(RedisConnectionError) as exc_info:
        get_redis_connection()
    assert "Connection failed" in str(exc_info.value)


def test_get_redis_connection_caching(mock_redis):
    """Test Redis connection caching."""
    conn1 = get_redis_connection()
    conn2 = get_redis_connection()
    assert conn1 is conn2  # Same instance due to lru_cache
    assert (
        mock_redis.ping.call_count == 1
    )  # Ping called only once


def test_check_redis_health_healthy(mock_redis):
    """Test health check with healthy Redis."""
    health = check_redis_health()
    assert health["status"] == "healthy"
    assert health["error"] is None


def test_check_redis_health_unhealthy(mock_redis):
    """Test health check with unhealthy Redis."""
    mock_redis.ping.side_effect = Exception(
        "Health check failed"
    )
    health = check_redis_health()
    assert health["status"] == "unhealthy"
    assert "Health check failed" in health["error"]
