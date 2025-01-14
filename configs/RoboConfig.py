"""Configuration for RoboService."""

from functools import lru_cache
from pydantic import BaseModel, SecretStr

from domain.exceptions import RoboConfigError
from configs.Environment import get_environment_variables
from domain.robo import RoboConfig as DomainRoboConfig


class RoboConfig(BaseModel):
    """Configuration for RoboService."""

    api_key: SecretStr | None = None
    model_name: str = "gpt-4o-mini"
    max_retries: int = 3
    timeout_seconds: int = 30
    temperature: float = 0.7
    max_tokens: int = 150
    note_enrichment_prompt: str = (
        "You are a note formatting assistant. "
        "Your task is to:\n"
        "1. Extract a concise title (<50 chars)\n"
        "2. Format the content in clean markdown\n"
        "3. Use appropriate formatting (bold, italic, lists)\n"
        "4. Keep the content concise but complete"
    )
    activity_schema_prompt: str = (
        "You are a helpful assistant that creates templates for "
        "displaying activity content. Your task is to analyze a JSON "
        "schema that defines the structure of an activity and create "
        "templates for displaying the activity's title and content. "
        "Use $variable_name syntax to reference schema variables that "
        "will be populated dynamically. For the title, create a short "
        "template (< 50 chars) that captures the key information. For "
        "the formatted content, use Markdown for emphasis (bold, "
        "italics, bullet points) to create a well-structured template."
    )

    def to_domain_config(self) -> DomainRoboConfig:
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

        return DomainRoboConfig(
            api_key=self.api_key.get_secret_value(),
            model_name=self.model_name,
            max_retries=self.max_retries,
            timeout_seconds=self.timeout_seconds,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
            note_enrichment_prompt=self.note_enrichment_prompt,
            activity_schema_prompt=self.activity_schema_prompt,
        )

    @classmethod
    def from_env(cls) -> "RoboConfig":
        """Create config from environment variables."""
        env = get_environment_variables()
        return cls(
            api_key=env.ROBO_API_KEY,
            model_name=env.ROBO_MODEL_NAME
            or "gpt-3.5-turbo",
            max_retries=env.ROBO_MAX_RETRIES,
            timeout_seconds=env.ROBO_TIMEOUT_SECONDS,
            temperature=env.ROBO_TEMPERATURE,
            max_tokens=env.ROBO_MAX_TOKENS,
            note_enrichment_prompt=getattr(
                env,
                "ROBO_NOTE_ENRICHMENT_PROMPT",
                (
                    "You are a note formatting assistant. "
                    "Your task is to:\n"
                    "1. Extract a concise title (<50 chars)\n"
                    "2. Format the content in clean markdown\n"
                    "3. Use appropriate formatting (bold, italic, lists)\n"
                    "4. Keep the content concise but complete"
                ),
            ),
            activity_schema_prompt=getattr(
                env,
                "ROBO_ACTIVITY_SCHEMA_PROMPT",
                (
                    "You are a helpful assistant that creates templates "
                    "for displaying activity content. Your task is to "
                    "analyze a JSON schema that defines the structure of "
                    "an activity and create templates for displaying the "
                    "activity's title and content. Use $variable_name "
                    "syntax to reference schema variables that will be "
                    "populated dynamically. For the title, create a short "
                    "template (< 50 chars) that captures the key "
                    "information. For the formatted content, use Markdown "
                    "for emphasis (bold, italics, bullet points) to "
                    "create a well-structured template."
                ),
            ),
        )


@lru_cache()
def get_robo_settings() -> RoboConfig:
    """Get RoboService settings.

    Returns:
        RoboSettings: Service settings

    Raises:
        RoboConfigError: If settings cannot be loaded
    """
    try:
        return RoboConfig.from_env()
    except Exception as e:
        raise RoboConfigError(
            f"Failed to load Robo settings: {str(e)}"
        )
