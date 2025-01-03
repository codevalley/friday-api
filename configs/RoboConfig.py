"""Configuration for RoboService."""

from functools import lru_cache
from pydantic import BaseModel, SecretStr

from domain.exceptions import RoboConfigError
from domain.robo import RoboConfig


class RoboSettings(BaseModel):
    """Settings for RoboService."""

    api_key: SecretStr | None = None
    model_name: str = "gpt-4o-mini"
    max_retries: int = 3
    timeout_seconds: int = 30
    temperature: float = 0.7
    max_tokens: int = 150

    def to_domain_config(self) -> RoboConfig:
        """Convert settings to domain config.

        Returns:
            RoboConfig: Domain configuration

        Raises:
            RoboConfigError: If required fields are missing
        """
        if not self.api_key:
            raise RoboConfigError(
                "OpenAI API key is required"
            )

        return RoboConfig(
            api_key=self.api_key.get_secret_value(),
            model_name=self.model_name,
            max_retries=self.max_retries,
            timeout_seconds=self.timeout_seconds,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
        )


@lru_cache()
def get_robo_settings() -> RoboSettings:
    """Get RoboService settings.

    Returns:
        RoboSettings: Service settings

    Raises:
        RoboConfigError: If settings cannot be loaded
    """
    try:
        from configs.Environment import (
            get_environment_variables,
        )

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
