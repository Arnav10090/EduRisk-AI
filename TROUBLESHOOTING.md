# EduRisk AI - Troubleshooting Guide

Common issues and their solutions for EduRisk AI deployment and operation.

## Table of Contents

1. [Docker Issues](#docker-issues)
2. [Database Issues](#database-issues)
3. [Backend Issues](#backend-issues)
4. [Frontend Issues](#frontend-issues)
5. [ML Model Issues](#ml-model-issues)
6. [API Issues](#api-issues)
7. [Performance Issues](#performance-issues)
8. [Network Issues](#network-issues)
9. [Environment Issues](#environment-issues)
10. [Debugging Tools](#debugging-tools)

---

## Docker Issues

### Issue: Docker daemon not running

**Symptoms:**
```
Cannot connect to the Docker daemon at unix:///var/run/docker.sock
```

**Solutions:**

**Linux:**
```bash
sudo systemctl start docker
sudo systemctl enable docker
```

**macOS:**
- Open Docker Desktop application
- Wait for Docker to start

**Windows:**
- Open Docker Desktop application
- Ensure WSL 2 is enabled
- Check Docker Desktop settings

---

### Issue: Port already in use

**Symptoms:**
```
Error starting userland proxy: listen tcp 0.0.0.0:8000: bind: address already in use
```

**Solutions:**

**Find and kill process using the port:**

**Linux/macOS:**
```bash
# Find process
lsof -i :8000

# Kill process
kill -9 <PID>
```

**Windows:**
```powershell
# Find process
netstat -ano | findstr :8000

# Kill process
taskkill /PID <PID> /F
```

**Or change the port in docker-compose.yml:**
```yaml
services:
  backend:
    ports:
      - "8001:8000"  # Change 8000 to 8001
```

---

### Issue: Docker Compose version incompatibility

**Symptoms:**
```
ERROR: Version in "./docker-compose.yml" is unsupported
```

**Solutions:**

**Update Docker Compose:**
```bash
# Linux
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# macOS/Windows
# Update Docker Desktop to latest version
```

**Or use older syntax in docker-compose.yml:**
```yaml
version: '3.8'  # Add version if missing
```

---

### Issue: Container keeps restarting

**Symptoms:**
```
edurisk-backend    Restarting (1) 5 seconds ago
```

**Solutions:**

**Check container logs:**
```bash
docker-compose logs backend
```

**Common causes:**
- Database not ready → Wait longer or check database logs
- Missing environment variables → Check .env file
- ML models not found → Train models or check volume mount
- Port conflict → Change port in docker-compose.yml

**Increase restart delay:**
```yaml
services:
  backend:
    restart: on-failure
    restart_policy:
      delay: 10s
      max_attempts: 5
```

---

## Database Issues

### Issue: Database connection refused

**Symptoms:**
```
sqlalchemy.exc.OperationalError: could not connect to server: Connection refused
```

**Solutions:**

**1. Check if PostgreSQL is running:**
```bash
docker-compose ps postgres
```

**2. Check PostgreSQL logs:**
```bash
docker-compose logs postgres
```

**3. Verify connection string:**
```bash
echo $DATABASE_URL
```

**4. Test connection manually:**
```bash
docker-compose exec postgres psql -U edurisk -d edurisk_db -c "SELECT 1"
```

**5. Restart PostgreSQL:**
```bash
docker-compose restart postgres
```

---

### Issue: Database migration failed

**Symptoms:**
```
alembic.util.exc.CommandError: Can't locate revision identified by 'xyz'
```

**Solutions:**

**1. Check current migration version:**
```bash
cd backend
alembic current
```

**2. Check migration history:**
```bash
alembic history
```

**3. Reset to specific version:**
```bash
alembic downgrade <revision>
alembic upgrade head
```

**4. Reset database (WARNING: deletes all data):**
```bash
docker-compose down -v
docker-compose up -d
```

---

### Issue: Database disk full

**Symptoms:**
```
ERROR: could not extend file: No space left on device
```

**Solutions:**

**1. Check disk usage:**
```bash
df -h
docker system df
```

**2. Clean up Docker:**
```bash
docker system prune -a --volumes
```

**3. Increase disk space:**
- Docker Desktop: Settings → Resources → Disk image size
- Linux: Expand filesystem or add volume

---

## Backend Issues

### Issue: Backend not starting

**Symptoms:**
- Health check returns 503 or times out
- Container exits immediately

**Solutions:**

**1. Check backend logs:**
```bash
docker-compose logs backend
```

**2. Common causes and fixes:**

**Missing environment variables:**
```bash
# Check .env file
cat .env

# Verify required variables
docker-compose exec backend env | grep -E 'DATABASE|REDIS|ANTHROPIC'
```

**ML models not found:**
```bash
# Check if models exist
ls -la ml/models/

# Train models
python ml/pipeline/train.py

# Verify volume mount
docker-compose exec backend ls -la /app/ml/models/
```

**Database not ready:**
```bash
# Wait for database
docker-compose logs postgres | grep "ready to accept connections"

# Increase wait time in docker/wait-for-db.py
```

---

### Issue: Import errors

**Symptoms:**
```
ModuleNotFoundError: No module named 'backend'
```

**Solutions:**

**1. Check Python path:**
```bash
docker-compose exec backend python -c "import sys; print('\n'.join(sys.path))"
```

**2. Rebuild container:**
```bash
docker-compose build --no-cache backend
docker-compose up -d backend
```

**3. Check requirements.txt:**
```bash
docker-compose exec backend pip list
```

---

### Issue: Slow predictions

**Symptoms:**
- Predictions take > 10 seconds
- Timeout errors

**Solutions:**

**1. Check CPU/memory usage:**
```bash
docker stats
```

**2. Increase container resources:**
```yaml
services:
  backend:
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 4G
```

**3. Enable model caching:**
- Models are cached in memory after first load
- Restart backend to clear cache if needed

**4. Check database query performance:**
```bash
# Enable query logging
docker-compose exec backend python -c "
from backend.db.session import engine
engine.echo = True
"
```

---

## Frontend Issues

### Issue: Frontend not loading

**Symptoms:**
- Blank page
- "Cannot GET /" error
- Connection refused

**Solutions:**

**1. Check frontend logs:**
```bash
docker-compose logs frontend
```

**2. Verify frontend is running:**
```bash
curl http://localhost:3000
```

**3. Check Next.js build:**
```bash
docker-compose exec frontend npm run build
```

**4. Restart frontend:**
```bash
docker-compose restart frontend
```

---

### Issue: API connection failed

**Symptoms:**
```
Failed to fetch
Network request failed
CORS error
```

**Solutions:**

**1. Check NEXT_PUBLIC_API_URL:**
```bash
docker-compose exec frontend env | grep NEXT_PUBLIC_API_URL
```

**2. Verify backend is accessible:**
```bash
curl http://localhost:8000/api/health
```

**3. Check CORS configuration:**
```bash
# Backend .env
CORS_ORIGINS=http://localhost:3000,http://frontend:3000
```

**4. Clear browser cache:**
- Chrome: Ctrl+Shift+Delete
- Firefox: Ctrl+Shift+Delete
- Safari: Cmd+Option+E

---

### Issue: Hot reload not working

**Symptoms:**
- Changes not reflected
- Need to restart container

**Solutions:**

**1. Use development mode:**
```bash
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up
```

**2. Check volume mounts:**
```yaml
services:
  frontend:
    volumes:
      - ./frontend:/app
      - /app/node_modules
```

**3. Restart frontend:**
```bash
docker-compose restart frontend
```

---

## ML Model Issues

### Issue: Models not found

**Symptoms:**
```
FileNotFoundError: [Errno 2] No such file or directory: '/app/ml/models/placement_model_3m.pkl'
```

**Solutions:**

**1. Check if models exist:**
```bash
ls -la ml/models/
```

**2. Train models:**
```bash
# Generate synthetic data
python ml/data/generate_synthetic.py

# Train models
python ml/pipeline/train.py
```

**3. Verify volume mount:**
```bash
docker-compose exec backend ls -la /app/ml/models/
```

**4. Check docker-compose.yml:**
```yaml
services:
  backend:
    volumes:
      - ./ml/models:/app/ml/models:ro
```

---

### Issue: Model loading errors

**Symptoms:**
```
pickle.UnpicklingError: invalid load key
EOFError: Ran out of input
```

**Solutions:**

**1. Retrain models:**
```bash
rm ml/models/*.pkl
python ml/pipeline/train.py
```

**2. Check model file integrity:**
```bash
file ml/models/placement_model_3m.pkl
```

**3. Verify Python version compatibility:**
```bash
# Models trained with Python 3.11
python --version
```

---

### Issue: SHAP computation slow

**Symptoms:**
- Predictions take > 5 seconds
- High CPU usage

**Solutions:**

**1. Use TreeExplainer (already implemented):**
- TreeExplainer is exact and fast for XGBoost

**2. Reduce SHAP computation:**
```python
# In backend/services/prediction_service.py
# Compute SHAP only for top features
explainer.explain(features, max_features=5)
```

**3. Cache SHAP values:**
- SHAP values are stored in database
- Retrieve from database instead of recomputing

---

## API Issues

### Issue: 422 Validation Error

**Symptoms:**
```json
{
  "detail": [
    {
      "loc": ["body", "institute_tier"],
      "msg": "ensure this value is less than or equal to 3"
    }
  ]
}
```

**Solutions:**

**Check request body:**
- `institute_tier` must be 1, 2, or 3
- `cgpa` must be >= 0 and <= cgpa_scale
- `year_of_grad` must be between 2020 and 2030
- All count fields must be >= 0

**Example valid request:**
```json
{
  "name": "John Doe",
  "course_type": "Engineering",
  "institute_tier": 2,
  "cgpa": 8.5,
  "cgpa_scale": 10.0,
  "year_of_grad": 2025,
  "internship_count": 2,
  "internship_months": 6,
  "internship_employer_type": "MNC",
  "certifications": 3,
  "region": "Mumbai",
  "loan_amount": 500000.0,
  "loan_emi": 15000.0
}
```

---

### Issue: 429 Rate Limit Exceeded

**Symptoms:**
```json
{
  "detail": "Rate limit exceeded",
  "retry_after": 60
}
```

**Solutions:**

**1. Wait for rate limit reset:**
- Check `X-RateLimit-Reset` header
- Wait until reset time

**2. Clear Redis cache:**
```bash
docker-compose exec redis redis-cli FLUSHALL
```

**3. Increase rate limits:**
```python
# Edit backend/middleware/rate_limit.py
RATE_LIMITS = {
    "predict": 200,  # Increase from 100
    "batch": 20,     # Increase from 10
    "get": 600       # Increase from 300
}
```

---

### Issue: 500 Internal Server Error

**Symptoms:**
```json
{
  "detail": "Internal server error",
  "status": "error"
}
```

**Solutions:**

**1. Check backend logs:**
```bash
docker-compose logs backend | tail -100
```

**2. Enable debug mode:**
```bash
# Edit .env
DEBUG=True
LOG_LEVEL=DEBUG

# Restart backend
docker-compose restart backend
```

**3. Common causes:**
- Database connection lost
- ML model loading failed
- Claude API timeout
- Invalid data in database

---

## Performance Issues

### Issue: High memory usage

**Symptoms:**
- Container OOM killed
- Slow response times
- System freezing

**Solutions:**

**1. Check memory usage:**
```bash
docker stats
```

**2. Increase container memory:**
```yaml
services:
  backend:
    deploy:
      resources:
        limits:
          memory: 4G
```

**3. Optimize database queries:**
```python
# Use pagination
GET /api/students?limit=20&offset=0

# Use indexes
CREATE INDEX idx_students_tier ON students(institute_tier);
```

**4. Clear Redis cache:**
```bash
docker-compose exec redis redis-cli FLUSHALL
```

---

### Issue: High CPU usage

**Symptoms:**
- Slow predictions
- High load average
- Container throttling

**Solutions:**

**1. Check CPU usage:**
```bash
docker stats
top
```

**2. Increase CPU allocation:**
```yaml
services:
  backend:
    deploy:
      resources:
        limits:
          cpus: '4'
```

**3. Optimize ML inference:**
- Use smaller batch sizes
- Reduce SHAP computation
- Cache predictions

---

## Network Issues

### Issue: Cannot access from external network

**Symptoms:**
- Works on localhost
- Fails from other machines

**Solutions:**

**1. Check firewall:**
```bash
# Linux
sudo ufw allow 8000
sudo ufw allow 3000

# Windows
# Add inbound rules in Windows Firewall
```

**2. Bind to 0.0.0.0:**
```yaml
services:
  backend:
    ports:
      - "0.0.0.0:8000:8000"
```

**3. Check Docker network:**
```bash
docker network ls
docker network inspect edurisk-network
```

---

### Issue: Services cannot communicate

**Symptoms:**
- Backend cannot connect to database
- Frontend cannot connect to backend

**Solutions:**

**1. Check Docker network:**
```bash
docker network inspect edurisk-network
```

**2. Use service names:**
```yaml
# In docker-compose.yml
DATABASE_URL=postgresql+asyncpg://edurisk:password@postgres:5432/edurisk_db
# Use 'postgres' not 'localhost'
```

**3. Restart network:**
```bash
docker-compose down
docker network prune
docker-compose up -d
```

---

## Environment Issues

### Issue: Environment variables not loaded

**Symptoms:**
- "Variable not set" errors
- Default values used

**Solutions:**

**1. Check .env file exists:**
```bash
ls -la .env
```

**2. Verify .env format:**
```env
# Correct
ANTHROPIC_API_KEY=sk-ant-...

# Incorrect (no spaces around =)
ANTHROPIC_API_KEY = sk-ant-...
```

**3. Restart services:**
```bash
docker-compose down
docker-compose up -d
```

**4. Check environment in container:**
```bash
docker-compose exec backend env
```

---

## Debugging Tools

### View Logs

**All services:**
```bash
docker-compose logs -f
```

**Specific service:**
```bash
docker-compose logs -f backend
docker-compose logs -f frontend
docker-compose logs -f postgres
docker-compose logs -f redis
```

**Last N lines:**
```bash
docker-compose logs --tail=100 backend
```

---

### Execute Commands in Container

**Backend:**
```bash
# Shell
docker-compose exec backend bash

# Python
docker-compose exec backend python

# Run script
docker-compose exec backend python test_integration.py
```

**Database:**
```bash
# psql
docker-compose exec postgres psql -U edurisk -d edurisk_db

# SQL query
docker-compose exec postgres psql -U edurisk -d edurisk_db -c "SELECT COUNT(*) FROM students"
```

**Redis:**
```bash
# redis-cli
docker-compose exec redis redis-cli

# Check keys
docker-compose exec redis redis-cli KEYS '*'

# Clear cache
docker-compose exec redis redis-cli FLUSHALL
```

---

### Health Checks

**Backend:**
```bash
curl http://localhost:8000/api/health
```

**Database:**
```bash
docker-compose exec postgres pg_isready -U edurisk
```

**Redis:**
```bash
docker-compose exec redis redis-cli ping
```

---

### Performance Profiling

**Monitor resources:**
```bash
docker stats
```

**Profile Python code:**
```bash
pip install py-spy
py-spy top --pid $(pgrep -f uvicorn)
```

**Database query analysis:**
```sql
-- Enable query logging
ALTER SYSTEM SET log_statement = 'all';
SELECT pg_reload_conf();

-- View slow queries
SELECT * FROM pg_stat_statements ORDER BY total_time DESC LIMIT 10;
```

---

## Getting Help

If you're still experiencing issues:

1. **Check logs:** `docker-compose logs -f`
2. **Run integration tests:** `python test_integration.py`
3. **Review documentation:**
   - [README.md](README.md)
   - [API_DOCUMENTATION.md](API_DOCUMENTATION.md)
   - [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)
4. **Check GitHub issues:** Search for similar problems
5. **Create new issue:** Include logs, error messages, and steps to reproduce

---

**Last Updated:** January 2025
