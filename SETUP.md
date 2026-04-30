# EduRisk AI - Setup Guide

This guide provides detailed instructions for setting up the EduRisk AI development environment.

## Quick Start

### Using Docker (Recommended)

```bash
# 1. Configure environment
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env
# Edit backend/.env and add your ANTHROPIC_API_KEY

# 2. Start all services
docker-compose up -d

# 3. Run database migrations (once services are up)
docker-compose exec backend alembic upgrade head

# 4. Access the application
# Frontend: http://localhost:3000
# Backend: http://localhost:8000/docs
```

### Using Local Development

```bash
# 1. Run setup script
chmod +x setup.sh
./setup.sh

# 2. Start PostgreSQL and Redis
docker run -d -p 5432:5432 -e POSTGRES_USER=edurisk -e POSTGRES_PASSWORD=edurisk_password -e POSTGRES_DB=edurisk_db postgres:16-alpine
docker run -d -p 6379:6379 redis:7-alpine

# 3. Start backend (in terminal 1)
source venv/bin/activate
uvicorn backend.main:app --reload

# 4. Start frontend (in terminal 2)
cd frontend
npm run dev
```

## Detailed Setup Instructions

### 1. Prerequisites

#### Required Software
- **Python 3.11+**: [Download](https://www.python.org/downloads/)
- **Node.js 20+**: [Download](https://nodejs.org/)
- **Git**: [Download](https://git-scm.com/)

#### Optional (for Docker setup)
- **Docker Desktop**: [Download](https://www.docker.com/products/docker-desktop/)
- **Docker Compose**: Included with Docker Desktop

#### For Local Development
- **PostgreSQL 16**: [Download](https://www.postgresql.org/download/)
- **Redis 7**: [Download](https://redis.io/download/)

### 2. Clone Repository

```bash
git clone <repository-url>
cd edurisk-ai
```

### 3. Backend Setup

#### Create Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

#### Install Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

#### Configure Environment

```bash
cp backend/.env.example backend/.env
```

Edit `backend/.env` and configure:

```env
# Required
DATABASE_URL=postgresql+asyncpg://edurisk:edurisk_password@localhost:5432/edurisk_db
REDIS_URL=redis://localhost:6379/0
ANTHROPIC_API_KEY=your_actual_api_key_here

# Optional (defaults provided)
ML_MODEL_PATH=../ml/models
SECRET_KEY=your_secret_key_here
CORS_ORIGINS=http://localhost:3000
```

#### Setup Database

If using Docker for PostgreSQL:

```bash
docker run -d \
  --name edurisk-postgres \
  -p 5432:5432 \
  -e POSTGRES_USER=edurisk \
  -e POSTGRES_PASSWORD=edurisk_password \
  -e POSTGRES_DB=edurisk_db \
  postgres:16-alpine
```

If using local PostgreSQL:

```bash
createdb edurisk_db
```

#### Run Migrations

```bash
cd backend
alembic upgrade head
cd ..
```

#### Start Backend Server

```bash
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

Verify at: http://localhost:8000/docs

### 4. Frontend Setup

#### Install Dependencies

```bash
cd frontend
npm install
```

#### Configure Environment

```bash
cp .env.example .env
```

Edit `frontend/.env` if needed:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

#### Start Development Server

```bash
npm run dev
```

Verify at: http://localhost:3000

### 5. ML Model Setup

#### Create Directories

```bash
mkdir -p ml/models
mkdir -p ml/data/synthetic
mkdir -p ml/data/raw
```

#### Generate Training Data

```bash
python ml/data/generate_synthetic.py
```

#### Train Models

```bash
# Train placement models (3m, 6m, 12m)
python ml/pipeline/train.py

# Train salary model
python ml/pipeline/salary_model.py
```

Models will be saved to `ml/models/`:
- `placement_model_3m.pkl`
- `placement_model_6m.pkl`
- `placement_model_12m.pkl`
- `salary_model.pkl`
- `feature_names.json`
- `version.json`

### 6. Verify Installation

#### Check Backend Health

```bash
curl http://localhost:8000/api/health
```

Expected response:
```json
{
  "status": "ok",
  "version": "1.0.0"
}
```

#### Check Frontend

Open http://localhost:3000 in your browser. You should see the EduRisk AI landing page.

## Troubleshooting

### Backend Issues

**Issue**: `ModuleNotFoundError: No module named 'fastapi'`
**Solution**: Ensure virtual environment is activated and dependencies are installed:
```bash
source venv/bin/activate
pip install -r requirements.txt
```

**Issue**: Database connection error
**Solution**: Verify PostgreSQL is running and credentials in `.env` are correct:
```bash
docker ps  # Check if postgres container is running
psql -U edurisk -d edurisk_db  # Test connection
```

**Issue**: Redis connection error
**Solution**: Verify Redis is running:
```bash
docker ps  # Check if redis container is running
redis-cli ping  # Should return PONG
```

### Frontend Issues

**Issue**: `Module not found` errors
**Solution**: Delete `node_modules` and reinstall:
```bash
cd frontend
rm -rf node_modules package-lock.json
npm install
```

**Issue**: API connection errors
**Solution**: Verify backend is running and `NEXT_PUBLIC_API_URL` is correct in `frontend/.env`

### Docker Issues

**Issue**: Port already in use
**Solution**: Stop conflicting services or change ports in `docker-compose.yml`

**Issue**: Container fails to start
**Solution**: Check logs:
```bash
docker-compose logs backend
docker-compose logs frontend
```

## Development Workflow

### Running Tests

```bash
# Backend tests
pytest backend/tests/ -v --cov=backend

# Frontend tests
cd frontend
npm run test
```

### Code Quality

```bash
# Python linting
flake8 backend/ ml/
black backend/ ml/

# TypeScript type checking
cd frontend
npm run type-check
```

### Database Migrations

```bash
# Create new migration
cd backend
alembic revision --autogenerate -m "Description"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```

## Next Steps

1. **Train ML Models**: Follow ML Model Setup section
2. **Explore API**: Visit http://localhost:8000/docs
3. **Build Features**: Start implementing tasks from `tasks.md`
4. **Run Tests**: Ensure all tests pass before committing

## Support

For issues or questions:
1. Check this guide and README.md
2. Review error logs
3. Contact the development team
