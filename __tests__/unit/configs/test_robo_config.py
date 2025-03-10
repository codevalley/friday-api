"""Unit tests for RoboConfig."""

import pytest
from pydantic import SecretStr

from domain.exceptions import RoboConfigError
from domain.robo import RoboConfig as DomainRoboConfig
from configs.RoboConfig import RoboConfig


def test_robo_config_default_values():
    """Test RoboConfig default values."""
    config = RoboConfig()
    assert config.api_key is None
    assert config.model_name == "gpt-4o-mini"
    assert config.max_retries == 0
    assert config.timeout_seconds == 30
    assert config.temperature == 0.7
    assert config.max_tokens == 150
    assert (
        "You are a note formatting assistant"
        in config.note_enrichment_prompt
    )


def test_to_domain_config_missing_required_fields():
    """Test conversion to domain config with missing fields."""
    config = RoboConfig()
    with pytest.raises(RoboConfigError) as exc_info:
        config.to_domain_config()
    assert "OpenAI API key is required" in str(
        exc_info.value
    )


def test_to_domain_config_success():
    """Test successful conversion to domain config."""
    test_prompt = "Test prompt for note enrichment"
    config = RoboConfig(
        api_key=SecretStr("test-key"),
        model_name="test-model",
        service_implementation="manual",
        max_retries=5,
        timeout_seconds=60,
        temperature=0.5,
        max_tokens=200,
        note_enrichment_prompt=test_prompt,
        task_enrichment_prompt="Test task enrichment prompt",
        task_extraction_prompt="Test task extraction prompt",
    )
    domain_config = config.to_domain_config()
    assert isinstance(domain_config, DomainRoboConfig)
    assert domain_config.api_key == "test-key"
    assert domain_config.model_name == "test-model"
    from domain.robo import (
        ServiceImplementation as DomainServiceImplementation,
    )

    assert (
        domain_config.service_implementation
        == DomainServiceImplementation.MANUAL
    )
    assert domain_config.max_retries == 5
    assert domain_config.timeout_seconds == 60
    assert domain_config.temperature == 0.5
    assert domain_config.max_tokens == 200
    assert (
        domain_config.note_enrichment_prompt == test_prompt
    )
    assert (
        domain_config.task_enrichment_prompt
        == "Test task enrichment prompt"
    )
    assert (
        domain_config.task_extraction_prompt
        == "Test task extraction prompt"
    )
