import os
import pytest
from pydantic import SecretStr
from configs.RoboConfig import (
    RoboSettings,
    get_robo_settings,
)
from domain.exceptions import RoboConfigError


def test_robo_settings_default_values():
    """Test that RoboSettings has correct default values."""
    settings = RoboSettings()
    assert settings.api_key is None
    assert settings.model_name is None
    assert settings.max_retries == 3
    assert settings.timeout_seconds == 30
    assert settings.temperature == 0.7
    assert settings.max_tokens == 150


def test_robo_settings_custom_values():
    """Test that RoboSettings accepts custom values."""
    settings = RoboSettings(
        api_key=SecretStr("test_key"),
        model_name="test_model",
        max_retries=5,
        timeout_seconds=60,
        temperature=0.5,
        max_tokens=200,
    )
    assert settings.api_key.get_secret_value() == "test_key"
    assert settings.model_name == "test_model"
    assert settings.max_retries == 5
    assert settings.timeout_seconds == 60
    assert settings.temperature == 0.5
    assert settings.max_tokens == 200


def test_to_domain_config_with_valid_settings():
    """Test conversion to domain config with valid settings."""
    settings = RoboSettings(
        api_key=SecretStr("test_key"),
        model_name="test_model",
    )
    config = settings.to_domain_config()
    assert config.api_key == "test_key"
    assert config.model_name == "test_model"
    assert config.max_retries == 3
    assert config.timeout_seconds == 30
    assert config.temperature == 0.7
    assert config.max_tokens == 150


def test_to_domain_config_in_test_environment():
    """Test conversion to domain config in test environment."""
    os.environ["ENV"] = "test"
    settings = RoboSettings()
    config = settings.to_domain_config()
    assert config.api_key == "test_key"
    assert config.model_name == "test_model"
    os.environ.pop("ENV", None)


def test_to_domain_config_missing_required_fields():
    """Test conversion to domain config with missing required fields."""
    os.environ["ENV"] = "production"
    settings = RoboSettings()
    with pytest.raises(RoboConfigError) as exc_info:
        settings.to_domain_config()
    assert "API key and model name are required" in str(
        exc_info.value
    )
    os.environ.pop("ENV", None)


def test_get_robo_settings_success(monkeypatch):
    """Test successful retrieval of Robo settings."""

    class MockEnv:
        ROBO_API_KEY = SecretStr("test_key")
        ROBO_MODEL_NAME = "test_model"
        ROBO_MAX_RETRIES = 5
        ROBO_TIMEOUT_SECONDS = 60
        ROBO_TEMPERATURE = 0.5
        ROBO_MAX_TOKENS = 200

    def mock_get_env():
        return MockEnv()

    monkeypatch.setattr(
        "configs.Environment.get_environment_variables",
        mock_get_env,
    )

    settings = get_robo_settings()
    assert settings.api_key.get_secret_value() == "test_key"
    assert settings.model_name == "test_model"
    assert settings.max_retries == 5
    assert settings.timeout_seconds == 60
    assert settings.temperature == 0.5
    assert settings.max_tokens == 200


def test_get_robo_settings_failure(monkeypatch):
    """Test failure in retrieving Robo settings."""
    # Clear the cache before running the test
    get_robo_settings.cache_clear()

    def mock_get_env():
        raise ValueError("Test error")

    monkeypatch.setattr(
        "configs.Environment.get_environment_variables",
        mock_get_env,
    )

    with pytest.raises(RoboConfigError) as exc_info:
        get_robo_settings()

    assert (
        str(exc_info.value)
        == "Failed to load Robo settings: Test error"
    )
