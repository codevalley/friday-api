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
        "You are a skilled writer crafting natural, conversational "
        "templates for activity content. Your task is to analyze a JSON "
        "schema and create human-like templates that feel personal and "
        "engaging. Use $variable_name syntax to reference schema "
        "variables that will be populated dynamically.\n\n"
        "For the title:\n"
        "- Create a short, natural phrase (< 50 chars)\n"
        "- Avoid form-like formats (e.g. 'Description: $x')\n"
        "- Make it flow like natural speech\n"
        "- Example: '$amount steps on my morning walk' instead of "
        "'Steps: $amount'\n\n"
        "For the content:\n"
        "- Write in a natural, conversational style\n"
        "- Avoid form-like 'Field: Value' formats\n"
        "- Integrate variables naturally into sentences\n"
        "- Use Markdown for subtle emphasis where it enhances readability\n"
        "- Example: 'Walked for *$duration minutes* this morning' instead of "
        "'**Duration**: $duration minutes'\n\n"
        "Only return valid JSON with the structure:\n"
        "{\n"
        '  "title": "...",\n'
        '  "formatted": "..."\n'
        "}\n"
        "Do not include extra keys or commentary"
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
                    "You are a skilled writer crafting natural, "
                    "conversational templates for activity content. Your "
                    "task is to analyze a JSON schema and create human-like "
                    "templates that feel personal and engaging. Use "
                    "$variable_name syntax to reference schema variables "
                    "that will be populated dynamically.\n\n"
                    "For the title:\n"
                    "- Create a short, natural phrase (< 50 chars)\n"
                    "- Avoid form-like formats (e.g. 'Description: $x')\n"
                    "- Make it flow like natural speech\n"
                    "- Example: '$amount steps on my morning walk' instead of "
                    "'Steps: $amount'\n\n"
                    "For the content:\n"
                    "- Write in a natural, conversational style\n"
                    "- Avoid form-like 'Field: Value' formats\n"
                    "- Integrate variables naturally into sentences\n"
                    "- Use Markdown for subtle emphasis where it "
                    "enhances readability\n"
                    "- Example: 'Walked for *$duration minutes* this morning' "
                    "instead of '**Duration**: $duration minutes'\n\n"
                    "Only return valid JSON with the structure:\n"
                    "{\n"
                    '  "title": "...",\n'
                    '  "formatted": "..."\n'
                    "}\n"
                    "Do not include extra keys or commentary"
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
