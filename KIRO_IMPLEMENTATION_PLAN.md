# EduRisk AI - Kiro Implementation Plan
## Based on Claude Sonnet 4.6 Comprehensive Review

**Project Rating**: 7.5/10 → Target: 9.5/10  
**Estimated Total Effort**: 12-18 hours  
**Priority**: Make submission-ready for TenzorX 2026 Hackathon

---

## 🚨 Phase 1: Critical Fixes (MUST DO - 4-6 hours)

### Task 1.1: Fix ML Model Availability at Startup
**Priority**: CRITICAL  
**Estimated Time**: 1-2 hours  
**Issue**: Docker container health check fails because `.pkl` model files are missing

**Implementation Steps**:
1. Modify `docker/start-backend.sh` to check for model files and train if missing
2. Add model training to Docker startup sequence
3. Ensure health check passes after training

**Files to Modify**:
- `docker/start-backend.sh`
- `docker/Dockerfile.backend` (add training dependencies if needed)

**Acceptance Criteria**:
- [ ] Health check returns `ml_models: available` on first boot
- [ ] Models are trained automatically if missing
- [ ] Training completes in <2 minutes
- [ ] All 4 models exist: `placement_model_3m.pkl`, `placement_model_6m.pkl`, `placement_model_12m.pkl`, `salary_model.pkl`

**Code to Add**:
```bash
# In docker/start-backend.sh, after database init:
echo "📦 Checking ML models..."
if [ ! -f /app/ml/models/placement_model_3m.pkl ]; then
    echo "⚠️  ML models not found. Training models..."
    python /app/ml/data/generate_synthetic.py
    python /app/ml/pipeline/train_quick.py
    echo "✅ ML models trained successfully"
else
    echo "✅ ML models found"
fi
```

---

### Task 1.2: Add API Key Authentication
**Priority**: CRITICAL  
**Estimated Time**: 30-45 minutes  
**Issue**: All API endpoints are completely open with no authentication

**Implementation Steps**:
1. Create `backend/middleware/api_key_auth.py`
2. Add API key middleware to `backend/main.py`
3. Update `.env.example` with `API_KEY` variable
4. Update `docker-compose.yml` with `API_KEY` environment variable
5. Document in README

**Files to Create**:
- `backend/middleware/api_key_auth.py`

**Files to Modify**:
- `backend/main.py`
- `.env.example`
- `docker-compose.yml`
- `README.md`

**Acceptance Criteria**:
- [ ] All API endpoints (except `/api/health`, `/docs`, `/redoc`, `/`) require `X-API-Key` header
- [ ] Invalid/missing API key returns HTTP 401
- [ ] Health check and docs remain publicly accessible
- [ ] README documents how to use API key

**Code to Add**:
```python
# backend/middleware/api_key_auth.py
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
import os

class ApiKeyMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Public endpoints
        if request.url.path in ["/api/health", "/docs", "/redoc", "/openapi.json", "/"]:
            return await call_next(request)
        
        # Check API key
        api_key = request.headers.get("X-API-Key")
        expected = os.getenv("API_KEY", "")
        
        if not expected:
            # If no API key is configured, allow all requests (dev mode)
            return await call_next(request)
        
        if api_key != expected:
            raise HTTPException(
                status_code=401,
                detail="Invalid or missing API key. Include X-API-Key header."
            )
        
        return await call_next(request)
```

---

### Task 1.3: Fix README Environment Variable Inconsistency
**Priority**: CRITICAL  
**Estimated Time**: 15 minutes  
**Issue**: README references `ANTHROPIC_API_KEY` but code uses `LLM_API_KEY` and `LLM_PROVIDER`

**Files to Modify**:
- `README.md`

**Acceptance Criteria**:
- [ ] README setup section matches `.env.example` exactly
- [ ] All environment variables are documented correctly
- [ ] LLM configuration is clear (Groq vs Anthropic)
- [ ] Fallback behavior is documented

**Changes Needed**:
1. Replace all `ANTHROPIC_API_KEY` references with `LLM_API_KEY`
2. Add `LLM_PROVIDER=groq` to setup instructions
3. Clarify that LLM is optional (system degrades gracefully)
4. Update example `.env` snippet in README

---

### Task 1.4: Fix alembic.ini Database URL
**Priority**: HIGH  
**Estimated Time**: 10 minutes  
**Issue**: `alembic.ini` has hardcoded localhost URL, won't work in Docker

**Files to Modify**:
- `backend/alembic/env.py`

**Acceptance Criteria**:
- [ ] Alembic reads `DATABASE_URL` from environment
- [ ] Migrations work inside Docker container
- [ ] No hardcoded database URLs remain

**Code to Add**:
```python
# In backend/alembic/env.py, before run_migrations_online():
from backend.config import get_config
config_obj = get_config()
config.set_main_option("sqlalchemy.url", config_obj.database_url)
```

---

### Task 1.5: Set DEBUG=False in Production Environment
**Priority**: HIGH  
**Estimated Time**: 15 minutes  
**Issue**: `DEBUG=True` exposes stack traces in production

**Files to Modify**:
- `.env.example`
- `docker-compose.yml`
- Create `docker-compose.prod.yml`

**Acceptance Criteria**:
- [ ] `.env.example` has `DEBUG=False` by default
- [ ] Production docker-compose file exists
- [ ] README documents production vs development modes

---

### Task 1.6: Add Audit Logging to Explain Endpoint
**Priority**: HIGH  
**Estimated Time**: 10 minutes  
**Issue**: `/api/explain` doesn't log to audit trail (compliance gap)

**Files to Modify**:
- `backend/routes/explain.py`

**Acceptance Criteria**:
- [ ] EXPLAIN actions are logged to audit_logs table
- [ ] Log includes student_id, prediction_id, performed_by

**Code to Add**:
```python
# In backend/routes/explain.py, after retrieving prediction:
await AuditLogger.log_explain(
    db=db,
    student_id=student_id,
    prediction_id=prediction.id,
    performed_by="api_user"  # TODO: Replace with actual user when auth is added
)
```

---

## ⚡ Phase 2: Important Improvements (SHOULD DO - 5-8 hours)

### Task 2.1: Add Navigation Bar to Frontend
**Priority**: HIGH  
**Estimated Time**: 2 hours  
**Issue**: No navigation between pages, poor UX

**Implementation Steps**:
1. Create `frontend/components/layout/Navigation.tsx`
2. Create `frontend/components/layout/Layout.tsx`
3. Wrap all pages with Layout component
4. Add links to Dashboard, Alerts, New Student, API Docs

**Files to Create**:
- `frontend/components/layout/Navigation.tsx`
- `frontend/components/layout/Layout.tsx`

**Files to Modify**:
- `frontend/app/layout.tsx`

**Acceptance Criteria**:
- [ ] Navigation bar appears on all pages
- [ ] Active page is highlighted
- [ ] Alert badge shows count of high-risk alerts
- [ ] Responsive on mobile

---

### Task 2.2: Add "New Prediction" Button to Dashboard
**Priority**: HIGH  
**Estimated Time**: 15 minutes  
**Issue**: `/student/new` page exists but no way to discover it

**Files to Modify**:
- `frontend/app/dashboard/page.tsx`

**Acceptance Criteria**:
- [ ] "Add Student" button visible in dashboard header
- [ ] Button links to `/student/new`
- [ ] Button has appropriate icon

---

### Task 2.3: Fix Batch Scoring Database Session Issue
**Priority**: HIGH  
**Estimated Time**: 30 minutes  
**Issue**: Concurrent batch requests share same DB session (race condition)

**Files to Modify**:
- `backend/routes/predict.py` (`predict_batch` function)

**Acceptance Criteria**:
- [ ] Each batch item gets its own database session
- [ ] No concurrent session corruption
- [ ] Batch processing still uses asyncio.gather for parallelism

**Code to Fix**:
```python
# In backend/routes/predict.py, predict_batch function:
async def process_one_student(student_data: dict):
    async with async_session_maker() as db:
        try:
            student = StudentCreate(**student_data)
            result = await prediction_service.predict_student(student, db)
            return {"success": True, "data": result}
        except Exception as e:
            return {"success": False, "error": str(e), "student": student_data}

tasks = [process_one_student(s) for s in students]
results = await asyncio.gather(*tasks, return_exceptions=True)
```

---

### Task 2.4: Add Unit Tests for Risk Calculator
**Priority**: HIGH  
**Estimated Time**: 1 hour  
**Issue**: Core functions have no tests

**Files to Create**:
- `backend/services/test_risk_calculator_unit.py`
- `backend/services/test_action_recommender_unit.py`

**Acceptance Criteria**:
- [ ] Test `calculate_risk_score()` with various inputs
- [ ] Test `assign_risk_level()` boundary conditions
- [ ] Test `calculate_emi_affordability()` edge cases
- [ ] Test action recommender rules
- [ ] All tests pass with pytest

---

### Task 2.5: Add EMI Context to Salary Card
**Priority**: MEDIUM  
**Estimated Time**: 30 minutes  
**Issue**: Salary range shown without EMI affordability context

**Files to Modify**:
- `frontend/components/student/SalaryRangeCard.tsx`

**Acceptance Criteria**:
- [ ] EMI affordability percentage displayed
- [ ] Color indicator (green <30%, amber 30-50%, red >50%)
- [ ] Tooltip explains what affordability means

---

### Task 2.6: Add Risk Score Gauge Visualization
**Priority**: MEDIUM  
**Estimated Time**: 1 hour  
**Issue**: Risk score is just a number, not intuitive

**Files to Modify**:
- `frontend/components/student/RiskScoreDisplay.tsx`

**Acceptance Criteria**:
- [ ] Circular gauge shows risk score 0-100
- [ ] Color zones: 0-33 green, 34-66 amber, 67-100 red
- [ ] Animated on load
- [ ] Responsive design

---

### Task 2.7: Add Empty State to Dashboard
**Priority**: MEDIUM  
**Estimated Time**: 30 minutes  
**Issue**: Empty dashboard has no call-to-action

**Files to Modify**:
- `frontend/app/dashboard/page.tsx`

**Acceptance Criteria**:
- [ ] When no students exist, show friendly empty state
- [ ] "Add Your First Student" button links to `/student/new`
- [ ] Includes helpful text about getting started

---

## 🎨 Phase 3: Nice-to-Have Enhancements (OPTIONAL - 3-5 hours)

### Task 3.1: Add CSV Batch Upload UI
**Priority**: MEDIUM  
**Estimated Time**: 2 hours  
**Issue**: Backend batch endpoint has no frontend

**Files to Create**:
- `frontend/app/student/batch/page.tsx`

**Acceptance Criteria**:
- [ ] File upload component for CSV
- [ ] Preview table of parsed students
- [ ] Submit button calls `/api/batch-score`
- [ ] Progress indicator during upload
- [ ] Results summary after completion

---

### Task 3.2: Add Risk Score Trend Chart
**Priority**: MEDIUM  
**Estimated Time**: 1.5 hours  
**Issue**: No visualization of prediction history

**Files to Modify**:
- `frontend/app/student/[id]/page.tsx`

**Acceptance Criteria**:
- [ ] Line chart shows risk score over time
- [ ] Uses data from `/api/students/{id}/predictions`
- [ ] Shows trend direction (improving/declining)

---

### Task 3.3: Optimize Docker Build with Multi-Stage
**Priority**: LOW  
**Estimated Time**: 1 hour  
**Issue**: Backend Docker image is 2-3 GB

**Files to Modify**:
- `docker/Dockerfile.backend`

**Acceptance Criteria**:
- [ ] Multi-stage build separates builder and runtime
- [ ] Final image size <1 GB
- [ ] Build time improved with layer caching

---

### Task 3.4: Add Pagination to Student Table
**Priority**: LOW  
**Estimated Time**: 1 hour  
**Issue**: Can only see first 100 students

**Files to Modify**:
- `frontend/app/dashboard/page.tsx`
- `frontend/components/dashboard/StudentTable.tsx`

**Acceptance Criteria**:
- [ ] Page controls (Previous/Next)
- [ ] Page size selector (20/50/100)
- [ ] Total count displayed

---

### Task 3.5: Add Integration Tests
**Priority**: LOW  
**Estimated Time**: 2 hours  
**Issue**: No automated API tests

**Files to Create**:
- `backend/tests/test_api_integration.py`

**Acceptance Criteria**:
- [ ] Test each API endpoint (happy path)
- [ ] Test error cases (400, 404, 500)
- [ ] Use FastAPI TestClient
- [ ] Tests run in CI

---

## 📋 Implementation Order

### Day 1 (4-6 hours): Critical Fixes
1. Task 1.1: ML Model Availability (1-2 hours)
2. Task 1.2: API Key Authentication (45 min)
3. Task 1.3: README Fix (15 min)
4. Task 1.4: Alembic Fix (10 min)
5. Task 1.5: DEBUG=False (15 min)
6. Task 1.6: Audit Logging (10 min)

### Day 2 (5-8 hours): Important Improvements
7. Task 2.1: Navigation Bar (2 hours)
8. Task 2.2: New Prediction Button (15 min)
9. Task 2.3: Batch Session Fix (30 min)
10. Task 2.4: Unit Tests (1 hour)
11. Task 2.5: EMI Context (30 min)
12. Task 2.6: Risk Gauge (1 hour)
13. Task 2.7: Empty State (30 min)

### Day 3 (Optional - 3-5 hours): Enhancements
14. Task 3.1: Batch Upload UI (2 hours)
15. Task 3.2: Trend Chart (1.5 hours)
16. Task 3.3: Docker Optimization (1 hour)
17. Task 3.4: Pagination (1 hour)
18. Task 3.5: Integration Tests (2 hours)

---

## 🎯 Success Criteria

Project is submission-ready when:
- [ ] All Phase 1 tasks complete (6/6)
- [ ] At least 5/7 Phase 2 tasks complete
- [ ] Health check passes on first boot
- [ ] API requires authentication
- [ ] README is accurate and complete
- [ ] Navigation works across all pages
- [ ] Dashboard has empty state
- [ ] No critical security issues
- [ ] Code quality is professional
- [ ] Demo is impressive and polished

---

## 🚀 Let's Start!

**Begin with Phase 1, Task 1.1: Fix ML Model Availability**

This is the most critical issue - without it, the demo is broken. Let's make sure models are trained automatically on first boot.

Ready to start implementing?
