"""Domain models package.

This package contains the core domain models that represent the fundamental
business entities in the application. These models are the single source of
truth for data structure and validation rules.

Architecture Overview:
--------------------
1. Domain Models (this package):
   - Define core business entities and their relationships
   - Implement validation rules and business logic
   - Serve as the source of truth for data structure
   - Are independent of persistence and presentation layers

2. Data Flow:
   - API Layer → Domain Models: Conversion via to_domain() methods
   - Domain Models → Database: Conversion via from_dict()/to_dict()
   - Database → Domain Models: Conversion via from_orm()
   - Domain Models → API Response: Conversion via from_domain()

Key Principles:
-------------
1. Single Source of Truth: Domain models are the authoritative source
   for data structure and validation rules.
2. Separation of Concerns: Domain models are independent of how they
   are stored (ORM) or presented (REST/GraphQL).
3. Rich Domain Models: Business logic and validation rules live in
   the domain models, not in services or controllers.
4. Type Safety: All domain models use strong typing and validate
   their data on creation.

Available Models:
---------------
- ActivityData: Core activity type definitions
- MomentData: Individual moment/event records
- UserData: User account information
"""

from .activity import ActivityData
from .moment import MomentData
from .user import UserData

__all__ = ["ActivityData", "MomentData", "UserData"]
