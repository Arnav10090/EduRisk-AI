# EduRisk AI - Docker Deployment Checklist

Use this checklist to ensure your Docker deployment is ready.

## Pre-Deployment Checklist

### ✅ 1. Prerequisites Installed
- [ ] Docker Engine 20.10+ installed
- [ ] Docker Compose 2.0+ installed
- [ ] At least 4GB RAM available
- [ ] At least 10GB disk space available

**Verify:**
```bash
docker --version
docker-compose --version
```

### ✅ 2. ML Models Trained
- [ ] `ml/models/placement_model_3m.pkl` exists
- [ ] `ml/models/placement_model_6m.pkl` exists
- [ ] `ml/models/placement_model_12m.pkl` exists
- [ ] `ml/models/salary_model.pkl` exists
- [ ] `ml/models/version.json` exists
- [ ] `ml/models/feature_names.json` exists

**Train if missing:**
```bash
python ml/pipeline/train_all.py
```

### ✅ 3. Environment Configuration
- [ ] `.env` file created (copy from `.env.example`)
- [ ] `ANTHROPIC_API_KEY` set in `.env`
- [ ] `SECRET_KEY` set in `.env` (use strong random string)
- [ ] Other environment variables reviewed

**Create .env:**
```bash
cp .env.example .env
# Edit .env with your values
```

### ✅ 4. Port Availability
- [ ] Port 3000 available (frontend)
- [ ] Port 5432 available (postgres)
- [ ] Port 6379 available (redis)
- [ ] Port 8000 available (backend)

**Check ports:**
```bash
# Windows
netstat -ano | findstr "3000 5432 6379 8000"

# Linux/Mac
lsof -i :3000,5432,6379,8000
```

### ✅ 5. Docker Files Present
- [ ] `docker/Dockerfile.backend`
- [ ] `docker/Dockerfile.frontend`
- [ ] `docker/Dockerfile.postgres`
- [ ] `docker/wait-for-db.py`
- [ ] `docker/start-backend.sh`
- [ ] `docker-compose.yml`

**Validate:**
```bash
bash docker/validate-setup.sh
```

## Deployment Steps

### Step 1: Build Images
```bash
docker-compose build
```

**Expected:** All images build successfully without errors.

### Step 2: Start Services
```bash
docker-compose up -d
```

**Expected:** All services start in detached mode.

### Step 3: Monitor Startup
```bash
docker-compose ps
```

**Expected:** All services show "healthy" or "running" status within 60 seconds.

### Step 4: Check Logs
```bash
docker-compose logs -f
```

**Expected:** 
- Postgres: "database system is ready to accept connections"
- Redis: "Ready to accept connections"
- Backend: "Application startup complete"
- Frontend: "ready started server on 0.0.0.0:3000"

### Step 5: Verify Health Checks
```bash
# Backend health
curl http://localhost:8000/api/health

# Frontend
curl http://localhost:3000
```

**Expected:**
- Backend: `{"status": "ok", "database": "connected", "ml_models": "loaded"}`
- Frontend: HTML response

### Step 6: Test API
```bash
# API documentation
curl http://localhost:8000/docs

# Test prediction endpoint
curl -X POST http://localhost:8000/api/predict \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test Student",
    "course_type": "BTech",
    "institute_tier": 1,
    "institute_name": "Test Institute",
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

**Expected:** JSON response with prediction results.

### Step 7: Access Frontend
Open browser: http://localhost:3000

**Expected:** Dashboard page loads successfully.

## Post-Deployment Verification

### ✅ Database
- [ ] Database migrations completed
- [ ] Tables created (students, predictions, audit_logs)
- [ ] Database accessible from backend

**Verify:**
```bash
docker-compose exec backend alembic current
docker-compose exec postgres psql -U edurisk -d edurisk_db -c "\dt"
```

### ✅ Backend
- [ ] Health check returns 200 OK
- [ ] API documentation accessible at /docs
- [ ] ML models loaded successfully
- [ ] Database connection working
- [ ] Redis connection working

**Verify:**
```bash
curl http://localhost:8000/api/health
curl http://localhost:8000/docs
docker-compose logs backend | grep "ML models loaded"
```

### ✅ Frontend
- [ ] Homepage loads
- [ ] Dashboard accessible
- [ ] API calls to backend working
- [ ] No console errors

**Verify:**
- Open http://localhost:3000
- Check browser console for errors
- Navigate to dashboard

### ✅ Integration
- [ ] Frontend can call backend API
- [ ] Backend can query database
- [ ] Backend can access Redis
- [ ] ML predictions working end-to-end

**Verify:**
- Submit a prediction from frontend
- Check if student appears in database
- Verify prediction stored correctly

## Troubleshooting

### Issue: Services won't start
**Solution:**
1. Check logs: `docker-compose logs`
2. Verify ports available
3. Check .env file exists and is valid
4. Ensure ML models exist

### Issue: Backend can't connect to database
**Solution:**
1. Check postgres is healthy: `docker-compose ps postgres`
2. Verify DATABASE_URL in backend environment
3. Check postgres logs: `docker-compose logs postgres`
4. Restart services: `docker-compose restart backend`

### Issue: Frontend can't reach backend
**Solution:**
1. Verify backend is running: `curl http://localhost:8000/api/health`
2. Check CORS_ORIGINS includes frontend URL
3. Check NEXT_PUBLIC_API_URL in frontend environment
4. Review backend logs for CORS errors

### Issue: ML models not found
**Solution:**
1. Verify models exist: `ls -la ml/models/`
2. Train models: `python ml/pipeline/train_all.py`
3. Rebuild backend: `docker-compose build backend`
4. Restart backend: `docker-compose restart backend`

### Issue: Database migrations fail
**Solution:**
1. Check alembic.ini configuration
2. Verify DATABASE_URL is correct
3. Run migrations manually:
   ```bash
   docker-compose exec backend alembic upgrade head
   ```
4. Check migration logs for errors

## Cleanup

### Stop Services
```bash
docker-compose down
```

### Remove Volumes (⚠️ Deletes all data)
```bash
docker-compose down -v
```

### Remove Images
```bash
docker-compose down --rmi all
```

### Full Cleanup
```bash
docker-compose down -v --rmi all
docker system prune -a
```

## Development Mode

For development with hot-reload:

```bash
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up
```

**Features:**
- Backend hot-reload on code changes
- Frontend hot-reload on code changes
- Debug logging enabled
- Source code mounted as volumes

## Production Considerations

### Security
- [ ] Change default passwords
- [ ] Use strong SECRET_KEY
- [ ] Configure proper CORS_ORIGINS
- [ ] Use HTTPS (reverse proxy)
- [ ] Scan images for vulnerabilities
- [ ] Use secrets management

### Performance
- [ ] Configure resource limits
- [ ] Adjust worker count based on CPU
- [ ] Configure database connection pooling
- [ ] Enable Redis caching
- [ ] Use CDN for static assets

### Monitoring
- [ ] Set up container metrics (Prometheus)
- [ ] Configure log aggregation (ELK/Loki)
- [ ] Set up health check monitoring
- [ ] Configure error tracking (Sentry)
- [ ] Set up uptime monitoring

### Backup
- [ ] Schedule database backups
- [ ] Backup ML models
- [ ] Backup environment configuration
- [ ] Test restore procedures

## Success Criteria

✅ **Deployment is successful when:**

1. All services show "healthy" status
2. Backend health check returns 200 OK
3. Frontend loads without errors
4. End-to-end prediction flow works
5. Database migrations completed
6. ML models loaded successfully
7. No errors in service logs
8. All ports accessible
9. Inter-service communication working
10. API documentation accessible

## Support

For issues:
1. Check logs: `docker-compose logs -f`
2. Review DOCKER_README.md
3. Check TASK_24_IMPLEMENTATION_SUMMARY.md
4. Verify environment configuration
5. Ensure all prerequisites met

## Quick Reference

```bash
# Start services
docker-compose up -d

# Stop services
docker-compose down

# View logs
docker-compose logs -f

# Check status
docker-compose ps

# Restart service
docker-compose restart backend

# Rebuild service
docker-compose build backend && docker-compose up -d backend

# Run command in container
docker-compose exec backend bash

# View backend logs
docker-compose logs -f backend

# View database logs
docker-compose logs -f postgres

# Access database
docker-compose exec postgres psql -U edurisk -d edurisk_db

# Run migrations
docker-compose exec backend alembic upgrade head

# Health check
curl http://localhost:8000/api/health
```
