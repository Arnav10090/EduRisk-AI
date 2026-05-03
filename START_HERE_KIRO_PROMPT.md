# 🚀 Start Here - Kiro Prompt for EduRisk AI Improvements

Copy and paste this entire prompt into Kiro to begin implementing the improvements:

---

# Make EduRisk AI Submission-Ready

## Context
I have an EduRisk AI project (AI-powered placement risk assessment for education loans) that received a comprehensive code review from Claude Sonnet 4.6. The project is currently functional (7.5/10) but needs critical fixes and improvements to be submission-ready for a hackathon (target: 9.5/10).

**Tech Stack**: FastAPI (Python), Next.js 14 (TypeScript), PostgreSQL, Redis, Docker, Groq API

**Review Files Available**:
- `EduRisk_AI_Comprehensive_Review.md` - Full review from Claude
- `KIRO_IMPLEMENTATION_PLAN.md` - Detailed task breakdown
- `REVIEW_SUMMARY.md` - Executive summary

---

## 🎯 Your Mission

Implement improvements in 3 phases, starting with critical fixes. Work systematically through each task, testing after each change.

---

## 📋 Phase 1: Critical Fixes (START HERE)

### Task 1.1: Fix ML Model Availability at Startup ⚠️ MOST CRITICAL

**Problem**: Docker health check fails because ML model `.pkl` files are missing. Demo is broken on first boot.

**Solution**: Modify `docker/start-backend.sh` to automatically train models if they don't exist.

**Steps**:
1. Read `docker/start-backend.sh`
2. Add model check and training logic after database initialization
3. Ensure models are trained before starting FastAPI

**Code to add** (after database init, before starting uvicorn):
```bash
echo ""
echo "📦 Checking ML models..."
if [ ! -f /app/ml/models/placement_model_3m.pkl ]; then
    echo "⚠️  ML models not found. Training models with synthetic data..."
    echo "   This will take 1-2 minutes on first boot..."
    
    # Generate synthetic training data
    python /app/ml/data/generate_synthetic.py
    
    # Train models quickly
    python /app/ml/pipeline/train_quick.py
    
    echo "✅ ML models trained successfully"
else
    echo "✅ ML models found and ready"
fi
```

**Acceptance Criteria**:
- [ ] Health check returns `ml_models: available` on first boot
- [ ] All 4 models exist after training
- [ ] Training completes in <2 minutes
- [ ] Startup script shows clear progress messages

---

### Task 1.2: Add API Key Authentication ⚠️ CRITICAL SECURITY

**Problem**: All API endpoints are completely open. No authentication whatsoever.

**Solution**: Create API key middleware and require `X-API-Key` header for all endpoints except health/docs.

**Steps**:
1. Create `backend/middleware/api_key_auth.py`
2. Add middleware to `backend/main.py`
3. Update `.env.example` with `API_KEY` variable
4. Update `docker-compose.yml` environment variables
5. Document in README

**Code for `backend/middleware/api_key_auth.py`**:
```python
"""
API Key Authentication Middleware

Requires X-API-Key header for all endpoints except:
- /api/health (health check)
- /docs (API documentation)
- /redoc (alternative docs)
- /openapi.json (OpenAPI schema)
- / (root)
"""

from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
import os
import logging

logger = logging.getLogger(__name__)

class ApiKeyMiddleware(BaseHTTPMiddleware):
    """Middleware to enforce API key authentication"""
    
    PUBLIC_PATHS = {"/api/health", "/docs", "/redoc", "/openapi.json", "/"}
    
    async def dispatch(self, request: Request, call_next):
        # Allow public endpoints
        if request.url.path in self.PUBLIC_PATHS:
            return await call_next(request)
        
        # Get expected API key from environment
        expected_key = os.getenv("API_KEY", "")
        
        # If no API key is configured, allow all requests (development mode)
        if not expected_key:
            logger.warning("API_KEY not configured - authentication disabled")
            return await call_next(request)
        
        # Check for API key in request headers
        provided_key = request.headers.get("X-API-Key")
        
        if not provided_key:
            raise HTTPException(
                status_code=401,
                detail="Missing API key. Include X-API-Key header in your request."
            )
        
        if provided_key != expected_key:
            logger.warning(f"Invalid API key attempt from {request.client.host}")
            raise HTTPException(
                status_code=401,
                detail="Invalid API key"
            )
        
        # API key is valid, proceed with request
        return await call_next(request)
```

**Add to `backend/main.py`** (after CORS, before other middleware):
```python
from backend.middleware.api_key_auth import ApiKeyMiddleware

# Add API key authentication
app.add_middleware(ApiKeyMiddleware)
```

**Add to `.env.example`**:
```
# API Authentication
API_KEY=your_secure_api_key_here_change_in_production
```

**Add to `docker-compose.yml`** (backend environment):
```yaml
API_KEY: ${API_KEY:-demo_api_key_12345}
```

**Acceptance Criteria**:
- [ ] All API endpoints require X-API-Key header
- [ ] Health check and docs remain public
- [ ] Invalid key returns HTTP 401
- [ ] Missing key returns HTTP 401 with helpful message
- [ ] README documents API key usage

---

### Task 1.3: Fix README Environment Variable Inconsistency

**Problem**: README says `ANTHROPIC_API_KEY` but code uses `LLM_API_KEY` and `LLM_PROVIDER=groq`.

**Solution**: Update README to match actual `.env.example`.

**Steps**:
1. Read `README.md`
2. Find all references to `ANTHROPIC_API_KEY`
3. Replace with `LLM_API_KEY` and `LLM_PROVIDER`
4. Clarify that LLM is optional (graceful degradation)

**Changes needed**:
- Replace `ANTHROPIC_API_KEY=your_anthropic_api_key_here` with `LLM_API_KEY=your_groq_api_key_here`
- Add `LLM_PROVIDER=groq` to environment variable list
- Add note: "LLM integration is optional. If no API key is provided, the system will use a fallback summary message."
- Update example `.env` snippet to match `.env.example` exactly

**Acceptance Criteria**:
- [ ] No references to ANTHROPIC_API_KEY remain
- [ ] LLM_API_KEY and LLM_PROVIDER documented
- [ ] Fallback behavior explained
- [ ] Example .env matches actual .env.example

---

### Task 1.4: Fix alembic.ini Database URL

**Problem**: `alembic.ini` has hardcoded `localhost` URL, won't work in Docker.

**Solution**: Make Alembic read `DATABASE_URL` from environment.

**Steps**:
1. Read `backend/alembic/env.py`
2. Add code to override database URL from environment
3. Test that migrations work in Docker

**Code to add to `backend/alembic/env.py`** (near the top, after imports):
```python
# Override database URL from environment
from backend.config import get_config
try:
    config_obj = get_config()
    config.set_main_option("sqlalchemy.url", config_obj.database_url)
except Exception as e:
    # If config fails, fall back to alembic.ini value
    import sys
    print(f"Warning: Could not load database URL from config: {e}", file=sys.stderr)
```

**Acceptance Criteria**:
- [ ] Alembic reads DATABASE_URL from environment
- [ ] Migrations work inside Docker container
- [ ] No hardcoded localhost URLs

---

### Task 1.5: Set DEBUG=False in Production

**Problem**: `DEBUG=True` exposes stack traces in HTTP responses.

**Solution**: Update default environment files to use `DEBUG=False`.

**Steps**:
1. Update `.env.example` to set `DEBUG=False`
2. Update `docker-compose.yml` to default to `DEBUG=False`
3. Add comment explaining when to use DEBUG=True

**Changes**:
- `.env.example`: `DEBUG=False  # Set to True only for local development`
- `docker-compose.yml`: `DEBUG: ${DEBUG:-False}`

**Acceptance Criteria**:
- [ ] Production defaults to DEBUG=False
- [ ] Documentation explains DEBUG flag
- [ ] Stack traces not exposed in production

---

### Task 1.6: Add Audit Logging to Explain Endpoint

**Problem**: `/api/explain` endpoint doesn't log to audit trail (compliance gap).

**Solution**: Add audit log call to explain route.

**Steps**:
1. Read `backend/routes/explain.py`
2. Import `AuditLogger`
3. Add log call after retrieving prediction

**Code to add** (after `prediction = ...` line):
```python
# Log EXPLAIN action to audit trail (Requirement 14.2)
await AuditLogger.log_explain(
    db=db,
    student_id=student_id,
    prediction_id=prediction.id,
    performed_by="api_user"  # TODO: Replace with actual user ID when auth is implemented
)
```

**Acceptance Criteria**:
- [ ] EXPLAIN actions logged to audit_logs table
- [ ] Log includes student_id, prediction_id, performed_by
- [ ] Audit trail query shows EXPLAIN actions

---

## ✅ Phase 1 Complete Checklist

After completing all Phase 1 tasks, verify:

- [ ] `docker-compose up --build` succeeds
- [ ] Health check returns `ml_models: available`
- [ ] API requires X-API-Key header
- [ ] README setup instructions work correctly
- [ ] Alembic migrations work in Docker
- [ ] DEBUG=False in production
- [ ] Explain endpoint logs to audit trail

**Test command**:
```bash
# Rebuild and start
docker-compose down -v
docker-compose up --build

# In another terminal, test health check
curl http://127.0.0.1:8000/api/health

# Test API key requirement
curl http://127.0.0.1:8000/api/students
# Should return 401

curl -H "X-API-Key: demo_api_key_12345" http://127.0.0.1:8000/api/students
# Should return 200
```

---

## 🎯 After Phase 1

Once Phase 1 is complete, let me know and I'll provide Phase 2 tasks (navigation, UX improvements, testing).

**Estimated time for Phase 1**: 4-6 hours

---

## 📝 Implementation Guidelines

For each task:
1. **Read relevant files first** - Understand current code
2. **Make incremental changes** - One task at a time
3. **Test after each change** - Ensure nothing breaks
4. **Update documentation** - Keep README current
5. **Commit with clear messages** - e.g., "feat: add API key authentication"

---

## 🚀 Let's Start!

**Begin with Task 1.1: Fix ML Model Availability**

This is the most critical issue. Without it, the demo is completely broken.

Ready? Let's make this project submission-ready! 💪
