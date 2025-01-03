## Note Enrichment Feature Plan

### 1. Overview

Implement note enrichment feature using OpenAI's O1-mini model to:
1. Restructure raw note content into well-formatted markdown
2. Extract a concise title (< 50 characters)
3. Return structured JSON with title and formatted content

### 2. Implementation Plan

#### 2.1 Domain Layer Updates

1. **Update RoboService Interface**
```python
@dataclass
class NoteEnrichmentResult:
    title: str  # Extracted title (<50 chars)
    formatted: str  # Markdown formatted content
    tokens_used: int  # Token usage tracking
    model_name: str  # Name of model used
    created_at: datetime  # Timestamp
```

2. **Enhance OpenAIService Implementation**
```python
class OpenAIService(RoboService):
    def process_text(
        self,
        text: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> RoboProcessingResult:
        """Process text using various enrichment methods based on context."""
        if context.get("type") == "note_enrichment":
            return self._enrich_note(text)
        # ... other processing types ...

    def _enrich_note(self, content: str) -> RoboProcessingResult:
        """Internal method to enrich notes using function calling."""
        # Implementation using OpenAI function calling
```

#### 2.2 Infrastructure Layer

1. **OpenAI Function Definition**
```python
ENRICH_NOTE_FUNCTION = {
    "name": "enrich_note",
    "description": "Enrich a raw note by formatting content and extracting title",
    "parameters": {
        "type": "object",
        "properties": {
            "title": {
                "type": "string",
                "description": "Extracted title under 50 characters"
            },
            "formatted": {
                "type": "string",
                "description": "Well-formatted markdown content"
            }
        },
        "required": ["title", "formatted"]
    }
}
```

2. **Environment Configuration**
- Reuse existing OpenAI configuration
- Add model selection config
- Add token usage limits

#### 2.3 Application Layer Updates

1. **Update NoteWorker**
```python
def process_note_job(note_id: int):
    # Get note
    note = note_repository.get_by_id(note_id)

    # Process with context
    result = robo_service.process_text(
        note.content,
        context={"type": "note_enrichment"}
    )

    # Store results
    note.enrichment_data = {
        "title": result.metadata["title"],
        "formatted": result.content,
        "tokens_used": result.tokens_used,
        "model_name": result.model_name,
    }
```

2. **Error Handling**
- Reuse existing error types:
  - RoboAPIError
  - RoboConfigError
  - RoboRateLimitError
  - RoboValidationError

### 3. Implementation Steps

1. **Phase 1: Core Implementation**
- [✓] Create NoteEnrichmentResult class
- [✓] Update RoboService interface
- [✓] Update OpenAIService with note enrichment
- [✓] Add function calling support
- [✓] Add error handling
- [✓] Add unit tests

2. **Phase 2: Worker Integration**
- [✓] Update note_worker.py to use process_text with context
- [✓] Add configuration handling
- [✓] Implement retry logic
- [✓] Add integration tests

3. **Phase 3: Monitoring & Optimization**
- [✓] Add token usage tracking
- [ ] Add performance monitoring
- [ ] Optimize prompt for better results
- [ ] Add result quality metrics

### 4. Current Status

1. **Completed Features**
- Core note enrichment functionality implemented
- OpenAI function calling integration
- Worker processing with retry logic
- Token usage tracking
- Comprehensive test coverage

2. **Next Steps**
- Implement performance monitoring
- Add quality metrics tracking
- Optimize prompts based on usage data
- Set up monitoring dashboards

3. **Recent Updates**
- Fixed test suite to properly handle token usage
- Updated OpenAIService to use function calling
- Implemented proper error handling in worker
- Added integration tests for note processing

### 4. Example Usage

```python
# Example usage in note_worker
result = robo_service.process_text(
    note.content,
    context={"type": "note_enrichment"}
)

# Example enrichment result in metadata
{
    "title": "Weekly Team Sync Notes",
    "formatted": """
- Discussed Q1 goals and progress
- *Action items*:
  - Update project timeline
  - Schedule follow-up with design team
- **Next steps**: Review metrics by Friday

_Note: Sarah to lead next week's sync_
""",
    "model_name": "openai/o1-mini",
    "tokens_used": 150,
    "created_at": "2024-01-20T10:30:00Z"
}
```

### 5. Considerations

1. **Performance**
- Monitor token usage and costs
- Track processing time per note
- Set up alerts for high usage

2. **Error Handling**
- Reuse existing error handling
- Log failed enrichments
- Track error rates by type

3. **Quality**
- Regular review of enriched notes
- Feedback mechanism for quality
- Iterative prompt improvement

### 6. Future Enhancements

1. **Additional Processing Types**
- Extract tasks from notes
- Extract moments/events
- Sentiment analysis
- Topic classification

2. **Monitoring Additions**
- Quality metrics dashboard
- Cost tracking per note
- Performance analytics

### 7. Success Metrics

1. **Technical Metrics**
- Processing success rate > 99%
- Average processing time < 2s
- Token usage within budget

2. **Quality Metrics**
- Title accuracy > 95%
- Formatting improvement score
- User satisfaction rating
