# Activity Schema Render Implementation Plan

## Overview

This document outlines the plan to implement schema rendering for activities, similar to note enrichment. The system will analyze activity schemas using AI to determine optimal rendering strategies.

## Current System Analysis

### Relevant Components
1. **RoboService Interface**
   - Defines abstract methods for AI processing
   - Currently handles note enrichment
   - Implemented by OpenAIService

2. **Worker System**
   - Uses RQ for background processing
   - Currently processes notes
   - Defined in run_worker.py

3. **Activity Domain**
   - Rich domain model with schema validation
   - ORM implementation with comprehensive tests
   - No current async processing capabilities

## Database Changes

### 1. Update Activity Table Schema

```sql
ALTER TABLE activities ADD COLUMN
    processing_status ENUM(
        'NOT_PROCESSED',
        'PENDING',
        'PROCESSING',
        'COMPLETED',
        'FAILED',
        'SKIPPED'
    ) NOT NULL DEFAULT 'NOT_PROCESSED';

ALTER TABLE activities ADD COLUMN
    schema_render JSON NULL,
    processed_at TIMESTAMP NULL;
```

## Implementation Plan

### Epic 1: Database and Model Updates ✅

#### Task 1: Update Database Schema ✅
- [x] Add migration script for new columns
- [x] Update init_database.sql with new schema
- [-] Add rollback script (skipped as not in production)

#### Task 2: Update Activity Models ✅
- [x] Update ActivityModel.py with new fields
- [x] Update domain/activity.py to include new fields
- [x] Add tests for new functionality

To verify the tests, run:
```bash
pytest __tests__/unit/domain/test_activity.py -v
```

### Epic 2: Queue Integration ✅

#### Task 1: Update Queue Service Interface ✅
- [x] Added enqueue_activity method to QueueService interface
- [x] Updated method signatures and documentation

#### Task 2: Update RQ Queue Implementation ✅
- [x] Added enqueue_activity implementation to RQNoteQueue
- [x] Maintained consistent patterns with note processing
- [x] Added proper error handling

### Epic 3: RoboService Updates ✅

#### Task 1: Update RoboService Interface ✅
- [x] Add analyze_activity_schema method to RoboService
- [x] Define interface and documentation
- [x] Add schema analysis prompt to RoboConfig

#### Task 2: Update OpenAI Implementation ✅
- [x] Add ANALYZE_SCHEMA_FUNCTION definition
- [x] Implement analyze_activity_schema method
- [x] Add error handling and logging
- [x] Add comprehensive tests

### Epic 4: Worker Implementation ✅

#### Task 1: Create Activity Worker ✅
- [x] Created activity_worker.py
- [x] Implemented process_activity_job function
- [x] Added error handling and logging

#### Task 2: Update Worker Runner ✅
- [x] Modified run_worker.py to handle both note and activity processing
- [x] Added proper error handling and logging
- [x] Added tests for worker initialization and shutdown
- [x] Fixed RQ library integration issues

### Epic 5: Service Layer Integration 🚧

#### Task 1: Update ActivityService ✅
- [x] Add queue service to ActivityService constructor
- [x] Implement activity processing queue integration
- [x] Add status check methods
- [x] Add retry/error handling logic
- [x] Add comprehensive tests

#### Task 2: Add Integration Tests 🚧 (Next Up)
- [ ] Test activity creation with queue integration
- [ ] Test processing status updates
- [ ] Test error scenarios
- [ ] Test retry mechanisms

#### Task 3: Update API Layer
- [ ] Add processing status to activity responses
- [ ] Add endpoints for checking processing status
- [ ] Add documentation for new endpoints

### Epic 6: Testing 🚧

#### Task 1: Fix Unit Tests (Current Focus)
- [x] Domain Tests
  - Fixed `test_activity_data_completed_without_processed_at` by adding validation for processed_at field
  - Updated ActivityData validation logic to ensure COMPLETED status requires both schema_render and processed_at

- [x] Queue Tests
  - Fixed `RQNoteQueue` missing queue attribute by using `note_queue` and `activity_queue`
  - Updated tests for `test_enqueue_note_success`, `test_enqueue_note_failure`, `test_get_queue_health`
  - Added proper mocking for queue health metrics using `count` and `Worker.all()`
  - All queue tests now passing

- [x] Redis Config Tests
  - Updated tests to use `queue_names` instead of `queue_name`
  - Fixed `test_redis_config_defaults` and `test_redis_config_queue_settings`
  - Added support for multiple queues in configuration
  - All Redis config tests now passing

- [ ] Activity Router Tests (Next Up)
  - Update tests to include required `user_id` parameter
  - Fix `test_get_processing_status` and `test_retry_processing` tests
  - Add tests for new processing status endpoints

- [ ] Activity Service Tests
  - Add `to_domain` method to `ActivityData`
  - Fix `test_create_activity_success` and `test_create_activity_queue_failure`
  - Add tests for processing status updates

#### Task 2: Integration Tests
- [ ] Fix and implement `test_activity_schema_success`
  - Test activity creation with schema
  - Verify processing status transitions
  - Check schema render output

- [ ] Fix and implement `test_activity_schema_failure`
  - Test invalid schema handling
  - Verify error status updates
  - Check error message propagation

- [ ] Fix and implement `test_activity_schema_retry`
  - Test retry mechanism for failed processing
  - Verify status updates during retry
  - Check final processing outcome

#### Task 3: Test Infrastructure
- [ ] Ensure consistent test data and fixtures
  - Create shared test data for activities
  - Set up proper database state
  - Add cleanup procedures

- [ ] Add proper cleanup in teardown
  - Clear queues between tests
  - Reset database state
  - Clean up any created files

- [ ] Implement proper mocking for external services
  - Mock RoboService for testing
  - Mock Redis for queue tests
  - Mock database connections where needed

### Next Steps
1. Fix Activity Router Tests
   - Focus on proper user_id handling
   - Add tests for processing status endpoints
   - Ensure proper error handling

2. Complete Activity Service Tests
   - Implement missing domain methods
   - Add tests for queue integration
   - Verify processing status handling

3. Implement Integration Tests
   - Set up test infrastructure
   - Add comprehensive test cases
   - Ensure proper cleanup

### Timeline
Week 1:
- Complete Activity Router Tests
- Fix Activity Service Tests
- Set up test infrastructure

Week 2:
- Implement integration tests
- Add cleanup procedures
- Document test coverage

## Notes

1. **Reuse Existing Infrastructure**:
   - Use existing worker infrastructure
   - Leverage RoboService pattern
   - Follow note enrichment patterns

2. **Error Handling**:
   - Implement proper retries
   - Handle API rate limits
   - Log failures appropriately

3. **Performance Considerations**:
   - Monitor queue length
   - Track processing times
   - Consider batch processing

4. **Future Improvements**:
   - Cache common rendering patterns
   - Implement schema versioning
   - Add rendering preview capability

## Activity Schema Render Implementation

### Current Status
- Epic 1: Database and Model Updates ✅
  - Added processing_status field to Activity model
  - Added schema_render field to Activity model
  - Added processed_at timestamp field
  - Added timezone awareness to all datetime fields

- Epic 2: Queue Integration ✅
  - Implemented activity_schema queue in RQNoteQueue
  - Added queue health monitoring
  - Fixed queue tests:
    - Corrected function path comparison in enqueue tests
    - Updated queue health metrics to use count() instead of len()
    - Properly mocked queue attributes and worker counts
    - All queue tests now passing

- Epic 3: RoboService Updates ✅
  - Added analyze_activity_schema method
  - Implemented schema analysis logic
  - Added test coverage

- Epic 4: Worker Implementation ✅
  - Implemented activity_worker.py
  - Added error handling and retries
  - Added proper logging

- Epic 5: Service Layer Updates
  Task 1: ActivityService Updates ✅
    - Added queue integration
    - Updated error handling
    - Fixed timezone handling

  Task 2: Integration Tests 🔄
    - Added basic test structure
    - Need to add more test cases for:
      - Error scenarios
      - Retry mechanisms
      - Edge cases

  Task 3: API Layer Updates (Pending)
    - Add new endpoints for:
      - Getting processing status
      - Retrying failed processing
      - Getting schema render results

### Next Steps
1. Fix Redis Config Tests
   - Update RedisConfig to handle multiple queue names
   - Update tests to reflect new queue configuration
   - Ensure backward compatibility

2. Complete Integration Tests
   - Add remaining test cases
   - Ensure proper test isolation
   - Add cleanup procedures

3. Implement API Layer Updates
   - Design new endpoints
   - Add request/response schemas
   - Add error handling

4. Documentation
   - Update API documentation
   - Add usage examples
   - Document error scenarios and recovery procedures

### Timeline
- Week 1: Complete Redis Config Tests and remaining Integration Tests
- Week 2: Implement API Layer Updates and Documentation

### Notes
- All datetime fields are now timezone-aware
- Queue health monitoring is working correctly
- Worker properly handles both note and activity processing
