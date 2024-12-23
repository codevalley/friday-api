# Test Migration Plan

## Overview
Moving tests from `/tests` to `/__tests__` to consolidate all tests in one location.

## Files to Review and Migrate

### Note-Related Tests
1. `/tests/services/test_note_service.py` -> `/__tests__/unit/services/test_note_service.py`
   - Contains comprehensive service layer tests
   - Need to merge with existing service tests pattern

2. `/tests/unit/routers/test_note_router.py` -> `/__tests__/unit/routers/test_note_router.py`
   - Router tests with good coverage
   - Follows similar pattern to other router tests

3. `/tests/unit/models/test_note_model.py` -> `/__tests__/unit/models/test_note_model.py`
   - Model tests with validation checks
   - Matches existing model test structure

4. `/tests/unit/repositories/test_note_repository.py` -> `/__tests__/unit/repositories/test_note_repository.py`
   - Repository layer tests
   - Consistent with other repository tests

### Activity-Related Tests
5. `/tests/services/test_activity_service.py` -> Already exists in `/__tests__/unit/services/test_activity_service.py`
   - Review for any unique test cases to merge
   - Can be discarded after review

### Other Tests to Review
6. `/tests/conftest.py` -> Compare with `/__tests__/conftest.py`
   - Review fixtures and test configurations
   - Merge any unique fixtures

7. `/tests/test_user_auth.py` -> Compare with `/__tests__/test_user_auth.py`
   - Review authentication test coverage
   - Merge any missing test cases

8. `/tests/unit/models/test_activity_model.py` -> Already exists in `/__tests__/unit/models/test_activity_model.py`
   - Review for any unique test cases
   - Can be discarded after review

9. `/tests/unit/models/test_base_model.py` -> Already exists in `/__tests__/unit/models/test_base_model.py`
   - Review for any unique test cases
   - Can be discarded after review

10. `/tests/unit/models/test_moment_model.py` -> Already exists in `/__tests__/unit/models/test_moment_model.py`
    - Review for any unique test cases
    - Can be discarded after review

11. `/tests/unit/models/test_user_model.py` -> Already exists in `/__tests__/unit/models/test_user_model.py`
    - Review for any unique test cases
    - Can be discarded after review

12. `/tests/unit/repositories/test_activity_repository.py` -> Already exists in `/__tests__/unit/repositories/test_activity_repository.py`
    - Review for any unique test cases
    - Can be discarded after review

13. `/tests/unit/repositories/test_base_repository.py` -> Already exists in `/__tests__/unit/repositories/test_base_repository.py`
    - Review for any unique test cases
    - Can be discarded after review

14. `/tests/unit/repositories/test_moment_repository.py` -> Already exists in `/__tests__/unit/repositories/test_moment_repository.py`
    - Review for any unique test cases
    - Can be discarded after review

## Migration Steps
1. Review each file in `/tests` against its counterpart in `/__tests__`
2. Create missing test files in `/__tests__` structure
3. Merge unique test cases from `/tests` into `/__tests__`
4. Update imports and dependencies
5. Run tests to verify functionality
6. Delete original files from `/tests`

## Progress
- [x] Review and compare conftest.py files
- [x] Review and merge user auth tests
- [x] Review activity-related tests
- [x] Review moment-related tests
- [x] Review user model tests
- [x] Review repository tests
- [x] Migrate note service tests
- [-] Migrate note router tests (in progress)
- [x] Migrate note model tests
- [x] Migrate note repository tests
- [ ] Verify all tests pass
- [ ] Remove old test files

## Additional Test Coverage Needed
### Note Service Tests
- [ ] Test error handling (invalid content, attachments)
- [ ] Test activity/moment validation
- [ ] Test user authorization edge cases

## Migration Order
1. First Wave (Base Infrastructure)
   - conftest.py (merge fixtures first)
   - test_base_model.py (foundational tests)
   - test_base_repository.py (foundational tests)

2. Second Wave (Core Domain)
   - Activity tests
   - Moment tests
   - User tests

3. Final Wave (New Features)
   - Note tests (migrate all note-related tests)
   - Verify end-to-end functionality

## Test Commands
```bash
# Run all migrated note tests
pytest __tests__/unit/*/test_note_*.py -v

# Run specific note test files
pytest __tests__/unit/models/test_note_model.py -v
pytest __tests__/unit/repositories/test_note_repository.py -v
pytest __tests__/unit/services/test_note_service.py -v
```