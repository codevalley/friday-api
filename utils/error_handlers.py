from fastapi import HTTPException, status
from typing import TypeVar, Callable, Any
from functools import wraps

T = TypeVar("T")


def handle_exceptions(
    func: Callable[..., T]
) -> Callable[..., T]:
    """Decorator for handling common exceptions in routers

    Args:
        func: The route handler function to wrap

    Returns:
        Wrapped function with standardized error handling
    """

    @wraps(func)
    async def wrapper(*args: Any, **kwargs: Any) -> T:
        try:
            return await func(*args, **kwargs)
        except HTTPException:
            # Re-raise HTTP exceptions as they are already
            # properly formatted
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=str(e),
            )

    return wrapper
