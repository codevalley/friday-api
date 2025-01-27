## Technical Debt and Improvements Backlog

### Bugs

- [ ] TaskRouter: Update task should support updating notes as well. (Review overall and see what fields can be updated)
- [ ] TaskRouter: Subtask, do we need this ? Or just another update method to add parent task id ?
- [ ] Standardize schema implementations across entities
  - [ ] Standardize list response pattern:
    - Use `PaginationResponse` consistently (instead of mix of BaseModel/PaginatedResponse)
    - Ensure all list responses include proper pagination metadata
    - Add example responses in model_config
  - [ ] Standardize model configuration:
    - Use consistent ConfigDict settings
    - Add proper JSON encoders for datetime
    - Document required model configuration
  - [ ] Standardize domain conversion methods:
    - Implement consistent to_domain/from_domain patterns
    - Add proper type hints and validation
    - Document conversion method requirements
  - [ ] Update related components:
    - Align service layer responses with schema changes
    - Update router response models
    - Fix affected unit tests
  - [ ] Add comprehensive schema documentation:
    - Document standard patterns
    - Add examples for each pattern
    - Include validation rules
- [ ] Document: Test and verify endpoints in `test_flow.sh` to verify S3 upload/download

### Configuration and Code Organization 🔧

- [x] Resolve RedisConfig duplication
  - ✓ Removed duplicate RedisConfig class from infrastructure/redis
  - ✓ Consolidated into configs/redis/RedisConfig.py using Pydantic settings
  - ✓ Updated all related imports and tests
- [x] Consolidate database connection handling
  - ✓ Moved all database connection logic to configs/Database.py
  - ✓ Removed duplicate get_db_connection from db_dependencies.py
  - ✓ Fixed database schema to match ORM models
- [x] Review and refactor OpenAIService
  - ✓ Converted from async to sync for background worker compatibility
  - ✓ Simplified RateLimiter implementation
  - ✓ Removed redundant async/sync method variants
  - ✓ Updated all tests to match synchronous implementation
  - ✓ Fixed timezone handling in RateLimiter tests
- [x] Update RoboService interface
  - ✓ Make base interface consistently synchronous
  - ✓ Update interface documentation
  - ✓ Ensure all implementations follow sync pattern
  - ✓ Add comprehensive test coverage
- [ ] If many notes fail repeatedly, you might have logs flooded with “Failed to process note X”. Possibly consider a more robust circuit-breaker approach if the external AI is consistently failing. Right now, it’s probably fine if you only have moderate load.

### Code Quality and Performance 📈

- [ ] Optimize logging implementation
  - Remove unnecessary debug logging statements
  - Establish clear logging guidelines
  - Define appropriate log levels for different scenarios
- [ ] Remove magic strings
  - Create constants/enums for commonly used strings
  - Establish string constant organization strategy
- [ ] Optimize validation layers
  - Review validation duplication across domain/services/schemas
  - Measure and optimize validation performance
  - Consider caching validation results where appropriate

### Architecture and Patterns 🏗

- [ ] Standardize exception handling
  - Review current domain/app/HTTP exception pattern
  - Consider implementing consistent domain->HTTP mapping
  - Document exception handling guidelines
- [ ] Optimize service layer error handling
  - Review and reduce try/catch blocks
  - Implement more focused error handling
  - Consider using decorators for common error patterns
- [ ] Clarify service vs domain responsibilities
  - Review validation placement
  - Document layer responsibilities
  - Create clear boundaries between layers

### API and Repository Standardization 📚

- [ ] Standardize repository method naming
  - Create consistent naming conventions
  - Refactor get*by*\* methods
  - Document repository method naming guidelines

### Documentation Updates 📝

- [ ] Update architecture documentation
  - Document exception handling patterns
  - Clarify layer responsibilities
  - Add validation flow diagrams
- [ ] Create coding standards guide
  - Document naming conventions
  - Define logging guidelines
  - Establish error handling patterns
