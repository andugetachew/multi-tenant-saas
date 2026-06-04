FROM python:3.12-slim

# Prevents .pyc files and enables stdout/stderr logging
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    postgresql-client \
    libpq-dev \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy project source
COPY . .

# Create non-root user and fix permissions
RUN useradd -m -u 1000 saas_user && \
    mkdir -p /app/staticfiles /app/media && \
    chown -R saas_user:saas_user /app

USER saas_user

EXPOSE 8000 8001
