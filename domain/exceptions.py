"""Domain-specific exceptions for the application."""

from enum import Enum
from typing import Any, Optional


class ErrorCode(str, Enum):
    """Error codes for domain exceptions."""

    # Activity-related error codes
    INVALID_COLOR_FORMAT = "INVALID_COLOR_FORMAT"
    INVALID_SCHEMA_FORMAT = "INVALID_SCHEMA_FORMAT"
    INVALID_SCHEMA_TYPE = "INVALID_SCHEMA_TYPE"
    INVALID_SCHEMA_PROPERTIES = "INVALID_SCHEMA_PROPERTIES"
    INVALID_SCHEMA_CONSTRAINTS = (
        "INVALID_SCHEMA_CONSTRAINTS"
    )
    INVALID_FIELD_TYPE = "INVALID_FIELD_TYPE"
    INVALID_FIELD_VALUE = "INVALID_FIELD_VALUE"
    MISSING_REQUIRED_FIELD = "MISSING_REQUIRED_FIELD"


class DomainException(Exception):
    """Base exception for all domain exceptions."""

    def __init__(
        self,
        message: str,
        code: ErrorCode,
        details: Optional[Any] = None,
    ):
        self.message = message
        self.code = code
        self.details = details
        super().__init__(self.message)


class ValidationException(DomainException):
    """Base exception for validation errors."""

    pass


class ActivityValidationError(ValidationException):
    """Exception raised for activity validation errors."""

    @classmethod
    def invalid_color(
        cls, color: str
    ) -> "ActivityValidationError":
        """Create an invalid color error."""
        return cls(
            message=(
                f"Invalid color format: {color}. "
                "Must be in #RRGGBB format"
            ),
            code=ErrorCode.INVALID_COLOR_FORMAT,
            details={"color": color},
        )

    @classmethod
    def invalid_schema_type(
        cls,
    ) -> "ActivityValidationError":
        """Create an invalid schema type error."""
        return cls(
            message="Activity schema type must be 'object'",
            code=ErrorCode.INVALID_SCHEMA_TYPE,
        )

    @classmethod
    def missing_type_field(
        cls,
    ) -> "ActivityValidationError":
        """Create a missing type field error."""
        return cls(
            message="Activity schema must contain 'type' field",
            code=ErrorCode.INVALID_SCHEMA_FORMAT,
        )

    @classmethod
    def invalid_schema_constraints(
        cls,
    ) -> "ActivityValidationError":
        """Create an invalid schema constraints error."""
        return cls(
            message=(
                "Activity schema with constraints must contain "
                "either 'properties' or 'patternProperties'"
            ),
            code=ErrorCode.INVALID_SCHEMA_CONSTRAINTS,
        )

    @classmethod
    def invalid_field_value(
        cls, field: str, message: str
    ) -> "ActivityValidationError":
        """Create an invalid field value error."""
        return cls(
            message=message,
            code=ErrorCode.INVALID_FIELD_VALUE,
            details={"field": field},
        )


class MomentValidationError(Exception):
    """Base exception for moment domain validation failures."""

    def __init__(
        self,
        message: str,
        code: str = "MOMENT_VALIDATION_ERROR",
    ):
        self.message = message
        self.code = code
        super().__init__(self.message)


class MomentTimestampError(MomentValidationError):
    """Raised when moment timestamp validation fails."""

    def __init__(self, message: str):
        super().__init__(
            message, code="MOMENT_TIMESTAMP_ERROR"
        )


class MomentDataError(MomentValidationError):
    """Raised when moment data validation fails."""

    def __init__(self, message: str):
        super().__init__(message, code="MOMENT_DATA_ERROR")


class MomentSchemaError(MomentValidationError):
    """Raised when moment schema validation fails."""

    def __init__(self, message: str):
        super().__init__(
            message, code="MOMENT_SCHEMA_ERROR"
        )


class UserValidationError(Exception):
    """Base exception for user domain validation failures."""
    def __init__(self, message: str, code: str = "USER_VALIDATION_ERROR"):
        self.message = message
        self.code = code
        super().__init__(self.message)


class UserAuthenticationError(UserValidationError):
    """Raised when user authentication fails."""
    def __init__(self, message: str):
        super().__init__(message, code="USER_AUTHENTICATION_ERROR")


class UserKeyValidationError(UserValidationError):
    """Raised when user key validation fails."""
    def __init__(self, message: str):
        super().__init__(message, code="USER_KEY_VALIDATION_ERROR")


class UserIdentifierError(UserValidationError):
    """Raised when user identifier validation fails."""
    def __init__(self, message: str):
        super().__init__(message, code="USER_IDENTIFIER_ERROR")
