import asyncio
import random
from functools import wraps
from typing import (
    TypeVar,
    Callable,
    Any,
    Type,
    Union,
    Tuple,
)
from domain.exceptions import (
    RoboAPIError,
    RoboRateLimitError,
)

T = TypeVar("T")


def calculate_backoff(
    attempt: int,
    base_delay: float = 1.0,
    jitter: float = 0.1,
) -> float:
    """Calculate delay with exponential backoff and jitter.

    Args:
        attempt: Current attempt number (1-based)
        base_delay: Base delay in seconds
        jitter: Jitter factor (0-1) to add randomness

    Returns:
        Delay in seconds
    """
    # Calculate exponential backoff
    delay = min(
        base_delay * (2 ** (attempt - 1)), 60
    )  # Cap at 60 seconds
    # Add jitter
    jitter_amount = delay * jitter
    return delay + random.uniform(
        -jitter_amount, jitter_amount
    )


def with_retry(
    max_retries: int = 3,
    retry_on: Union[
        Type[Exception], Tuple[Type[Exception], ...]
    ] = (RoboAPIError,),
    exclude_on: Union[
        Type[Exception], Tuple[Type[Exception], ...]
    ] = (RoboRateLimitError,),
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """Decorator for retrying async functions with exponential backoff.

    Args:
        max_retries: Maximum number of retry attempts
        retry_on: Exception(s) to retry on
        exclude_on: Exception(s) to not retry on

    Returns:
        Decorated function
    """

    def decorator(
        func: Callable[..., T]
    ) -> Callable[..., T]:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> T:
            last_exception = None

            for attempt in range(1, max_retries + 1):
                try:
                    return await func(*args, **kwargs)
                except exclude_on:
                    # Don't retry if exception is in exclude list
                    raise
                except retry_on as e:
                    last_exception = e
                    if attempt == max_retries:
                        # Don't sleep on last attempt
                        break

                    # Calculate and apply backoff
                    delay = calculate_backoff(attempt)
                    await asyncio.sleep(delay)

            # If we get here, all retries failed
            raise last_exception or RuntimeError(
                "Retry failed for unknown reason"
            )

        return wrapper

    return decorator
