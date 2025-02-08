# Development Setup Guide

## Prerequisites

- Python 3.12 or higher
- pipenv (for dependency management)
- Git

## Getting Started

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd friday-api
   ```

2. Install dependencies using pipenv:
   ```bash
   pipenv install --dev
   ```

## Key Dependencies

The project uses several key dependencies:

### Core Dependencies
- **fastapi**: Web framework for building APIs
- **pydantic**: Data validation using Python type annotations
- **openai**: OpenAI API client
- **instructor**: Enhanced OpenAI function calling with Pydantic
  - Version: >=0.4.0
  - Used for type-safe OpenAI function calls
  - Provides better integration between Pydantic models and OpenAI

### Development Dependencies
- **black**: Code formatting
- **flake8**: Code linting
- **mypy**: Static type checking
- **pytest**: Testing framework
- **pytest-mock**: Mocking for tests
- **pytest-asyncio**: Async test support

## Configuration

1. Create a `.env` file in the project root:
   ```bash
   cp .env.example .env
   ```

2. Update the `.env` file with your configuration:
   ```env
   OPENAI_API_KEY=your-api-key
   MODEL_NAME=gpt-4
   ```

## Development Workflow

1. Activate the virtual environment:
   ```bash
   pipenv shell
   ```

2. Run tests:
   ```bash
   pytest
   ```

3. Format code:
   ```bash
   black .
   ```

4. Run linting:
   ```bash
   flake8
   ```

5. Run type checking:
   ```bash
   mypy .
   ```

## Code Quality Standards

1. All code must pass:
   - black formatting
   - flake8 linting
   - mypy type checking
   - pytest tests

2. Follow these practices:
   - Write docstrings for all public functions and classes
   - Add type hints for all function parameters and return types
   - Write unit tests for new functionality
   - Keep functions focused and single-purpose
   - Use meaningful variable and function names
