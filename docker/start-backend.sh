#!/bin/bash
# Startup script for EduRisk AI backend
# This script waits for the database to be ready before starting the application

set -e

echo ""
echo "=========================================="
echo "🚀 EduRisk AI Backend Starting..."
echo "=========================================="

# Wait for database to be ready
python /app/wait-for-db.py

# Initialize database tables
echo ""
echo "📦 Initializing database tables..."
if [ -f /app/init-db.py ]; then
    python /app/init-db.py 2>&1 | grep -E "(✅|⚠️|❌)" || echo "✅ Database tables ready"
else
    echo "⚠️  Database initialization script not found, tables may need manual creation"
fi

# Start the application
echo ""
echo "=========================================="
echo "✅ Backend Server Ready!"
echo "=========================================="
echo ""
echo "📍 Backend API:  http://localhost:8000"
echo "📚 API Docs:     http://localhost:8000/docs"
echo "📚 ReDoc:        http://localhost:8000/redoc"
echo "🏥 Health Check: http://localhost:8000/api/health"
echo ""
echo "=========================================="
echo "🎯 Starting FastAPI application..."
echo "=========================================="
echo ""

cd /app
exec uvicorn backend.main:app --host 0.0.0.0 --port 8000
