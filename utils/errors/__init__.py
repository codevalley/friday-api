"""Error handling package.

This package contains all error handling related code:

1. Application Exceptions (exceptions.py):
   - Base application exceptions
   - HTTP-aware exceptions
   - Used by infrastructure layer

2. Domain Exception Mapping (domain_exceptions.py):
   - Maps domain exceptions to HTTP exceptions
   - Acts as an adapter between domain and infrastructure

3. Error Handlers (handlers.py):
   - Global error handlers for FastAPI
   - Converts exceptions to HTTP responses
   - Handles logging and error formatting

4. Error Responses (responses.py):
   - Pydantic models for error responses
   - Standardizes error output format
"""

from .exceptions import (
    AppException,
    ValidationError,
    NotFoundError,
    AuthenticationError,
    AuthorizationError,
    ConflictError,
)
from .domain_exceptions import handle_domain_exception
from .handlers import (
    app_exception_handler,
    validation_exception_handler,
    internal_exception_handler,
)
from .responses import ErrorResponse, ErrorDetail

__all__ = [
    # Application exceptions
    "AppException",
    "ValidationError",
    "NotFoundError",
    "AuthenticationError",
    "AuthorizationError",
    "ConflictError",
    # Domain exception handling
    "handle_domain_exception",
    # Error handlers
    "app_exception_handler",
    "validation_exception_handler",
    "internal_exception_handler",
    # Response models
    "ErrorResponse",
    "ErrorDetail",
]
