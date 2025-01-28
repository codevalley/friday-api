# Entity Extraction System Design

## Overview
The entity extraction system is designed to process notes in a sequential manner, breaking down the complex task into three distinct steps with different success probabilities. This approach ensures that even if later steps fail, we still get partial success from earlier steps.

## Implementation Progress

### Current Status
✅ **Step 1: Note Enrichment**
- Implemented in OpenAIService.enrich_note()
- Successfully processes raw notes into cleaner format
- High success rate achieved

🔄 **Step 2: Task Extraction** (In Planning)
- Next priority
- Need to implement:
  - New OpenAIService.extract_tasks() method
  - Task extraction prompt
  - Integration with existing task creation flow

⏳ **Step 3: Moment Extraction** (Not Started)
- Planned for future implementation
- Dependencies on activity schema definition

### Next Steps
1. Design and implement task extraction prompt
2. Create extract_tasks() method in OpenAIService
3. Update note_worker to handle task extraction step
4. Add error handling and logging for task extraction

## Sequential Processing Steps

### 1. Note Enrichment (High Success Rate)
**Purpose**: Clean and restructure the note content into a more standardized format.

**Process**:
- Takes raw note text as input
- Restructures and formats the content
- Maintains the original meaning while improving clarity
- Returns enriched note content

**Characteristics**:
- Highest probability of success
- Minimal complexity
- Foundation for subsequent processing
- No external dependencies

### 2. Task Extraction (Medium/Low Success Rate)
**Purpose**: Identify and extract tasks mentioned in the note text.

**Process**:
- Takes raw note text as input
- Analyzes content for task-like statements
- For each identified task:
  - Creates a basic task object with required content
  - Associates the source note_id with the task
  - Automatically triggers task_enrichment queue via task_worker.py (already part of the create task API)

**Characteristics**:
- Medium complexity
- Independent of activity definitions
- Creates minimal task objects (only requires content string)
- Leverages existing task enrichment pipeline

### 3. Moment Extraction (Medium/Low Success Rate, High Error Probability)
**Purpose**: Identify and extract moments based on defined activity types.

**Process**:
1. Pre-check:
   - Query activities table
   - Skip entire step if no activities are defined
2. If activities exist:
   - Pass activity schemas to LLM
   - Analyze raw note content for matching activities
   - Create moment objects for each identified instance
   - Associate note_id with moment

**Characteristics**:
- Highest complexity
- Dependent on activity definitions
- Most error-prone step
- Creates concrete moment instances of abstract activity types

## Implementation Details

### Error Handling
- Each step is isolated from others
- Failures in later steps don't affect earlier successes
- Each step has its own error logging and recovery mechanisms

### Data Flow
```
Raw Note → Enriched Note → Tasks + Enriched Note → Moments
```

### Dependencies
- Task creation triggers existing task_worker.py pipeline
- Moment extraction requires defined activity schemas
- Each step uses separate LLM prompts and validation

### Success Metrics
- Note enrichment: Expected ~99% success rate
- Task extraction: Expected ~90% success rate [if note contains tasks]
- Moment extraction: Expected ~50% success rate (when activities exist)

## Future Enhancements
- Add more sophisticated validation for each step
- Implement retry mechanisms for failed steps
- Add support for new entity types
- Enhance prompt engineering for better accuracy
- Add confidence scores for extracted entities
