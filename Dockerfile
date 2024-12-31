# syntax=docker/dockerfile:1

FROM python:3.10-slim

# Create a working directory
WORKDIR /app

# Copy Pipfile and Pipfile.lock
COPY Pipfile /app/Pipfile
COPY Pipfile.lock /app/Pipfile.lock

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
