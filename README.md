# Friday API

A powerful life logging API built with FastAPI. Track your daily activities and moments with rich, structured data.

[![Python](https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54)](https://docs.python.org/3/)
[![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)](https://fastapi.tiangolo.com/)
[![OpenAPI](https://img.shields.io/badge/openapi-6BA539?style=for-the-badge&logo=openapi-initiative&logoColor=fff)](https://www.openapis.org/)
[![Swagger](https://img.shields.io/badge/-Swagger-%23Clojure?style=for-the-badge&logo=swagger&logoColor=white)](https://swagger.io/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg?style=for-the-badge)](https://black.readthedocs.io/en/stable/)
[![Typed with: pydantic](https://img.shields.io/badge/typed%20with-pydantic-BA600F.svg?style=for-the-badge)](https://docs.pydantic.dev/)

## Features

- **Activity Management**: Create and manage activity types with custom JSON schemas
- **Moment Logging**: Log moments with structured data based on activity schemas
- **Flexible Querying**: Filter moments by time range and activity type
- **Data Validation**: Automatic validation of moment data against activity schemas
- **UTC Time Handling**: Proper timezone handling for global usage

## Getting Started

### Prerequisites

- Python 3.8+
- MySQL 8.0+
- [Pipenv](https://pipenv.pypa.io/en/latest/)

### Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/friday-api.git
cd friday-api
```

2. Install dependencies:
```bash
pipenv install
```

3. Set up your environment variables in `.env`:
```env
APP_ENV=development
APP_NAME=friday-api
DATABASE_DIALECT=mysql
DATABASE_HOSTNAME=localhost
DATABASE_NAME=test_fridaystore
DATABASE_PASSWORD=your_password
DATABASE_PORT=3306
DATABASE_USERNAME=your_username
```

4. Initialize the database:
```bash
# Run the SQL script in scripts/init_database.sql
```

5. Start the server:
```bash
pipenv run uvicorn main:app --reload
```

The API will be available at:
- REST API: http://localhost:8000/v1
- API Documentation: http://localhost:8000/docs

## API Documentation

See [API Reference](docs/api-reference.md) for detailed endpoint documentation.

### Quick Examples

#### Create an Activity
```bash
curl -X POST "http://localhost:8000/v1/activities" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Reading",
    "description": "Track reading sessions",
    "activity_schema": {
      "type": "object",
      "properties": {
        "book": { "type": "string" },
        "pages": { "type": "number" },
        "notes": { "type": "string" }
      }
    },
    "icon": "📚",
    "color": "#4A90E2"
  }'
```

#### Log a Moment
```bash
curl -X POST "http://localhost:8000/v1/moments" \
  -H "Content-Type: application/json" \
  -d '{
    "activity_id": 1,
    "timestamp": "2024-12-11T05:30:00Z",
    "data": {
      "book": "The Pragmatic Programmer",
      "pages": 50,
      "notes": "Great chapter on code quality"
    }
  }'
```

## Development

### Project Structure
```
friday-api/
├── configs/            # Configuration modules
├── models/            # SQLAlchemy models
├── schemas/           # Pydantic schemas
│   └── pydantic/     # Data validation schemas
├── repositories/     # Database operations
├── services/        # Business logic
├── routers/         # API endpoints
│   └── v1/         # API version 1
└── docs/           # Documentation
```

### Running Tests
```bash
pipenv run pytest
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
