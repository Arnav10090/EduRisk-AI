#!/bin/bash
# Validation script for Docker setup
# This script checks if all required files and configurations are in place

set -e

echo "🔍 Validating EduRisk AI Docker Setup..."
echo ""

# Color codes
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check function
check_file() {
    if [ -f "$1" ]; then
        echo -e "${GREEN}✓${NC} $1 exists"
        return 0
    else
        echo -e "${RED}✗${NC} $1 is missing"
        return 1
    fi
}

check_dir() {
    if [ -d "$1" ]; then
        echo -e "${GREEN}✓${NC} $1 exists"
        return 0
    else
        echo -e "${RED}✗${NC} $1 is missing"
        return 1
    fi
}

# Track errors
ERRORS=0

echo "📁 Checking Docker files..."
check_file "docker/Dockerfile.backend" || ((ERRORS++))
check_file "docker/Dockerfile.frontend" || ((ERRORS++))
check_file "docker/Dockerfile.postgres" || ((ERRORS++))
check_file "docker/Dockerfile.frontend.dev" || ((ERRORS++))
check_file "docker-compose.yml" || ((ERRORS++))
check_file "docker-compose.dev.yml" || ((ERRORS++))
echo ""

echo "📁 Checking support scripts..."
check_file "docker/wait-for-db.py" || ((ERRORS++))
check_file "docker/start-backend.sh" || ((ERRORS++))
echo ""

echo "📁 Checking configuration files..."
check_file ".env.example" || ((ERRORS++))
check_file ".dockerignore" || ((ERRORS++))
check_file "backend/.env.example" || ((ERRORS++))
check_file "frontend/.env.example" || ((ERRORS++))
echo ""

echo "📁 Checking application files..."
check_file "requirements.txt" || ((ERRORS++))
check_file "backend/main.py" || ((ERRORS++))
check_file "frontend/package.json" || ((ERRORS++))
check_file "frontend/next.config.js" || ((ERRORS++))
echo ""

echo "📁 Checking ML models directory..."
check_dir "ml/models" || ((ERRORS++))
if [ -d "ml/models" ]; then
    echo "   Checking for model files..."
    check_file "ml/models/placement_model_3m.pkl" || echo -e "   ${YELLOW}⚠${NC} ml/models/placement_model_3m.pkl not found (run training first)"
    check_file "ml/models/placement_model_6m.pkl" || echo -e "   ${YELLOW}⚠${NC} ml/models/placement_model_6m.pkl not found (run training first)"
    check_file "ml/models/placement_model_12m.pkl" || echo -e "   ${YELLOW}⚠${NC} ml/models/placement_model_12m.pkl not found (run training first)"
    check_file "ml/models/salary_model.pkl" || echo -e "   ${YELLOW}⚠${NC} ml/models/salary_model.pkl not found (run training first)"
    check_file "ml/models/version.json" || echo -e "   ${YELLOW}⚠${NC} ml/models/version.json not found (run training first)"
fi
echo ""

echo "🔧 Checking Docker installation..."
if command -v docker &> /dev/null; then
    echo -e "${GREEN}✓${NC} Docker is installed ($(docker --version))"
else
    echo -e "${RED}✗${NC} Docker is not installed"
    ((ERRORS++))
fi

if command -v docker-compose &> /dev/null; then
    echo -e "${GREEN}✓${NC} Docker Compose is installed ($(docker-compose --version))"
else
    echo -e "${RED}✗${NC} Docker Compose is not installed"
    ((ERRORS++))
fi
echo ""

echo "📋 Checking environment file..."
if [ -f ".env" ]; then
    echo -e "${GREEN}✓${NC} .env file exists"
    
    # Check for required variables
    if grep -q "ANTHROPIC_API_KEY=" .env; then
        if grep -q "ANTHROPIC_API_KEY=your_anthropic_api_key_here" .env; then
            echo -e "   ${YELLOW}⚠${NC} ANTHROPIC_API_KEY needs to be set"
        else
            echo -e "   ${GREEN}✓${NC} ANTHROPIC_API_KEY is configured"
        fi
    else
        echo -e "   ${YELLOW}⚠${NC} ANTHROPIC_API_KEY not found in .env"
    fi
    
    if grep -q "SECRET_KEY=" .env; then
        if grep -q "SECRET_KEY=your_secret_key_here" .env; then
            echo -e "   ${YELLOW}⚠${NC} SECRET_KEY needs to be set"
        else
            echo -e "   ${GREEN}✓${NC} SECRET_KEY is configured"
        fi
    else
        echo -e "   ${YELLOW}⚠${NC} SECRET_KEY not found in .env"
    fi
else
    echo -e "${YELLOW}⚠${NC} .env file not found (copy from .env.example)"
fi
echo ""

# Summary
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
if [ $ERRORS -eq 0 ]; then
    echo -e "${GREEN}✓ All checks passed!${NC}"
    echo ""
    echo "You can now start the application with:"
    echo "  docker-compose up -d"
    echo ""
    echo "Or for development mode:"
    echo "  docker-compose -f docker-compose.yml -f docker-compose.dev.yml up"
    exit 0
else
    echo -e "${RED}✗ Found $ERRORS error(s)${NC}"
    echo ""
    echo "Please fix the errors above before starting the application."
    exit 1
fi
