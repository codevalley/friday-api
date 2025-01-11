from fastapi import HTTPException, status, Request
from fastapi.responses import JSONResponse
from typing import TypeVar, Callable, Any
from functools import wraps
from domain.exceptions import (
    ActivityNotFoundError,
    ActivityServiceError,
    ValidationException,
    DomainException,
)
from schemas.pydantic.CommonSchema import (
    GenericResponse,
    ErrorDetail,
)

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
        except ActivityNotFoundError as e:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content=GenericResponse(
                    message=str(e),
                    error=ErrorDetail(
                        code=e.code,
                        message=str(e),
                    ),
                ).model_dump(),
            )
        except (
            ValidationException,
            ActivityServiceError,
        ) as e:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content=GenericResponse(
                    message=str(e),
                    error=ErrorDetail(
                        code=e.code,
                        message=str(e),
                    ),
                ).model_dump(),
            )
        except Exception as e:
            if isinstance(e, DomainException):
                return JSONResponse(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    content=GenericResponse(
                        message=str(e),
                        error=ErrorDetail(
                            code=e.code,
                            message=str(e),
                        ),
                    ).model_dump(),
                )
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content=GenericResponse(
                    message="Internal server error",
                    error=ErrorDetail(
                        code="INTERNAL_ERROR",
                        message=str(e),
                    ),
                ).model_dump(),
            )

    return wrapper


async def handle_global_exception(
    request: Request, exc: Exception
) -> JSONResponse:
    """Handle all unhandled exceptions globally."""
    if isinstance(exc, HTTPException):
        if isinstance(exc.detail, dict):
            return JSONResponse(
                status_code=exc.status_code,
                content=exc.detail,
            )
        return JSONResponse(
            status_code=exc.status_code,
            content=GenericResponse(
                message=str(exc.detail),
                error=ErrorDetail(
                    code="HTTP_ERROR",
                    message=str(exc.detail),
                ),
            ).model_dump(),
        )

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=GenericResponse(
            message="Internal server error",
            error=ErrorDetail(
                code="INTERNAL_ERROR",
                message=str(exc),
            ),
        ).model_dump(),
    )
