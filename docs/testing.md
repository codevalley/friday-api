# Testing Strategy

## Overview

The project implements a comprehensive testing strategy that covers all layers of the clean architecture. Tests are organized in the `__tests__` directory and use pytest as the test runner along with unittest for assertions.

## Current Test Coverage Status (as of 2024-12-12)

### Completed Tests
1. **Model Tests**:
   - Activity Model
     - Model initialization
     - Database persistence
     - Moment relationships
     - Unique name constraint
     - Required fields validation
     - Schema validation
   - Moment Model
     - Model initialization
     - Database persistence
     - Activity relationships
     - Cascade delete behavior
     - Required fields validation
     - Data validation against activity schema

### Pending Tests
1. **Service Layer**:
   - Activity Service
   - Moment Service
   - Data validation and business logic

2. **Repository Layer**:
   - Activity Repository
   - Moment Repository
   - Query filters and constraints

3. **API Layer**:
   - GraphQL queries and mutations
   - REST endpoints
   - Error handling
   - Authentication/Authorization

## Test Structure

```
__tests__/
├── unit/
│   ├── models/              
│   │   ├── test_activity_model.py
│   │   └── test_moment_model.py
│   ├── services/           
│   │   ├── test_activity_service.py
│   │   └── test_moment_service.py
│   └── repositories/       
│       ├── test_activity_repository.py
│       └── test_moment_repository.py
├── integration/           
│   ├── graphql/
│   │   ├── test_activity_queries.py
│   │   ├── test_moment_queries.py
│   │   ├── test_activity_mutations.py
│   │   └── test_moment_mutations.py
│   └── rest/
│       ├── test_activity_endpoints.py
│       └── test_moment_endpoints.py
├── conftest.py            
└── fixtures/             
    ├── activity_fixtures.py
    └── moment_fixtures.py
```

## Test Categories

### 1. Unit Tests

#### Model Tests (`unit/models/`)
Currently implemented tests cover:
- Model initialization and validation
- Database persistence and constraints
- Field validations (required fields, unique constraints)
- Relationships between models
- Schema validation for Activity and Moment data
- Cascade delete behavior

Example (`test_activity_model.py`):
```python
def test_activity_model_initialization():
    activity = Activity(
        name="test_activity",
        description="Test activity",
        activity_schema={"type": "object"},
        icon="",
        color="#000000"
    )
    assert activity.name == "test_activity"
    assert activity.icon == ""

def test_activity_required_fields():
    activity = Activity()  # Missing required fields
    with pytest.raises(IntegrityError):
        db_session.add(activity)
        db_session.commit()
```

## Running Tests

To run the tests, use the following commands:

```bash
# Install dependencies
pipenv install --dev

# Run all tests
pipenv run pytest

# Run specific test category
pipenv run pytest __tests__/unit/models -v

# Run with coverage report
pipenv run pytest --cov=./ --cov-report=term-missing
```

## Next Steps

1. Implement Service Layer Tests
   - CRUD operations
   - Business logic validation
   - Error handling

2. Implement Repository Layer Tests
   - Database operations
   - Query filters
   - Error conditions

3. Implement Integration Tests
   - GraphQL API
   - REST endpoints
   - End-to-end workflows

4. Add Performance Tests
   - Load testing
   - Response time benchmarks
   - Database query optimization

## Best Practices

1. **Test Isolation**: Each test should be independent and not rely on the state from other tests
2. **Clean Setup/Teardown**: Use fixtures to set up and clean up test data
3. **Meaningful Assertions**: Tests should verify specific behaviors and edge cases
4. **Clear Test Names**: Use descriptive names that indicate what is being tested
5. **DRY Test Code**: Use fixtures and helper functions to avoid repetition
6. **Complete Coverage**: Aim for high test coverage, especially in critical paths