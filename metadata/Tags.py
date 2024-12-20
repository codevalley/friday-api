"""OpenAPI tag definitions for API documentation.

This module defines the tags used to group and categorize API endpoints
in the OpenAPI/Swagger documentation.
"""

from typing import List, Dict

Tags: List[Dict[str, str]] = [
    {
        "name": "activities",
        "description": "Create, manage activity types with custom JSON schema",
    },
    {
        "name": "moments",
        "description": "Log and track moments with structured data",
    },
    {
        "name": "notes",
        "description": "Create and manage user notes with optional extras",
    },
]
