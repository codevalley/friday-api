from fastapi import HTTPException, status, Request
from fastapi.responses import JSONResponse
from typing import TypeVar, Callable, Any
from functools import wraps

T = TypeVar("T")


def handle_exceptions(
    func: Callable[..., T]
) -> Callable[..., T]:
    """Decorator for handling common exceptions in routers."""

    @wraps(func)
    async def wrapper(*args: Any, **kwargs: Any) -> T:
        try:
            return await func(*args, **kwargs)
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=str(e),
            )

    return wrapper


async def handle_global_exception(
    request: Request, exc: Exception
) -> JSONResponse:
    """Handle all unhandled exceptions globally."""
    if isinstance(exc, HTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail},
        )

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "Internal server error",
            "message": str(exc),
        },
    )
