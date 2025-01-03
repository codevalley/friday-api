"""Factory for getting RoboService implementations."""

import os
from functools import lru_cache

from domain.robo import RoboService
from services.OpenAIService import OpenAIService
from services.TestRoboService import TestRoboService
from configs.RoboConfig import get_robo_settings


@lru_cache()
def get_robo_service() -> RoboService:
    """Get appropriate RoboService implementation based on environment.

    Returns:
        RoboService: Service implementation (OpenAI in prod, Test in test)
    """
    settings = get_robo_settings()
    config = settings.to_domain_config()

    # Use TestRoboService in test environment
    if os.getenv("ENV", "").lower() == "test":
        return TestRoboService(config)

    # Use OpenAIService in production
    return OpenAIService(config)
