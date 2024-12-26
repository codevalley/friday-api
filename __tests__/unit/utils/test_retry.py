import pytest
from unittest.mock import Mock, patch
from domain.exceptions import (
    RoboAPIError,
    RoboRateLimitError,
)
from utils.retry import with_retry, calculate_backoff


def test_calculate_backoff():
    """Test backoff calculation."""
    # Test basic calculation
    delay = calculate_backoff(1, base_delay=1.0, jitter=0)
    assert delay == 1.0

    # Test exponential growth
    delay = calculate_backoff(2, base_delay=1.0, jitter=0)
    assert delay == 2.0

    # Test maximum cap
    delay = calculate_backoff(10, base_delay=1.0, jitter=0)
    assert delay == 60.0  # Capped at 60 seconds


@pytest.mark.asyncio
async def test_retry_success_first_attempt():
    """Test successful execution on first attempt."""
    mock_func = Mock(return_value=True)

    @with_retry(max_retries=3)
    async def test_func():
        return mock_func()

    result = await test_func()
    assert result is True
    assert mock_func.call_count == 1


@pytest.mark.asyncio
async def test_retry_success_after_retries():
    """Test successful execution after some retries."""
    mock_func = Mock(
        side_effect=[
            RoboAPIError("Error"),
            RoboAPIError("Error"),
            True,
        ]
    )

    @with_retry(max_retries=3)
    async def test_func():
        return mock_func()

    with patch("asyncio.sleep") as mock_sleep:
        result = await test_func()
        assert result is True
        assert mock_func.call_count == 3
        assert (
            mock_sleep.call_count == 2
        )  # Sleep called between retries


@pytest.mark.asyncio
async def test_retry_max_attempts_exceeded():
    """Test failure after max retries exceeded."""
    error = RoboAPIError("Persistent error")
    mock_func = Mock(side_effect=[error, error, error])

    @with_retry(max_retries=3)
    async def test_func():
        return mock_func()

    with patch("asyncio.sleep"), pytest.raises(
        RoboAPIError
    ) as exc_info:
        await test_func()
    assert str(exc_info.value) == "Persistent error"
    assert mock_func.call_count == 3


@pytest.mark.asyncio
async def test_retry_excluded_exception():
    """Test immediate failure on excluded exception."""
    error = RoboRateLimitError("Rate limit exceeded")
    mock_func = Mock(side_effect=error)

    @with_retry(max_retries=3)
    async def test_func():
        return mock_func()

    with pytest.raises(RoboRateLimitError) as exc_info:
        await test_func()
    assert str(exc_info.value) == "Rate limit exceeded"
    assert (
        mock_func.call_count == 1
    )  # Only called once, no retries
