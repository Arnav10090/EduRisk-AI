#!/bin/bash

# EduRisk AI - Setup Script
# This script sets up the development environment

set -e

echo "=========================================="
echo "EduRisk AI - Development Setup"
echo "=========================================="
echo ""

# Check prerequisites
echo "Checking prerequisites..."

if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is not installed"
    exit 1
fi

if ! command -v node &> /dev/null; then
    echo "Error: Node.js is not installed"
    exit 1
fi

if ! command -v docker &> /dev/null; then
    echo "Warning: Docker is not installed (optional for containerized setup)"
fi

echo "✓ Prerequisites check passed"
echo ""

# Setup Python virtual environment
echo "Setting up Python virtual environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "✓ Virtual environment created"
else
    echo "✓ Virtual environment already exists"
fi

# Activate virtual environment
source venv/bin/activate

# Install Python dependencies
echo ""
echo "Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt
echo "✓ Python dependencies installed"

# Setup backend environment
echo ""
echo "Setting up backend environment..."
if [ ! -f "backend/.env" ]; then
    cp backend/.env.example backend/.env
    echo "✓ Created backend/.env from template"
    echo "⚠ Please edit backend/.env and add your ANTHROPIC_API_KEY"
else
    echo "✓ backend/.env already exists"
fi

# Setup frontend
echo ""
echo "Setting up frontend..."
cd frontend

if [ ! -d "node_modules" ]; then
    echo "Installing frontend dependencies..."
    npm install
    echo "✓ Frontend dependencies installed"
else
    echo "✓ Frontend dependencies already installed"
fi

if [ ! -f ".env" ]; then
    cp .env.example .env
    echo "✓ Created frontend/.env from template"
else
    echo "✓ frontend/.env already exists"
fi

cd ..

# Create necessary directories
echo ""
echo "Creating necessary directories..."
mkdir -p ml/models
mkdir -p ml/data/synthetic
mkdir -p ml/data/raw
mkdir -p backend/logs
echo "✓ Directories created"

echo ""
echo "=========================================="
echo "Setup Complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Edit backend/.env and add your ANTHROPIC_API_KEY"
echo "2. Start services:"
echo "   - Option A (Docker): docker-compose up -d"
echo "   - Option B (Local):"
echo "     - Start PostgreSQL and Redis"
echo "     - Run: uvicorn backend.main:app --reload"
echo "     - Run: cd frontend && npm run dev"
echo "3. Train ML models: python ml/pipeline/train.py"
echo "4. Access the application:"
echo "   - Frontend: http://localhost:3000"
echo "   - Backend API: http://localhost:8000/docs"
echo ""
