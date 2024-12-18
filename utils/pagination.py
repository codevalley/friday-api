"""Pagination utilities for consistent handling across the application"""

from typing import Tuple


def page_to_skip(page: int, size: int) -> Tuple[int, int]:
    """Convert page/size pagination to skip/limit

    Args:
        page: Page number (1-based)
        size: Items per page

    Returns:
        Tuple of (skip, limit)
    """
    skip = (page - 1) * size
    return skip, size


def skip_to_page(skip: int, limit: int) -> Tuple[int, int]:
    """Convert skip/limit pagination to page/size

    Args:
        skip: Number of items to skip
        limit: Maximum items to return

    Returns:
        Tuple of (page, size)
    """
    page = (skip // limit) + 1
    return page, limit


def calculate_pages(total: int, size: int) -> int:
    """Calculate total number of pages

    Args:
        total: Total number of items
        size: Items per page

    Returns:
        Total number of pages
    """
    return (total + size - 1) // size if total > 0 else 0
