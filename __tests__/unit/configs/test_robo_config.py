"""Unit tests for RoboConfig."""

import pytest
from pydantic import SecretStr

from domain.exceptions import RoboConfigError
from domain.robo import RoboConfig
from configs.RoboConfig import RoboSettings


def test_robo_settings_default_values():
    """Test RoboSettings default values."""
    settings = RoboSettings()
    assert settings.api_key is None
    assert settings.model_name == "gpt-4o-mini"
    assert settings.max_retries == 3
    assert settings.timeout_seconds == 30
    assert settings.temperature == 0.7
    assert settings.max_tokens == 150


def test_to_domain_config_missing_required_fields():
    """Test conversion to domain config with missing fields."""
    settings = RoboSettings()
    with pytest.raises(RoboConfigError) as exc_info:
        settings.to_domain_config()
    assert "OpenAI API key is required" in str(
        exc_info.value
    )


def test_to_domain_config_success():
    """Test successful conversion to domain config."""
    settings = RoboSettings(
        api_key=SecretStr("test-key"),
        model_name="test-model",
        max_retries=5,
        timeout_seconds=60,
        temperature=0.5,
        max_tokens=200,
    )
    config = settings.to_domain_config()
    assert isinstance(config, RoboConfig)
    assert config.api_key == "test-key"
    assert config.model_name == "test-model"
    assert config.max_retries == 5
    assert config.timeout_seconds == 60
    assert config.temperature == 0.5
    assert config.max_tokens == 200
