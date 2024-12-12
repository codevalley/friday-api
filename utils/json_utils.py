import json
from typing import Dict, Optional, Union


def to_json_string(data: Optional[Dict]) -> Optional[str]:
    """Convert a dictionary to a JSON string, handling None values"""
    if data is None:
        return None
    return json.dumps(data)


def from_json_string(data: Optional[str]) -> Optional[Dict]:
    """Convert a JSON string to a dictionary, handling None values"""
    if data is None:
        return None
    return json.loads(data)


def ensure_dict(
    data: Union[str, Dict, None]
) -> Optional[Dict]:
    """Ensure data is a dictionary, converting from string if necessary"""
    if data is None:
        return None
    if isinstance(data, str):
        return json.loads(data)
    return data


def ensure_string(
    data: Union[str, Dict, None]
) -> Optional[str]:
    """Ensure data is a JSON string, converting from dict if necessary"""
    if data is None:
        return None
    if isinstance(data, dict):
        return json.dumps(data)
    return data
