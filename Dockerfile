FROM python:3.10-slim

# Install postgres dependencies
RUN apt-get update && apt-get install -y \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements first
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the project
COPY . .

# Generate static files for production
RUN python manage.py collectstatic --noinput

# Start the Django server
CMD gunicorn mental_health_backend.wsgi --log-file -
