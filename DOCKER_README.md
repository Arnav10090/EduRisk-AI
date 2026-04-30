# EduRisk AI - Docker Deployment Guide

This guide explains how to deploy EduRisk AI using Docker and Docker Compose.

## Prerequisites

- Docker Engine 20.10 or later
- Docker Compose 2.0 or later
- At least 4GB of available RAM
- At least 10GB of available disk space

## Quick Start

1. **Clone the repository and navigate to the project directory**

2. **Create environment file**
   ```bash
   cp .env.example .env
   ```

3. **Edit `.env` and set required variables**
   - `ANTHROPIC_API_KEY`: Your Anthropic API key for AI summaries
   - `SECRET_KEY`: A secure random string for JWT tokens

4. **Ensure ML models are trained**
   ```bash
   # If models don't exist in ml/models/, train them first
   python ml/pipeline/train_all.py
   ```

5. **Start all services**
   ```bash
   docker-compose up -d
   ```

6. **Wait for services to be ready** (usually 30-60 seconds)
   ```bash
   docker-compose ps
   ```

7. **Access the application**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs

## Architecture

The Docker setup includes four services:

### 1. PostgreSQL Database (`postgres`)
- **Image**: Custom build from `docker/Dockerfile.postgres` (based on postgres:16-alpine)
- **Port**: 5432
- **Volume**: `postgres_data` for persistent storage
- **Health Check**: `pg_isready` command

### 2. Redis Cache (`redis`)
- **Image**: redis:7-alpine
- **Port**: 6379
- **Volume**: `redis_data` for persistent storage
- **Health Check**: `redis-cli ping` command

### 3. Backend API (`backend`)
- **Build**: `docker/Dockerfile.backend`
- **Port**: 8000
- **Dependencies**: Waits for postgres and redis to be healthy
- **Volumes**: ML models mounted as read-only at `/app/ml/models`
- **Features**:
  - Automatic database migration on startup
  - Database connection retry logic
  - Health check endpoint at `/api/health`

### 4. Frontend (`frontend`)
- **Build**: `docker/Dockerfile.frontend` (multi-stage production build)
- **Port**: 3000
- **Dependencies**: Waits for backend to start
- **Features**:
  - Optimized production build
  - Non-root user for security
  - Health check on root endpoint

## Development Mode

For development with hot-reload:

```bash
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up
```

This enables:
- Backend hot-reload on code changes
- Frontend hot-reload on code changes
- Debug logging
- Volume mounts for live code updates

## Service Management

### Start services
```bash
docker-compose up -d
```

### Stop services
```bash
docker-compose down
```

### Stop services and remove volumes (⚠️ deletes all data)
```bash
docker-compose down -v
```

### View logs
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend
docker-compose logs -f frontend
```

### Restart a service
```bash
docker-compose restart backend
```

### Rebuild a service
```bash
docker-compose build backend
docker-compose up -d backend
```

## Health Checks

All services include health checks:

```bash
# Check service health status
docker-compose ps

# Check backend health endpoint
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

## Database Migrations

Database migrations run automatically on backend startup. To run manually:

```bash
docker-compose exec backend alembic upgrade head
```

To create a new migration:

```bash
docker-compose exec backend alembic revision --autogenerate -m "Description"
```

## Troubleshooting

### Backend fails to start

1. **Check database connectivity**
   ```bash
   docker-compose logs postgres
   docker-compose exec postgres pg_isready -U edurisk
   ```

2. **Check backend logs**
   ```bash
   docker-compose logs backend
   ```

3. **Verify ML models exist**
   ```bash
   ls -la ml/models/
   ```
   Should contain: `placement_model_3m.pkl`, `placement_model_6m.pkl`, `placement_model_12m.pkl`, `salary_model.pkl`

### Frontend fails to connect to backend

1. **Verify backend is running**
   ```bash
   curl http://localhost:8000/api/health
   ```

2. **Check CORS configuration**
   Ensure `CORS_ORIGINS` in backend environment includes frontend URL

3. **Check frontend logs**
   ```bash
   docker-compose logs frontend
   ```

### Database connection errors

1. **Ensure postgres is healthy**
   ```bash
   docker-compose ps postgres
   ```

2. **Check DATABASE_URL format**
   Should be: `postgresql+asyncpg://edurisk:edurisk_password@postgres:5432/edurisk_db`

3. **Restart services in order**
   ```bash
   docker-compose down
   docker-compose up -d postgres redis
   # Wait 10 seconds
   docker-compose up -d backend frontend
   ```

### Port conflicts

If ports 3000, 5432, 6379, or 8000 are already in use:

1. **Stop conflicting services**
2. **Or modify ports in docker-compose.yml**
   ```yaml
   ports:
     - "8001:8000"  # Map to different host port
   ```

## Production Deployment

For production deployment:

1. **Use production environment variables**
   - Set `DEBUG=False`
   - Use strong `SECRET_KEY`
   - Configure proper `CORS_ORIGINS`

2. **Use external database** (recommended)
   - Remove postgres service from docker-compose.yml
   - Update `DATABASE_URL` to point to external PostgreSQL

3. **Use external Redis** (recommended)
   - Remove redis service from docker-compose.yml
   - Update `REDIS_URL` to point to external Redis

4. **Enable HTTPS**
   - Use a reverse proxy (nginx, Traefik, Caddy)
   - Configure SSL certificates

5. **Set resource limits**
   ```yaml
   services:
     backend:
       deploy:
         resources:
           limits:
             cpus: '2'
             memory: 4G
   ```

6. **Configure logging**
   - Use log aggregation (ELK, Loki, CloudWatch)
   - Set `LOG_LEVEL=WARNING` or `ERROR`

## Environment Variables Reference

### Backend Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `DATABASE_URL` | Yes | - | PostgreSQL connection URL |
| `REDIS_URL` | Yes | - | Redis connection URL |
| `ANTHROPIC_API_KEY` | Yes | - | Anthropic API key for AI summaries |
| `ML_MODEL_PATH` | Yes | `/app/ml/models` | Path to ML model files |
| `SECRET_KEY` | Yes | - | Secret key for JWT tokens |
| `CORS_ORIGINS` | No | `http://localhost:3000` | Comma-separated allowed origins |
| `DEBUG` | No | `False` | Enable debug mode |
| `LOG_LEVEL` | No | `INFO` | Logging level (DEBUG, INFO, WARNING, ERROR) |

### Frontend Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `NEXT_PUBLIC_API_URL` | No | `http://localhost:8000` | Backend API URL |

## Volumes

- `postgres_data`: PostgreSQL database files
- `redis_data`: Redis persistence files
- `./ml/models`: ML model artifacts (mounted read-only in backend)

## Networks

All services communicate via the `edurisk-network` bridge network.

## Security Considerations

1. **Change default passwords** in production
2. **Use secrets management** for sensitive values (Docker secrets, Vault)
3. **Run containers as non-root** (frontend already does this)
4. **Keep images updated** regularly
5. **Scan images for vulnerabilities** using `docker scan`
6. **Limit network exposure** - only expose necessary ports
7. **Use read-only volumes** where possible (ML models)

## Performance Tuning

### Database
- Adjust PostgreSQL connection pool size in backend config
- Increase shared_buffers for better performance
- Configure appropriate work_mem

### Backend
- Adjust number of Uvicorn workers based on CPU cores
- Configure connection pool size based on expected load
- Enable Redis caching for frequently accessed data

### Frontend
- Use CDN for static assets in production
- Enable Next.js image optimization
- Configure appropriate cache headers

## Monitoring

Recommended monitoring setup:

1. **Container metrics**: cAdvisor + Prometheus + Grafana
2. **Application logs**: Loki or ELK stack
3. **Health checks**: Uptime monitoring (UptimeRobot, Pingdom)
4. **APM**: Sentry for error tracking

## Backup and Recovery

### Database Backup
```bash
# Backup
docker-compose exec postgres pg_dump -U edurisk edurisk_db > backup.sql

# Restore
docker-compose exec -T postgres psql -U edurisk edurisk_db < backup.sql
```

### Volume Backup
```bash
# Backup volumes
docker run --rm -v edurisk_postgres_data:/data -v $(pwd):/backup alpine tar czf /backup/postgres_backup.tar.gz /data
```

## Support

For issues and questions:
- Check logs: `docker-compose logs`
- Review health checks: `docker-compose ps`
- Consult API documentation: http://localhost:8000/docs
