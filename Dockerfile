FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    wget \
    netcat-traditional \
    build-essential \
    libssl-dev \
    libffi-dev \
    git \
    && rm -rf /var/lib/apt/lists/*

# Create application directory
WORKDIR /app

# Copy requirements files
COPY requirements.txt requirements-dev.txt ./

# Install Python dependencies
RUN pip install --upgrade pip setuptools wheel && \
    pip install -r requirements.txt && \
    pip install -r requirements-dev.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p /app/logs /app/public/uploads

# Health check
HEALTHCHECK --interval=10s --timeout=5s --retries=3 --start-period=30s \
    CMD curl -f http://localhost:8000/health || exit 1

# Expose port
EXPOSE 8000

# Start the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
