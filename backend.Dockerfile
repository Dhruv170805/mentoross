# Backend Dockerfile
FROM python:3.13-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY backend/requirements.txt .
COPY backend/requirements-ml.txt .
RUN pip install --no-cache-dir -r requirements-ml.txt
RUN pip install certifi # Ensure SSL certs utility is present

# Copy backend source
COPY backend /app/backend

WORKDIR /app/backend

# Environment variables
ENV PYTHONUNBUFFERED=1
ENV ENVIRONMENT=production

# Expose API port
EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
