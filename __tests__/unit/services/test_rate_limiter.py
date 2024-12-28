import pytest
from datetime import datetime, timedelta, UTC
from unittest.mock import patch
from services.RateLimiter import RateLimiter


@pytest.fixture
def rate_limiter():
    """Create a RateLimiter instance for testing."""
    return RateLimiter(
        requests_per_minute=60,
        tokens_per_minute=90_000,
        max_wait_seconds=2,  # Reduce wait time for tests
    )


def test_wait_for_capacity_success(rate_limiter):
    """Test successful capacity acquisition."""
    result = rate_limiter.wait_for_capacity(1000)
    assert result is True


def test_wait_for_capacity_exceeded(rate_limiter):
    """Test capacity exceeded."""
    # Fill up the capacity
    now = datetime.now(UTC)
    rate_limiter.record_usage(now, 90_000)
    result = rate_limiter.wait_for_capacity(1000)
    assert result is False


def test_record_usage_cleanup(rate_limiter):
    """Test cleanup of old usage records."""
    now = datetime.now(UTC)
    # Add old usage record
    old_time = now - timedelta(minutes=2)
    rate_limiter.record_usage(old_time, 1000)

    # Add recent usage record
    rate_limiter.record_usage(now, 1000)

    # Force cleanup by checking current usage
    (
        request_count,
        token_count,
    ) = rate_limiter._get_current_usage(now)

    # Only recent record should remain
    assert len(rate_limiter.token_history) == 1
    assert any(
        abs((ts - now).total_seconds()) < 1
        for ts, _ in rate_limiter.token_history
    )


def test_get_current_usage(rate_limiter):
    """Test calculation of current usage."""
    # Record multiple usage entries
    now = datetime.now(UTC)
    rate_limiter.record_usage(now, 1000)
    rate_limiter.record_usage(now, 2000)

    # Get current usage
    (
        request_count,
        token_count,
    ) = rate_limiter._get_current_usage(now)

    # Total usage should be sum of all entries
    assert token_count == 3000
    assert (
        request_count == 0
    )  # No requests recorded, only tokens


def test_wait_for_capacity_with_retries(rate_limiter):
    """Test waiting for capacity with retries."""
    # Create a fixed time reference
    base_time = datetime(2024, 1, 1, 12, 0, 0, tzinfo=UTC)
    old_time = base_time - timedelta(
        seconds=61
    )  # Just over a minute old

    # Record usage with the old timestamp
    rate_limiter.record_usage(old_time, 90_000)

    # Mock datetime.now to return our fixed time
    with patch(
        "services.RateLimiter.datetime"
    ) as mock_datetime:
        mock_datetime.now.return_value = base_time
        mock_datetime.UTC = UTC

        # Should succeed as the record will be cleaned up
        result = rate_limiter.wait_for_capacity(1000)
        assert result is True
