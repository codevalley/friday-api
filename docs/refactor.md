# Code Refactoring Plan

## 1. Unused Imports & Code Cleanup

### Services Layer
- ~~Remove unused validation imports (Draft7Validator, ValidationError)~~ ✅
- ~~Remove redundant json imports~~ ✅
- ~~Clean up unused exception imports~~ ✅
- ~~Review and remove any commented-out code~~ ✅
- ~~Migrate from jsonschema to Pydantic validation~~ ✅

### Repositories Layer
- ~~Optimize type imports (replace broad imports with specific ones)~~ ✅
- ~~Review and consolidate SQLAlchemy imports~~ ✅
- ~~Remove any unused exception classes~~ ✅
- ~~Improve error handling and messages~~ ✅
- ~~Add proper transaction management~~ ✅

### Routers Layer
- ~~Clean up unused exception imports~~ ✅
- ~~Remove redundant schema imports~~ ✅
- ~~Consolidate common dependencies~~ ✅
- ~~Add standardized response format (GenericResponse)~~ ✅
- ~~Improve error handling with common decorator~~ ✅

### Models Layer ✅
- ~~Review and remove unused SQLAlchemy imports~~ ✅
- ~~Clean up any unused model relationships~~ ✅
- ~~Remove deprecated model fields if any~~ ✅
- ~~Add proper type hints for relationships~~ ✅
- ~~Add proper validation methods~~ ✅
- ~~Improve model documentation~~ ✅
- ~~Add proper model constraints~~ ✅
- ~~Fix moment_count property in ActivityModel~~ ✅
- ~~Fix MySQL timestamp columns for updated_at~~ ✅

### Schemas Layer ✅
- ~~Consolidate duplicate Pydantic imports~~ ✅
- ~~Remove redundant schema definitions~~ ✅
- ~~Clean up unused GraphQL type imports~~ ✅
- ~~Create base schema with common patterns~~ ✅
- ~~Add generic paginated response~~ ✅
- ~~Update Activity schema to use new base~~ ✅
- ~~Update to Pydantic v2 style config~~ ✅
- ~~Update Moment schema to use new base~~ ✅
- ~~Update User schema to use new base~~ ✅
- ~~Fix generic models to use Pydantic v2~~ ✅
- Add comprehensive schema documentation
- Add schema examples
- Consider schema versioning support

## Progress Tracking

- [x] Phase 1: Code Cleanup
  - [x] Services Layer
  - [x] Repositories Layer
  - [x] Routers Layer
  - [x] Models Layer
  - [x] Schemas Layer

- [ ] Phase 2: Type Improvements
  - [x] Services Layer
  - [x] Repositories Layer
  - [x] Routers Layer
  - [x] Models Layer
  - [ ] GraphQL Layer

- [ ] Phase 3: Documentation
  - [ ] Services Layer
  - [ ] Repositories Layer
  - [ ] Routers Layer
  - [x] Models Layer
  - [ ] GraphQL Layer 

## Next Steps:
1. Focus on Documentation:
   - Add comprehensive schema documentation
   - Add schema examples
   - Add API endpoint documentation
   - Add database schema documentation
   - Add deployment process documentation
   - Add error handling documentation

2. Then move to GraphQL Layer:
   - Update GraphQL types to match new schemas
   - Add proper error handling
   - Add comprehensive documentation
   - Add schema validation
   - Add proper type hints

3. Future Considerations:
   - Add metrics and monitoring
   - Add rate limiting for API endpoints
   - Add API versioning
   - Add API documentation using OpenAPI/Swagger
   - Add proper error handling documentation
   - Add database migration guides