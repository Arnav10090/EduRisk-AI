#!/bin/bash
# Startup script for EduRisk AI backend
# This script waits for the database to be ready before starting the application

set -e

echo "Starting EduRisk AI Backend..."

# Wait for database to be ready
python /app/wait-for-db.py

# Run database migrations
echo "Running database migrations..."
cd /app/backend && alembic upgrade head

# Start the application
echo "Starting FastAPI application..."
cd /app
exec uvicorn backend.main:app --host 0.0.0.0 --port 8000
