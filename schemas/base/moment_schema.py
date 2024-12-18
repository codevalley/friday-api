"""Base schema for moment data."""

from domain.models.moment import MomentData

# Re-export MomentData for backward compatibility
__all__ = ["MomentData"]
