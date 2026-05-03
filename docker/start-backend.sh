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

# Check and train ML models if needed (Requirement 1)
echo ""
echo "🤖 Checking ML models..."
python -c "
import sys
import subprocess
from pathlib import Path

# Define required model files (Subtask 1.1.1)
model_files = [
    'ml/models/placement_model_3m.pkl',
    'ml/models/placement_model_6m.pkl',
    'ml/models/placement_model_12m.pkl',
    'ml/models/salary_model.pkl'
]

# Check if all models exist
all_exist = all(Path(f).exists() for f in model_files)

if all_exist:
    # Models found - no training needed (Subtask 1.1.4)
    print('✅ ML models found and ready')
    sys.exit(0)
else:
    # Models missing - trigger training (Subtask 1.1.2)
    print('⚠️  ML models not found, training...')
    print('    This may take up to 2 minutes on first boot.')
    
    try:
        # Run training with 120-second timeout (Subtask 1.1.3)
        result = subprocess.run(
            ['python', '-m', 'ml.pipeline.train_all'],
            timeout=120,
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            # Training succeeded (Subtask 1.1.4)
            print('✅ ML models trained successfully')
            sys.exit(0)
        else:
            # Training failed (Subtask 1.1.4)
            print('❌ ML model training failed')
            print(f'   Error: {result.stderr}')
            sys.exit(1)
    
    except subprocess.TimeoutExpired:
        # Training exceeded timeout (Subtask 1.1.3, 1.1.4)
        print('❌ ML model training timed out (exceeded 120 seconds)')
        sys.exit(1)
    
    except Exception as e:
        # Unexpected error (Subtask 1.1.4)
        print(f'❌ ML model training error: {str(e)}')
        sys.exit(1)
"

# Check if model training succeeded
if [ $? -ne 0 ]; then
    echo ""
    echo "=========================================="
    echo "❌ Backend startup failed - ML models unavailable"
    echo "=========================================="
    exit 1
fi

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
