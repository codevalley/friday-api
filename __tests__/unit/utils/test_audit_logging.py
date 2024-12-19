"""Tests for the audit logging module."""

import pytest
import logging
from utils.audit_logging import (
    AuditEventType,
    log_audit_event,
)
from configs.Logging import configure_logging


@pytest.fixture(autouse=True)
def setup_test_logging(caplog):
    """Configure logging for this test module."""
    # Configure logging for tests
    configure_logging(is_test=True)

    # Clear any existing logs
    caplog.clear()

    # Set level for specific logger and handler
    caplog.set_level(logging.INFO)
    logger = logging.getLogger("utils.audit_logging")
    logger.handlers = []  # Remove any existing handlers
    logger.addHandler(caplog.handler)
    logger.propagate = False

    yield

    # Clean up after test
    caplog.clear()


def test_log_audit_event_basic(caplog):
    """Test basic audit event logging."""
    log_audit_event(
        event_type=AuditEventType.USER_LOGIN,
        user_id="test_user_123",
    )

    assert len(caplog.records) > 0, "No logs were captured"
    log_message = caplog.records[0].getMessage().lower()
    assert "audit event: user_login" in log_message
    assert "user_id=test_user_123" in log_message


def test_log_audit_event_with_resource(caplog):
    """Test audit event logging with resource ID."""
    log_audit_event(
        event_type=AuditEventType.ACTIVITY_CREATED,
        user_id="test_user_123",
        resource_id="activity_456",
    )

    assert len(caplog.records) > 0, "No logs were captured"
    log_message = caplog.records[0].getMessage().lower()
    assert "audit event: activity_created" in log_message
    assert "user_id=test_user_123" in log_message
    assert "resource_id=activity_456" in log_message


def test_log_audit_event_with_details(caplog):
    """Test audit event logging with additional details."""
    details = {
        "ip_address": "127.0.0.1",
        "browser": "Chrome",
    }

    log_audit_event(
        event_type=AuditEventType.USER_LOGIN,
        user_id="test_user_123",
        details=details,
    )

    assert len(caplog.records) > 0, "No logs were captured"
    log_message = caplog.records[0].getMessage().lower()
    assert "audit event: user_login" in log_message
    assert "user_id=test_user_123" in log_message
    assert "ip_address=127.0.0.1" in log_message
    assert "browser=chrome" in log_message


def test_log_format(caplog):
    """Test that logs are properly formatted."""
    log_audit_event(
        event_type=AuditEventType.USER_LOGIN,
        user_id="test_user_123",
    )

    assert len(caplog.records) > 0, "No logs were captured"
    record = caplog.records[0]

    # Check that we have the basic log record attributes
    assert record.name == "utils.audit_logging"
    assert record.levelno == logging.INFO

    # Check the message format
    message = record.getMessage()
    assert message.startswith("Audit event:")
    assert "user_id=" in message
