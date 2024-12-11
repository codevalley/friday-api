# Testing Strategy

## Overview

The project implements a comprehensive testing strategy that covers all layers of the clean architecture. Tests are organized in the `__tests__` directory and use pytest as the test runner along with unittest for assertions.

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
Test all model functionality including:
- Model initialization
- Field validations
- Relationships
- Model methods

Example (`test_activity_model.py`):
```python
def test_activity_model_initialization():
    activity = ActivityModel(
        name="test_activity",
        description="Test activity",
        activity_schema={"type": "object"},
        icon="📝",
        color="#000000"
    )
    assert activity.name == "test_activity"
    assert activity.icon == "📝"

def test_activity_moment_relationship():
    activity = ActivityModel(name="test_activity")
    moment = MomentModel(
        activity=activity,
        timestamp=datetime.utcnow(),
        data={"notes": "test"}
    )
    assert moment in activity.moments
```

#### Service Tests (`unit/services/`)
Test all business logic including:
- CRUD operations
- Data validation
- Error handling
- Computed fields (e.g., moment_count)

Example (`test_activity_service.py`):
```python
def test_create_activity_with_invalid_schema():
    with pytest.raises(HTTPException) as exc:
        activity_service.create_activity(ActivityCreate(
            name="test",
            activity_schema={"invalid": "schema"}
        ))
    assert exc.value.status_code == 400

def test_moment_count_computation():
    activity = activity_service.create_activity(valid_activity_data)
    assert activity.momentCount == 0
    
    moment_service.create_moment(create_moment_data(activity.id))
    updated_activity = activity_service.get_activity(activity.id)
    assert updated_activity.momentCount == 1
```

#### Repository Tests (`unit/repositories/`)
Test all data access including:
- CRUD operations
- Query filters
- Database constraints
- Error conditions

Example (`test_moment_repository.py`):
```python
def test_list_moments_with_filters():
    repository = MomentRepository(db_session)
    moments = repository.list_moments(
        activity_id=1,
        start_time=datetime(2024, 1, 1),
        end_time=datetime(2024, 12, 31)
    )
    assert all(m.activity_id == 1 for m in moments.items)
    assert all(
        datetime(2024, 1, 1) <= m.timestamp <= datetime(2024, 12, 31) 
        for m in moments.items
    )
```

### 2. Integration Tests

#### GraphQL Tests (`integration/graphql/`)
Test the GraphQL API including:
- Queries
- Mutations
- Field resolvers
- Error handling
- Data loading

Example (`test_activity_queries.py`):
```python
async def test_get_activity_with_moment_count():
    # Create test data
    activity_id = await create_test_activity()
    await create_test_moments(activity_id, count=3)
    
    # Execute query
    response = await client.post("/graphql", json={
        "query": """
        query {
            getActivity(id: 1) {
                id
                name
                momentCount
                moments { id }
            }
        }
        """
    })
    
    data = response.json()["data"]["getActivity"]
    assert data["momentCount"] == 3
    assert len(data["moments"]) == 3
```

#### REST Tests (`integration/rest/`)
Test the REST API including:
- Endpoints
- Request validation
- Response formats
- Error handling

Example (`test_moment_endpoints.py`):
```python
async def test_create_moment_endpoint():
    # Create test activity
    activity = await create_test_activity()
    
    # Test moment creation
    response = await client.post(
        "/api/v1/moments",
        json={
            "activity_id": activity.id,
            "timestamp": "2024-12-11T08:58:02Z",
            "data": {"notes": "Test moment"}
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["activity_id"] == activity.id
```

## Test Fixtures

### Base Fixtures (`conftest.py`)
```python
@pytest.fixture
def db_session():
    """Provides a clean database session for each test"""
    engine = create_engine(settings.TEST_DATABASE_URL)
    SessionLocal = sessionmaker(bind=engine)
    Base.metadata.create_all(bind=engine)
    
    session = SessionLocal()
    try:
        yield session
    finally:
        session.rollback()
        session.close()

@pytest.fixture
def client(db_session):
    """Test client with database session"""
    app.dependency_overrides[get_db_connection] = lambda: db_session
    with TestClient(app) as test_client:
        yield test_client
```

### Activity Fixtures (`fixtures/activity_fixtures.py`)
```python
@pytest.fixture
def valid_activity_data():
    return {
        "name": "test_activity",
        "description": "Test activity",
        "activity_schema": {
            "type": "object",
            "properties": {
                "notes": {"type": "string"}
            }
        },
        "icon": "📝",
        "color": "#000000"
    }

@pytest.fixture
def sample_activity(db_session):
    activity = ActivityModel(**valid_activity_data())
    db_session.add(activity)
    db_session.commit()
    return activity
```

### Moment Fixtures (`fixtures/moment_fixtures.py`)
```python
@pytest.fixture
def valid_moment_data(sample_activity):
    return {
        "activity_id": sample_activity.id,
        "timestamp": datetime.utcnow(),
        "data": {"notes": "Test moment"}
    }

@pytest.fixture
def sample_moments(db_session, sample_activity):
    moments = []
    for i in range(3):
        moment = MomentModel(
            activity_id=sample_activity.id,
            timestamp=datetime.utcnow(),
            data={"notes": f"Test moment {i}"}
        )
        moments.append(moment)
    db_session.add_all(moments)
    db_session.commit()
    return moments
```

## Coverage Goals

1. **Models**: 100% coverage
   - All model attributes
   - All model methods
   - All relationships

2. **Services**: 95%+ coverage
   - All business logic paths
   - All validation rules
   - Error handling
   - Edge cases

3. **Repositories**: 95%+ coverage
   - All CRUD operations
   - Query filters
   - Error conditions

4. **API Layer**: 90%+ coverage
   - All endpoints
   - All GraphQL operations
   - Input validation
   - Error responses

## Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=. --cov-report=html

# Run specific test categories
pytest __tests__/unit/
pytest __tests__/integration/

# Run tests matching a pattern
pytest -k "activity"

# Run tests with detailed output
pytest -v
```

## Best Practices

1. **Test Independence**
   - Each test should be independent
   - Use fixtures for setup/teardown
   - Clean up test data

2. **Test Naming**
   - Clear, descriptive names
   - Follow pattern: test_[what]_[expected]

3. **Assertions**
   - One logical assertion per test
   - Use appropriate assertion methods
   - Include meaningful messages

4. **Mocking**
   - Mock external dependencies
   - Use proper scoping
   - Verify mock interactions

5. **Database Tests**
   - Use transactions
   - Roll back after tests
   - Use test database

6. **Coverage**
   - Regular coverage reports
   - Address coverage gaps
   - Focus on critical paths