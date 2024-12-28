"""Unit tests for Redis configuration."""

import pytest
from unittest.mock import patch
from configs.redis.RedisConfig import RedisConfig


def test_redis_config_defaults():
    """Test default configuration values."""
    config = RedisConfig()
    assert config.host == "localhost"
    assert config.port == 6379
    assert config.db == 0
    assert config.password is None
    assert config.ssl is False
    assert config.timeout == 10
    assert config.decode_responses is True
    assert config.job_timeout == 600
    assert config.job_ttl == 3600
    assert config.queue_name == "note_enrichment"


@pytest.mark.parametrize(
    "env_vars,expected",
    [
        (
            {
                "REDIS_HOST": "redis.example.com",
                "REDIS_PORT": "6380",
                "REDIS_DB": "1",
                "REDIS_PASSWORD": "secret",
                "REDIS_SSL": "true",
                "REDIS_TIMEOUT": "20",
            },
            {
                "host": "redis.example.com",
                "port": 6380,
                "db": 1,
                "password": "secret",
                "ssl": True,
                "socket_timeout": 20,
                "decode_responses": True,
            },
        ),
    ],
)
def test_redis_config_from_env(env_vars, expected):
    """Test configuration from environment variables."""
    with patch.dict("os.environ", env_vars, clear=True):
        config = RedisConfig()
        connection_params = config.get_connection_params()
        assert connection_params == expected


def test_redis_config_invalid_port():
    """Test handling of invalid port number."""
    with patch.dict(
        "os.environ", {"REDIS_PORT": "invalid"}, clear=True
    ):
        with pytest.raises(ValueError):
            RedisConfig()


def test_redis_config_invalid_db():
    """Test handling of invalid database number."""
    with patch.dict(
        "os.environ", {"REDIS_DB": "invalid"}, clear=True
    ):
        with pytest.raises(ValueError):
            RedisConfig()


def test_redis_config_queue_settings():
    """Test queue-specific settings."""
    with patch.dict(
        "os.environ",
        {
            "REDIS_JOB_TIMEOUT": "300",
            "REDIS_JOB_TTL": "1800",
            "REDIS_QUEUE_NAME": "test_queue",
        },
        clear=True,
    ):
        config = RedisConfig()
        assert config.job_timeout == 300
        assert config.job_ttl == 1800
        assert config.queue_name == "test_queue"
