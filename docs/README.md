# Friday API Documentation

## Overview

This project implements a clean architecture using FastAPI and GraphQL for a life logging system. The application allows users to track various activities and moments in their life, with flexible data schemas and validation.

## Project Structure

```
friday-api/
├── models/              # Domain entities (Activity, Moment)
├── services/           # Application business logic layer
├── repositories/       # Data access layer
├── schemas/           # Data transfer objects and validation schemas
│   ├── pydantic/     # Pydantic models
│   └── graphql/      # GraphQL type definitions
├── configs/           # Application configuration
└── docs/             # Documentation
```

## Architecture Layers

The project follows the Clean Architecture pattern with the following layers:

1. **Domain Layer** (`models/`)
   - Contains the core business entities (Activity, Moment)
   - Independent of external frameworks and tools
   - Defines the core business rules

2. **Application Layer** (`services/`)
   - Contains business logic
   - Orchestrates the flow of data
   - Implements use cases
   - Independent of external concerns

3. **Infrastructure Layer**
   - `repositories/`: Data access implementation
   - `schemas/`: Data transfer objects
   - `configs/`: External configurations

4. **Interface Layer**
   - GraphQL API with both queries and mutations
   - Data validation with Pydantic and JSON Schema
   - Type-safe operations

## Key Features

- Clean Architecture implementation
- GraphQL API with proper type definitions
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
