# syntax=docker/dockerfile:1

FROM python:3.10-slim

# Create a working directory
WORKDIR /app

# Copy requirements
COPY requirements.txt /app/requirements.txt

# Install dependencies
RUN pip install --no-cache-dir -r /app/requirements.txt

# Copy rest of the code
COPY . /app

# Expose port (FastAPI default)
EXPOSE 8000

# Env var to run in production mode if needed
ENV ENV=production

# Start the app using uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
