"""Utility module for loading prompts from files."""

from pathlib import Path
from typing import Optional


def get_prompt_content(prompt_file: str) -> str:
    """
    Read prompt content from a file in the prompts directory.

    Args:
        prompt_file: Name of the prompt file (e.g., 'note_enrichment.txt')

    Returns:
        str: Content of the prompt file

    Raises:
        FileNotFoundError: If the prompt file doesn't exist
    """
    # Get the project root directory (where prompts/ is located)
    root_dir = Path(__file__).parent.parent
    prompt_path = root_dir / "prompts" / prompt_file

    if not prompt_path.exists():
        raise FileNotFoundError(
            f"Prompt file '{prompt_file}' not found in prompts directory"
        )

    with open(prompt_path, "r", encoding="utf-8") as f:
        return f.read().strip()


def get_prompt_from_env(
    env_value: Optional[str], default_file: str
) -> str:
    """
    Get prompt content either directly from env var or from a file.

    Args:
        env_value: Value from environment variable
        default_file: Default prompt file to use if env_value is a filename

    Returns:
        str: The prompt content
    """
    if not env_value:
        # If no env value, try to load from default file
        return get_prompt_content(default_file)

    # If the env value ends with .txt, treat it as a filename
    if env_value.endswith(".txt"):
        return get_prompt_content(env_value)

    # Otherwise, use the env value directly as the prompt
    return env_value
