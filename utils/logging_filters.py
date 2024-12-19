"""Logging filters for the application."""

import logging


class ExtraFilter(logging.Filter):
    """Filter that ensures all records have an extra field."""

    def filter(self, record: logging.LogRecord) -> bool:
        """Add extra fields to the record if they don't exist."""
        if not hasattr(record, "extra"):
            record.extra = {}

        # Convert extra dict to string if it exists
        if hasattr(record, "extra") and isinstance(
            record.extra, dict
        ):
            extras = []
            for key, value in record.extra.items():
                extras.append(f"{key}={value}")
            record.extra = " ".join(extras)

        return True
