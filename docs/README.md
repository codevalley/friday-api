# FastAPI Clean Architecture Example Documentation

## Overview

This project demonstrates a clean architecture (hexagonal architecture) implementation using FastAPI. The application showcases a book management system with authors and books as the main entities, implementing both REST and GraphQL APIs.

## Project Structure

```
fastapi-clean-example/
├── models/              # Domain entities and business objects
├── services/           # Application business logic layer
├── repositories/       # Data access layer
├── routers/           # API endpoints and route handlers
├── schemas/           # Data transfer objects and validation schemas
├── configs/           # Application configuration
├── metadata/          # Metadata definitions
└── __tests__/         # Test suites
```

## Architecture Layers

The project follows the Clean Architecture pattern with the following layers:

1. **Domain Layer** (`models/`)
   - Contains the core business entities
   - Independent of external frameworks and tools
   - Defines the core business rules

2. **Application Layer** (`services/`)
   - Contains business logic
   - Orchestrates the flow of data
   - Implements use cases
   - Independent of external concerns

3. **Infrastructure Layer**
   - `repositories/`: Data access implementation
   - `routers/`: HTTP/API handlers
   - `configs/`: External configurations

4. **Interface Layer**
   - REST API endpoints
   - GraphQL API
   - Data transfer objects (DTOs)

## Key Features

- Clean Architecture implementation
- Dual API support (REST and GraphQL)
- Domain-Driven Design principles
- Dependency injection
- Repository pattern
- Type safety with Pydantic
- Comprehensive testing setup

## Documentation Structure

1. [Architecture Overview](architecture.md)
2. [Domain Models](domain-models.md)
3. [Application Services](application-services.md)
4. [API Layer](api-layer.md)
5. [Data Access Layer](data-access.md)
6. [Testing Strategy](testing.md)

## Getting Started

Please refer to the main project README.md for setup and installation instructions. 