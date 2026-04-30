# EduRisk AI - Docker Quick Start Guide

Get EduRisk AI running in 5 minutes with Docker.

## Prerequisites

- Docker and Docker Compose installed
- 4GB RAM and 10GB disk space available
- ML models trained (or run training script)

## Quick Start (5 Steps)

### 1. Create Environment File
```bash
cp .env.example .env
```

Edit `.env` and set:
- `ANTHROPIC_API_KEY=your_api_key_here`
- `SECRET_KEY=your_secret_key_here`

### 2. Train ML Models (if not already trained)
```bash
python ml/pipeline/train_all.py
```

This creates model files in `ml/models/` directory.

### 3. Start All Services
```bash
docker-compose up -d
```

This starts:
- PostgreSQL database (port 5432)
- Redis cache (port 6379)
- Backend API (port 8000)
- Frontend UI (port 3000)

### 4. Wait for Services (30-60 seconds)
```bash
docker-compose ps
```

Wait until all services show "healthy" or "running" status.

### 5. Access the Application

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

## Verify Installation

### Check Backend Health
```bash
curl http://localhost:8000/api/health
```

Expected response:
```json
{
  "status": "ok",
  "database": "connected",
  "ml_models": "loaded",
  "timestamp": "2024-01-01T00:00:00Z"
}
```

### Test Prediction API
```bash
curl -X POST http://localhost:8000/api/predict \
  -H "Content-Type: application/json" \
  -d '{
    "name": "John Doe",
    "course_type": "BTech",
    "institute_tier": 1,
    "institute_name": "IIT Delhi",
    "cgpa": 8.5,
    "cgpa_scale": 10.0,
    "year_of_grad": 2024,
    "internship_count": 2,
    "internship_months": 6,
    "internship_employer_type": "MNC",
    "certifications": 3,
    "region": "North",
    "loan_amount": 500000,
    "loan_emi": 15000
  }'
```

### Access Frontend
Open browser: http://localhost:3000

You should see the EduRisk AI dashboard.

## Common Commands

### View Logs
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend
```

### Stop Services
```bash
docker-compose down
```

### Restart Services
```bash
docker-compose restart
```

### Rebuild After Code Changes
```bash
docker-compose build
docker-compose up -d
```

## Development Mode

For hot-reload during development:

```bash
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up
```

This enables:
- Automatic backend reload on Python file changes
- Automatic frontend reload on TypeScript/React changes
- Debug logging

## Troubleshooting

### Services won't start
1. Check if ports are available:
   ```bash
   # Windows
   netstat -ano | findstr "3000 5432 6379 8000"
   
   # Linux/Mac
   lsof -i :3000,5432,6379,8000
   ```

2. Check logs:
   ```bash
   docker-compose logs
   ```

### Backend can't connect to database
```bash
# Check postgres is running
docker-compose ps postgres

# Restart backend
docker-compose restart backend
```

### ML models not found
```bash
# Verify models exist
ls -la ml/models/

# Train models if missing
python ml/pipeline/train_all.py

# Rebuild backend
docker-compose build backend
docker-compose up -d backend
```

### Frontend can't reach backend
1. Verify backend is running:
   ```bash
   curl http://localhost:8000/api/health
   ```

2. Check CORS configuration in backend logs

3. Restart frontend:
   ```bash
   docker-compose restart frontend
   ```

## What's Running?

| Service | Port | Purpose |
|---------|------|---------|
| Frontend | 3000 | Next.js web interface |
| Backend | 8000 | FastAPI REST API |
| Postgres | 5432 | Database |
| Redis | 6379 | Cache & rate limiting |

## Next Steps

1. **Explore the API**: http://localhost:8000/docs
2. **Create a prediction**: Use the frontend form at http://localhost:3000/student/new
3. **View dashboard**: See portfolio overview at http://localhost:3000/dashboard
4. **Check alerts**: View high-risk students at http://localhost:3000/alerts

## Production Deployment

For production, see:
- `DOCKER_README.md` - Comprehensive deployment guide
- `DOCKER_DEPLOYMENT_CHECKLIST.md` - Pre-deployment checklist

Key production changes:
- Set `DEBUG=False`
- Use strong `SECRET_KEY`
- Configure proper `CORS_ORIGINS`
- Use external database and Redis
- Enable HTTPS with reverse proxy
- Set up monitoring and backups

## Getting Help

1. Check logs: `docker-compose logs -f`
2. Review `DOCKER_README.md` for detailed documentation
3. Check `DOCKER_DEPLOYMENT_CHECKLIST.md` for troubleshooting
4. Verify environment variables in `.env`

## Clean Up

To stop and remove everything:

```bash
# Stop services
docker-compose down

# Remove volumes (⚠️ deletes all data)
docker-compose down -v

# Remove images
docker-compose down --rmi all
```

---

**That's it!** You now have EduRisk AI running in Docker. 🚀

For more details, see:
- `DOCKER_README.md` - Full documentation
- `DOCKER_DEPLOYMENT_CHECKLIST.md` - Deployment checklist
- `TASK_24_IMPLEMENTATION_SUMMARY.md` - Implementation details
