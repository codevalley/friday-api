"""Logging configuration for the application."""

import logging
import logging.config
from typing import Dict, Any
from datetime import datetime
from pythonjsonlogger import jsonlogger


class CustomJsonFormatter(jsonlogger.JsonFormatter):
    """Custom JSON formatter for logging."""

    def add_fields(
        self,
        log_record: Dict[str, Any],
        record: logging.LogRecord,
        message_dict: Dict[str, Any],
    ) -> None:
        """Add custom fields to the log record.

        Args:
            log_record: The log record to add fields to
            record: The original log record
            message_dict: The message dictionary
        """
        super().add_fields(log_record, record, message_dict)
        if not log_record.get("timestamp"):
            log_record["timestamp"] = (
                datetime.utcnow().isoformat()
            )
        if log_record.get("level"):
            log_record["level"] = log_record[
                "level"
            ].upper()
        else:
            log_record["level"] = record.levelname


def configure_logging(is_test: bool = False) -> None:
    """Configure logging for the application.

    Args:
        is_test: Whether the application is running in test mode
    """
    if is_test:
        # Simple configuration for tests
        config = {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "simple": {
                    "format": (
                        "%(asctime)s - %(name)s - "
                        "%(levelname)s - %(message)s"
                    )
                }
            },
            "handlers": {
                "console": {
                    "class": "logging.StreamHandler",
                    "level": "DEBUG",
                    "formatter": "simple",
                    "stream": "ext://sys.stdout",
                }
            },
            "root": {
                "level": "INFO",
                "handlers": ["console"],
            },
        }
    else:
        # Production configuration
        config = {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "json": {
                    "()": CustomJsonFormatter,
                    "format": "%(timestamp)s %(level)s %(name)s %(message)s",
                }
            },
            "handlers": {
                "console": {
                    "class": "logging.StreamHandler",
                    "level": "DEBUG",
                    "formatter": "json",
                    "stream": "ext://sys.stdout",
                },
                "file": {
                    "class": "logging.handlers.RotatingFileHandler",
                    "level": "INFO",
                    "formatter": "json",
                    "filename": "app.log",
                    "maxBytes": 10485760,  # 10MB
                    "backupCount": 5,
                },
            },
            "root": {
                "level": "INFO",
                "handlers": ["console", "file"],
            },
        }

    logging.config.dictConfig(config)
