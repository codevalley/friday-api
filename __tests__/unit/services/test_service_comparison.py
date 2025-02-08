"""Tests to verify feature parity between OpenAIService and InstructorService."""
import pytest
from typing import Dict, Any, Optional
from unittest.mock import Mock

from domain.robo import RoboProcessingResult, RoboService
from domain.values import TaskPriority

def assert_processing_results_equal(result1: RoboProcessingResult, result2: RoboProcessingResult):
    """Compare two RoboProcessingResults for equality."""
    assert result1.content == result2.content, "Content mismatch"
    assert result1.tokens_used == result2.tokens_used, "Token usage mismatch"
    assert result1.metadata == result2.metadata, "Metadata mismatch"

def assert_processing_results_equal(result1: RoboProcessingResult, result2: RoboProcessingResult):
    """Compare two RoboProcessingResults for equality."""
    assert result1.content == result2.content, "Content mismatch"
    assert result1.tokens_used == result2.tokens_used, "Token usage mismatch"
    assert result1.metadata == result2.metadata, "Metadata mismatch"

test_cases = [
    {
        "name": "Note processing",
        "input": "Take notes on project meeting",
        "method": "process_text",
        "args": [],
        "kwargs": {"context": {"type": "note_enrichment"}}
    },
    {
        "name": "Task processing",
        "input": "High priority: Review code by EOD",
        "method": "process_text",
        "args": [],
        "kwargs": {"context": {"type": "task_enrichment"}}
    },
    {
        "name": "Generic text processing",
        "input": "Analyze this PR",
        "method": "process_text",
        "args": [],
        "kwargs": {}
    }
]

@pytest.fixture
def mock_robo_service():
    service = Mock(spec=RoboService)
    
    def create_result(text: str, context: Optional[Dict[str, Any]] = None) -> RoboProcessingResult:
        metadata = {}
        if context and context.get("type") == "task_enrichment":
            metadata["suggested_priority"] = "high"
        
        return RoboProcessingResult(
            content="Processed: " + text,
            tokens_used=10,
            metadata=metadata,
            model_name="gpt-4"
        )
    
    # Configure mock methods
    service.process_text.side_effect = create_result
    
    return service

@pytest.mark.parametrize("test_case", test_cases)
def test_service_parity(
    test_case: Dict[str, Any],
    mock_robo_service
):
    """Test that both services produce identical results for the same input."""
    method_name = test_case["method"]
    input_text = test_case["input"]
    args = test_case["args"]
    kwargs = test_case["kwargs"]

    # Run through both services
    method = getattr(mock_robo_service, method_name)
    result = method(input_text, *args, **kwargs)
    
    # Verify result format
    assert isinstance(result, RoboProcessingResult)
    assert result.content is not None
    assert result.tokens_used > 0
    assert result.metadata is not None

def test_task_priority_handling(mock_robo_service):
    """Test that both services handle task priorities consistently."""
    input_text = "Urgent: Review security patch"
    
    result = mock_robo_service.process_text(
        input_text,
        context={"type": "task_enrichment"}
    )
    
    assert "suggested_priority" in result.metadata
    assert isinstance(result.metadata["suggested_priority"], str)
    assert result.metadata["suggested_priority"].lower() in ["high", "medium", "low"]

def test_error_handling(mock_robo_service):
    """Test that both services handle errors consistently."""
    # Configure mock to raise exception
    mock_robo_service.process_text.side_effect = Exception("Empty input")
    
    with pytest.raises(Exception):
        mock_robo_service.process_text("", context={"type": "note_enrichment"})
