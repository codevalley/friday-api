# OpenAI Service Refactoring Plan

## Objective
Add task processing functionality to the OpenAI service using the same robust pattern as the existing note and activity processing.

## Completed Changes

### 1. Function Definition
- Added PROCESS_TASK_FUNCTION with:
  - Title extraction
  - Formatted content
  - Priority suggestion
  - Due date extraction

### 2. Common Methods
- Added `_estimate_tokens` for consistent token estimation
- Added `_validate_tool_response` for robust response validation
- Implemented proper error handling and logging

### 3. Task Processing
- Implemented `_process_task` internal method with:
  - Function calling pattern
  - Token estimation
  - Rate limiting
  - Error handling
- Implemented `process_task` public method with:
  - Input validation
  - Retry decorator
  - Proper error categorization

## Remaining Tasks

### 1. Testing
1. Unit Tests (`test_openai_service.py`):
```python
def test_estimate_tokens():
    """Test token estimation logic."""

def test_validate_tool_response():
    """Test response validation with various scenarios."""

def test_process_task_success():
    """Test successful task processing."""

def test_process_task_empty_content():
    """Test validation of empty content."""

def test_process_task_rate_limit():
    """Test rate limiting behavior."""

def test_process_task_api_error():
    """Test API error handling."""
```

2. Integration Tests (`test_task_processing.py`):
```python
def test_task_processing_end_to_end():
    """Test complete task processing flow."""

def test_task_processing_with_priority():
    """Test priority extraction."""

def test_task_processing_with_due_date():
    """Test due date extraction."""
```

### 2. Documentation
1. Update docstrings with:
   - Complete parameter descriptions
   - Return value details
   - Error scenarios
   - Example usage

2. Add inline comments explaining:
   - Token estimation logic
   - Rate limiting strategy
   - Error handling approach

### 3. Code Quality
1. Run and fix any linting issues:
   ```bash
   flake8 services/OpenAIService.py
   black services/OpenAIService.py
   mypy services/OpenAIService.py
   ```

2. Verify type hints are complete and accurate

## Next Steps
1. Implement unit tests
2. Implement integration tests
3. Run linting and type checking
4. Update documentation
5. Final review and cleanup

## Validation Criteria
- All existing tests continue to pass
- New task processing functionality is properly tested
- Rate limiting works correctly
- Error handling is consistent with existing patterns
- Response format matches existing patterns
