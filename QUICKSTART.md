# EduRisk AI - Quick Start Guide

Get up and running with EduRisk AI in 5 minutes.

## Prerequisites

- Docker Desktop installed and running
- Git installed
- Text editor (VS Code recommended)

## Setup (5 minutes)

### 1. Clone and Configure (2 minutes)

```bash
# Clone repository
git clone <repository-url>
cd edurisk-ai

# Configure backend
cp backend/.env.example backend/.env
# Edit backend/.env and add your ANTHROPIC_API_KEY

# Configure frontend
cp frontend/.env.example frontend/.env
```

### 2. Start Services (2 minutes)

```bash
# Start all services with Docker
docker-compose up -d

# Wait for services to be healthy (check with)
docker-compose ps
```

### 3. Verify Installation (1 minute)

```bash
# Check backend health
curl http://localhost:8000/api/health

# Open frontend in browser
open http://localhost:3000

# View API documentation
open http://localhost:8000/docs
```

## What's Running?

After `docker-compose up -d`, you have:

- **PostgreSQL 16** on port 5432 - Database
- **Redis 7** on port 6379 - Caching and rate limiting
- **FastAPI Backend** on port 8000 - API server
- **Next.js Frontend** on port 3000 - Web interface

## Next Steps

### 1. Train ML Models

Before making predictions, train the models:

```bash
# Enter backend container
docker-compose exec backend bash

# Generate synthetic training data
python ml/data/generate_synthetic.py

# Train placement models
python ml/pipeline/train.py

# Train salary model
python ml/pipeline/salary_model.py

# Exit container
exit
```

### 2. Explore the API

Visit http://localhost:8000/docs to see interactive API documentation.

Try the health check endpoint:
```bash
curl http://localhost:8000/api/health
```

### 3. Start Development

The project is now ready for feature development. See `tasks.md` for the implementation plan.

## Common Commands

```bash
# View logs
docker-compose logs -f backend
docker-compose logs -f frontend

# Restart a service
docker-compose restart backend

# Stop all services
docker-compose down

# Stop and remove volumes (clean slate)
docker-compose down -v

# Run backend tests
docker-compose exec backend pytest

# Access database
docker-compose exec postgres psql -U edurisk -d edurisk_db

# Access Redis CLI
docker-compose exec redis redis-cli
```

## Troubleshooting

### Services won't start
```bash
# Check if ports are already in use
lsof -i :3000  # Frontend
lsof -i :8000  # Backend
lsof -i :5432  # PostgreSQL
lsof -i :6379  # Redis

# Stop conflicting services or change ports in docker-compose.yml
```

### Backend errors
```bash
# Check logs
docker-compose logs backend

# Restart backend
docker-compose restart backend
```

### Frontend errors
```bash
# Check logs
docker-compose logs frontend

# Rebuild frontend
docker-compose up -d --build frontend
```

### Database connection issues
```bash
# Verify PostgreSQL is running
docker-compose ps postgres

# Check database logs
docker-compose logs postgres

# Restart database
docker-compose restart postgres
```

## Development Workflow

### Making Code Changes

**Backend changes:**
- Edit files in `backend/` or `ml/`
- Changes auto-reload (FastAPI --reload mode)
- No restart needed

**Frontend changes:**
- Edit files in `frontend/`
- Changes auto-reload (Next.js dev mode)
- No restart needed

### Running Tests

```bash
# Backend tests
docker-compose exec backend pytest -v

# Frontend tests
docker-compose exec frontend npm test
```

### Database Migrations

```bash
# Create migration
docker-compose exec backend alembic revision --autogenerate -m "Description"

# Apply migrations
docker-compose exec backend alembic upgrade head

# Rollback
docker-compose exec backend alembic downgrade -1
```

## Project Structure

```
edurisk-ai/
├── ml/                    # ML Pipeline (Python)
├── backend/               # API Backend (FastAPI)
├── frontend/              # Web UI (Next.js)
├── docker/                # Docker configs
├── docker-compose.yml     # Service orchestration
└── requirements.txt       # Python dependencies
```

## Key URLs

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **API Redoc**: http://localhost:8000/redoc

## Getting Help

1. Check `README.md` for detailed documentation
2. Check `SETUP.md` for detailed setup instructions
3. Check `PROJECT_STATUS.md` for current implementation status
4. Review error logs: `docker-compose logs <service>`

## Clean Slate

To start fresh:

```bash
# Stop and remove everything
docker-compose down -v

# Remove Python cache
find . -type d -name __pycache__ -exec rm -rf {} +
find . -type f -name "*.pyc" -delete

# Remove frontend build
rm -rf frontend/.next frontend/node_modules

# Start again
docker-compose up -d
```

---

**Ready to build!** 🚀

For detailed documentation, see:
- `README.md` - Full project documentation
- `SETUP.md` - Detailed setup guide
- `tasks.md` - Implementation task list
