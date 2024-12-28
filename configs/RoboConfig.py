"""RoboService configuration module."""

import os
from functools import lru_cache
from pydantic import SecretStr
from pydantic_settings import BaseSettings
from typing import Optional

from domain.exceptions import RoboConfigError
from configs.Environment import get_environment_variables


class RoboSettings(BaseSettings):
    """RoboService configuration settings."""

    api_key: Optional[SecretStr] = None
    model_name: Optional[str] = None
    max_retries: int = 3
    timeout_seconds: int = 30
    temperature: float = 0.7
    max_tokens: int = 150

    def to_domain_config(self) -> "RoboConfig":
        """Convert settings to domain config.

        Returns:
            RoboConfig: Domain configuration object

        Raises:
            RoboConfigError: If required fields are missing in production
        """
        env = os.getenv("ENV", "").lower()
        if env == "test":
            return RoboConfig(
                api_key="test_key",
                model_name="test_model",
                max_retries=self.max_retries,
                timeout_seconds=self.timeout_seconds,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                is_test=True,
            )

        if not self.api_key or not self.model_name:
            raise RoboConfigError(
                "API key and model name are required in non-test environment"
            )

        return RoboConfig(
            api_key=self.api_key.get_secret_value(),
            model_name=self.model_name,
            max_retries=self.max_retries,
            timeout_seconds=self.timeout_seconds,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
            is_test=False,
        )

    class Config:
        """Pydantic configuration."""

        env_prefix = "ROBO_"


class RoboConfig:
    """Domain configuration for RoboService."""

    def __init__(
        self,
        api_key: str,
        model_name: str,
        max_retries: int = 3,
        timeout_seconds: int = 30,
        temperature: float = 0.7,
        max_tokens: int = 150,
        is_test: bool = False,
    ):
        """Initialize RoboConfig.

        Args:
            api_key: API key for the service
            model_name: Model name to use
            max_retries: Maximum number of retries
            timeout_seconds: Timeout in seconds
            temperature: Temperature parameter for generation
            max_tokens: Maximum tokens to generate
            is_test: Whether this is a test configuration
        """
        self.api_key = api_key
        self.model_name = model_name
        self.max_retries = max_retries
        self.timeout_seconds = timeout_seconds
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.is_test = is_test


@lru_cache()
def get_robo_settings() -> RoboSettings:
    """Get RoboService settings with caching.

    Returns:
        RoboSettings: Service settings

    Raises:
        RoboConfigError: If settings cannot be loaded
    """
    try:
        env = get_environment_variables()
        return RoboSettings(
            api_key=env.ROBO_API_KEY,
            model_name=env.ROBO_MODEL_NAME,
            max_retries=env.ROBO_MAX_RETRIES,
            timeout_seconds=env.ROBO_TIMEOUT_SECONDS,
            temperature=env.ROBO_TEMPERATURE,
            max_tokens=env.ROBO_MAX_TOKENS,
        )
    except Exception as e:
        raise RoboConfigError(
            f"Failed to load Robo settings: {str(e)}"
        )
