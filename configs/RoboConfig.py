"""Configuration for RoboService."""

from functools import lru_cache
from pydantic import BaseModel, SecretStr

from domain.exceptions import RoboConfigError
from configs.Environment import get_environment_variables
from domain.robo import RoboConfig as DomainRoboConfig
from utils.prompt_loader import get_prompt_from_env


from enum import Enum


class ServiceImplementation(str, Enum):
    """Available RoboService implementations."""

    MANUAL = "manual"  # Manual function definition approach
    INSTRUCTOR = "instructor"  # Instructor-based approach


class RoboConfig(BaseModel):
    """Configuration for RoboService."""

    api_key: SecretStr | None = None
    model_name: str = "gpt-4o-mini"
    service_implementation: ServiceImplementation = (
        ServiceImplementation.MANUAL
    )
    max_retries: int = 0
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
        "You are a helpful assistant that creates templates "
        "for displaying activity content. Your task is to "
        "analyze a JSON schema that defines the structure of "
        "an activity and create templates for displaying the "
        "activity's title and content. Use $variable_name "
        "syntax to reference schema variables that will be "
        "populated dynamically. For the title, create a "
        "short template (< 50 chars) that captures the key "
        "information. For the formatted content, use "
        "Markdown for emphasis (bold, italics, bullet "
        "points) to create a well-structured template."
    )
    task_enrichment_prompt: str = (
        "You are a task processing assistant. Your task is to:\n"
        "1. Extract a descriptive title (<50 chars)\n"
        "2. Format the content in clean markdown\n"
        "3. Suggest a priority (high/medium/low)\n"
        "4. Extract any mentioned due dates (ISO format)\n"
        "5. Keep the content clear and actionable"
    )
    task_extraction_prompt: str = (
        "You are a task extraction assistant. Your task is to:\n"
        "1. Analyze the given note content\n"
        "2. Identify and extract any tasks or action items\n"
        "3. For each task, extract only the essential task description\n"
        "4. Return tasks in a clear, actionable format\n"
        "5. Exclude any non-task content or context\n"
        "Note: A task is any actionable item that requires completion"
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

        # Convert service implementation to domain enum
        from domain.robo import (
            ServiceImplementation as DomainServiceImplementation,
        )

        try:
            domain_impl = getattr(
                DomainServiceImplementation,
                self.service_implementation.name,
            )
        except (AttributeError, ValueError):
            domain_impl = DomainServiceImplementation.MANUAL

        return DomainRoboConfig(
            api_key=self.api_key.get_secret_value(),
            model_name=self.model_name,
            service_implementation=domain_impl,
            max_retries=self.max_retries,
            timeout_seconds=self.timeout_seconds,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
            note_enrichment_prompt=self.note_enrichment_prompt,
            activity_schema_prompt=self.activity_schema_prompt,
            task_enrichment_prompt=self.task_enrichment_prompt,
            task_extraction_prompt=self.task_extraction_prompt,
        )

    @classmethod
    def from_env(cls) -> "RoboConfig":
        """Create config from environment variables."""
        env = get_environment_variables()

        # Get prompts from files or environment
        note_enrichment_prompt = get_prompt_from_env(
            env.ROBO_NOTE_ENRICHMENT_PROMPT,
            "note_enrichment.txt",
        )
        activity_schema_prompt = get_prompt_from_env(
            env.ROBO_ACTIVITY_SCHEMA_PROMPT,
            "activity_schema.txt",
        )
        task_extraction_prompt = get_prompt_from_env(
            env.ROBO_TASK_EXTRACTION_PROMPT,
            "task_extraction.txt",
        )
        task_enrichment_prompt = get_prompt_from_env(
            env.ROBO_TASK_ENRICHMENT_PROMPT,
            "task_enrichment.txt",
        )

        # Parse service implementation
        try:
            # Strip any comments and whitespace, convert to lowercase
            impl_value = (
                env.ROBO_SERVICE_IMPLEMENTATION.split("#")[
                    0
                ]
                .strip()
                .lower()
            )
            service_impl = ServiceImplementation(impl_value)
        except (ValueError, AttributeError):
            # Default to MANUAL if parsing fails
            service_impl = ServiceImplementation.MANUAL

        return cls(
            api_key=env.ROBO_API_KEY,
            model_name=env.ROBO_MODEL_NAME
            or "gpt-3.5-turbo",
            service_implementation=service_impl,
            max_retries=env.ROBO_MAX_RETRIES,
            timeout_seconds=env.ROBO_TIMEOUT_SECONDS,
            temperature=env.ROBO_TEMPERATURE,
            max_tokens=env.ROBO_MAX_TOKENS,
            note_enrichment_prompt=note_enrichment_prompt,
            activity_schema_prompt=activity_schema_prompt,
            task_extraction_prompt=task_extraction_prompt,
            task_enrichment_prompt=task_enrichment_prompt,
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
            f"Failed to load RoboService settings: {e}"
        ) from e
