import json
from typing import Dict, Union, TypeVar, Optional

T = TypeVar("T", Dict, str)


def ensure_dict(value: Union[str, Dict, None]) -> Dict:
    """
    Ensure a value is a dictionary, converting from JSON string if necessary.

    Args:
        value: A string containing JSON, a dictionary, or None

    Returns:
        Dict: The input converted to a dictionary,
        or an empty dict if conversion fails
    """
    if value is None:
        return {}
    if isinstance(value, str):
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return {}
    if isinstance(value, dict):
        return value
    return {}


def ensure_string(value: Union[str, Dict, None]) -> str:
    """
    Ensure a value is a JSON string, converting from dictionary if necessary.

    Args:
        value: A dictionary, JSON string, or None

    Returns:
        str: The input converted to a JSON string, or "{}" if conversion fails
    """
    if value is None:
        return "{}"
    if isinstance(value, str):
        try:
            # Validate it's proper JSON by parsing and re-stringifying
            return json.dumps(json.loads(value))
        except json.JSONDecodeError:
            return "{}"
    if isinstance(value, dict):
        return json.dumps(value)
    return "{}"


def safe_json_loads(value: Optional[str]) -> Dict:
    """
    Safely load a JSON string into a dictionary.

    Args:
        value: A string containing JSON or None

    Returns:
        Dict: The parsed dictionary, or an empty dict if parsing fails
    """
    try:
        return json.loads(value) if value else {}
    except json.JSONDecodeError:
        return {}
