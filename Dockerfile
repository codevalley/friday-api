# syntax=docker/dockerfile:1

FROM python:3.12-slim

# Create a working directory
WORKDIR /app

# Copy Pipfile and Pipfile.lock
COPY Pipfile /app/Pipfile
COPY Pipfile.lock /app/Pipfile.lock

# If you plan to use local MySQL or otherwise need 'mysqlclient':
RUN apt-get update && apt-get install -y \
    build-essential \
    libmariadb-dev \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# Increase pip’s default timeout to reduce “read timed out” errors
ENV PIP_DEFAULT_TIMEOUT=300

# Install pipenv, then have pipenv install all packages into the system site-packages
RUN pip install --no-cache-dir pipenv
RUN pipenv install --system --deploy

# Copy rest of the code
COPY . /app

# Expose port (FastAPI default)
EXPOSE 8000

# Env var to run in production mode if needed
ENV ENV=production

# Start the app using uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
