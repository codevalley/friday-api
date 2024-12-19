"""Audit logging module for tracking critical operations."""

import logging
from enum import Enum
from typing import Any, Dict, Optional
from datetime import datetime


logger = logging.getLogger(__name__)


class AuditEventType(Enum):
    """Types of audit events that can be logged."""

    USER_LOGIN = "user_login"
    USER_LOGOUT = "user_logout"
    USER_CREATED = "user_created"
    USER_UPDATED = "user_updated"
    USER_DELETED = "user_deleted"
    ACTIVITY_CREATED = "activity_created"
    ACTIVITY_UPDATED = "activity_updated"
    ACTIVITY_DELETED = "activity_deleted"
    MOMENT_CREATED = "moment_created"
    MOMENT_UPDATED = "moment_updated"
    MOMENT_DELETED = "moment_deleted"


def log_audit_event(
    event_type: AuditEventType,
    user_id: str,
    resource_id: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None,
) -> None:
    """
    Log an audit event with the specified details.

    Args:
        event_type: The type of audit event
        user_id: The ID of the user performing the action
        resource_id: Optional ID of the resource being acted upon
        details: Optional additional details about the event
    """
    event_data = {
        "event_type": event_type.value,
        "user_id": user_id,
        "timestamp": datetime.utcnow().isoformat(),
        "resource_id": resource_id,
        **(details or {}),
    }

    # Format the message with key details
    message_parts = [f"Audit event: {event_type.value}"]
    message_parts.append(f"user_id={user_id}")
    if resource_id:
        message_parts.append(f"resource_id={resource_id}")
    if details:
        message_parts.extend(
            f"{k}={v}" for k, v in details.items()
        )

    logger.info(" ".join(message_parts), extra=event_data)
