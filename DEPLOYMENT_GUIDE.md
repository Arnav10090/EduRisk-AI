# EduRisk AI - Deployment Guide

Complete guide for deploying EduRisk AI in various environments.

## Table of Contents

1. [Local Development](#local-development)
2. [Docker Deployment](#docker-deployment)
3. [Production Deployment](#production-deployment)
4. [Environment Configuration](#environment-configuration)
5. [Database Setup](#database-setup)
6. [ML Model Deployment](#ml-model-deployment)
7. [Monitoring & Logging](#monitoring--logging)
8. [Backup & Recovery](#backup--recovery)
9. [Troubleshooting](#troubleshooting)

---

## Local Development

### Prerequisites

- Python 3.11+
- Node.js 20+
- PostgreSQL 16
- Redis 7
- Git

### Backend Setup

1. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment**
   ```bash
   cd backend
   cp .env.example .env
   # Edit .env with your configuration
   ```

4. **Run database migrations**
   ```bash
   cd backend
   alembic upgrade head
   ```

5. **Train ML models** (if not already trained)
   ```bash
   python ml/data/generate_synthetic.py
   python ml/pipeline/train.py
   ```

6. **Start backend server**
   ```bash
   cd backend
   uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```

### Frontend Setup

1. **Install dependencies**
   ```bash
   cd frontend
   npm install
   ```

2. **Configure environment**
   ```bash
   cp .env.example .env.local
   # Edit .env.local with backend API URL
   ```

3. **Start development server**
   ```bash
   npm run dev
   ```

4. **Access application**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Docs: http://localhost:8000/docs

---

## Docker Deployment

### Quick Start

1. **Validate setup**
   ```bash
   chmod +x docker/validate-setup.sh
   ./docker/validate-setup.sh
   ```

2. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. **Start services**
   ```bash
   docker-compose up -d
   ```

4. **Check service health**
   ```bash
   docker-compose ps
   curl http://localhost:8000/api/health
   ```

5. **View logs**
   ```bash
   docker-compose logs -f
   ```

### Development Mode

For hot-reload during development:

```bash
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up
```

This enables:
- Backend hot-reload with volume mounts
- Frontend hot-reload
- Debug logging
- Source code synchronization

### Production Mode

1. **Build optimized images**
   ```bash
   docker-compose build --no-cache
   ```

2. **Start with production settings**
   ```bash
   docker-compose up -d
   ```

3. **Scale services** (if needed)
   ```bash
   docker-compose up -d --scale backend=3
   ```

### Docker Commands Reference

```bash
# Start services
docker-compose up -d

# Stop services
docker-compose down

# Restart specific service
docker-compose restart backend

# View logs
docker-compose logs -f backend

# Execute command in container
docker-compose exec backend bash

# Remove volumes (WARNING: deletes data)
docker-compose down -v

# Rebuild images
docker-compose build --no-cache

# Pull latest images
docker-compose pull
```

---

## Production Deployment

### Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│                    Load Balancer                         │
│                   (Nginx/HAProxy)                        │
└────────────────────┬────────────────────────────────────┘
                     │
        ┌────────────┴────────────┐
        │                         │
┌───────▼────────┐      ┌─────────▼────────┐
│  Frontend      │      │   Backend API    │
│  (Next.js)     │      │   (FastAPI)      │
│  x3 instances  │      │   x3 instances   │
└────────────────┘      └─────────┬────────┘
                                  │
                    ┌─────────────┴─────────────┐
                    │                           │
            ┌───────▼────────┐        ┌────────▼────────┐
            │  PostgreSQL    │        │     Redis       │
            │  (Primary +    │        │   (Cluster)     │
            │   Replicas)    │        │                 │
            └────────────────┘        └─────────────────┘
```

### Infrastructure Requirements

**Minimum Production Setup:**
- **Backend**: 3 instances, 2 CPU, 4GB RAM each
- **Frontend**: 3 instances, 1 CPU, 2GB RAM each
- **PostgreSQL**: 1 primary + 2 replicas, 4 CPU, 8GB RAM
- **Redis**: 3-node cluster, 2 CPU, 4GB RAM each
- **Load Balancer**: 2 CPU, 4GB RAM
- **Total**: ~40GB RAM, 20+ CPU cores

**Recommended Production Setup:**
- **Backend**: 5 instances, 4 CPU, 8GB RAM each
- **Frontend**: 5 instances, 2 CPU, 4GB RAM each
- **PostgreSQL**: 1 primary + 2 replicas, 8 CPU, 16GB RAM
- **Redis**: 6-node cluster, 4 CPU, 8GB RAM each
- **Load Balancer**: 4 CPU, 8GB RAM
- **Total**: ~120GB RAM, 60+ CPU cores

### Cloud Deployment Options

#### AWS Deployment

**Services:**
- **Compute**: ECS Fargate or EKS
- **Database**: RDS PostgreSQL (Multi-AZ)
- **Cache**: ElastiCache Redis (Cluster mode)
- **Load Balancer**: Application Load Balancer
- **Storage**: S3 for ML models
- **Monitoring**: CloudWatch
- **Secrets**: AWS Secrets Manager

**Estimated Monthly Cost:**
- Minimum setup: ~$500-800/month
- Recommended setup: ~$1500-2500/month

#### Google Cloud Deployment

**Services:**
- **Compute**: Cloud Run or GKE
- **Database**: Cloud SQL PostgreSQL (HA)
- **Cache**: Memorystore Redis
- **Load Balancer**: Cloud Load Balancing
- **Storage**: Cloud Storage for ML models
- **Monitoring**: Cloud Monitoring
- **Secrets**: Secret Manager

**Estimated Monthly Cost:**
- Minimum setup: ~$450-750/month
- Recommended setup: ~$1400-2300/month

#### Azure Deployment

**Services:**
- **Compute**: Container Instances or AKS
- **Database**: Azure Database for PostgreSQL (HA)
- **Cache**: Azure Cache for Redis
- **Load Balancer**: Application Gateway
- **Storage**: Blob Storage for ML models
- **Monitoring**: Azure Monitor
- **Secrets**: Key Vault

**Estimated Monthly Cost:**
- Minimum setup: ~$500-800/month
- Recommended setup: ~$1500-2500/month

### Kubernetes Deployment

1. **Create namespace**
   ```bash
   kubectl create namespace edurisk-ai
   ```

2. **Create secrets**
   ```bash
   kubectl create secret generic edurisk-secrets \
     --from-literal=database-url='postgresql://...' \
     --from-literal=redis-url='redis://...' \
     --from-literal=anthropic-api-key='sk-...' \
     --from-literal=secret-key='...' \
     -n edurisk-ai
   ```

3. **Deploy PostgreSQL** (or use managed service)
   ```bash
   kubectl apply -f k8s/postgres.yaml -n edurisk-ai
   ```

4. **Deploy Redis** (or use managed service)
   ```bash
   kubectl apply -f k8s/redis.yaml -n edurisk-ai
   ```

5. **Deploy backend**
   ```bash
   kubectl apply -f k8s/backend.yaml -n edurisk-ai
   ```

6. **Deploy frontend**
   ```bash
   kubectl apply -f k8s/frontend.yaml -n edurisk-ai
   ```

7. **Create ingress**
   ```bash
   kubectl apply -f k8s/ingress.yaml -n edurisk-ai
   ```

---

## Environment Configuration

### Backend Environment Variables

**Required:**
```env
DATABASE_URL=postgresql+asyncpg://user:password@host:5432/dbname
REDIS_URL=redis://host:6379/0
ANTHROPIC_API_KEY=sk-ant-...
ML_MODEL_PATH=/app/ml/models
SECRET_KEY=your-secret-key-here
```

**Optional:**
```env
CORS_ORIGINS=https://app.example.com,https://www.example.com
DEBUG=False
LOG_LEVEL=INFO
LOG_JSON_FORMAT=True
HOST=0.0.0.0
PORT=8000
```

### Frontend Environment Variables

**Required:**
```env
NEXT_PUBLIC_API_URL=https://api.example.com
```

**Optional:**
```env
NODE_ENV=production
```

### Generating Secrets

**SECRET_KEY:**
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

**Database Password:**
```bash
openssl rand -base64 32
```

---

## Database Setup

### PostgreSQL Configuration

**Recommended Settings for Production:**

```sql
-- postgresql.conf
max_connections = 200
shared_buffers = 4GB
effective_cache_size = 12GB
maintenance_work_mem = 1GB
checkpoint_completion_target = 0.9
wal_buffers = 16MB
default_statistics_target = 100
random_page_cost = 1.1
effective_io_concurrency = 200
work_mem = 10MB
min_wal_size = 1GB
max_wal_size = 4GB
max_worker_processes = 4
max_parallel_workers_per_gather = 2
max_parallel_workers = 4
```

### Database Migrations

**Apply migrations:**
```bash
cd backend
alembic upgrade head
```

**Create new migration:**
```bash
alembic revision --autogenerate -m "Description"
```

**Rollback migration:**
```bash
alembic downgrade -1
```

**Check current version:**
```bash
alembic current
```

### Database Backup

**Manual backup:**
```bash
pg_dump -h localhost -U edurisk -d edurisk_db > backup_$(date +%Y%m%d_%H%M%S).sql
```

**Automated backup script:**
```bash
#!/bin/bash
# backup-db.sh
BACKUP_DIR="/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/edurisk_backup_$TIMESTAMP.sql"

pg_dump -h $DB_HOST -U $DB_USER -d $DB_NAME > $BACKUP_FILE
gzip $BACKUP_FILE

# Keep only last 7 days of backups
find $BACKUP_DIR -name "edurisk_backup_*.sql.gz" -mtime +7 -delete
```

**Restore from backup:**
```bash
gunzip -c backup_20250115_120000.sql.gz | psql -h localhost -U edurisk -d edurisk_db
```

---

## ML Model Deployment

### Model Storage

**Local Development:**
- Models stored in `ml/models/` directory
- Mounted as volume in Docker

**Production:**
- Store models in object storage (S3, GCS, Azure Blob)
- Download on container startup
- Cache in container filesystem

### Model Versioning

**Version file structure:**
```json
{
  "version": "1.0.0",
  "training_date": "2025-01-15T10:00:00Z",
  "metrics": {
    "placement_3m_auc": 0.87,
    "placement_6m_auc": 0.89,
    "placement_12m_auc": 0.91,
    "salary_r2": 0.82
  },
  "features": 16,
  "training_samples": 5000
}
```

### Model Update Process

1. **Train new models**
   ```bash
   python ml/pipeline/train.py
   ```

2. **Run bias audit**
   ```bash
   python ml/pipeline/bias_audit.py
   ```

3. **Test new models**
   ```bash
   python test_integration.py
   ```

4. **Upload to storage**
   ```bash
   aws s3 sync ml/models/ s3://edurisk-models/v1.1.0/
   ```

5. **Update version in deployment**
   ```bash
   kubectl set env deployment/backend \
     ML_MODEL_VERSION=1.1.0 \
     -n edurisk-ai
   ```

6. **Rolling update**
   ```bash
   kubectl rollout restart deployment/backend -n edurisk-ai
   ```

---

## Monitoring & Logging

### Health Checks

**Backend health endpoint:**
```bash
curl http://localhost:8000/api/health
```

**Expected response:**
```json
{
  "status": "ok",
  "model_version": "1.0.0",
  "database": "connected",
  "timestamp": "2025-01-15T10:30:00Z"
}
```

### Logging

**Backend logs:**
```bash
# Docker
docker-compose logs -f backend

# Kubernetes
kubectl logs -f deployment/backend -n edurisk-ai
```

**Log format (JSON):**
```json
{
  "timestamp": "2025-01-15T10:30:00Z",
  "level": "INFO",
  "logger": "backend.services.prediction_service",
  "message": "Prediction generated",
  "context": {
    "student_id": "550e8400-e29b-41d4-a716-446655440000",
    "risk_score": 45,
    "processing_time_ms": 1234
  }
}
```

### Metrics to Monitor

**Application Metrics:**
- Request rate (requests/second)
- Response time (p50, p95, p99)
- Error rate (%)
- Prediction latency
- Batch processing time

**Infrastructure Metrics:**
- CPU usage (%)
- Memory usage (%)
- Disk I/O
- Network I/O
- Database connections
- Redis memory usage

**Business Metrics:**
- Total predictions
- High-risk alerts
- Average risk score
- Placement probability distribution
- API usage by endpoint

### Alerting Rules

**Critical Alerts:**
- Health check fails for > 2 minutes
- Error rate > 5% for > 5 minutes
- Database connection pool exhausted
- Redis unavailable
- Disk usage > 90%

**Warning Alerts:**
- Response time p95 > 5 seconds
- Error rate > 1% for > 10 minutes
- CPU usage > 80% for > 10 minutes
- Memory usage > 85% for > 10 minutes

---

## Backup & Recovery

### Backup Strategy

**Daily Backups:**
- Full database backup at 2 AM UTC
- Retain for 30 days
- Store in S3/GCS with versioning

**Weekly Backups:**
- Full system backup (database + models)
- Retain for 90 days
- Store in separate region

**Continuous Backups:**
- PostgreSQL WAL archiving
- Point-in-time recovery capability

### Disaster Recovery

**RTO (Recovery Time Objective):** 1 hour
**RPO (Recovery Point Objective):** 5 minutes

**Recovery Steps:**

1. **Database failure**
   ```bash
   # Promote replica to primary
   pg_ctl promote -D /var/lib/postgresql/data
   
   # Update backend connection string
   kubectl set env deployment/backend \
     DATABASE_URL=postgresql://new-primary:5432/edurisk_db
   ```

2. **Complete system failure**
   ```bash
   # Restore database from backup
   gunzip -c latest_backup.sql.gz | psql -h new-db -U edurisk -d edurisk_db
   
   # Deploy application
   kubectl apply -f k8s/ -n edurisk-ai
   
   # Verify health
   curl https://api.example.com/api/health
   ```

---

## Troubleshooting

### Common Issues

#### 1. Database Connection Failed

**Symptoms:**
- Backend health check returns 503
- Logs show "connection refused"

**Solutions:**
```bash
# Check if PostgreSQL is running
docker-compose ps postgres

# Check PostgreSQL logs
docker-compose logs postgres

# Verify connection string
echo $DATABASE_URL

# Test connection manually
psql $DATABASE_URL -c "SELECT 1"

# Restart database
docker-compose restart postgres
```

#### 2. ML Models Not Found

**Symptoms:**
- Prediction returns 500 error
- Logs show "Model file not found"

**Solutions:**
```bash
# Check if models exist
ls -la ml/models/

# Train models if missing
python ml/pipeline/train.py

# Verify model path in container
docker-compose exec backend ls -la /app/ml/models/

# Check volume mount
docker-compose config | grep volumes -A 5
```

#### 3. High Memory Usage

**Symptoms:**
- Container OOM killed
- Slow response times

**Solutions:**
```bash
# Check memory usage
docker stats

# Increase container memory limit
# Edit docker-compose.yml:
services:
  backend:
    deploy:
      resources:
        limits:
          memory: 4G

# Restart services
docker-compose up -d
```

#### 4. Rate Limit Issues

**Symptoms:**
- Requests return 429
- X-RateLimit-Remaining is 0

**Solutions:**
```bash
# Clear Redis cache
docker-compose exec redis redis-cli FLUSHALL

# Increase rate limits
# Edit backend/middleware/rate_limit.py

# Restart backend
docker-compose restart backend
```

#### 5. Frontend Can't Connect to Backend

**Symptoms:**
- Frontend shows connection errors
- Network requests fail

**Solutions:**
```bash
# Check backend is running
curl http://localhost:8000/api/health

# Verify NEXT_PUBLIC_API_URL
cat frontend/.env.local

# Check CORS configuration
# Edit backend/.env:
CORS_ORIGINS=http://localhost:3000

# Restart backend
docker-compose restart backend
```

### Debug Mode

**Enable debug logging:**
```bash
# Edit .env
DEBUG=True
LOG_LEVEL=DEBUG

# Restart services
docker-compose restart
```

**View detailed logs:**
```bash
docker-compose logs -f --tail=100 backend
```

### Performance Profiling

**Profile API endpoint:**
```bash
# Install profiling tools
pip install py-spy

# Profile running process
py-spy top --pid $(pgrep -f uvicorn)

# Generate flame graph
py-spy record -o profile.svg --pid $(pgrep -f uvicorn)
```

---

## Security Checklist

- [ ] Change default passwords
- [ ] Use strong SECRET_KEY
- [ ] Enable HTTPS/TLS
- [ ] Configure firewall rules
- [ ] Implement authentication
- [ ] Enable audit logging
- [ ] Regular security updates
- [ ] Backup encryption
- [ ] API rate limiting
- [ ] Input validation
- [ ] SQL injection prevention
- [ ] XSS protection
- [ ] CORS configuration
- [ ] Secrets management
- [ ] Network segmentation

---

## Support

For deployment issues:
- Review logs: `docker-compose logs -f`
- Check health: `curl http://localhost:8000/api/health`
- Run integration tests: `python test_integration.py`
- Consult [README.md](README.md) and [API_DOCUMENTATION.md](API_DOCUMENTATION.md)

---

**Last Updated:** January 2025
