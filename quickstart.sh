#!/bin/bash
# EduRisk AI - Quick Start Script
# This script helps you get started with EduRisk AI quickly

set -e

# Color codes
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║         EduRisk AI - Quick Start Setup                    ║${NC}"
echo -e "${BLUE}║    Placement Risk Intelligence for Education Lenders      ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Check prerequisites
echo -e "${BLUE}[1/6] Checking prerequisites...${NC}"

# Check Docker
if ! command -v docker &> /dev/null; then
    echo -e "${RED}✗ Docker is not installed${NC}"
    echo "Please install Docker from https://docs.docker.com/get-docker/"
    exit 1
fi
echo -e "${GREEN}✓ Docker is installed ($(docker --version))${NC}"

# Check Docker Compose
if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}✗ Docker Compose is not installed${NC}"
    echo "Please install Docker Compose from https://docs.docker.com/compose/install/"
    exit 1
fi
echo -e "${GREEN}✓ Docker Compose is installed ($(docker-compose --version))${NC}"

# Check if Docker daemon is running
if ! docker info &> /dev/null; then
    echo -e "${RED}✗ Docker daemon is not running${NC}"
    echo "Please start Docker and try again"
    exit 1
fi
echo -e "${GREEN}✓ Docker daemon is running${NC}"

echo ""

# Setup environment file
echo -e "${BLUE}[2/6] Setting up environment configuration...${NC}"

if [ -f ".env" ]; then
    echo -e "${YELLOW}⚠ .env file already exists${NC}"
    read -p "Do you want to overwrite it? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${BLUE}ℹ Using existing .env file${NC}"
    else
        cp .env.example .env
        echo -e "${GREEN}✓ Created .env file from template${NC}"
    fi
else
    cp .env.example .env
    echo -e "${GREEN}✓ Created .env file from template${NC}"
fi

# Prompt for Anthropic API key
echo ""
echo -e "${YELLOW}⚠ Anthropic API Key Required${NC}"
echo "EduRisk AI uses Claude AI for generating risk summaries."
echo "You need an Anthropic API key to use this feature."
echo ""
echo "Get your API key from: https://console.anthropic.com/"
echo ""
read -p "Enter your Anthropic API key (or press Enter to skip): " api_key

if [ -n "$api_key" ]; then
    # Update .env file with API key
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        sed -i '' "s/ANTHROPIC_API_KEY=.*/ANTHROPIC_API_KEY=$api_key/" .env
    else
        # Linux
        sed -i "s/ANTHROPIC_API_KEY=.*/ANTHROPIC_API_KEY=$api_key/" .env
    fi
    echo -e "${GREEN}✓ API key configured${NC}"
else
    echo -e "${YELLOW}⚠ Skipped API key configuration${NC}"
    echo -e "${YELLOW}  AI summaries will not be available${NC}"
    echo -e "${YELLOW}  You can add it later in the .env file${NC}"
fi

# Generate secret key
echo ""
echo -e "${BLUE}Generating secure SECRET_KEY...${NC}"
if command -v python3 &> /dev/null; then
    secret_key=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")
    if [[ "$OSTYPE" == "darwin"* ]]; then
        sed -i '' "s/SECRET_KEY=.*/SECRET_KEY=$secret_key/" .env
    else
        sed -i "s/SECRET_KEY=.*/SECRET_KEY=$secret_key/" .env
    fi
    echo -e "${GREEN}✓ Generated secure SECRET_KEY${NC}"
else
    echo -e "${YELLOW}⚠ Python not found, using default SECRET_KEY${NC}"
    echo -e "${YELLOW}  Please change it in production!${NC}"
fi

echo ""

# Check ML models
echo -e "${BLUE}[3/6] Checking ML models...${NC}"

if [ -f "ml/models/placement_model_3m.pkl" ] && \
   [ -f "ml/models/placement_model_6m.pkl" ] && \
   [ -f "ml/models/placement_model_12m.pkl" ] && \
   [ -f "ml/models/salary_model.pkl" ]; then
    echo -e "${GREEN}✓ ML models found${NC}"
else
    echo -e "${YELLOW}⚠ ML models not found${NC}"
    echo -e "${BLUE}ℹ Models will be trained on first startup${NC}"
    echo -e "${BLUE}  This may take a few minutes...${NC}"
fi

echo ""

# Validate setup
echo -e "${BLUE}[4/6] Validating setup...${NC}"

if [ -f "docker/validate-setup.sh" ]; then
    chmod +x docker/validate-setup.sh
    if ./docker/validate-setup.sh; then
        echo -e "${GREEN}✓ Setup validation passed${NC}"
    else
        echo -e "${RED}✗ Setup validation failed${NC}"
        echo "Please fix the errors above and try again"
        exit 1
    fi
else
    echo -e "${YELLOW}⚠ Validation script not found, skipping...${NC}"
fi

echo ""

# Start services
echo -e "${BLUE}[5/6] Starting services...${NC}"
echo "This may take a few minutes on first run..."
echo ""

docker-compose up -d

echo ""
echo -e "${BLUE}Waiting for services to be ready...${NC}"

# Wait for backend to be ready
max_attempts=30
attempt=0
while [ $attempt -lt $max_attempts ]; do
    if curl -s http://localhost:8000/api/health > /dev/null 2>&1; then
        echo -e "${GREEN}✓ Backend is ready${NC}"
        break
    fi
    attempt=$((attempt + 1))
    echo -e "${YELLOW}⏳ Waiting for backend... (attempt $attempt/$max_attempts)${NC}"
    sleep 2
done

if [ $attempt -eq $max_attempts ]; then
    echo -e "${RED}✗ Backend failed to start${NC}"
    echo "Check logs with: docker-compose logs backend"
    exit 1
fi

# Wait for frontend to be ready
attempt=0
while [ $attempt -lt $max_attempts ]; do
    if curl -s http://localhost:3000 > /dev/null 2>&1; then
        echo -e "${GREEN}✓ Frontend is ready${NC}"
        break
    fi
    attempt=$((attempt + 1))
    echo -e "${YELLOW}⏳ Waiting for frontend... (attempt $attempt/$max_attempts)${NC}"
    sleep 2
done

if [ $attempt -eq $max_attempts ]; then
    echo -e "${YELLOW}⚠ Frontend may still be starting${NC}"
    echo "Check logs with: docker-compose logs frontend"
fi

echo ""

# Verify deployment
echo -e "${BLUE}[6/6] Verifying deployment...${NC}"

health_response=$(curl -s http://localhost:8000/api/health)
if echo "$health_response" | grep -q '"status":"ok"'; then
    echo -e "${GREEN}✓ Health check passed${NC}"
    echo -e "${BLUE}ℹ System status:${NC}"
    echo "$health_response" | python3 -m json.tool 2>/dev/null || echo "$health_response"
else
    echo -e "${YELLOW}⚠ Health check returned unexpected response${NC}"
    echo "$health_response"
fi

echo ""

# Success message
echo -e "${GREEN}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║              🎉 Setup Complete! 🎉                         ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${BLUE}Access the application:${NC}"
echo -e "  • Frontend:  ${GREEN}http://localhost:3000${NC}"
echo -e "  • Backend:   ${GREEN}http://localhost:8000${NC}"
echo -e "  • API Docs:  ${GREEN}http://localhost:8000/docs${NC}"
echo ""
echo -e "${BLUE}Useful commands:${NC}"
echo -e "  • View logs:        ${YELLOW}docker-compose logs -f${NC}"
echo -e "  • Stop services:    ${YELLOW}docker-compose down${NC}"
echo -e "  • Restart services: ${YELLOW}docker-compose restart${NC}"
echo -e "  • Run tests:        ${YELLOW}python test_integration.py${NC}"
echo ""
echo -e "${BLUE}Documentation:${NC}"
echo -e "  • README.md                - Getting started guide"
echo -e "  • API_DOCUMENTATION.md     - Complete API reference"
echo -e "  • DEPLOYMENT_GUIDE.md      - Production deployment"
echo -e "  • ENVIRONMENT_VARIABLES.md - Configuration reference"
echo ""
echo -e "${GREEN}Happy predicting! 🚀${NC}"
echo ""
