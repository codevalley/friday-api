"""Test JSON utilities."""

from utils.json_utils import (
    ensure_dict,
    ensure_string,
    safe_json_loads,
)


def test_ensure_dict_with_valid_json_string():
    """Test ensure_dict with valid JSON string."""
    json_str = '{"key": "value"}'
    result = ensure_dict(json_str)
    assert result == {"key": "value"}


def test_ensure_dict_with_dict():
    """Test ensure_dict with dictionary input."""
    input_dict = {"key": "value"}
    result = ensure_dict(input_dict)
    assert result == input_dict


def test_ensure_dict_with_invalid_json():
    """Test ensure_dict with invalid JSON string."""
    result = ensure_dict("invalid json")
    assert result == {}


def test_ensure_dict_with_none():
    """Test ensure_dict with None input."""
    result = ensure_dict(None)
    assert result == {}


def test_ensure_string_with_dict():
    """Test ensure_string with dictionary input."""
    input_dict = {"key": "value"}
    result = ensure_string(input_dict)
    assert result == '{"key": "value"}'


def test_ensure_string_with_valid_json():
    """Test ensure_string with valid JSON string."""
    json_str = '{"key": "value"}'
    result = ensure_string(json_str)
    assert result == json_str


def test_ensure_string_with_invalid_json():
    """Test ensure_string with invalid JSON string."""
    result = ensure_string("invalid json")
    assert result == "{}"


def test_ensure_string_with_none():
    """Test ensure_string with None input."""
    result = ensure_string(None)
    assert result == "{}"


def test_safe_json_loads_with_valid_json():
    """Test safe_json_loads with valid JSON string."""
    json_str = '{"key": "value"}'
    result = safe_json_loads(json_str)
    assert result == {"key": "value"}


def test_safe_json_loads_with_invalid_json():
    """Test safe_json_loads with invalid JSON string."""
    result = safe_json_loads("invalid json")
    assert result == {}


def test_safe_json_loads_with_none():
    """Test safe_json_loads with None input."""
    result = safe_json_loads(None)
    assert result == {}
