# Soulfra Ghost Writer Platform - Docker Image
# https://github.com/calriven/soulfra

FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    sqlite3 \
    nginx \
    supervisor \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt requirements-dev.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p /app/logs \
    /app/static/qr \
    /app/static/generated \
    /app/neural_networks \
    /app/brands

# Initialize database (will create schema)
RUN python3 -c "from database import init_db; init_db()" || true
RUN python3 -c "from license_manager import init_license_tables; init_license_tables()" || true

# Create default .env if not exists
RUN if [ ! -f .env ]; then \
    echo "BASE_URL=http://localhost:5001" > .env; \
    echo "SECRET_KEY=change-me-in-production" >> .env; \
    echo "PLATFORM_VERSION=1.0.0" >> .env; \
    fi

# Expose port
EXPOSE 5001

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python3 -c "import requests; requests.get('http://localhost:5001/api/health')" || exit 1

# Run with gunicorn
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5001", "--timeout", "120", "app:app"]
