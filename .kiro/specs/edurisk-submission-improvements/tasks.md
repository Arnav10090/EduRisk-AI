# Implementation Tasks: EduRisk AI Submission Improvements

## Overview

This document outlines the implementation tasks for 32 critical improvements to the EduRisk AI platform, organized into 3 phases based on priority. Each task includes sub-tasks for implementation, testing, and documentation.

**Total Requirements**: 32 across 3 phases
**Estimated Effort**: 40-50 hours total
**Tech Stack**: FastAPI (Python), Next.js 14 (TypeScript), PostgreSQL, Redis, Docker, XGBoost, SHAP, Groq API

## Task Status Legend

- `[ ]` Not started
- `[-]` In progress
- `[x]` Completed
- `[~]` Queued

## Phase 1: Critical Fixes (MUST DO)

Priority: CRITICAL | Estimated: 16-20 hours | Requirements: 1-6, 20-22, 25-26

### Task 1: ML Model Auto-Training on Startup (Requirement 1)

**Goal**: Ensure ML models are automatically trained on first boot if missing, enabling zero-configuration deployment.

**Files**: `docker/start-backend.sh`, `ml/pipeline/train_all.py`, `backend/routes/health.py`

- [x] 1.1 Modify startup script to check for model files
  - [x] 1.1.1 Add Python inline check for 4 model files (placement_model_3m.pkl, placement_model_6m.pkl, placement_model_12m.pkl, salary_model.pkl)
  - [x] 1.1.2 Implement conditional training trigger if models missing
  - [x] 1.1.3 Add 120-second timeout for training process
  - [x] 1.1.4 Add success/failure logging with emoji indicators
- [x] 1.2 Update health endpoint to report ML model status
  - [x] 1.2.1 Add `ml_models: available` field to health check response
  - [x] 1.2.2 Verify model files exist before returning status
- [x] 1.3 Test startup behavior
  - [x] 1.3.1 Test first boot without models (should auto-train)
  - [x] 1.3.2 Test subsequent boot with models (should skip training)
  - [x] 1.3.3 Verify training completes within 120 seconds
  - [x] 1.3.4 Verify FastAPI server doesn't start if training fails

---

### Task 2: API Key Authentication Middleware (Requirement 2)

**Goal**: Secure all API endpoints except public documentation with API key authentication.

**Files**: `backend/middleware/api_key_auth.py` (new), `backend/main.py`, `.env.example`
c  
- [x] 2.1 Create API key middleware
  - [x] 2.1.1 Create `backend/middleware/api_key_auth.py`
  - [x] 2.1.2 Implement `ApiKeyMiddleware` class extending `BaseHTTPMiddleware`
  - [x] 2.1.3 Define public paths: /api/health, /docs, /redoc, /openapi.json, /
  - [x] 2.1.4 Implement X-API-Key header validation
  - [x] 2.1.5 Add client IP extraction for logging
  - [x] 2.1.6 Return 401 with descriptive messages for missing/invalid keys
- [x] 2.2 Integrate middleware in FastAPI app
  - [x] 2.2.1 Import `ApiKeyMiddleware` in `backend/main.py`
  - [x] 2.2.2 Add middleware with `app.add_middleware(ApiKeyMiddleware)`
- [x] 2.3 Update environment configuration
  - [x] 2.3.1 Add `API_KEY` to `.env.example` with placeholder value
  - [x] 2.3.2 Add `API_KEY` to `docker-compose.yml` environment section
- [x] 2.4 Test authentication
  - [x] 2.4.1 Test protected endpoint with valid API key (should succeed)
  - [x] 2.4.2 Test protected endpoint without API key (should return 401)
  - [x] 2.4.3 Test protected endpoint with invalid API key (should return 401)
  - [x] 2.4.4 Test public endpoints without API key (should succeed)
  - [x] 2.4.5 Verify warning logged when API_KEY not configured

---

### Task 3: Environment Variable Documentation (Requirement 3)

**Goal**: Update all documentation to accurately reflect environment variables used by the code.

**Files**: `README.md`, `.env.example`, `ENVIRONMENT_VARIABLES.md`

- [x] 3.1 Update README.md
  - [x] 3.1.1 Remove all references to ANTHROPIC_API_KEY
  - [x] 3.1.2 Document LLM_API_KEY for LLM integration
  - [x] 3.1.3 Document LLM_PROVIDER (groq or anthropic)
  - [x] 3.1.4 Document API_KEY for API authentication
  - [x] 3.1.5 Document DEBUG variable with usage guidance
  - [x] 3.1.6 Add note about optional LLM integration with graceful degradation
  - [x] 3.1.7 Provide .env snippet matching .env.example exactly
- [x] 3.2 Update .env.example
  - [x] 3.2.1 Remove ANTHROPIC_API_KEY
  - [x] 3.2.2 Add LLM_API_KEY with comment
  - [x] 3.2.3 Add LLM_PROVIDER with default value
  - [x] 3.2.4 Add API_KEY with placeholder
  - [x] 3.2.5 Ensure DEBUG=False with comment "Set to True only for local development"
- [x] 3.3 Update ENVIRONMENT_VARIABLES.md
  - [x] 3.3.1 Remove ANTHROPIC_API_KEY documentation
  - [x] 3.3.2 Add comprehensive LLM_API_KEY documentation
  - [x] 3.3.3 Add LLM_PROVIDER documentation
  - [x] 3.3.4 Add API_KEY documentation
  - [x] 3.3.5 Add DEBUG documentation with examples

---

### Task 4: Database Migration Configuration (Requirement 4)

**Goal**: Configure Alembic to use DATABASE_URL from environment variables for Docker compatibility.

**Files**: `backend/alembic/env.py`

- [x] 4.1 Modify Alembic environment configuration
  - [x] 4.1.1 Add `os.getenv("DATABASE_URL")` check in `backend/alembic/env.py`
  - [x] 4.1.2 Override `config.set_main_option("sqlalchemy.url", database_url)` when env var exists
  - [x] 4.1.3 Add logging for DATABASE_URL source (environment vs alembic.ini)
  - [x] 4.1.4 Add warning log if DATABASE_URL not found in environment
- [x] 4.2 Test migrations in Docker
  - [x] 4.2.1 Run `docker exec -it edurisk-backend alembic upgrade head`
  - [x] 4.2.2 Verify migrations apply successfully using DATABASE_URL from docker-compose.yml
  - [x] 4.2.3 Verify no hardcoded localhost URLs in alembic configuration

---

### Task 5: Production Debug Mode Configuration (Requirement 5)

**Goal**: Default to DEBUG=False to prevent stack trace exposure in production.

**Files**: `.env.example`, `docker-compose.yml`, `backend/config.py`

- [x] 5.1 Update default DEBUG configuration
  - [x] 5.1.1 Set DEBUG=False in `.env.example`
  - [x] 5.1.2 Add comment "Set to True only for local development"
  - [x] 5.1.3 Update `docker-compose.yml` to default DEBUG to False
- [x] 5.2 Verify error handling behavior
  - [x] 5.2.1 Test API error with DEBUG=False (should hide stack traces)
  - [x] 5.2.2 Test API error with DEBUG=True (should show stack traces)
  - [x] 5.2.3 Verify error responses don't leak sensitive information in production mode

---

### Task 6: Audit Logging for Explanation Requests (Requirement 6)

**Goal**: Log all SHAP explanation requests to the audit trail for compliance tracking.

**Files**: `backend/services/audit_logger.py`, `backend/routes/explain.py`

- [x] 6.1 Add log_explain method to AuditLogger
  - [x] 6.1.1 Create `log_explain()` static method in `backend/services/audit_logger.py`
  - [x] 6.1.2 Accept parameters: db, student_id, prediction_id, performed_by
  - [x] 6.1.3 Create AuditLog entry with action="EXPLAIN"
  - [x] 6.1.4 Include explanation_type="SHAP" in details
  - [x] 6.1.5 Record timestamp automatically
- [x] 6.2 Integrate logging in explain endpoint
  - [x] 6.2.1 Import AuditLogger in `backend/routes/explain.py`
  - [x] 6.2.2 Call `await AuditLogger.log_explain()` in GET /api/explain/{student_id}
  - [x] 6.2.3 Pass student_id, prediction_id, and performed_by="api_user"
  - [x] 6.2.4 Commit audit log entry to database
- [x] 6.3 Test audit logging
  - [x] 6.3.1 Request explanation for a student
  - [x] 6.3.2 Query audit_logs table and verify EXPLAIN action recorded
  - [x] 6.3.3 Verify student_id, prediction_id, and timestamp are correct
  - [x] 6.3.4 Verify EXPLAIN actions appear alongside PREDICT actions

---

### Task 7: JWT OAuth2 Authentication (Requirement 20)

**Goal**: Implement production-grade user authentication with JWT tokens.

**Files**: `backend/core/security.py` (new), `backend/routes/auth.py` (new), `backend/main.py`

- [x] 7.1 Create security utilities
  - [x] 7.1.1 Create `backend/core/security.py`
  - [x] 7.1.2 Implement `create_access_token(data: dict)` function
  - [x] 7.1.3 Implement `verify_token(token: str)` function
  - [x] 7.1.4 Implement `get_password_hash(password: str)` function
  - [x] 7.1.5 Implement `verify_password(plain, hashed)` function
  - [x] 7.1.6 Use SECRET_KEY from environment variables
  - [x] 7.1.7 Set JWT expiration to 24 hours
- [x] 7.2 Create authentication routes
  - [x] 7.2.1 Create `backend/routes/auth.py`
  - [x] 7.2.2 Implement POST /api/auth/login endpoint
  - [x] 7.2.3 Accept username and password in request body
  - [x] 7.2.4 Validate credentials against database
  - [x] 7.2.5 Return access_token and token_type="bearer" on success
  - [x] 7.2.6 Implement POST /api/auth/refresh endpoint for token renewal
  - [x] 7.2.7 Return 401 with "Invalid or expired token" for auth failures
- [x] 7.3 Create JWT dependency for protected routes
  - [x] 7.3.1 Create `get_current_user()` dependency function
  - [x] 7.3.2 Extract and validate JWT from Authorization header
  - [x] 7.3.3 Return user information from JWT payload
  - [x] 7.3.4 Raise 401 exception for invalid/expired tokens
- [x] 7.4 Update environment configuration
  - [x] 7.4.1 Add SECRET_KEY to `.env.example` with strong placeholder
  - [x] 7.4.2 Add comment warning to keep SECRET_KEY secure
- [x] 7.5 Test JWT authentication
  - [x] 7.5.1 Test login with valid credentials (should return JWT)
  - [x] 7.5.2 Test login with invalid credentials (should return 401)
  - [x] 7.5.3 Test protected endpoint with valid JWT (should succeed)
  - [x] 7.5.4 Test protected endpoint with expired JWT (should return 401)
  - [x] 7.5.5 Test token refresh endpoint
  - [x] 7.5.6 Verify JWTs and passwords are not logged

---

### Task 8: Secure Database Credentials (Requirement 21)

**Goal**: Remove hardcoded database passwords and use environment variables exclusively.

**Files**: `docker-compose.yml`, `.env.example`, `.gitignore`

- [x] 8.1 Update docker-compose.yml
  - [x] 8.1.1 Replace hardcoded POSTGRES_PASSWORD with ${POSTGRES_PASSWORD}
  - [x] 8.1.2 Replace hardcoded POSTGRES_USER with ${POSTGRES_USER}
  - [x] 8.1.3 Replace hardcoded POSTGRES_DB with ${POSTGRES_DB}
  - [x] 8.1.4 Verify no other hardcoded credentials exist
- [x] 8.2 Update .env.example
  - [x] 8.2.1 Add POSTGRES_PASSWORD with placeholder value
  - [x] 8.2.2 Add POSTGRES_USER with placeholder value
  - [x] 8.2.3 Add POSTGRES_DB with placeholder value
  - [x] 8.2.4 Add warning comment: "DO NOT commit real credentials to version control"
- [x] 8.3 Verify .gitignore
  - [x] 8.3.1 Confirm .env is in .gitignore
  - [x] 8.3.2 Confirm backend/.env is in .gitignore
- [x] 8.4 Test credential management
  - [x] 8.4.1 Run `docker-compose up` with credentials from .env
  - [x] 8.4.2 Verify database connection succeeds
  - [x] 8.4.3 Verify no credentials appear in docker-compose.yml

---

### Task 9: Strict CORS Configuration (Requirement 22)

**Goal**: Configure CORS for known frontend domains only, removing wildcard origins.

**Files**: `backend/main.py`, `.env.example`, `backend/config.py`

- [x] 9.1 Update CORS configuration
  - [x] 9.1.1 Read CORS_ORIGINS from environment variables in `backend/config.py`
  - [x] 9.1.2 Parse CORS_ORIGINS as comma-separated list of URLs
  - [x] 9.1.3 Add validation to reject wildcard (*) in production
  - [x] 9.1.4 Log warning if CORS_ORIGINS contains wildcard
  - [x] 9.1.5 Update `backend/main.py` to use parsed CORS_ORIGINS
- [x] 9.2 Update environment configuration
  - [x] 9.2.1 Add CORS_ORIGINS to `.env.example`
  - [x] 9.2.2 Provide example with production and development URLs
  - [x] 9.2.3 Add comment explaining CORS security implications
- [x] 9.3 Test CORS behavior
  - [x] 9.3.1 Test request from allowed origin (should succeed)
  - [x] 9.3.2 Test request from unauthorized origin (should fail with CORS error)
  - [x] 9.3.3 Verify warning logged if wildcard detected

---

### Task 10: Real Kaggle Data Integration (Requirement 25)

**Goal**: Support real Kaggle datasets for ML training alongside synthetic data.

**Files**: `ml/data/download_kaggle.py` (new), `ml/data/README.md` (new), `ml/pipeline/train_all.py`

- [x] 10.1 Create Kaggle data documentation
  - [x] 10.1.1 Create `ml/data/README.md`
  - [x] 10.1.2 Document expected Kaggle dataset schemas
  - [x] 10.1.3 Document required columns and data types
  - [x] 10.1.4 Provide example dataset links
- [x] 10.2 Create Kaggle download script
  - [x] 10.2.1 Create `ml/data/download_kaggle.py`
  - [x] 10.2.2 Implement automated dataset download using Kaggle API
  - [x] 10.2.3 Add schema validation for downloaded CSVs
  - [x] 10.2.4 Handle missing columns with appropriate defaults
- [x] 10.3 Update training pipeline
  - [x] 10.3.1 Modify `ml/pipeline/train_all.py` to accept Kaggle CSV files
  - [x] 10.3.2 Implement data merging logic (synthetic + Kaggle)
  - [x] 10.3.3 Log data source (synthetic, kaggle, or mixed) in training metrics
  - [x] 10.3.4 Validate incoming CSV files match expected schema
- [x] 10.4 Test Kaggle data integration
  - [x] 10.4.1 Test training with synthetic data only
  - [x] 10.4.2 Test training with Kaggle data only
  - [x] 10.4.3 Test training with mixed data sources
  - [x] 10.4.4 Verify data source logged in training_metrics.json

---

### Task 11: N+1 Query Optimization (Requirement 26)

**Goal**: Optimize database queries to eliminate N+1 patterns for fast dashboard loading.

**Files**: `backend/routes/students.py`, `backend/db/session.py`, `backend/config.py`

- [x] 11.1 Optimize student queries
  - [x] 11.1.1 Add `joinedload()` for student predictions in GET /api/students
  - [x] 11.1.2 Add `selectinload()` for audit logs when needed
  - [x] 11.1.3 Ensure dashboard heatmap uses at most 2 queries
  - [x] 11.1.4 Remove any N+1 query patterns in student fetching
- [x] 11.2 Add query performance monitoring
  - [x] 11.2.1 Add slow query logging (>100ms) in DEBUG mode
  - [x] 11.2.2 Include query details in slow query logs
  - [x] 11.2.3 Add database query profiling in DEBUG mode
- [x] 11.3 Test query performance
  - [x] 11.3.1 Create test database with 100+ students
  - [x] 11.3.2 Measure GET /api/students response time
  - [x] 11.3.3 Verify response completes in under 500ms
  - [x] 11.3.4 Verify at most 2 queries executed for dashboard heatmap
  - [x] 11.3.5 Check slow query logs for optimization opportunities



---

## Phase 2: Important Improvements (SHOULD DO)

Priority: HIGH | Estimated: 18-22 hours | Requirements: 7-13, 23-24, 27-30

### Task 12: Navigation Bar Component (Requirement 7)

**Goal**: Create persistent navigation bar for easy movement between application pages.

**Files**: `frontend/components/layout/NavigationBar.tsx` (new), `frontend/app/layout.tsx`

- [x] 12.1 Create NavigationBar component
  - [x] 12.1.1 Create `frontend/components/layout/NavigationBar.tsx`
  - [x] 12.1.2 Add links: Dashboard (/dashboard), Alerts (/alerts), New Student (/student/new), API Docs (/docs)
  - [x] 12.1.3 Implement active page highlighting using usePathname()
  - [x] 12.1.4 Add EduRisk AI logo/title on left side
  - [x] 12.1.5 Add high-risk alert badge with count
  - [x] 12.1.6 Implement responsive design for mobile (< 768px)
- [x] 12.2 Create Layout wrapper component
  - [x] 12.2.1 Create `frontend/components/layout/Layout.tsx`
  - [x] 12.2.2 Include NavigationBar at top
  - [x] 12.2.3 Add main content area with proper spacing
- [x] 12.3 Integrate Layout in app
  - [x] 12.3.1 Update `frontend/app/layout.tsx` to use Layout component
  - [x] 12.3.2 Wrap all page components with Layout
- [x] 12.4 Test navigation
  - [x] 12.4.1 Test navigation between all pages
  - [x] 12.4.2 Verify active page highlighting works
  - [x] 12.4.3 Test alert badge displays correct count
  - [x] 12.4.4 Test responsive behavior on mobile viewport

---

### Task 13: Dashboard New Prediction Button (Requirement 8)

**Goal**: Add prominent "Add Student" button to dashboard for easy access to student creation form.

**Files**: `frontend/app/dashboard/page.tsx`

- [x] 13.1 Add "Add Student" button to dashboard
  - [x] 13.1.1 Add button in dashboard header (top-right area)
  - [x] 13.1.2 Include plus icon from lucide-react
  - [x] 13.1.3 Apply primary button styling
  - [x] 13.1.4 Add onClick handler to navigate to /student/new
- [x] 13.2 Test button functionality
  - [x] 13.2.1 Verify button is visually prominent
  - [x] 13.2.2 Test navigation to /student/new on click
  - [x] 13.2.3 Verify button displays correctly on mobile

---

### Task 14: Batch Scoring Database Session Safety (Requirement 9)

**Goal**: Ensure each student in batch gets independent database session to prevent race conditions.

**Files**: `backend/routes/predict.py`, `backend/db/session.py`

- [x] 14.1 Create independent session factory
  - [x] 14.1.1 Add `get_async_session()` context manager in `backend/db/session.py`
  - [x] 14.1.2 Ensure session is properly closed after use
- [x] 14.2 Refactor batch scoring endpoint
  - [x] 14.2.1 Create `process_student()` helper function
  - [x] 14.2.2 Use `async with get_async_session()` for each student
  - [x] 14.2.3 Implement parallel processing with `asyncio.gather()`
  - [x] 14.2.4 Return success=True/False for each student
  - [x] 14.2.5 Handle exceptions without affecting other students
  - [x] 14.2.6 Ensure each session is closed after processing
- [x] 14.3 Test batch scoring safety
  - [x] 14.3.1 Test batch with all valid students (all should succeed)
  - [x] 14.3.2 Test batch with one invalid student (others should succeed)
  - [x] 14.3.3 Test batch with 50+ students (verify parallel processing)
  - [x] 14.3.4 Verify no database session corruption

---

### Task 15: Risk Calculator Unit Tests (Requirement 10)

**Goal**: Create comprehensive unit tests for risk calculator functions with 100% coverage.

**Files**: `backend/services/test_risk_calculator_unit.py` (new)

- [x] 15.1 Create test file structure
  - [x] 15.1.1 Create `backend/services/test_risk_calculator_unit.py`
  - [x] 15.1.2 Import risk calculator functions
  - [x] 15.1.3 Set up pytest fixtures if needed
- [x] 15.2 Test calculate_risk_score()
  - [x] 15.2.1 Test high placement probabilities (should yield low risk)
  - [x] 15.2.2 Test medium placement probabilities (should yield medium risk)
  - [x] 15.2.3 Test low placement probabilities (should yield high risk)
  - [x] 15.2.4 Test zero probabilities (should yield maximum risk)
  - [x] 15.2.5 Test boundary values (0.0, 0.5, 1.0)
  - [x] 15.2.6 Test weighted average calculation
- [x] 15.3 Test assign_risk_level()
  - [x] 15.3.1 Test boundary value 0 (should be "low")
  - [x] 15.3.2 Test boundary value 33 (should be "low")
  - [x] 15.3.3 Test boundary value 34 (should be "medium")
  - [x] 15.3.4 Test boundary value 66 (should be "medium")
  - [x] 15.3.5 Test boundary value 67 (should be "high")
  - [x] 15.3.6 Test boundary value 100 (should be "high")
- [x] 15.4 Test calculate_emi_affordability()
  - [x] 15.4.1 Test normal case (should return correct ratio)
  - [x] 15.4.2 Test zero salary (should return 1.0)
  - [x] 15.4.3 Test zero EMI (should return 0.0)
  - [x] 15.4.4 Test very high EMI (should return >1.0)
  - [x] 15.4.5 Test rounding to 3 decimal places
- [x] 15.5 Test action recommender
  - [x] 15.5.1 Test recommendations for low risk level
  - [x] 15.5.2 Test recommendations for medium risk level
  - [x] 15.5.3 Test recommendations for high risk level
- [x] 15.6 Run tests and verify coverage
  - [x] 15.6.1 Run `pytest backend/services/test_risk_calculator_unit.py`
  - [x] 15.6.2 Run coverage report
  - [x] 15.6.3 Verify 100% coverage for risk_calculator.py

---

### Task 16: Salary Card EMI Context (Requirement 11)

**Goal**: Display EMI affordability percentage with color-coded labels in salary card.

**Files**: `frontend/components/student/SalaryRangeCard.tsx`

- [x] 16.1 Add EMI affordability display
  - [x] 16.1.1 Calculate affordability percentage from prediction data
  - [x] 16.1.2 Display percentage below salary range
  - [x] 16.1.3 Format to one decimal place (e.g., "32.5%")
- [x] 16.2 Implement color-coded labels
  - [x] 16.2.1 Show green with "Good" label for < 30%
  - [x] 16.2.2 Show amber with "Moderate" label for 30-50%
  - [x] 16.2.3 Show red with "High Risk" label for > 50%
- [x] 16.3 Add tooltip
  - [x] 16.3.1 Add tooltip with explanation text
  - [x] 16.3.2 Text: "EMI Affordability: Percentage of expected salary required for loan repayment. Lower is better."
- [x] 16.4 Test EMI display
  - [x] 16.4.1 Test with low affordability (< 30%)
  - [x] 16.4.2 Test with moderate affordability (30-50%)
  - [x] 16.4.3 Test with high affordability (> 50%)
  - [x] 16.4.4 Verify tooltip displays correctly

---

### Task 17: Risk Score Gauge Visualization (Requirement 12)

**Goal**: Create circular gauge visualization for risk score with color zones and animation.

**Files**: `frontend/components/student/RiskScoreDisplay.tsx`

- [x] 17.1 Implement circular gauge component
  - [x] 17.1.1 Use Recharts RadialBarChart or custom SVG
  - [x] 17.1.2 Display risk score from 0 to 100 on circular arc
  - [x] 17.1.3 Show numeric score in center of gauge
- [x] 17.2 Implement color zones
  - [x] 17.2.1 Green color for scores 0-33 (low risk)
  - [x] 17.2.2 Amber color for scores 34-66 (medium risk)
  - [x] 17.2.3 Red color for scores 67-100 (high risk)
- [x] 17.3 Add animation
  - [x] 17.3.1 Animate from 0 to actual score on component mount
  - [x] 17.3.2 Use smooth easing function
  - [x] 17.3.3 Duration: 1-2 seconds
- [x] 17.4 Implement responsive design
  - [x] 17.4.1 Scale gauge appropriately for mobile devices
  - [x] 17.4.2 Test on various screen sizes
- [x] 17.5 Test gauge visualization
  - [x] 17.5.1 Test with low risk score (0-33)
  - [x] 17.5.2 Test with medium risk score (34-66)
  - [x] 17.5.3 Test with high risk score (67-100)
  - [x] 17.5.4 Verify animation plays smoothly
  - [x] 17.5.5 Test responsive behavior

---

### Task 18: Dashboard Empty State (Requirement 13)

**Goal**: Display helpful empty state when no students exist in database.

**Files**: `frontend/app/dashboard/page.tsx`, `frontend/components/dashboard/EmptyState.tsx` (new)

- [x] 18.1 Create EmptyState component
  - [x] 18.1.1 Create `frontend/components/dashboard/EmptyState.tsx`
  - [x] 18.1.2 Add friendly message: "No students yet. Add your first student to get started."
  - [x] 18.1.3 Add "Add Your First Student" button linking to /student/new
  - [x] 18.1.4 Include empty state icon or illustration
  - [x] 18.1.5 Center component vertically and horizontally
- [x] 18.2 Integrate in dashboard
  - [x] 18.2.1 Check if students array is empty in dashboard page
  - [x] 18.2.2 Render EmptyState when no students exist
  - [x] 18.2.3 Render normal student table when students exist
- [x] 18.3 Test empty state
  - [x] 18.3.1 Test dashboard with no students (should show EmptyState)
  - [x] 18.3.2 Test dashboard with students (should show table)
  - [x] 18.3.3 Test button navigation to /student/new

---

### Task 19: Frontend Login Portal (Requirement 23)

**Goal**: Create secure login screen for user authentication.

**Files**: `frontend/app/login/page.tsx` (new), `frontend/components/auth/LoginForm.tsx` (new)

- [x] 19.1 Create login page
  - [x] 19.1.1 Create `frontend/app/login/page.tsx`
  - [x] 19.1.2 Set as default route for unauthenticated users
  - [x] 19.1.3 Display EduRisk AI logo and branding
- [x] 19.2 Create LoginForm component
  - [x] 19.2.1 Create `frontend/components/auth/LoginForm.tsx`
  - [x] 19.2.2 Add username input field with validation
  - [x] 19.2.3 Add password input field with validation
  - [x] 19.2.4 Add "Forgot Password" link (non-functional for MVP)
  - [x] 19.2.5 Add submit button
  - [x] 19.2.6 Validate non-empty fields before submission
- [x] 19.3 Implement login logic
  - [x] 19.3.1 Call POST /api/auth/login on form submit
  - [x] 19.3.2 Store JWT token on successful login
  - [x] 19.3.3 Redirect to /dashboard on success
  - [x] 19.3.4 Display user-friendly error message on failure
- [x] 19.4 Test login portal
  - [x] 19.4.1 Test with valid credentials (should redirect to dashboard)
  - [x] 19.4.2 Test with invalid credentials (should show error)
  - [x] 19.4.3 Test form validation (empty fields)
  - [x] 19.4.4 Verify logo and branding display correctly

---

### Task 20: Frontend Auth State Management (Requirement 24)

**Goal**: Implement centralized authentication state with automatic JWT token handling.

**Files**: `frontend/lib/auth.ts` (new), `frontend/lib/api.ts`, `frontend/hooks/useAuth.ts` (new)

- [x] 20.1 Create auth utilities
  - [x] 20.1.1 Create `frontend/lib/auth.ts`
  - [x] 20.1.2 Implement token storage (httpOnly cookies or secure localStorage)
  - [x] 20.1.3 Implement `getToken()` function
  - [x] 20.1.4 Implement `setToken(token)` function
  - [x] 20.1.5 Implement `clearToken()` function
  - [x] 20.1.6 Implement `logout()` function
- [x] 20.2 Create API client with interceptor
  - [x] 20.2.1 Update `frontend/lib/api.ts`
  - [x] 20.2.2 Add request interceptor to attach Authorization: Bearer {token}
  - [x] 20.2.3 Add response interceptor to handle 401 errors
  - [x] 20.2.4 Redirect to /login and clear tokens on 401
- [x] 20.3 Create useAuth hook
  - [x] 20.3.1 Create `frontend/hooks/useAuth.ts`
  - [x] 20.3.2 Provide authentication state (isAuthenticated, user)
  - [x] 20.3.3 Provide login function
  - [x] 20.3.4 Provide logout function
  - [x] 20.3.5 Handle token refresh if needed
- [x] 20.4 Update NavigationBar
  - [x] 20.4.1 Display username when authenticated
  - [x] 20.4.2 Add logout button
  - [x] 20.4.3 Hide user info when not authenticated
- [x] 20.5 Implement route protection
  - [x] 20.5.1 Create route guard middleware
  - [x] 20.5.2 Redirect unauthenticated users to /login
  - [x] 20.5.3 Apply to protected routes (dashboard, alerts, student pages)
- [x] 20.6 Test auth state management
  - [x] 20.6.1 Test login flow (token stored, redirected to dashboard)
  - [x] 20.6.2 Test logout flow (token cleared, redirected to login)
  - [x] 20.6.3 Test API requests include JWT token
  - [x] 20.6.4 Test 401 handling (redirect to login)
  - [x] 20.6.5 Test route protection (unauthenticated users redirected)

---

### Task 21: Async SHAP Computation for Batch Requests (Requirement 27)

**Goal**: Compute SHAP values asynchronously for batch requests to avoid timeouts.

**Files**: `backend/routes/predict.py`, `backend/routes/predictions.py` (new)

- [x] 21.1 Modify batch scoring endpoint
  - [x] 21.1.1 Use FastAPI BackgroundTasks for SHAP computation
  - [x] 21.1.2 Return prediction results immediately without SHAP values
  - [x] 21.1.3 Set shap_values to null in initial response
  - [x] 21.1.4 Compute SHAP values in background task
- [x] 21.2 Create SHAP retrieval endpoint
  - [x] 21.2.1 Create GET /api/predictions/{id}/shap endpoint
  - [x] 21.2.2 Return SHAP values once computed
  - [x] 21.2.3 Return 404 if SHAP values not yet available
- [x] 21.3 Add SHAP computation logging
  - [x] 21.3.1 Log SHAP computation time separately from prediction time
  - [x] 21.3.2 Log completion status
- [x] 21.4 Test async SHAP computation
  - [x] 21.4.1 Submit batch of 100 students
  - [x] 21.4.2 Verify response returns in under 5 seconds
  - [x] 21.4.3 Verify shap_values is null in initial response
  - [x] 21.4.4 Poll GET /api/predictions/{id}/shap until SHAP values available
  - [x] 21.4.5 Verify SHAP computation completes successfully

---

### Task 22: Feature Engineering Configuration (Requirement 28)

**Goal**: Move feature engineering weights to external config file for easy tuning.

**Files**: `ml/pipeline/config.json` (new), `ml/pipeline/feature_engineering.py`

- [x] 22.1 Create feature engineering config file
  - [x] 22.1.1 Create `ml/pipeline/config.json`
  - [x] 22.1.2 Define feature weights as JSON object
  - [x] 22.1.3 Include all hardcoded weights from FeatureEngineer
  - [x] 22.1.4 Add comments explaining each weight
- [x] 22.2 Update FeatureEngineer class
  - [x] 22.2.1 Load weights from config.json in __init__
  - [x] 22.2.2 Replace hardcoded weights with config values
  - [x] 22.2.3 Add fallback to default weights if config not found
  - [x] 22.2.4 Log which config file is being used
- [x] 22.3 Test feature engineering config
  - [x] 22.3.1 Test with default config.json
  - [x] 22.3.2 Test with modified weights
  - [x] 22.3.3 Verify features calculated correctly
  - [x] 22.3.4 Test fallback to defaults if config missing

---

### Task 23: Mock LLM Response Tests (Requirement 29)

**Goal**: Add tests that mock Groq API responses to ensure graceful degradation.

**Files**: `backend/tests/test_llm_service.py` (new)

- [x] 23.1 Create LLM service test file
  - [x] 23.1.1 Create `backend/tests/test_llm_service.py`
  - [x] 23.1.2 Set up pytest fixtures for mocking
  - [x] 23.1.3 Import LLMService
- [x] 23.2 Test successful LLM response
  - [x] 23.2.1 Mock successful Groq API response
  - [x] 23.2.2 Verify LLMService returns expected summary
- [x] 23.3 Test LLM timeout
  - [x] 23.3.1 Mock Groq API timeout
  - [x] 23.3.2 Verify LLMService returns fallback message
  - [x] 23.3.3 Verify no exception raised
- [x] 23.4 Test missing API key
  - [x] 23.4.1 Test with LLM_API_KEY not configured
  - [x] 23.4.2 Verify LLMService returns fallback message
  - [x] 23.4.3 Verify warning logged
- [x] 23.5 Test rate limit handling
  - [x] 23.5.1 Mock Groq API rate limit error
  - [x] 23.5.2 Verify LLMService implements exponential backoff
  - [x] 23.5.3 Verify fallback after max retries
- [x] 23.6 Run LLM tests
  - [x] 23.6.1 Run `pytest backend/tests/test_llm_service.py`
  - [x] 23.6.2 Verify all tests pass

---

### Task 24: Groq API Rate Limiting (Requirement 30)

**Goal**: Implement exponential backoff for Groq API rate limit handling.

**Files**: `backend/services/llm_service.py`

- [x] 24.1 Implement rate limit detection
  - [x] 24.1.1 Detect 429 status code from Groq API
  - [x] 24.1.2 Parse Retry-After header if present
- [x] 24.2 Implement exponential backoff
  - [x] 24.2.1 Add retry logic with exponential backoff
  - [x] 24.2.2 Start with 1 second delay, double each retry
  - [x] 24.2.3 Max retries: 3
  - [x] 24.2.4 Max delay: 8 seconds
- [x] 24.3 Add fallback handling
  - [x] 24.3.1 Return fallback message after max retries
  - [x] 24.3.2 Log rate limit events
  - [x] 24.3.3 Don't raise exceptions for rate limits
- [x] 24.4 Test rate limiting
  - [x] 24.4.1 Mock 429 response from Groq API
  - [x] 24.4.2 Verify exponential backoff behavior
  - [x] 24.4.3 Verify fallback after max retries
  - [x] 24.4.4 Verify rate limit events logged



---

## Phase 3: Optional Enhancements (NICE TO HAVE)

Priority: MEDIUM | Estimated: 12-16 hours | Requirements: 14-19, 31-32

### Task 25: CSV Batch Upload UI (Requirement 14)

**Goal**: Build CSV drag-and-drop interface for batch student scoring.

**Files**: `frontend/app/student/batch/page.tsx` (new), `frontend/components/forms/BatchUpload.tsx` (new)

- [x] 25.1 Create batch upload page
  - [x] 25.1.1 Create `frontend/app/student/batch/page.tsx`
  - [x] 25.1.2 Add page title and instructions
- [x] 25.2 Create BatchUpload component
  - [x] 25.2.1 Create `frontend/components/forms/BatchUpload.tsx`
  - [x] 25.2.2 Implement file upload component accepting .csv files
  - [x] 25.2.3 Add drag-and-drop functionality
  - [x] 25.2.4 Parse CSV file on selection
  - [x] 25.2.5 Display preview table of parsed students
- [x] 25.3 Implement CSV validation
  - [x] 25.3.1 Validate required columns: name, course_type, institute_tier, cgpa, year_of_grad, loan_amount, loan_emi
  - [x] 25.3.2 Display validation errors to user
  - [x] 25.3.3 Limit batch to 500 students
- [x] 25.4 Implement batch submission
  - [x] 25.4.1 Add "Submit Batch" button
  - [x] 25.4.2 Call POST /api/batch-score with parsed students
  - [x] 25.4.3 Display progress indicator during processing
  - [x] 25.4.4 Display results summary (success count, failure count, errors)
- [x] 25.5 Test batch upload UI
  - [x] 25.5.1 Test with valid CSV file
  - [x] 25.5.2 Test with invalid CSV (missing columns)
  - [x] 25.5.3 Test with large batch (500 students)
  - [x] 25.5.4 Test drag-and-drop functionality
  - [x] 25.5.5 Verify results summary displays correctly

---

### Task 26: Risk Score Trend Chart (Requirement 15)

**Goal**: Display line chart showing risk score history over time for a student.

**Files**: `frontend/components/student/RiskTrendChart.tsx` (new), `frontend/app/student/[id]/page.tsx`

- [x] 26.1 Create RiskTrendChart component
  - [x] 26.1.1 Create `frontend/components/student/RiskTrendChart.tsx`
  - [x] 26.1.2 Use Recharts LineChart
  - [x] 26.1.3 Fetch prediction history from GET /api/students/{id}/predictions
- [x] 26.2 Implement chart visualization
  - [x] 26.2.1 Plot risk_score on Y-axis
  - [x] 26.2.2 Plot created_at timestamp on X-axis
  - [x] 26.2.3 Add axis labels "Risk Score" and "Date"
  - [x] 26.2.4 Use green line when trend improving (risk decreasing)
  - [x] 26.2.5 Use red line when trend declining (risk increasing)
- [x] 26.3 Handle edge cases
  - [x] 26.3.1 Display "No historical data" when only one prediction exists
  - [x] 26.3.2 Handle empty prediction history
- [x] 26.4 Integrate in student detail page
  - [x] 26.4.1 Add RiskTrendChart to student detail page
  - [x] 26.4.2 Position below risk score display
- [x] 26.5 Test trend chart
  - [x] 26.5.1 Test with multiple predictions (should show chart)
  - [x] 26.5.2 Test with single prediction (should show "No historical data")
  - [x] 26.5.3 Test with improving trend (should be green)
  - [x] 26.5.4 Test with declining trend (should be red)

---

### Task 27: Docker Multi-Stage Build Optimization (Requirement 16)

**Goal**: Optimize backend Docker image to be under 1 GB using multi-stage builds.

**Files**: `docker/Dockerfile.backend`

- [x] 27.1 Implement multi-stage build
  - [x] 27.1.1 Create builder stage with python:3.11-slim
  - [x] 27.1.2 Install build dependencies: gcc, g++, libpq-dev
  - [x] 27.1.3 Install Python dependencies in builder stage
  - [x] 27.1.4 Create runtime stage with python:3.11-slim
  - [x] 27.1.5 Copy only installed packages from builder stage
  - [x] 27.1.6 Install only runtime dependencies: libpq5
- [x] 27.2 Optimize layer caching
  - [x] 27.2.1 Copy requirements.txt before copying source code
  - [x] 27.2.2 Install dependencies before copying application code
  - [x] 27.2.3 Use .dockerignore to exclude unnecessary files
- [x] 27.3 Test Docker build
  - [x] 27.3.1 Build image: `docker build -f docker/Dockerfile.backend -t edurisk-backend .`
  - [x] 27.3.2 Check image size: `docker images edurisk-backend`
  - [x] 27.3.3 Verify image size is under 1 GB
  - [x] 27.3.4 Test rebuild without code changes (should use cache)
  - [x] 27.3.5 Verify application runs correctly in optimized image

---

### Task 28: Student Table Pagination (Requirement 17)

**Goal**: Add pagination controls to student table for large portfolios.

**Files**: `frontend/components/dashboard/StudentTable.tsx`, `frontend/app/dashboard/page.tsx`

- [x] 28.1 Implement pagination state
  - [x] 28.1.1 Add state for current page number
  - [x] 28.1.2 Add state for page size (default: 20)
  - [x] 28.1.3 Calculate total pages from student count
- [x] 28.2 Create pagination controls
  - [x] 28.2.1 Add "Previous" and "Next" buttons
  - [x] 28.2.2 Add page size selector (20, 50, 100)
  - [x] 28.2.3 Display current page and total pages (e.g., "Page 2 of 5")
  - [x] 28.2.4 Display student count (e.g., "Showing 21-40 of 237 students")
- [x] 28.3 Implement pagination logic
  - [x] 28.3.1 Fetch paginated data from API with page and limit params
  - [x] 28.3.2 Update page on "Next"/"Previous" click
  - [x] 28.3.3 Reset to page 1 when page size changes
  - [x] 28.3.4 Disable "Previous" on first page
  - [x] 28.3.5 Disable "Next" on last page
- [x] 28.4 Test pagination
  - [x] 28.4.1 Test with 100+ students
  - [x] 28.4.2 Test navigation between pages
  - [x] 28.4.3 Test page size changes
  - [x] 28.4.4 Verify correct student count displayed

---

### Task 29: API Integration Tests (Requirement 18)

**Goal**: Create automated integration tests for all API endpoints.

**Files**: `backend/tests/test_api_integration.py` (new), `backend/tests/conftest.py`

- [x] 29.1 Set up test infrastructure
  - [x] 29.1.1 Create `backend/tests/test_api_integration.py`
  - [x] 29.1.2 Set up FastAPI TestClient
  - [x] 29.1.3 Create test database fixtures
  - [x] 29.1.4 Create test data fixtures
- [x] 29.2 Test prediction endpoints
  - [x] 29.2.1 Test POST /api/predict with valid data (expect 200)
  - [x] 29.2.2 Test POST /api/predict with invalid data (expect 400)
  - [x] 29.2.3 Test POST /api/batch-score with multiple students
- [x] 29.3 Test student endpoints
  - [x] 29.3.1 Test GET /api/students (expect list of students)
  - [x] 29.3.2 Test GET /api/students/{id} (expect student details)
  - [x] 29.3.3 Test GET /api/students/{id}/predictions (expect prediction history)
- [x] 29.4 Test alert endpoints
  - [x] 29.4.1 Test GET /api/alerts (expect high-risk alerts)
- [x] 29.5 Test explanation endpoints
  - [x] 29.5.1 Test GET /api/explain/{student_id} (expect SHAP values)
- [x] 29.6 Test health endpoint
  - [x] 29.6.1 Test GET /api/health (expect ml_models: available)
- [x] 29.7 Run integration tests
  - [x] 29.7.1 Run `pytest backend/tests/test_api_integration.py`
  - [x] 29.7.2 Verify all tests pass
  - [x] 29.7.3 Verify tests use test database (not production)

---

### Task 30: CSV Student Data Parser with Property-Based Tests (Requirement 19)

**Goal**: Create robust CSV parser with round-trip property validation.

**Files**: `backend/parsers/csv_parser.py` (new), `backend/tests/test_csv_parser.py` (new)

- [x] 30.1 Create CSV parser
  - [x] 30.1.1 Create `backend/parsers/csv_parser.py`
  - [x] 30.1.2 Implement `parse_csv(file)` function
  - [x] 30.1.3 Parse each row into StudentCreate object
  - [x] 30.1.4 Handle CSV with or without header row
  - [x] 30.1.5 Handle quoted fields containing commas
  - [x] 30.1.6 Return descriptive errors for missing fields
  - [x] 30.1.7 Return descriptive errors for invalid data types
- [x] 30.2 Create CSV pretty printer
  - [x] 30.2.1 Implement `format_to_csv(students)` function
  - [x] 30.2.2 Format StudentCreate objects back into CSV rows
  - [x] 30.2.3 Handle special characters and commas
- [x] 30.3 Create property-based tests
  - [x] 30.3.1 Create `backend/tests/test_csv_parser.py`
  - [x] 30.3.2 Install hypothesis for property-based testing
  - [x] 30.3.3 Test round-trip property: parse → format → parse produces equivalent object
  - [x] 30.3.4 Generate random valid StudentCreate objects
  - [x] 30.3.5 Verify round-trip for 100+ random examples
- [x] 30.4 Create example-based tests
  - [x] 30.4.1 Test parsing valid CSV
  - [x] 30.4.2 Test parsing CSV with missing fields
  - [x] 30.4.3 Test parsing CSV with invalid data types
  - [x] 30.4.4 Test parsing CSV with quoted fields
- [x] 30.5 Run parser tests
  - [x] 30.5.1 Run `pytest backend/tests/test_csv_parser.py`
  - [x] 30.5.2 Verify all tests pass
  - [x] 30.5.3 Verify round-trip property holds

---

### Task 31: Vercel Deployment Guide (Requirement 31)

**Goal**: Document step-by-step process for deploying Next.js frontend to Vercel.

**Files**: `DEPLOYMENT_GUIDE.md`

- [x] 31.1 Add Vercel deployment section
  - [x] 31.1.1 Add "Deploying Frontend to Vercel" section to DEPLOYMENT_GUIDE.md
  - [x] 31.1.2 Document prerequisites (Vercel account, GitHub repo)
  - [x] 31.1.3 Document Vercel CLI installation
  - [x] 31.1.4 Document project configuration
- [x] 31.2 Document deployment steps
  - [x] 31.2.1 Step 1: Connect GitHub repository to Vercel
  - [x] 31.2.2 Step 2: Configure build settings (Next.js framework preset)
  - [x] 31.2.3 Step 3: Set environment variables (NEXT_PUBLIC_API_URL)
  - [x] 31.2.4 Step 4: Deploy and verify
  - [x] 31.2.5 Step 5: Configure custom domain (optional)
- [x] 31.3 Document troubleshooting
  - [x] 31.3.1 Common build errors and solutions
  - [x] 31.3.2 API connection issues
  - [x] 31.3.3 Environment variable problems
- [x] 31.4 Test deployment guide
  - [x] 31.4.1 Follow guide to deploy to Vercel
  - [x] 31.4.2 Verify deployment succeeds
  - [x] 31.4.3 Update guide based on any issues encountered

---

### Task 32: Mock Alert Notification System (Requirement 32)

**Goal**: Implement mock email/SMS notification system for high-risk students.

**Files**: `backend/services/alert_service.py` (new), `backend/routes/predict.py`

- [x] 32.1 Create alert service
  - [x] 32.1.1 Create `backend/services/alert_service.py`
  - [x] 32.1.2 Implement `send_alert(student, risk_level)` function
  - [x] 32.1.3 Log mock SMS: "SMS SENT TO [NUMBER]: High risk alert for [STUDENT]"
  - [x] 32.1.4 Log mock Email: "EMAIL SENT TO [ADDRESS]: High risk alert for [STUDENT]"
  - [x] 32.1.5 Include risk score and recommended actions in log
- [x] 32.2 Integrate alert service
  - [x] 32.2.1 Import AlertService in prediction routes
  - [x] 32.2.2 Trigger alert when risk_level is "high"
  - [x] 32.2.3 Log alert to audit trail
- [x] 32.3 Add alert configuration
  - [x] 32.3.1 Add ALERT_ENABLED to environment variables
  - [x] 32.3.2 Add ALERT_PHONE_NUMBER to environment variables
  - [x] 32.3.3 Add ALERT_EMAIL to environment variables
  - [x] 32.3.4 Skip alerts if ALERT_ENABLED=False
- [x] 32.4 Test alert system
  - [x] 32.4.1 Create prediction with high risk score
  - [x] 32.4.2 Verify mock SMS logged
  - [x] 32.4.3 Verify mock Email logged
  - [x] 32.4.4 Verify alert recorded in audit trail
  - [x] 32.4.5 Test with ALERT_ENABLED=False (should skip alerts)

---

## Testing Strategy

### Unit Tests
- Risk calculator functions (Task 15)
- CSV parser round-trip property (Task 30)
- LLM service with mocked responses (Task 23)

### Integration Tests
- All API endpoints (Task 29)
- Database migrations (Task 4)
- Authentication flows (Tasks 7, 19, 20)

### Manual Testing
- UI components (Tasks 12, 13, 16, 17, 18, 25, 26, 28)
- Docker deployment (Tasks 1, 27)
- End-to-end workflows

### Performance Tests
- N+1 query optimization (Task 11)
- Batch scoring with 100+ students (Task 14, 21)
- Dashboard load time with 100+ students (Task 11)

---

## Implementation Order Recommendations

### Week 1: Critical Security & Infrastructure (Phase 1)
1. Task 1: ML Model Auto-Training (Day 1)
2. Task 2: API Key Authentication (Day 1)
3. Task 7: JWT OAuth2 Authentication (Day 2)
4. Task 8: Secure Database Credentials (Day 2)
5. Task 9: Strict CORS Configuration (Day 2)
6. Task 3: Environment Variable Documentation (Day 3)
7. Task 4: Database Migration Configuration (Day 3)
8. Task 5: Production Debug Mode (Day 3)
9. Task 6: Audit Logging Enhancement (Day 4)
10. Task 10: Kaggle Data Integration (Day 4-5)
11. Task 11: N+1 Query Optimization (Day 5)

### Week 2: UX & Testing (Phase 2)
1. Task 12: Navigation Bar (Day 1)
2. Task 13: Dashboard Button (Day 1)
3. Task 19: Login Portal (Day 2)
4. Task 20: Auth State Management (Day 2-3)
5. Task 14: Batch Scoring Safety (Day 3)
6. Task 15: Risk Calculator Tests (Day 4)
7. Task 16: Salary Card EMI (Day 4)
8. Task 17: Risk Score Gauge (Day 5)
9. Task 18: Dashboard Empty State (Day 5)
10. Task 21: Async SHAP Computation (Day 6)
11. Task 22: Feature Engineering Config (Day 6)
12. Task 23: Mock LLM Tests (Day 7)
13. Task 24: Groq Rate Limiting (Day 7)

### Week 3: Polish & Optional Features (Phase 3)
1. Task 29: API Integration Tests (Day 1-2)
2. Task 27: Docker Optimization (Day 2)
3. Task 28: Table Pagination (Day 3)
4. Task 25: CSV Batch Upload UI (Day 3-4)
5. Task 26: Risk Trend Chart (Day 4)
6. Task 30: CSV Parser with PBT (Day 5)
7. Task 31: Vercel Deployment Guide (Day 5)
8. Task 32: Mock Alert System (Day 6)

---

## Success Criteria

### Phase 1 Complete When:
- [ ] System works immediately after `docker-compose up` (no manual setup)
- [ ] All API endpoints require authentication
- [ ] Database credentials managed via environment variables only
- [ ] Documentation accurately reflects all environment variables
- [ ] JWT authentication fully functional
- [ ] CORS strictly configured for known domains
- [ ] Kaggle data integration working
- [ ] Dashboard loads in < 500ms for 100+ students

### Phase 2 Complete When:
- [ ] Navigation bar present on all pages
- [ ] Login portal functional with JWT tokens
- [ ] Auth state managed centrally with automatic token handling
- [ ] Batch scoring uses independent sessions
- [ ] Risk calculator has 100% test coverage
- [ ] EMI affordability displayed with color coding
- [ ] Risk score gauge animates smoothly
- [ ] Empty state displays when no students exist
- [ ] SHAP computation async for batch requests
- [ ] Feature weights configurable via external file
- [ ] LLM service degrades gracefully with mocked tests
- [ ] Groq rate limiting implemented with exponential backoff

### Phase 3 Complete When:
- [ ] CSV batch upload UI functional
- [ ] Risk trend chart displays historical data
- [ ] Backend Docker image under 1 GB
- [ ] Student table pagination working
- [ ] API integration tests passing
- [ ] CSV parser passes property-based tests
- [ ] Vercel deployment guide complete and tested
- [ ] Mock alert system logging notifications

### Overall Project Complete When:
- [ ] All Phase 1 tasks completed (MUST DO)
- [ ] At least 80% of Phase 2 tasks completed (SHOULD DO)
- [ ] Project rated 9.5/10 or higher for submission readiness
- [ ] All critical security issues resolved
- [ ] All tests passing
- [ ] Documentation complete and accurate
- [ ] System deployable with zero manual configuration

---

## Risk Mitigation

### High-Risk Tasks
- **Task 7 (JWT Auth)**: Complex, affects all endpoints. Implement incrementally, test thoroughly.
- **Task 11 (N+1 Optimization)**: Performance-critical. Benchmark before and after.
- **Task 14 (Batch Session Safety)**: Concurrency issues possible. Test with large batches.
- **Task 21 (Async SHAP)**: Background task complexity. Ensure proper error handling.

### Dependencies
- Task 20 depends on Task 7 (JWT auth must exist before frontend can use it)
- Task 19 depends on Task 7 (login portal needs auth endpoint)
- Task 25 depends on Task 14 (CSV upload uses batch scoring)
- Task 29 depends on Tasks 1-11 (integration tests need endpoints to test)

### Fallback Plans
- If JWT auth (Task 7) too complex: Keep API key auth only, document as future enhancement
- If Kaggle integration (Task 10) blocked: Continue with synthetic data, document integration path
- If async SHAP (Task 21) causes issues: Compute synchronously with timeout, document limitation
- If Docker optimization (Task 27) fails: Accept larger image size, document optimization attempts

---

## Notes

- Tasks marked with `*` are optional sub-tasks that can be skipped if time-constrained
- All Phase 1 tasks are CRITICAL and must be completed before submission
- Phase 2 tasks are IMPORTANT for a polished submission but not blocking
- Phase 3 tasks are OPTIONAL enhancements that demonstrate professionalism
- Estimated total effort: 40-50 hours across 3 weeks
- Target completion: All Phase 1 + 80% Phase 2 for submission readiness

