"""Logging utilities for the application."""

import logging
from typing import Optional


def get_logger(
    name: str, level: Optional[int] = None
) -> logging.Logger:
    """Get a logger instance with the specified name and level.

    Args:
        name (str): Name of the logger (typically __name__)
        level (Optional[int]): Optional logging level to set

    Returns:
        logging.Logger: Configured logger instance
    """
    logger = logging.getLogger(name)
    if level is not None:
        logger.setLevel(level)
    return logger
