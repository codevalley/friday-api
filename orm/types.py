"""Custom database-agnostic types for ORM models."""

from sqlalchemy import JSON, TypeDecorator
from sqlalchemy.dialects.postgresql import JSONB
from typing import Any, Optional


class JSONType(TypeDecorator):
    """Platform-independent JSON type.

    Uses PostgreSQL's JSONB type when available, falls back to
    standard JSON for other databases.
    """

    impl = JSON
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            return dialect.type_descriptor(JSONB())
        return dialect.type_descriptor(JSON())

    def process_bind_param(
        self, value: Any, dialect: Any
    ) -> Optional[Any]:
        return value

    def process_result_value(
        self, value: Any, dialect: Any
    ) -> Optional[Any]:
        return value
