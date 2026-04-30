# EduRisk AI - Environment Variables Reference

Complete reference for all environment variables used in the EduRisk AI system.

## Table of Contents

1. [Backend Environment Variables](#backend-environment-variables)
2. [Frontend Environment Variables](#frontend-environment-variables)
3. [Docker Compose Variables](#docker-compose-variables)
4. [Database Variables](#database-variables)
5. [Redis Variables](#redis-variables)
6. [Security Variables](#security-variables)
7. [Logging Variables](#logging-variables)
8. [ML Model Variables](#ml-model-variables)
9. [API Configuration](#api-configuration)
10. [Examples](#examples)

---

## Backend Environment Variables

### Required Variables

#### DATABASE_URL
- **Description**: PostgreSQL database connection string
- **Format**: `postgresql+asyncpg://user:password@host:port/database`
- **Example**: `postgresql+asyncpg://edurisk:edurisk_password@postgres:5432/edurisk_db`
- **Required**: Yes
- **Default**: None

#### REDIS_URL
- **Description**: Redis cache connection string
- **Format**: `redis://host:port/db`
- **Example**: `redis://redis:6379/0`
- **Required**: Yes
- **Default**: None

#### ANTHROPIC_API_KEY
- **Description**: Anthropic API key for Claude AI summaries
- **Format**: `sk-ant-...`
- **Example**: `sk-ant-api03-1234567890abcdef...`
- **Required**: Yes (for AI summaries)
- **Default**: None
- **Note**: Get your API key from https://console.anthropic.com/

#### ML_MODEL_PATH
- **Description**: Path to ML models directory
- **Format**: Absolute or relative path
- **Example**: `/app/ml/models` (Docker) or `./ml/models` (local)
- **Required**: Yes
- **Default**: `/app/ml/models`

#### SECRET_KEY
- **Description**: Secret key for JWT tokens and encryption
- **Format**: Random string (32+ characters recommended)
- **Example**: `your-secret-key-here-change-in-production`
- **Required**: Yes
- **Default**: None
- **Generate**: `python -c "import secrets; print(secrets.token_urlsafe(32))"`

### Optional Variables

#### CORS_ORIGINS
- **Description**: Comma-separated list of allowed CORS origins
- **Format**: `http://origin1,https://origin2`
- **Example**: `http://localhost:3000,https://app.example.com`
- **Required**: No
- **Default**: `http://localhost:3000`

#### DEBUG
- **Description**: Enable debug mode
- **Format**: `True` or `False`
- **Example**: `False`
- **Required**: No
- **Default**: `True`
- **Note**: Set to `False` in production

#### LOG_LEVEL
- **Description**: Logging level
- **Format**: `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`
- **Example**: `INFO`
- **Required**: No
- **Default**: `INFO`

#### LOG_JSON_FORMAT
- **Description**: Use JSON format for logs
- **Format**: `True` or `False`
- **Example**: `True`
- **Required**: No
- **Default**: `True`

#### HOST
- **Description**: Host to bind the server to
- **Format**: IP address or hostname
- **Example**: `0.0.0.0`
- **Required**: No
- **Default**: `0.0.0.0`

#### PORT
- **Description**: Port to bind the server to
- **Format**: Integer (1-65535)
- **Example**: `8000`
- **Required**: No
- **Default**: `8000`

---

## Frontend Environment Variables

### Required Variables

#### NEXT_PUBLIC_API_URL
- **Description**: Backend API base URL
- **Format**: `http://host:port` or `https://domain`
- **Example**: `http://localhost:8000` or `https://api.example.com`
- **Required**: Yes
- **Default**: `http://localhost:8000`
- **Note**: Must be prefixed with `NEXT_PUBLIC_` to be accessible in browser

### Optional Variables

#### NODE_ENV
- **Description**: Node.js environment
- **Format**: `development`, `production`, `test`
- **Example**: `production`
- **Required**: No
- **Default**: `development`
- **Note**: Automatically set by Next.js build process

---

## Docker Compose Variables

These variables are used in `docker-compose.yml` and should be set in the `.env` file at the project root.

### ANTHROPIC_API_KEY
- **Description**: Anthropic API key (passed to backend)
- **Required**: Yes
- **Example**: `sk-ant-api03-1234567890abcdef...`

### SECRET_KEY
- **Description**: Secret key (passed to backend)
- **Required**: Yes
- **Example**: `your-secret-key-here-change-in-production`

### DEBUG
- **Description**: Debug mode (passed to backend)
- **Required**: No
- **Default**: `True`

### LOG_LEVEL
- **Description**: Logging level (passed to backend)
- **Required**: No
- **Default**: `INFO`

---

## Database Variables

### PostgreSQL Configuration

#### POSTGRES_USER
- **Description**: PostgreSQL username
- **Format**: String
- **Example**: `edurisk`
- **Required**: No (set in docker-compose.yml)
- **Default**: `edurisk`

#### POSTGRES_PASSWORD
- **Description**: PostgreSQL password
- **Format**: String
- **Example**: `edurisk_password`
- **Required**: No (set in docker-compose.yml)
- **Default**: `edurisk_password`
- **Note**: Change in production!

#### POSTGRES_DB
- **Description**: PostgreSQL database name
- **Format**: String
- **Example**: `edurisk_db`
- **Required**: No (set in docker-compose.yml)
- **Default**: `edurisk_db`

---

## Redis Variables

Redis configuration is typically set in `docker-compose.yml` and doesn't require additional environment variables for basic usage.

For advanced Redis configuration, you can set:

#### REDIS_PASSWORD
- **Description**: Redis password (if authentication enabled)
- **Format**: String
- **Example**: `redis_password_here`
- **Required**: No
- **Default**: None (no authentication)

#### REDIS_MAXMEMORY
- **Description**: Maximum memory for Redis
- **Format**: Size with unit (e.g., `256mb`, `1gb`)
- **Example**: `512mb`
- **Required**: No
- **Default**: None (unlimited)

---

## Security Variables

### SECRET_KEY Generation

Generate a secure secret key:

```bash
# Python
python -c "import secrets; print(secrets.token_urlsafe(32))"

# OpenSSL
openssl rand -base64 32

# Node.js
node -e "console.log(require('crypto').randomBytes(32).toString('base64'))"
```

### Password Generation

Generate secure passwords:

```bash
# OpenSSL
openssl rand -base64 32

# Python
python -c "import secrets; print(secrets.token_urlsafe(24))"
```

---

## Logging Variables

### LOG_LEVEL Options

| Level | Description | Use Case |
|-------|-------------|----------|
| DEBUG | Detailed diagnostic information | Development, troubleshooting |
| INFO | General informational messages | Production (default) |
| WARNING | Warning messages for potential issues | Production |
| ERROR | Error messages for failures | Production |
| CRITICAL | Critical errors requiring immediate attention | Production |

### LOG_JSON_FORMAT

When enabled (`True`), logs are output in JSON format:

```json
{
  "timestamp": "2025-01-15T10:30:00Z",
  "level": "INFO",
  "logger": "backend.services.prediction_service",
  "message": "Prediction generated",
  "context": {
    "student_id": "550e8400-e29b-41d4-a716-446655440000",
    "risk_score": 45
  }
}
```

When disabled (`False`), logs use standard format:

```
2025-01-15 10:30:00 INFO backend.services.prediction_service: Prediction generated
```

---

## ML Model Variables

### ML_MODEL_PATH

This variable points to the directory containing trained ML models:

**Expected files:**
- `placement_model_3m.pkl` - 3-month placement model
- `placement_model_6m.pkl` - 6-month placement model
- `placement_model_12m.pkl` - 12-month placement model
- `salary_model.pkl` - Salary prediction model
- `version.json` - Model version metadata
- `feature_names.json` - Feature names list

**Docker setup:**
```yaml
volumes:
  - ./ml/models:/app/ml/models:ro
```

**Local setup:**
```env
ML_MODEL_PATH=./ml/models
```

---

## API Configuration

### CORS Configuration

CORS (Cross-Origin Resource Sharing) allows the frontend to communicate with the backend API.

**Single origin:**
```env
CORS_ORIGINS=http://localhost:3000
```

**Multiple origins:**
```env
CORS_ORIGINS=http://localhost:3000,https://app.example.com,https://www.example.com
```

**Wildcard (NOT recommended for production):**
```env
CORS_ORIGINS=*
```

### Rate Limiting

Rate limits are configured in the code (`backend/middleware/rate_limit.py`) but can be overridden with environment variables if needed:

```env
RATE_LIMIT_PREDICT=100  # requests per minute
RATE_LIMIT_BATCH=10     # requests per minute
RATE_LIMIT_GET=300      # requests per minute
```

---

## Examples

### Development Environment (.env)

```env
# API Keys
ANTHROPIC_API_KEY=sk-ant-api03-dev-key-here

# Security
SECRET_KEY=dev-secret-key-change-me

# Application
DEBUG=True
LOG_LEVEL=DEBUG
LOG_JSON_FORMAT=False

# Database (using Docker defaults)
DATABASE_URL=postgresql+asyncpg://edurisk:edurisk_password@localhost:5432/edurisk_db
REDIS_URL=redis://localhost:6379/0

# ML Models
ML_MODEL_PATH=./ml/models

# CORS
CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000

# Server
HOST=0.0.0.0
PORT=8000
```

### Production Environment (.env)

```env
# API Keys
ANTHROPIC_API_KEY=sk-ant-api03-prod-key-here

# Security (CHANGE THESE!)
SECRET_KEY=prod-secret-key-generated-with-secrets-module

# Application
DEBUG=False
LOG_LEVEL=INFO
LOG_JSON_FORMAT=True

# Database (use managed service)
DATABASE_URL=postgresql+asyncpg://edurisk:STRONG_PASSWORD@prod-db.example.com:5432/edurisk_db
REDIS_URL=redis://prod-redis.example.com:6379/0

# ML Models
ML_MODEL_PATH=/app/ml/models

# CORS (production domains only)
CORS_ORIGINS=https://app.example.com,https://www.example.com

# Server
HOST=0.0.0.0
PORT=8000
```

### Docker Compose (.env)

```env
# API Keys
ANTHROPIC_API_KEY=sk-ant-api03-your-key-here

# Security
SECRET_KEY=your-secret-key-here

# Application
DEBUG=True
LOG_LEVEL=INFO

# Note: Database and Redis URLs are configured in docker-compose.yml
# Frontend API URL is also configured in docker-compose.yml
```

### Frontend (.env.local)

```env
# Backend API URL
NEXT_PUBLIC_API_URL=http://localhost:8000

# For production:
# NEXT_PUBLIC_API_URL=https://api.example.com
```

### Backend Local Development (backend/.env)

```env
# Database
DATABASE_URL=postgresql+asyncpg://edurisk:edurisk_password@localhost:5432/edurisk_db

# Redis
REDIS_URL=redis://localhost:6379/0

# API Keys
ANTHROPIC_API_KEY=sk-ant-api03-your-key-here

# Security
SECRET_KEY=dev-secret-key

# ML Models
ML_MODEL_PATH=../ml/models

# Application
DEBUG=True
LOG_LEVEL=DEBUG
LOG_JSON_FORMAT=False

# CORS
CORS_ORIGINS=http://localhost:3000

# Server
HOST=0.0.0.0
PORT=8000
```

---

## Environment Variable Precedence

Environment variables are loaded in the following order (later sources override earlier ones):

1. **System environment variables**
2. **`.env` file** (project root for Docker Compose)
3. **`backend/.env` file** (for backend when running locally)
4. **`frontend/.env.local` file** (for frontend)
5. **Command-line arguments** (highest priority)

---

## Validation

### Check Environment Variables

**Backend:**
```bash
cd backend
python -c "from config import get_config; config = get_config(); print(config)"
```

**Frontend:**
```bash
cd frontend
npm run env-check  # If you have this script
```

**Docker:**
```bash
docker-compose config
```

### Test Configuration

**Backend:**
```bash
cd backend
python test_config.py
```

**Integration:**
```bash
python test_integration.py
```

---

## Troubleshooting

### Common Issues

**1. "ANTHROPIC_API_KEY variable is not set"**
- Create `.env` file from `.env.example`
- Add your Anthropic API key
- Restart services

**2. "Database connection failed"**
- Check `DATABASE_URL` format
- Verify database is running
- Check credentials

**3. "CORS error in frontend"**
- Add frontend URL to `CORS_ORIGINS`
- Restart backend
- Clear browser cache

**4. "Models not found"**
- Check `ML_MODEL_PATH` points to correct directory
- Verify model files exist
- Train models if missing

### Debug Environment

Enable debug mode to see all environment variables:

```bash
# Backend
cd backend
python -c "import os; print('\n'.join(f'{k}={v}' for k, v in os.environ.items() if 'EDURISK' in k or 'DATABASE' in k or 'REDIS' in k))"

# Docker
docker-compose exec backend env | grep -E 'DATABASE|REDIS|ANTHROPIC|SECRET'
```

---

## Security Best Practices

1. **Never commit `.env` files** to version control
2. **Use strong, unique passwords** for production
3. **Rotate secrets regularly** (every 90 days)
4. **Use secrets management** (AWS Secrets Manager, HashiCorp Vault)
5. **Limit CORS origins** to known domains
6. **Enable HTTPS** in production
7. **Use environment-specific keys** (dev, staging, prod)
8. **Audit access** to environment variables
9. **Encrypt backups** containing environment data
10. **Monitor for leaked secrets** (GitHub secret scanning)

---

## References

- [FastAPI Settings Management](https://fastapi.tiangolo.com/advanced/settings/)
- [Next.js Environment Variables](https://nextjs.org/docs/basic-features/environment-variables)
- [Docker Compose Environment Variables](https://docs.docker.com/compose/environment-variables/)
- [Twelve-Factor App Config](https://12factor.net/config)

---

**Last Updated:** January 2025
