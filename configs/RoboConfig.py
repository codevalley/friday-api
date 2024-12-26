from functools import lru_cache
from pydantic import BaseModel, Field, SecretStr
import os

from domain.robo import RoboConfig
from domain.exceptions import RoboConfigError


class RoboSettings(BaseModel):
    """Pydantic model for Robo configuration settings."""

    api_key: SecretStr | None = Field(
        None, description="API key for Robo service"
    )
    model_name: str | None = Field(
        None,
        description="Model name to use for Robo service",
    )
    max_retries: int = Field(
        default=3,
        ge=1,
        le=10,
        description="Maximum number of retry attempts",
    )
    timeout_seconds: int = Field(
        default=30,
        ge=1,
        le=300,
        description="Timeout in seconds for API calls",
    )
    temperature: float = Field(
        default=0.7,
        ge=0.0,
        le=2.0,
        description="Temperature parameter for response generation",
    )
    max_tokens: int = Field(
        default=150,
        ge=1,
        le=4096,
        description="Maximum number of tokens to generate",
    )

    def to_domain_config(self) -> RoboConfig:
        """Convert settings to domain RoboConfig object."""
        if not self.api_key or not self.model_name:
            if os.getenv("ENV") == "test":
                # Return test configuration
                return RoboConfig(
                    api_key="test_key",
                    model_name="test_model",
                    max_retries=self.max_retries,
                    timeout_seconds=self.timeout_seconds,
                    temperature=self.temperature,
                    max_tokens=self.max_tokens,
                )
            raise RoboConfigError(
                "API key and model name are required in non-test environments"
            )

        return RoboConfig(
            api_key=self.api_key.get_secret_value(),
            model_name=self.model_name,
            max_retries=self.max_retries,
            timeout_seconds=self.timeout_seconds,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
        )


@lru_cache
def get_robo_settings() -> RoboSettings:
    """Get Robo settings from environment variables."""
    try:
        from .Environment import get_environment_variables

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
