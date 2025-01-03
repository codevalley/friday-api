"""Domain models for the application.

This package contains the core domain models that represent the business
entities and their behavior. These models are independent of how they
are stored (ORM) or presented (REST).

The domain models encapsulate:
1. Business rules and validation
2. Core business logic
3. Domain-specific types and exceptions

Key principles:
1. Models are framework-agnostic
2. Models enforce their own invariants
3. Models represent a single source of truth
4. Models are testable in isolation

The domain layer is the heart of the application, containing all the
business rules and logic. It should be independent of any external
concerns like databases, APIs, or UI.
"""

from .activity import ActivityData
from .moment import MomentData
from .user import UserData

__all__ = ["ActivityData", "MomentData", "UserData"]
