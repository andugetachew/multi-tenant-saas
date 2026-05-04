FROM python:3.11-slim

WORKDIR /app


RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .


RUN pip install --no-cache-dir -r requirements.txt
COPY . .


ENV DJANGO_SETTINGS_MODULE=core.settings
ENV DATABASE_URL=postgres://postgres:postgres123@db:5432/multitenant_db

EXPOSE 8000

CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]