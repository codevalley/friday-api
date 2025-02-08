"""Factory for getting RoboService implementations."""

import os
from functools import lru_cache

from domain.robo import RoboService
from services.OpenAIService import OpenAIService
from services.TestRoboService import TestRoboService
from configs.RoboConfig import (
    get_robo_settings,
    ServiceImplementation,
)


@lru_cache()
def get_robo_service() -> RoboService:
    """Get appropriate RoboService implementation based on configuration.

    Returns:
        RoboService: Service implementation based on configuration
    """
    settings = get_robo_settings()
    config = settings.to_domain_config()

    # Use TestRoboService in test environment
    if os.getenv("ENV", "").lower() == "test":
        return TestRoboService(config)

    # Use configured service implementation
    if (
        config.service_implementation
        == ServiceImplementation.INSTRUCTOR
    ):
        from services.InstructorService import (
            InstructorService,
        )

        return InstructorService(config)
    elif (
        config.service_implementation
        == ServiceImplementation.MANUAL
    ):
        return OpenAIService(config)
    else:
        # Default to manual implementation
        return OpenAIService(config)
