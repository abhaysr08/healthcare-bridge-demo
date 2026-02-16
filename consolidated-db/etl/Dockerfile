FROM python:3.11-slim

WORKDIR /app

# Install system dependencies (no Oracle client for AWS deployment)
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy ETL scripts
COPY *.py ./
COPY .env.example .env

# Create log directory
RUN mkdir -p /var/log/healthbridge

# Create non-root user
RUN useradd -m -u 1000 etluser && \
    chown -R etluser:etluser /app /var/log/healthbridge
USER etluser

# Default command (can be overridden)
CMD ["python", "run_etl.py"]
