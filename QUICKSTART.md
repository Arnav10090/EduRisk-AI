# EduRisk AI - Quick Start Guide

## Prerequisites

- Docker Desktop installed and running
- Git (to clone the repository)
- Groq API key (free at https://console.groq.com)

## Step 1: Environment Setup

Create a `.env` file in the project root:

```bash
# LLM Configuration
LLM_API_KEY=your_groq_api_key_here
LLM_PROVIDER=groq

# Database (defaults work for Docker)
DATABASE_URL=postgresql+asyncpg://edurisk:edurisk_password@postgres:5432/edurisk_db

# Redis (defaults work for Docker)
REDIS_URL=redis://redis:6379/0

# Security
SECRET_KEY=your_secret_key_here_change_in_production

# Optional
DEBUG=True
LOG_LEVEL=INFO
```

## Step 2: Start All Services

```bash
docker-compose up -d --build
```

This will:
- Build and start PostgreSQL database
- Build and start Redis cache
- Build and start FastAPI backend
- Build and start Next.js frontend
- Create all database tables automatically

## Step 3: Verify Services

Check that all containers are running:

```bash
docker ps
```

You should see 4 containers:
- `edurisk-postgres` (database)
- `edurisk-redis` (cache)
- `edurisk-backend` (API)
- `edurisk-frontend` (web UI)

## Step 4: Access the Application

### Frontend (Web UI)
- **URL**: http://127.0.0.1:3000
- **Dashboard**: View portfolio risk overview
- **Add Student**: http://127.0.0.1:3000/student/new

### Backend (API)
- **API Base**: http://127.0.0.1:8000
- **API Docs**: http://127.0.0.1:8000/docs
- **Health Check**: http://127.0.0.1:8000/api/health

## Step 5: Add Your First Student

### Option A: Using the Web UI

1. Go to http://127.0.0.1:3000/student/new
2. Fill in the student details:
   - Name: John Doe
   - Course Type: Engineering
   - Institute Tier: 1 (Tier 1 = Top institutes)
   - CGPA: 8.5
   - Year of Graduation: 2024
3. Click "Submit"
4. View the generated risk assessment

### Option B: Using the API

```bash
curl -X POST http://127.0.0.1:8000/api/students \
  -H "Content-Type: application/json" \
  -d '{
    "name": "John Doe",
    "course_type": "Engineering",
    "institute_tier": 1,
    "cgpa": 8.5,
    "year_of_grad": 2024,
    "internship_count": 2,
    "internship_months": 6,
    "certifications": 3
  }'
```

## Step 6: View the Dashboard

Go to http://127.0.0.1:3000 to see:
- **Risk Score Cards**: Aggregate statistics (high/medium/low risk)
- **Portfolio Heatmap**: Visual representation of risk distribution
- **Student Table**: Sortable list of all students with risk scores
- **Alert Banner**: High-risk student notifications

## Common Commands

### View Logs
```bash
# Backend logs
docker logs edurisk-backend

# Frontend logs
docker logs edurisk-frontend

# Database logs
docker logs edurisk-postgres

# Follow logs in real-time
docker logs -f edurisk-backend
```

### Restart Services
```bash
# Restart all services
docker-compose restart

# Restart specific service
docker-compose restart backend
```

### Stop Services
```bash
# Stop all services
docker-compose down

# Stop and remove volumes (WARNING: deletes all data)
docker-compose down -v
```

### Rebuild After Code Changes
```bash
# Rebuild and restart all services
docker-compose up -d --build

# Rebuild specific service
docker-compose up -d --build backend
```

## Troubleshooting

### Frontend shows "Loading dashboard..."

1. Check if backend is running:
   ```bash
   curl http://127.0.0.1:8000/api/health
   ```

2. Check backend logs:
   ```bash
   docker logs edurisk-backend --tail 50
   ```

3. Verify database tables exist:
   ```bash
   docker exec edurisk-backend python /app/init-db.py
   ```

### Backend shows database errors

1. Check if PostgreSQL is running:
   ```bash
   docker ps | grep postgres
   ```

2. Verify database connection:
   ```bash
   docker exec edurisk-postgres psql -U edurisk -d edurisk_db -c "\dt"
   ```

3. Recreate database tables:
   ```bash
   docker exec edurisk-backend python /app/init-db.py
   ```

### Port already in use

If you see "port already allocated" errors:

1. Check what's using the port:
   ```bash
   # Windows
   netstat -ano | findstr :8000
   netstat -ano | findstr :3000
   ```

2. Stop the conflicting service or change ports in `docker-compose.yml`

### API returns 500 errors

1. Check if you have a valid Groq API key in `.env`
2. Verify ML models are available:
   ```bash
   docker exec edurisk-backend ls -la /app/ml/models
   ```

## Next Steps

1. **Train ML Models**: Follow `ml/README.md` to train placement prediction models
2. **Import Sample Data**: Use the bulk import API to add multiple students
3. **Configure Alerts**: Set up email/SMS notifications for high-risk students
4. **Customize Risk Thresholds**: Adjust risk scoring in `backend/services/risk_calculator.py`

## Support

- **Documentation**: See `API_DOCUMENTATION.md` for full API reference
- **Docker Issues**: See `DOCKER_FINAL_FIX_SUMMARY.md`
- **Environment Variables**: See `ENVIRONMENT_VARIABLES.md`

## Important Notes

### Windows Users
- Always use `127.0.0.1` instead of `localhost` when accessing services
- This is a Windows Docker Desktop networking requirement

### Production Deployment
- Change `SECRET_KEY` to a strong random value
- Set `DEBUG=False`
- Use a production-grade database (not Docker volume)
- Enable HTTPS/TLS
- Set up proper authentication
- Configure rate limiting
- See `DEPLOYMENT_GUIDE.md` for details
