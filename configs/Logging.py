"""Logging configuration for the application."""

import os
import logging.config
from configs.Environment import get_environment_variables

env = get_environment_variables()


def configure_logging(is_test: bool = False) -> None:
    """
    Configure logging for the application.

    Args:
        is_test: Whether the application is running in test mode
    """
    # Ensure logs directory exists
    os.makedirs("logs", exist_ok=True)

    # Reset logging configuration
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)
        handler.close()

    handlers = ["console"]
    if not is_test:
        handlers.append("file")

    config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "default": {"format": "%(message)s"},
            "json": {
                "()": "pythonjsonlogger.jsonlogger.JsonFormatter",
                "format": "%(message)s %(extra)s",
            },
        },
        "filters": {
            "extra_filter": {
                "()": "utils.logging_filters.ExtraFilter"
            }
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "formatter": "default",
                "filters": ["extra_filter"],
                "stream": "ext://sys.stdout",
            },
            "file": {
                "class": "logging.handlers.RotatingFileHandler",
                "formatter": "json",
                "filters": ["extra_filter"],
                "filename": "logs/app.log",
                "maxBytes": 10485760,  # 10MB
                "backupCount": 5,
            },
        },
        "loggers": {
            "": {  # Root logger
                "handlers": handlers,
                "level": "INFO",
            },
            "utils.request_logging": {
                "handlers": handlers,
                "level": "INFO",
                "propagate": False,
            },
            "utils.audit_logging": {
                "handlers": handlers,  # use console handler in test mode
                "level": "INFO",
                "propagate": False,
            },
        },
    }

    logging.config.dictConfig(config)
