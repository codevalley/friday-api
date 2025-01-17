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

    # Task-related error codes
    TASK_INVALID_STATUS = "TASK_INVALID_STATUS"
    TASK_INVALID_REFERENCE = "TASK_INVALID_REFERENCE"
    TASK_INVALID_DATA = "TASK_INVALID_DATA"

    # Topic-related error codes
    TOPIC_VALIDATION_ERROR = "TOPIC_VALIDATION_ERROR"
    TOPIC_NAME_ERROR = "TOPIC_NAME_ERROR"
    TOPIC_ICON_ERROR = "TOPIC_ICON_ERROR"


class DomainException(Exception):
    """Base exception for all domain exceptions."""

    def __init__(
        self,
        message: str,
        code: str,
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


class ActivityServiceError(DomainException):
    """Raised when activity service operations fail."""

    pass


class ActivityNotFoundError(DomainException):
    """Raised when an activity is not found."""

    pass


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

    def __init__(
        self,
        message: str,
        code: str = "USER_VALIDATION_ERROR",
    ):
        self.message = message
        self.code = code
        super().__init__(self.message)


class UserAuthenticationError(UserValidationError):
    """Raised when user authentication fails."""

    def __init__(self, message: str):
        super().__init__(
            message, code="USER_AUTHENTICATION_ERROR"
        )


class UserKeyValidationError(UserValidationError):
    """Raised when user key validation fails."""

    def __init__(self, message: str):
        super().__init__(
            message, code="USER_KEY_VALIDATION_ERROR"
        )


class UserIdentifierError(UserValidationError):
    """Raised when user identifier validation fails."""

    def __init__(self, message: str):
        super().__init__(
            message, code="USER_IDENTIFIER_ERROR"
        )


class NoteValidationError(Exception):
    """Base exception for note domain validation failures."""

    def __init__(
        self,
        message: str,
        code: str = "NOTE_VALIDATION_ERROR",
    ):
        self.message = message
        self.code = code
        super().__init__(self.message)


class NoteContentError(NoteValidationError):
    """Raised when note content validation fails."""

    def __init__(self, message: str):
        super().__init__(message, code="NOTE_CONTENT_ERROR")


class NoteAttachmentError(NoteValidationError):
    """Raised when note attachment validation fails."""

    def __init__(self, message: str):
        super().__init__(
            message, code="NOTE_ATTACHMENT_ERROR"
        )


class NoteReferenceError(NoteValidationError):
    """Raised when note reference (activity/moment) validation fails."""

    def __init__(self, message: str):
        super().__init__(
            message, code="NOTE_REFERENCE_ERROR"
        )


class RoboError(DomainException):
    """Base exception for all Robo-related errors."""

    pass


class RoboAPIError(RoboError):
    """Raised when there's an error communicating with the Robo API."""

    def __init__(
        self, message: str, status_code: int = None
    ):
        super().__init__(
            message=message, code="ROBO_API_ERROR"
        )
        self.status_code = status_code


class RoboRateLimitError(RoboAPIError):
    """Raised when API rate limits are exceeded."""

    pass


class RoboConfigError(DomainException):
    """Exception raised for invalid robo configuration."""

    def __init__(self, message: str):
        """Initialize RoboConfigError.

        Args:
            message: Error message
        """
        super().__init__(
            message=message, code="ROBO_CONFIG_ERROR"
        )


class RoboProcessingError(RoboError):
    """Raised when there's an error processing content through Robo."""

    pass


class RoboValidationError(RoboError):
    """Raised when there's an error validating Robo inputs or outputs."""

    pass


class RoboServiceError(DomainException):
    """Exception raised when RoboService encounters an error."""

    def __init__(
        self, message: str, code: str = "ROBO_SERVICE_ERROR"
    ):
        super().__init__(message=message, code=code)


class TaskValidationError(Exception):
    """Base exception for task domain validation failures."""

    def __init__(
        self,
        message: str,
        code: str = "TASK_VALIDATION_ERROR",
    ):
        self.message = message
        self.code = code
        super().__init__(self.message)


class TaskContentError(TaskValidationError):
    """Raised when task content validation fails."""

    def __init__(self, message: str):
        super().__init__(message, code="TASK_CONTENT_ERROR")


class TaskDateError(TaskValidationError):
    """Raised when task date validation fails."""

    def __init__(self, message: str):
        super().__init__(message, code="TASK_DATE_ERROR")


class TaskPriorityError(TaskValidationError):
    """Raised when task priority validation fails."""

    def __init__(self, message: str):
        super().__init__(
            message, code="TASK_PRIORITY_ERROR"
        )


class TaskStatusError(TaskValidationError):
    """Raised when task status transition is invalid."""

    def __init__(self, message: str):
        """Initialize task status error."""
        super().__init__(
            message, code=ErrorCode.TASK_INVALID_STATUS
        )


class TaskParentError(TaskValidationError):
    """Raised when task parent reference validation fails."""

    def __init__(self, message: str):
        super().__init__(message, code="TASK_PARENT_ERROR")


class TaskReferenceError(TaskValidationError):
    """Raised when task reference is invalid (e.g. self-reference)."""

    def __init__(self, message: str):
        """Initialize task reference error."""
        super().__init__(
            message, code=ErrorCode.TASK_INVALID_REFERENCE
        )


class TopicValidationError(DomainException):
    """Base exception for topic validation errors."""

    def __init__(
        self,
        message: str,
        code: str = ErrorCode.TOPIC_VALIDATION_ERROR,
        details: Optional[Any] = None,
    ):
        super().__init__(
            message=message, code=code, details=details
        )


class TopicNameError(TopicValidationError):
    """Exception for topic name validation errors."""

    def __init__(
        self,
        message: str,
        details: Optional[Any] = None,
    ):
        super().__init__(
            message=message,
            code=ErrorCode.TOPIC_NAME_ERROR,
            details=details,
        )


class TopicIconError(TopicValidationError):
    """Exception for topic icon validation errors."""

    def __init__(
        self,
        message: str,
        details: Optional[Any] = None,
    ):
        super().__init__(
            message=message,
            code=ErrorCode.TOPIC_ICON_ERROR,
            details=details,
        )
