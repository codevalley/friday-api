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
            # Convert single exception types to tuples
            exclude_types = (
                (exclude_on,)
                if isinstance(exclude_on, type)
                else exclude_on
            )
            retry_types = (
                (retry_on,)
                if isinstance(retry_on, type)
                else retry_on
            )

            last_exception = None

            for attempt in range(max_retries + 1):
                try:
                    result = await func(*args, **kwargs)
                    return result
                except Exception as e:
                    # Check if exception should be excluded first
                    if any(
                        isinstance(e, exc_type)
                        for exc_type in exclude_types
                    ):
                        raise

                    # Check if exception should trigger retry
                    if not any(
                        isinstance(e, exc_type)
                        for exc_type in retry_types
                    ):
                        raise

                    last_exception = e

                    # If this was the last attempt, raise the exception
                    if attempt == max_retries:
                        raise last_exception

                    # Wait before retrying with exponential backoff
                    delay = calculate_backoff(attempt + 1)
                    await asyncio.sleep(delay)

            # This should never be reached
            raise RuntimeError("Unexpected retry state")

        return wrapper

    return decorator
