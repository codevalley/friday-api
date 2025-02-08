"""Unit tests for InstructorService."""

import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime, timezone
import json
from dateutil.tz import UTC

from domain.robo import (
    RoboConfig,
    RoboProcessingResult
)
from domain.exceptions import RoboConfigError
from domain.exceptions import (
    RoboRateLimitError,
    RoboAPIError,
    RoboValidationError,
)
from services.InstructorService import (
    InstructorService,
    NoteEnrichmentSchema,
    TaskEnrichmentSchema,
    ActivitySchemaAnalysis,
)


@pytest.fixture
def mock_openai(mocker):
    """Mock OpenAI client with instructor support."""
    # Create mock response for note enrichment
    note_mock = mocker.MagicMock()
    note_mock.model_dump.return_value = {
        "title": "Test Note",
        "formatted": "# Test Note\n\nContent here",
        "metadata": {"topics": ["test"]},
    }

    # Create mock response for task enrichment
    task_mock = mocker.MagicMock()
    task_mock.model_dump.return_value = {
        "title": "Test Task",
        "formatted": "Complete test task",
        "suggested_priority": "HIGH",
        "suggested_due_date": "2024-02-15T17:00:00Z",
        "metadata": {"tags": ["test"]},
    }

    # Create OpenAI client mock
    client_mock = mocker.MagicMock()
    
    # Mock response for note processing
    note_response = mocker.MagicMock()
    note_response.choices = [
        mocker.MagicMock(
            message=mocker.MagicMock(
                content="# Test Note\n\nContent here"
            )
        )
    ]
    note_response.usage = mocker.MagicMock(total_tokens=100)
    
    # Mock response for task processing
    task_response = mocker.MagicMock()
    task_response.choices = [
        mocker.MagicMock(
            message=mocker.MagicMock(
                content="# Test Task\n\nComplete test task"
            )
        )
    ]
    task_response.usage = mocker.MagicMock(total_tokens=80)
    
    # Mock response for schema analysis
    schema_response = mocker.MagicMock()
    schema_response.choices = [
        mocker.MagicMock(
            message=mocker.MagicMock(
                content="Template content"
            )
        )
    ]
    schema_response.usage = mocker.MagicMock(total_tokens=120)
    
    # Configure mock to return different responses based on input
    def side_effect(*args, **kwargs):
        messages = kwargs.get('messages', [])
        if any('formats notes' in msg.get('content', '') for msg in messages):
            return note_response
        elif any('formats tasks' in msg.get('content', '') for msg in messages):
            return task_response
        else:
            return schema_response
    
    client_mock.chat.completions.create.side_effect = side_effect
    return client_mock


@pytest.fixture
def mock_rate_limiter():
    """Create a mock rate limiter."""
    limiter = MagicMock()
    limiter.wait_for_capacity.return_value = True
    return limiter


@pytest.fixture
def robo_config():
    """Create a test RoboConfig instance."""
    return RoboConfig(
        api_key="test-key",
        model_name="gpt-4",
        max_retries=1,
        timeout_seconds=5,
    )


@pytest.fixture
def instructor_service(
    robo_config, mock_openai, mock_rate_limiter
):
    """Create an InstructorService instance with mocks."""
    service = InstructorService(robo_config)
    service.client = mock_openai
    service.rate_limiter = mock_rate_limiter
    return service


class TestInstructorService:
    """Test suite for InstructorService."""

    def test_initialization(self, robo_config):
        """Test service initialization."""
        with patch("services.InstructorService.OpenAI") as mock_openai_class:
            service = InstructorService(robo_config)
            assert service.config == robo_config
            mock_openai_class.assert_called_once_with(api_key=robo_config.api_key)

    def test_initialization_without_api_key(self):
        """Test initialization fails without API key."""
        config = RoboConfig(api_key=None, model_name="gpt-4")
        with pytest.raises(RoboConfigError):
            InstructorService(config)

    def test_process_note_success(
        self, instructor_service, mock_openai
    ):
        """Test successful note processing."""
        content = "Meeting notes for project planning"
        result = instructor_service.process_note(content)

        assert isinstance(result, RoboProcessingResult)
        assert result.content == "# Test Note\n\nContent here"
        assert result.metadata["title"] == "Test Note"
        assert result.tokens_used > 0

    def test_process_note_rate_limit(
        self, instructor_service, mock_rate_limiter
    ):
        """Test note processing with rate limit."""
        mock_rate_limiter.wait_for_capacity.return_value = False
        with pytest.raises(RoboRateLimitError):
            instructor_service.process_note("test content")

    def test_process_task_success(
        self, instructor_service, mock_openai
    ):
        """Test successful task processing."""
        content = "Complete project proposal by next week"
        result = instructor_service.process_task(content)

        assert isinstance(result, RoboProcessingResult)
        assert result.content == "# Test Task\n\nComplete test task"
        assert result.metadata["title"] == "Test Task"
        assert result.metadata["suggested_priority"] == "HIGH"
        assert result.tokens_used > 0

    def test_process_task_validation(
        self, instructor_service
    ):
        """Test task processing input validation."""
        with pytest.raises(RoboValidationError, match="Content cannot be empty"):
            instructor_service.process_task("")

    def test_analyze_activity_schema_success(
        self, instructor_service, mock_openai
    ):
        """Test successful activity schema analysis."""
        schema = {
            "type": "object",
            "properties": {
                "action": {"type": "string"},
                "project": {"type": "string"},
            },
        }
        result = instructor_service.analyze_activity_schema(schema)

        assert "title_template" in result
        assert "content_template" in result
        assert "suggested_layout" in result

    def test_health_check_success(
        self, instructor_service
    ):
        """Test successful health check."""
        # Create a MagicMock for the models.list method
        models_list_mock = MagicMock(return_value=["gpt-4", "gpt-3.5-turbo"])
        # Set up the mock on the service's client
        instructor_service.client.models.list = models_list_mock
        assert instructor_service.health_check() is True

    def test_health_check_failure(
        self, instructor_service, mock_openai
    ):
        """Test health check failure."""
        mock_openai.models.list.side_effect = Exception("API Error")
        assert instructor_service.health_check() is False

    def test_estimate_tokens(self, instructor_service):
        """Test token estimation logic."""
        text = "This is a test" * 10  # 40 characters
        estimated = instructor_service._estimate_tokens(text)
        assert estimated == 135  # (40 // 4) + 100 buffer


class TestNoteEnrichmentSchema:
    """Test suite for NoteEnrichmentSchema."""

    def test_valid_schema(self):
        """Test schema with valid data."""
        data = {
            "title": "Test Note",
            "formatted": "# Test Note\n\nContent here",
            "metadata": {"topics": ["test"]},
        }
        schema = NoteEnrichmentSchema(**data)
        assert schema.title == data["title"]
        assert schema.formatted == data["formatted"]
        assert schema.metadata == data["metadata"]

    def test_title_max_length(self):
        """Test title length validation."""
        with pytest.raises(ValueError):
            NoteEnrichmentSchema(
                title="x" * 51,
                formatted="content",
            )

    def test_required_fields(self):
        """Test required field validation."""
        with pytest.raises(ValueError):
            NoteEnrichmentSchema(title="Test")

        with pytest.raises(ValueError):
            NoteEnrichmentSchema(formatted="Content")


class TestTaskEnrichmentSchema:
    """Test suite for TaskEnrichmentSchema."""

    def test_valid_schema(self):
        """Test schema with valid data."""
        data = {
            "title": "Test Task",
            "formatted": "Complete test task",
            "suggested_priority": "high",
            "suggested_due_date": "2024-02-15T17:00:00Z",
            "metadata": {"tags": ["test"]},
        }
        schema = TaskEnrichmentSchema(**data)
        assert schema.title == data["title"]
        assert schema.formatted == data["formatted"]
        assert (
            schema.suggested_due_date.isoformat().replace("+00:00", "Z")
            == data["suggested_due_date"]
        )

    def test_optional_fields(self):
        """Test schema with only required fields."""
        schema = TaskEnrichmentSchema(
            title="Test",
            formatted="Content",
        )
        assert schema.suggested_priority is None
        assert schema.suggested_due_date is None
        assert schema.metadata == {}

    def test_invalid_priority(self):
        """Test invalid priority validation."""
        with pytest.raises(ValueError):
            TaskEnrichmentSchema(
                title="Test",
                formatted="Content",
                suggested_priority="INVALID",
            )


class TestActivitySchemaAnalysis:
    """Test suite for ActivitySchemaAnalysis."""

    def test_valid_schema(self):
        """Test schema with valid data."""
        data = {
            "title_template": "$action on $project",
            "content_template": "**Action:** $action\n**Project:** $project",
            "suggested_layout": {
                "type": "card",
                "sections": [
                    {"title": "Action", "field": "action"},
                    {"title": "Project", "field": "project"},
                ],
            },
        }
        schema = ActivitySchemaAnalysis(**data)
        assert schema.title_template == data["title_template"]
        assert schema.content_template == data["content_template"]
        assert schema.suggested_layout == data["suggested_layout"]

    def test_required_fields(self):
        """Test required field validation."""
        with pytest.raises(ValueError):
            ActivitySchemaAnalysis(
                title_template="$action",
                content_template="Content",
            )

        with pytest.raises(ValueError):
            ActivitySchemaAnalysis(
                content_template="Content",
                suggested_layout={},
            )
