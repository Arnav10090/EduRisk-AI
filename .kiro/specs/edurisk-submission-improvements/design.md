# Design Document: EduRisk AI Submission Improvements

## Overview

### Purpose

This design document specifies the technical implementation for 32 critical improvements to the EduRisk AI placement risk assessment platform. These improvements address security vulnerabilities, functionality gaps, UX issues, testing deficiencies, authentication, performance optimization, and data integration identified in comprehensive code reviews. The goal is to transform the project from functionally complete (7.5/10) to submission-ready and portfolio-worthy (9.5/10) for the TenzorX 2026 Poonawalla Fincorp National AI Hackathon.

### Scope

The design covers three implementation phases:

**Phase 1 (Critical - Requirements 1-6, 20-22, 25-26)**: Core functionality and security fixes that MUST be completed before submission:
- ML model auto-training on first boot
- API key authentication middleware
- JWT OAuth2 authentication
- Secure database credentials
- Strict CORS configuration
- Environment variable documentation accuracy
- Database migration configuration
- Production debug mode defaults
- Audit logging for explanation requests
- Real Kaggle data integration
- N+1 query optimization

**Phase 2 (Important - Requirements 7-13, 23-24, 27-30)**: UX improvements, testing, and performance optimization that SHOULD be completed for a polished submission:
- Navigation bar component
- Dashboard new prediction button
- Batch scoring database session safety
- Risk calculator unit tests
- Salary card EMI context
- Risk score gauge visualization
- Dashboard empty state
- Frontend login portal
- Frontend auth state management
- Async SHAP computation for batch requests
- Feature engineering configuration
- Mock LLM response tests
- Groq API rate limiting

**Phase 3 (Optional - Requirements 14-19, 31-32)**: Advanced features demonstrating scalability and professionalism:
- CSV batch upload UI
- Risk score trend chart
- Docker multi-stage build optimization
- Student table pagination
- API integration tests
- CSV parser with property-based tests
- Vercel deployment guide
- Mock alert notification system

**Out of Scope**: Changes to ML model architecture, database schema modifications, framework replacements, or new feature additions beyond the 32 specified requirements.

### System Context

EduRisk AI is a full-stack web application for education loan lenders to assess student placement risk. The system architecture consists of:

- **Backend**: FastAPI (Python 3.11) REST API with async PostgreSQL database access
- **Frontend**: Next.js 14 (TypeScript) with React Server Components and Tailwind CSS
- **ML Pipeline**: XGBoost classifiers for placement prediction, SHAP for explainability, salary estimation models
- **Infrastructure**: Docker Compose orchestrating backend, frontend, PostgreSQL, and Redis containers
- **External Services**: Groq API for LLM-powered risk summaries (optional, graceful degradation)

The improvements focus on production readiness, security hardening, and user experience polish without altering the core ML or architectural patterns.

### Key Design Decisions

1. **ML Model Auto-Training Strategy**: Implement startup check in backend entrypoint script that detects missing models and triggers training pipeline before FastAPI server starts. This ensures zero-configuration deployment for judges.

2. **Authentication Approach**: Implement dual authentication strategy - API key middleware for simple stateless auth (hackathon demo) and JWT OAuth2 Password Flow for production-grade user authentication. This provides flexibility for different deployment scenarios while maintaining security.

3. **Database Session Management**: Refactor batch scoring to use independent database sessions per student with asyncio.gather() for parallel processing. This prevents race conditions and session corruption. Optimize queries with joinedload() to eliminate N+1 patterns.

4. **Docker Optimization**: Implement multi-stage builds with separate builder and runtime stages to reduce image size from ~1.5GB to <1GB while maintaining all functionality.

5. **Testing Strategy**: Focus on unit tests for pure functions (risk calculator) and integration tests for API endpoints. Property-based testing for CSV parser round-trip validation. Mock LLM responses to test graceful degradation.

6. **Graceful Degradation**: Maintain optional LLM integration with fallback messages when API keys are not configured, ensuring the system works without external dependencies. Implement exponential backoff for rate limit handling.

7. **Performance Optimization**: Compute SHAP values asynchronously for batch requests using BackgroundTasks. Load feature engineering weights from external config files for easy tuning without code changes.

8. **Data Integration**: Support real Kaggle datasets alongside synthetic data, with validation and merging capabilities. Document expected schemas and provide download scripts.



## Architecture

### High-Level Architecture

```mermaid
graph TB
    subgraph "Docker Compose Environment"
        subgraph "Frontend Container"
            NextJS[Next.js 14 App]
            NavBar[Navigation Bar]
            Dashboard[Dashboard Pages]
            StudentForm[Student Forms]
        end
        
        subgraph "Backend Container"
            FastAPI[FastAPI Server]
            AuthMW[API Key Middleware]
            StartupCheck[Startup ML Check]
            
            subgraph "Services Layer"
                PredService[Prediction Service]
                LLMService[LLM Service]
                AuditLogger[Audit Logger]
                RiskCalc[Risk Calculator]
            end
            
            subgraph "ML Pipeline"
                FeatureEng[Feature Engineer]
                PlacementPred[Placement Predictor]
                SalaryEst[Salary Estimator]
                ShapExplain[SHAP Explainer]
                ModelTrainer[Model Trainer]
            end
        end
        
        subgraph "Data Layer"
            Postgres[(PostgreSQL)]
            Redis[(Redis Cache)]
            MLModels[ML Models Volume]
        end
    end
    
    subgraph "External Services"
        GroqAPI[Groq API]
    end
    
    NextJS -->|HTTP + API Key| FastAPI
    FastAPI --> AuthMW
    AuthMW --> PredService
    PredService --> FeatureEng
    PredService --> PlacementPred
    PredService --> SalaryEst
    PredService --> ShapExplain
    PredService --> LLMService
    PredService --> RiskCalc
    PredService --> AuditLogger
    
    StartupCheck -->|Check/Train| ModelTrainer
    ModelTrainer -->|Save| MLModels
    PlacementPred -->|Load| MLModels
    SalaryEst -->|Load| MLModels
    
    PredService --> Postgres
    AuditLogger --> Postgres
    FastAPI --> Redis
    LLMService -.->|Optional| GroqAPI
    
    style AuthMW fill:#ff9999
    style StartupCheck fill:#ff9999
    style NavBar fill:#99ccff
    style Dashboard fill:#99ccff
```

### Component Interactions

#### Startup Sequence (Requirement 1)

```mermaid
sequenceDiagram
    participant Docker
    participant StartScript as start-backend.sh
    participant MLCheck as ML Model Check
    participant Trainer as Model Trainer
    participant FastAPI
    participant Health as /api/health
    
    Docker->>StartScript: docker-compose up
    StartScript->>MLCheck: Check for model files
    
    alt Models Missing
        MLCheck->>Trainer: Generate synthetic data
        Trainer->>Trainer: Train 4 models (3m, 6m, 12m, salary)
        Trainer-->>MLCheck: ✅ Models trained (< 120s)
        MLCheck->>FastAPI: Start server
    else Models Exist
        MLCheck->>FastAPI: ✅ Models found, start server
    end
    
    FastAPI->>Health: Register health endpoint
    Health-->>Docker: ml_models: available
```

#### Authentication Flow (Requirement 2)

```mermaid
sequenceDiagram
    participant Client
    participant AuthMW as API Key Middleware
    participant Endpoint as Protected Endpoint
    participant Service
    
    Client->>AuthMW: Request with X-API-Key header
    
    alt No API Key
        AuthMW-->>Client: 401 "Missing API key"
    else Invalid API Key
        AuthMW->>AuthMW: Compare with API_KEY env var
        AuthMW-->>Client: 401 "Invalid API key"
    else Valid API Key
        AuthMW->>Endpoint: Forward request
        Endpoint->>Service: Process request
        Service-->>Endpoint: Response
        Endpoint-->>Client: 200 OK
    end
    
    Note over AuthMW: Public endpoints bypass:<br/>/api/health, /docs, /redoc
```

#### Batch Scoring with Independent Sessions (Requirement 9)

```mermaid
sequenceDiagram
    participant Client
    participant BatchEndpoint as POST /api/batch-score
    participant SessionFactory as DB Session Factory
    participant PredService as Prediction Service
    
    Client->>BatchEndpoint: [student1, student2, student3]
    
    par Process Student 1
        BatchEndpoint->>SessionFactory: Create session 1
        SessionFactory->>PredService: predict(student1, session1)
        PredService-->>SessionFactory: result1
        SessionFactory->>SessionFactory: Close session 1
    and Process Student 2
        BatchEndpoint->>SessionFactory: Create session 2
        SessionFactory->>PredService: predict(student2, session2)
        PredService-->>SessionFactory: result2
        SessionFactory->>SessionFactory: Close session 2
    and Process Student 3
        BatchEndpoint->>SessionFactory: Create session 3
        SessionFactory->>PredService: predict(student3, session3)
        PredService-->>SessionFactory: result3
        SessionFactory->>SessionFactory: Close session 3
    end
    
    BatchEndpoint-->>Client: [result1, result2, result3]
    
    Note over SessionFactory: Each student gets<br/>independent session<br/>to prevent race conditions
```

### Technology Stack

| Layer | Technology | Version | Purpose |
|-------|-----------|---------|---------|
| Backend Framework | FastAPI | 0.104+ | Async REST API with OpenAPI docs |
| Backend Language | Python | 3.11 | Type-safe async programming |
| Frontend Framework | Next.js | 14.x | React Server Components, App Router |
| Frontend Language | TypeScript | 5.x | Type-safe UI development |
| Database | PostgreSQL | 15+ | Relational data storage |
| Cache | Redis | 7+ | Rate limiting, session storage |
| ML Framework | XGBoost | 2.0+ | Gradient boosting classifiers |
| Explainability | SHAP | 0.43+ | Model interpretation |
| LLM Provider | Groq API | - | Fast LLM inference (optional) |
| Containerization | Docker Compose | 2.x | Multi-container orchestration |
| ORM | SQLAlchemy | 2.0+ | Async database access |
| Migration Tool | Alembic | 1.12+ | Database schema versioning |
| UI Library | shadcn/ui | - | Tailwind-based components |
| Charts | Recharts | 2.x | Data visualization |

### Deployment Architecture

```mermaid
graph LR
    subgraph "Docker Host"
        subgraph "edurisk-network Bridge"
            FE[Frontend:3000]
            BE[Backend:8000]
            PG[Postgres:5432]
            RD[Redis:6379]
        end
        
        subgraph "Volumes"
            PGData[postgres_data]
            RDData[redis_data]
            MLVol[ml/models]
        end
    end
    
    User[User Browser] -->|localhost:3000| FE
    FE -->|API calls| BE
    BE --> PG
    BE --> RD
    BE --> MLVol
    PG --> PGData
    RD --> RDData
    
    style FE fill:#99ccff
    style BE fill:#99ff99
    style PG fill:#ffcc99
    style RD fill:#ff9999
```



## Components and Interfaces

### Backend Components

#### 1. ML Model Startup Check (Requirement 1)

**Purpose**: Automatically train ML models on first boot if they don't exist, ensuring zero-configuration deployment.

**Location**: `docker/start-backend.sh` (modified), `ml/pipeline/train_all.py` (existing)

**Interface**:
```python
# Pseudocode for startup check logic
def check_and_train_models():
    """
    Check for ML model files and train if missing.
    Must complete within 120 seconds.
    """
    model_files = [
        "ml/models/placement_model_3m.pkl",
        "ml/models/placement_model_6m.pkl", 
        "ml/models/placement_model_12m.pkl",
        "ml/models/salary_model.pkl"
    ]
    
    if all_files_exist(model_files):
        log("✅ ML models found and ready")
        return True
    
    log("⚠️ ML models not found, training...")
    generate_synthetic_data()
    train_all_models()  # Must complete in < 120s
    
    if all_files_exist(model_files):
        log("✅ ML models trained successfully")
        return True
    else:
        log("❌ ML model training failed")
        sys.exit(1)
```

**Bash Script Integration**:
```bash
#!/bin/bash
# docker/start-backend.sh

# Wait for database
python /app/wait-for-db.py

# Check and train ML models if needed
python -c "
import sys
from pathlib import Path

model_files = [
    'ml/models/placement_model_3m.pkl',
    'ml/models/placement_model_6m.pkl',
    'ml/models/placement_model_12m.pkl',
    'ml/models/salary_model.pkl'
]

if all(Path(f).exists() for f in model_files):
    print('✅ ML models found and ready')
else:
    print('⚠️ ML models not found, training...')
    import subprocess
    result = subprocess.run(['python', '-m', 'ml.pipeline.train_all'], timeout=120)
    if result.returncode == 0:
        print('✅ ML models trained successfully')
    else:
        print('❌ ML model training failed')
        sys.exit(1)
"

# Initialize database
python /app/init-db.py

# Start FastAPI server
uvicorn backend.main:app --host 0.0.0.0 --port 8000
```

**Dependencies**: 
- `ml/pipeline/train_all.py` (existing)
- `ml/data/generate_synthetic.py` (existing)
- Model files must be writable in Docker volume

**Error Handling**:
- If training exceeds 120s timeout, exit with error code 1
- If training fails, log error and exit (don't start server with missing models)
- If models exist but are corrupted, training will overwrite them

---

#### 2. API Key Authentication Middleware (Requirement 2)

**Purpose**: Secure all API endpoints except public documentation with API key authentication.

**Location**: `backend/middleware/api_key_auth.py` (new file)

**Interface**:
```python
from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
import os
import logging

logger = logging.getLogger(__name__)

class ApiKeyMiddleware(BaseHTTPMiddleware):
    """
    Middleware to enforce API key authentication on protected endpoints.
    
    Public endpoints (no auth required):
    - /api/health
    - /docs
    - /redoc
    - /openapi.json
    - /
    
    Protected endpoints (require X-API-Key header):
    - All other /api/* endpoints
    """
    
    PUBLIC_PATHS = {"/api/health", "/docs", "/redoc", "/openapi.json", "/"}
    
    def __init__(self, app):
        super().__init__(app)
        self.api_key = os.getenv("API_KEY")
        
        if not self.api_key:
            logger.warning("API_KEY not configured - authentication disabled")
    
    async def dispatch(self, request: Request, call_next):
        # Skip authentication for public endpoints
        if request.url.path in self.PUBLIC_PATHS:
            return await call_next(request)
        
        # Skip authentication if API_KEY not configured
        if not self.api_key:
            return await call_next(request)
        
        # Check for X-API-Key header
        provided_key = request.headers.get("X-API-Key")
        
        if not provided_key:
            logger.warning(f"Missing API key from {self._get_client_ip(request)}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Missing API key. Include X-API-Key header in your request."
            )
        
        if provided_key != self.api_key:
            logger.warning(f"Invalid API key from {self._get_client_ip(request)}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid API key"
            )
        
        # Authentication successful
        return await call_next(request)
    
    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP for logging."""
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
        return request.client.host if request.client else "unknown"
```

**Integration in main.py**:
```python
from backend.middleware.api_key_auth import ApiKeyMiddleware

# Add after other middleware
app.add_middleware(ApiKeyMiddleware)
```

**Environment Variable**:
```bash
# .env
API_KEY=your_secret_api_key_here
```

**Testing**:
```bash
# Valid request
curl -H "X-API-Key: your_secret_api_key_here" http://localhost:8000/api/predict

# Missing key (should return 401)
curl http://localhost:8000/api/predict

# Invalid key (should return 401)
curl -H "X-API-Key: wrong_key" http://localhost:8000/api/predict

# Public endpoint (should work without key)
curl http://localhost:8000/api/health
```

---

#### 3. Alembic Environment Configuration (Requirement 4)

**Purpose**: Configure Alembic to use DATABASE_URL from environment variables instead of hardcoded values in alembic.ini.

**Location**: `backend/alembic/env.py` (modify existing)

**Interface**:
```python
# backend/alembic/env.py
import os
from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context

# Import your models' Base
from backend.models import Base

# Get Alembic config
config = context.config

# Override sqlalchemy.url with DATABASE_URL from environment
database_url = os.getenv("DATABASE_URL")
if database_url:
    config.set_main_option("sqlalchemy.url", database_url)
    print(f"Using DATABASE_URL from environment: {database_url}")
else:
    print("WARNING: DATABASE_URL not found in environment, using alembic.ini value")

# Configure logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Set target metadata
target_metadata = Base.metadata

def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
```

**Testing in Docker**:
```bash
# Inside backend container
docker exec -it edurisk-backend bash
alembic upgrade head  # Should use DATABASE_URL from docker-compose.yml
```

---

#### 4. Audit Logger Enhancement (Requirement 6)

**Purpose**: Log EXPLAIN actions to audit trail alongside PREDICT actions.

**Location**: `backend/services/audit_logger.py` (modify existing)

**Interface**:
```python
# backend/services/audit_logger.py
from sqlalchemy.ext.asyncio import AsyncSession
from backend.models.audit_log import AuditLog
from uuid import UUID
from typing import Optional

class AuditLogger:
    """Service for logging audit trail events."""
    
    @staticmethod
    async def log_predict(
        db: AsyncSession,
        student_id: UUID,
        prediction_id: UUID,
        model_version: str,
        risk_level: str,
        risk_score: int,
        alert_triggered: bool,
        performed_by: str = "api_user"
    ) -> AuditLog:
        """Log a PREDICT action."""
        audit_entry = AuditLog(
            action="PREDICT",
            student_id=student_id,
            prediction_id=prediction_id,
            performed_by=performed_by,
            details={
                "model_version": model_version,
                "risk_level": risk_level,
                "risk_score": risk_score,
                "alert_triggered": alert_triggered
            }
        )
        db.add(audit_entry)
        await db.flush()
        return audit_entry
    
    @staticmethod
    async def log_explain(
        db: AsyncSession,
        student_id: UUID,
        prediction_id: UUID,
        performed_by: str = "api_user"
    ) -> AuditLog:
        """
        Log an EXPLAIN action when SHAP explanation is requested.
        
        Requirements: 6.1, 6.2, 6.3, 6.4, 6.5, 6.6
        """
        audit_entry = AuditLog(
            action="EXPLAIN",
            student_id=student_id,
            prediction_id=prediction_id,
            performed_by=performed_by,
            details={
                "explanation_type": "SHAP"
            }
        )
        db.add(audit_entry)
        await db.flush()
        return audit_entry
```

**Integration in explain endpoint**:
```python
# backend/routes/explain.py
from backend.services.audit_logger import AuditLogger

@router.get("/explain/{student_id}")
async def get_explanation(
    student_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    # ... existing explanation logic ...
    
    # Log EXPLAIN action (Requirement 6)
    await AuditLogger.log_explain(
        db=db,
        student_id=student_id,
        prediction_id=prediction.id,
        performed_by="api_user"  # TODO: Replace with actual user ID when auth implemented
    )
    
    await db.commit()
    
    return explanation_response
```

---

#### 5. Batch Scoring Session Safety (Requirement 9)

**Purpose**: Ensure each student in a batch gets an independent database session to prevent race conditions.

**Location**: `backend/routes/predict.py` (modify existing batch endpoint)

**Interface**:
```python
# backend/routes/predict.py
import asyncio
from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from backend.db.session import get_db
from backend.schemas.student import StudentInput, BatchPredictionResponse
from backend.services.prediction_service import PredictionService

router = APIRouter()

@router.post("/batch-score", response_model=BatchPredictionResponse)
async def batch_score_students(
    students: List[StudentInput],
    prediction_service: PredictionService = Depends(get_prediction_service)
):
    """
    Score multiple students in parallel with independent database sessions.
    
    Each student gets its own database session to prevent race conditions
    and session corruption during concurrent processing.
    
    Requirements: 9.1, 9.2, 9.3, 9.4, 9.5, 9.6
    """
    async def process_student(student_data: StudentInput) -> dict:
        """Process a single student with independent DB session."""
        # Create independent session for this student
        async with get_async_session() as db:
            try:
                result = await prediction_service.predict_student(
                    student_data=student_data,
                    db=db,
                    performed_by="batch_api"
                )
                await db.commit()
                
                return {
                    "success": True,
                    "student_name": student_data.name,
                    "prediction": result
                }
            except Exception as e:
                await db.rollback()
                return {
                    "success": False,
                    "student_name": student_data.name,
                    "error": str(e)
                }
    
    # Process all students in parallel with independent sessions
    results = await asyncio.gather(
        *[process_student(student) for student in students],
        return_exceptions=False
    )
    
    # Separate successes and failures
    successes = [r for r in results if r["success"]]
    failures = [r for r in results if not r["success"]]
    
    return BatchPredictionResponse(
        total=len(students),
        successful=len(successes),
        failed=len(failures),
        results=results
    )
```

**Session Factory**:
```python
# backend/db/session.py
from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

engine = create_async_engine(DATABASE_URL, echo=False)
AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

@asynccontextmanager
async def get_async_session():
    """
    Create an independent async database session.
    
    Use this for batch processing where each item needs its own session.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
```

---

#### 6. Risk Calculator (Requirement 10)

**Purpose**: Pure functions for risk score calculation, risk level assignment, and EMI affordability.

**Location**: `backend/services/risk_calculator.py` (existing, ensure testability)

**Interface**:
```python
# backend/services/risk_calculator.py

def calculate_risk_score(
    prob_3m: float,
    prob_6m: float,
    prob_12m: float
) -> int:
    """
    Calculate composite risk score from placement probabilities.
    
    Risk score is 0-100 where higher = riskier (inverse of placement probability).
    Weighted average: 50% weight on 3m, 30% on 6m, 20% on 12m.
    
    Args:
        prob_3m: 3-month placement probability (0.0 to 1.0)
        prob_6m: 6-month placement probability (0.0 to 1.0)
        prob_12m: 12-month placement probability (0.0 to 1.0)
    
    Returns:
        Risk score from 0 to 100 (integer)
    
    Examples:
        >>> calculate_risk_score(0.9, 0.95, 0.98)
        8  # Low risk
        >>> calculate_risk_score(0.4, 0.6, 0.7)
        52  # Medium risk
        >>> calculate_risk_score(0.2, 0.3, 0.4)
        75  # High risk
    """
    # Weighted average of placement probabilities
    weighted_prob = (0.5 * prob_3m) + (0.3 * prob_6m) + (0.2 * prob_12m)
    
    # Convert to risk score (inverse)
    risk_score = int((1.0 - weighted_prob) * 100)
    
    # Clamp to 0-100 range
    return max(0, min(100, risk_score))


def assign_risk_level(risk_score: int) -> str:
    """
    Assign risk level category based on risk score.
    
    Args:
        risk_score: Risk score from 0 to 100
    
    Returns:
        Risk level: "low", "medium", or "high"
    
    Thresholds:
        - 0-33: low
        - 34-66: medium
        - 67-100: high
    
    Examples:
        >>> assign_risk_level(25)
        'low'
        >>> assign_risk_level(50)
        'medium'
        >>> assign_risk_level(75)
        'high'
    """
    if risk_score <= 33:
        return "low"
    elif risk_score <= 66:
        return "medium"
    else:
        return "high"


def calculate_emi_affordability(loan_emi: float, predicted_salary: float) -> float:
    """
    Calculate EMI affordability as percentage of salary.
    
    Args:
        loan_emi: Monthly loan EMI amount
        predicted_salary: Predicted annual salary
    
    Returns:
        EMI affordability ratio (0.0 to 1.0+)
        - < 0.3: Good affordability
        - 0.3-0.5: Moderate affordability
        - > 0.5: High risk
    
    Examples:
        >>> calculate_emi_affordability(10000, 500000)
        0.24  # Good (24% of monthly salary)
        >>> calculate_emi_affordability(20000, 500000)
        0.48  # Moderate (48% of monthly salary)
        >>> calculate_emi_affordability(30000, 500000)
        0.72  # High risk (72% of monthly salary)
    """
    if predicted_salary <= 0:
        return 1.0  # Maximum risk if no salary
    
    monthly_salary = predicted_salary / 12
    affordability = loan_emi / monthly_salary
    
    return round(affordability, 3)
```

**Unit Test Structure** (Requirement 10):
```python
# backend/services/test_risk_calculator_unit.py
import pytest
from backend.services.risk_calculator import (
    calculate_risk_score,
    assign_risk_level,
    calculate_emi_affordability
)

class TestCalculateRiskScore:
    """Test risk score calculation with various probability combinations."""
    
    def test_high_placement_probs_low_risk(self):
        """High placement probabilities should yield low risk score."""
        score = calculate_risk_score(0.9, 0.95, 0.98)
        assert 0 <= score <= 33
    
    def test_medium_placement_probs_medium_risk(self):
        """Medium placement probabilities should yield medium risk score."""
        score = calculate_risk_score(0.5, 0.6, 0.7)
        assert 34 <= score <= 66
    
    def test_low_placement_probs_high_risk(self):
        """Low placement probabilities should yield high risk score."""
        score = calculate_risk_score(0.2, 0.3, 0.4)
        assert 67 <= score <= 100
    
    def test_zero_probs_maximum_risk(self):
        """Zero placement probabilities should yield maximum risk."""
        score = calculate_risk_score(0.0, 0.0, 0.0)
        assert score == 100
    
    def test_perfect_probs_minimum_risk(self):
        """Perfect placement probabilities should yield minimum risk."""
        score = calculate_risk_score(1.0, 1.0, 1.0)
        assert score == 0
    
    def test_weighted_average_3m_dominant(self):
        """3-month probability should have 50% weight."""
        score_high_3m = calculate_risk_score(0.9, 0.3, 0.3)
        score_low_3m = calculate_risk_score(0.3, 0.9, 0.9)
        assert score_high_3m < score_low_3m  # Higher 3m prob = lower risk


class TestAssignRiskLevel:
    """Test risk level assignment with boundary values."""
    
    def test_zero_is_low(self):
        assert assign_risk_level(0) == "low"
    
    def test_boundary_33_is_low(self):
        assert assign_risk_level(33) == "low"
    
    def test_boundary_34_is_medium(self):
        assert assign_risk_level(34) == "medium"
    
    def test_boundary_66_is_medium(self):
        assert assign_risk_level(66) == "medium"
    
    def test_boundary_67_is_high(self):
        assert assign_risk_level(67) == "high"
    
    def test_hundred_is_high(self):
        assert assign_risk_level(100) == "high"


class TestCalculateEMIAffordability:
    """Test EMI affordability calculation with edge cases."""
    
    def test_good_affordability(self):
        """EMI < 30% of monthly salary is good."""
        affordability = calculate_emi_affordability(10000, 500000)
        assert affordability < 0.3
    
    def test_moderate_affordability(self):
        """EMI 30-50% of monthly salary is moderate."""
        affordability = calculate_emi_affordability(20000, 500000)
        assert 0.3 <= affordability <= 0.5
    
    def test_high_risk_affordability(self):
        """EMI > 50% of monthly salary is high risk."""
        affordability = calculate_emi_affordability(30000, 500000)
        assert affordability > 0.5
    
    def test_zero_salary_maximum_risk(self):
        """Zero salary should return maximum risk (1.0)."""
        affordability = calculate_emi_affordability(10000, 0)
        assert affordability == 1.0
    
    def test_zero_emi_zero_risk(self):
        """Zero EMI should return zero risk."""
        affordability = calculate_emi_affordability(0, 500000)
        assert affordability == 0.0
    
    def test_very_high_emi(self):
        """EMI exceeding salary should return > 1.0."""
        affordability = calculate_emi_affordability(50000, 500000)
        assert affordability > 1.0
```



### Frontend Components

#### 7. Navigation Bar Component (Requirement 7)

**Purpose**: Persistent navigation across all pages with active page highlighting and alert badge.

**Location**: `frontend/components/layout/NavigationBar.tsx` (new file)

**Interface**:
```typescript
// frontend/components/layout/NavigationBar.tsx
'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { Home, AlertTriangle, UserPlus, FileText } from 'lucide-react';
import { Badge } from '@/components/ui/badge';
import { useEffect, useState } from 'react';

interface NavItem {
  href: string;
  label: string;
  icon: React.ComponentType<{ className?: string }>;
}

const NAV_ITEMS: NavItem[] = [
  { href: '/dashboard', label: 'Dashboard', icon: Home },
  { href: '/alerts', label: 'Alerts', icon: AlertTriangle },
  { href: '/student/new', label: 'New Student', icon: UserPlus },
  { href: '/docs', label: 'API Docs', icon: FileText },
];

export function NavigationBar() {
  const pathname = usePathname();
  const [alertCount, setAlertCount] = useState<number>(0);

  // Fetch high-risk alert count
  useEffect(() => {
    async function fetchAlertCount() {
      try {
        const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/alerts`);
        const data = await response.json();
        const highRiskCount = data.filter((alert: any) => alert.risk_level === 'high').length;
        setAlertCount(highRiskCount);
      } catch (error) {
        console.error('Failed to fetch alert count:', error);
      }
    }

    fetchAlertCount();
    // Refresh every 30 seconds
    const interval = setInterval(fetchAlertCount, 30000);
    return () => clearInterval(interval);
  }, []);

  return (
    <nav className="border-b bg-white">
      <div className="container mx-auto px-4">
        <div className="flex h-16 items-center justify-between">
          {/* Logo */}
          <div className="flex items-center space-x-2">
            <div className="text-2xl font-bold text-primary">EduRisk AI</div>
          </div>

          {/* Navigation Links */}
          <div className="flex items-center space-x-1">
            {NAV_ITEMS.map((item) => {
              const Icon = item.icon;
              const isActive = pathname === item.href;

              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={`
                    flex items-center space-x-2 px-4 py-2 rounded-md transition-colors
                    ${isActive 
                      ? 'bg-primary text-primary-foreground' 
                      : 'text-muted-foreground hover:bg-muted hover:text-foreground'
                    }
                  `}
                >
                  <Icon className="h-4 w-4" />
                  <span>{item.label}</span>
                  
                  {/* Alert badge */}
                  {item.href === '/alerts' && alertCount > 0 && (
                    <Badge variant="destructive" className="ml-1">
                      {alertCount}
                    </Badge>
                  )}
                </Link>
              );
            })}
          </div>
        </div>
      </div>
    </nav>
  );
}
```

**Layout Integration**:
```typescript
// frontend/app/layout.tsx
import { NavigationBar } from '@/components/layout/NavigationBar';

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <NavigationBar />
        <main className="container mx-auto px-4 py-8">
          {children}
        </main>
      </body>
    </html>
  );
}
```

**Responsive Design** (mobile < 768px):
```typescript
// Mobile version with hamburger menu
export function NavigationBar() {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  
  return (
    <nav className="border-b bg-white">
      {/* Desktop navigation (hidden on mobile) */}
      <div className="hidden md:flex ...">
        {/* Desktop nav items */}
      </div>
      
      {/* Mobile navigation */}
      <div className="md:hidden">
        <button onClick={() => setMobileMenuOpen(!mobileMenuOpen)}>
          <Menu className="h-6 w-6" />
        </button>
        
        {mobileMenuOpen && (
          <div className="absolute top-16 left-0 right-0 bg-white border-b shadow-lg">
            {NAV_ITEMS.map((item) => (
              <Link key={item.href} href={item.href} className="block px-4 py-3">
                {item.label}
              </Link>
            ))}
          </div>
        )}
      </div>
    </nav>
  );
}
```

---

#### 13. JWT OAuth2 Authentication (Requirement 20)

**Purpose**: Implement production-grade user authentication with JWT tokens for secure access to sensitive student risk data.

**Location**: `backend/middleware/jwt_auth.py` (new file), `backend/routes/auth.py` (new file)

**Interface**:
```python
# backend/middleware/jwt_auth.py
from datetime import datetime, timedelta
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel
import os

# Configuration
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-here")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = 24

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

class TokenData(BaseModel):
    username: Optional[str] = None
    user_id: Optional[str] = None

class Token(BaseModel):
    access_token: str
    token_type: str

class User(BaseModel):
    username: str
    email: Optional[str] = None
    full_name: Optional[str] = None
    disabled: Optional[bool] = None

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Hash a password for storing."""
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT access token.
    
    Args:
        data: Payload data to encode in the token
        expires_delta: Optional custom expiration time
    
    Returns:
        Encoded JWT token string
    
    Requirements: 20.3, 20.4, 20.5
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    """
    Validate JWT token and extract user information.
    
    Args:
        token: JWT token from Authorization header
    
    Returns:
        User object with username and metadata
    
    Raises:
        HTTPException: If token is invalid or expired
    
    Requirements: 20.7, 20.8, 20.9
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired token",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        user_id: str = payload.get("user_id")
        
        if username is None:
            raise credentials_exception
        
        token_data = TokenData(username=username, user_id=user_id)
    except JWTError:
        raise credentials_exception
    
    # In production, fetch user from database
    # For now, return user from token data
    user = User(username=token_data.username)
    
    if user is None:
        raise credentials_exception
    
    return user

async def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """
    Ensure the current user is active (not disabled).
    
    Args:
        current_user: User from JWT token
    
    Returns:
        Active user object
    
    Raises:
        HTTPException: If user is disabled
    """
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user
```

**Authentication Routes**:
```python
# backend/routes/auth.py
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from backend.middleware.jwt_auth import (
    create_access_token,
    verify_password,
    Token,
    User,
    get_current_active_user
)
from datetime import timedelta
import logging

router = APIRouter(prefix="/api/auth", tags=["authentication"])
logger = logging.getLogger(__name__)

# Mock user database (replace with real database in production)
fake_users_db = {
    "admin": {
        "username": "admin",
        "full_name": "Admin User",
        "email": "admin@edurisk.ai",
        "hashed_password": "$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW",  # "secret"
        "disabled": False,
    }
}

def authenticate_user(username: str, password: str):
    """
    Authenticate user with username and password.
    
    Args:
        username: User's username
        password: User's plain text password
    
    Returns:
        User dict if authentication succeeds, False otherwise
    
    Requirements: 20.2
    """
    user = fake_users_db.get(username)
    if not user:
        return False
    if not verify_password(password, user["hashed_password"]):
        return False
    return user

@router.post("/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    OAuth2 Password Flow login endpoint.
    
    Accepts username and password, returns JWT access token.
    
    Requirements: 20.1, 20.2, 20.3, 20.10
    """
    user = authenticate_user(form_data.username, form_data.password)
    
    if not user:
        logger.warning(f"Failed login attempt for username: {form_data.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = create_access_token(
        data={"sub": user["username"], "user_id": user["username"]}
    )
    
    logger.info(f"Successful login for user: {user['username']}")
    
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/refresh", response_model=Token)
async def refresh_token(current_user: User = Depends(get_current_active_user)):
    """
    Refresh JWT token for authenticated user.
    
    Requirements: 20.6
    """
    access_token = create_access_token(
        data={"sub": current_user.username, "user_id": current_user.username}
    )
    
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/me", response_model=User)
async def read_users_me(current_user: User = Depends(get_current_active_user)):
    """
    Get current authenticated user information.
    
    Requirements: 20.9
    """
    return current_user
```

**Integration in main.py**:
```python
# backend/main.py
from backend.routes import auth

# Add auth router
app.include_router(auth.router)

# Protect endpoints with JWT dependency
from backend.middleware.jwt_auth import get_current_active_user

@router.post("/predict")
async def predict_student(
    student_data: StudentInput,
    current_user: User = Depends(get_current_active_user),  # JWT protection
    db: AsyncSession = Depends(get_db)
):
    # ... existing prediction logic ...
    pass
```

**Environment Variables**:
```bash
# .env
SECRET_KEY=your-secret-key-min-32-characters-long
ACCESS_TOKEN_EXPIRE_HOURS=24
```

**Testing**:
```bash
# Login to get token
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=secret"

# Use token for protected endpoints
curl -H "Authorization: Bearer <token>" http://localhost:8000/api/predict
```

---

#### 14. Secure Database Credentials (Requirement 21)

**Purpose**: Ensure all database credentials are managed through environment variables with no hardcoded secrets.

**Location**: `docker-compose.yml` (modify), `.env.example` (modify), `.gitignore` (verify)

**Implementation**:

**docker-compose.yml**:
```yaml
# docker-compose.yml
version: '3.8'

services:
  postgres:
    image: postgres:15
    environment:
      POSTGRES_USER: ${POSTGRES_USER}           # From .env
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}   # From .env
      POSTGRES_DB: ${POSTGRES_DB}               # From .env
    volumes:
      - postgres_data:/var/lib/postgresql/data
    networks:
      - edurisk-network
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER}"]
      interval: 10s
      timeout: 5s
      retries: 5

  backend:
    build:
      context: .
      dockerfile: docker/Dockerfile.backend
    environment:
      DATABASE_URL: postgresql+asyncpg://${POSTGRES_USER}:${POSTGRES_PASSWORD}@postgres:5432/${POSTGRES_DB}
      REDIS_URL: redis://redis:6379/0
      SECRET_KEY: ${SECRET_KEY}
      API_KEY: ${API_KEY}
      LLM_API_KEY: ${LLM_API_KEY:-}
      LLM_PROVIDER: ${LLM_PROVIDER:-groq}
      DEBUG: ${DEBUG:-False}
      CORS_ORIGINS: ${CORS_ORIGINS}
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_started
    networks:
      - edurisk-network

volumes:
  postgres_data:

networks:
  edurisk-network:
    driver: bridge
```

**.env.example**:
```bash
# .env.example

# ⚠️ WARNING: DO NOT commit real credentials to version control
# Copy this file to .env and fill in your actual values

# Database Configuration (Requirement 21)
POSTGRES_USER=edurisk_user
POSTGRES_PASSWORD=change_this_secure_password_123
POSTGRES_DB=edurisk_db

# Authentication (Requirements 20, 21)
SECRET_KEY=change-this-to-a-random-32-character-string
API_KEY=your_api_key_here

# LLM Integration (Optional)
LLM_API_KEY=
LLM_PROVIDER=groq

# CORS Configuration (Requirement 22)
CORS_ORIGINS=http://localhost:3000,https://yourdomain.com

# Debug Mode (Requirement 5)
DEBUG=False
```

**.gitignore verification**:
```bash
# .gitignore
.env
.env.local
*.env
!.env.example
```

**Validation Script**:
```python
# docker/validate_env.py
"""
Validate that no hardcoded credentials exist in docker-compose.yml.

Requirements: 21.1, 21.2, 21.3, 21.4
"""
import yaml
import sys

def validate_docker_compose():
    """Check docker-compose.yml for hardcoded credentials."""
    with open('docker-compose.yml', 'r') as f:
        config = yaml.safe_load(f)
    
    errors = []
    
    # Check postgres service
    postgres_env = config['services']['postgres']['environment']
    for key in ['POSTGRES_USER', 'POSTGRES_PASSWORD', 'POSTGRES_DB']:
        value = postgres_env.get(key, '')
        if not value.startswith('${'):
            errors.append(f"Hardcoded credential found: {key}={value}")
    
    # Check backend DATABASE_URL
    backend_env = config['services']['backend']['environment']
    database_url = backend_env.get('DATABASE_URL', '')
    if 'password' in database_url.lower() and '${' not in database_url:
        errors.append("Hardcoded password in DATABASE_URL")
    
    if errors:
        print("❌ Security validation failed:")
        for error in errors:
            print(f"  - {error}")
        sys.exit(1)
    else:
        print("✅ No hardcoded credentials found")

if __name__ == "__main__":
    validate_docker_compose()
```

---

#### 15. Strict CORS Configuration (Requirement 22)

**Purpose**: Configure CORS to only allow known frontend domains, preventing unauthorized origins from accessing the API.

**Location**: `backend/main.py` (modify), `backend/config.py` (modify)

**Implementation**:

**Configuration**:
```python
# backend/config.py
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
from typing import List
import logging

logger = logging.getLogger(__name__)

class Configuration(BaseSettings):
    # ... existing fields ...
    
    # CORS Configuration (Requirement 22)
    cors_origins: str = Field(
        default="http://localhost:3000",
        description="Comma-separated list of allowed CORS origins"
    )
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    def get_cors_origins(self) -> List[str]:
        """
        Parse CORS_ORIGINS into list and validate.
        
        Requirements: 22.1, 22.2, 22.3, 22.4
        """
        origins = [origin.strip() for origin in self.cors_origins.split(',')]
        
        # Warn if wildcard is used
        if '*' in origins:
            logger.warning(
                "⚠️ CORS wildcard (*) detected! This is insecure for production. "
                "Set CORS_ORIGINS to specific domains."
            )
        
        # Validate each origin is a full URL
        for origin in origins:
            if origin != '*' and not origin.startswith(('http://', 'https://')):
                logger.error(f"Invalid CORS origin (must be full URL): {origin}")
                raise ValueError(f"Invalid CORS origin: {origin}")
        
        logger.info(f"CORS origins configured: {origins}")
        return origins

config = Configuration()
```

**CORS Middleware**:
```python
# backend/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.config import config

app = FastAPI(title="EduRisk AI API")

# Strict CORS Configuration (Requirement 22)
allowed_origins = config.get_cors_origins()

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,  # Specific origins only
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# Log CORS configuration on startup
@app.on_event("startup")
async def log_cors_config():
    logger.info(f"CORS configured with origins: {allowed_origins}")
    if '*' in allowed_origins:
        logger.warning("⚠️ CORS wildcard enabled - NOT recommended for production")
```

**Environment Configuration**:
```bash
# .env (development)
CORS_ORIGINS=http://localhost:3000,http://localhost:3001

# .env (production)
CORS_ORIGINS=https://edurisk.yourdomain.com,https://app.yourdomain.com
```

**Testing**:
```bash
# Valid origin (should succeed)
curl -H "Origin: http://localhost:3000" \
     -H "Access-Control-Request-Method: POST" \
     -X OPTIONS http://localhost:8000/api/predict

# Invalid origin (should be rejected)
curl -H "Origin: https://malicious-site.com" \
     -H "Access-Control-Request-Method: POST" \
     -X OPTIONS http://localhost:8000/api/predict
```

---

### Frontend Components

#### 7. Navigation Bar Component (Requirement 7)

**Purpose**: Persistent navigation across all pages with active page highlighting and alert badge.

**Location**: `frontend/components/layout/NavigationBar.tsx` (new file)

**Interface**:
```typescript
// frontend/components/layout/NavigationBar.tsx
'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { Home, AlertTriangle, UserPlus, FileText } from 'lucide-react';
import { Badge } from '@/components/ui/badge';
import { useEffect, useState } from 'react';

interface NavItem {
  href: string;
  label: string;
  icon: React.ComponentType<{ className?: string }>;
}

const NAV_ITEMS: NavItem[] = [
  { href: '/dashboard', label: 'Dashboard', icon: Home },
  { href: '/alerts', label: 'Alerts', icon: AlertTriangle },
  { href: '/student/new', label: 'New Student', icon: UserPlus },
  { href: '/docs', label: 'API Docs', icon: FileText },
];

export function NavigationBar() {
  const pathname = usePathname();
  const [alertCount, setAlertCount] = useState<number>(0);

  // Fetch high-risk alert count
  useEffect(() => {
    async function fetchAlertCount() {
      try {
        const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/alerts`);
        const data = await response.json();
        const highRiskCount = data.filter((alert: any) => alert.risk_level === 'high').length;
        setAlertCount(highRiskCount);
      } catch (error) {
        console.error('Failed to fetch alert count:', error);
      }
    }

    fetchAlertCount();
    // Refresh every 30 seconds
    const interval = setInterval(fetchAlertCount, 30000);
    return () => clearInterval(interval);
  }, []);

  return (
    <nav className="border-b bg-white">
      <div className="container mx-auto px-4">
        <div className="flex h-16 items-center justify-between">
          {/* Logo */}
          <div className="flex items-center space-x-2">
            <div className="text-2xl font-bold text-primary">EduRisk AI</div>
          </div>

          {/* Navigation Links */}
          <div className="flex items-center space-x-1">
            {NAV_ITEMS.map((item) => {
              const Icon = item.icon;
              const isActive = pathname === item.href;

              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={`
                    flex items-center space-x-2 px-4 py-2 rounded-md transition-colors
                    ${isActive 
                      ? 'bg-primary text-primary-foreground' 
                      : 'text-muted-foreground hover:bg-muted hover:text-foreground'
                    }
                  `}
                >
                  <Icon className="h-4 w-4" />
                  <span>{item.label}</span>
                  
                  {/* Alert badge */}
                  {item.href === '/alerts' && alertCount > 0 && (
                    <Badge variant="destructive" className="ml-1">
                      {alertCount}
                    </Badge>
                  )}
                </Link>
              );
            })}
          </div>
        </div>
      </div>
    </nav>
  );
}
```

**Layout Integration**:
```typescript
// frontend/app/layout.tsx
import { NavigationBar } from '@/components/layout/NavigationBar';

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <NavigationBar />
        <main className="container mx-auto px-4 py-8">
          {children}
        </main>
      </body>
    </html>
  );
}
```

**Responsive Design** (mobile < 768px):
```typescript
// Mobile version with hamburger menu
export function NavigationBar() {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  
  return (
    <nav className="border-b bg-white">
      {/* Desktop navigation (hidden on mobile) */}
      <div className="hidden md:flex ...">
        {/* Desktop nav items */}
      </div>
      
      {/* Mobile navigation */}
      <div className="md:hidden">
        <button onClick={() => setMobileMenuOpen(!mobileMenuOpen)}>
          <Menu className="h-6 w-6" />
        </button>
        
        {mobileMenuOpen && (
          <div className="absolute top-16 left-0 right-0 bg-white border-b shadow-lg">
            {NAV_ITEMS.map((item) => (
              <Link key={item.href} href={item.href} className="block px-4 py-3">
                {item.label}
              </Link>
            ))}
          </div>
        )}
      </div>
    </nav>
  );
}
```

---

#### 8. Dashboard Add Student Button (Requirement 8)

**Purpose**: Prominent button in dashboard header to navigate to student creation form.

**Location**: `frontend/app/dashboard/page.tsx` (modify existing)

**Interface**:
```typescript
// frontend/app/dashboard/page.tsx
import { Button } from '@/components/ui/button';
import { Plus } from 'lucide-react';
import Link from 'next/link';

export default function DashboardPage() {
  return (
    <div className="space-y-6">
      {/* Dashboard Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Dashboard</h1>
          <p className="text-muted-foreground">
            Monitor student placement risk across your portfolio
          </p>
        </div>
        
        {/* Add Student Button (Requirement 8) */}
        <Link href="/student/new">
          <Button size="lg" className="gap-2">
            <Plus className="h-5 w-5" />
            Add Student
          </Button>
        </Link>
      </div>

      {/* Dashboard Content */}
      <StudentTable />
      <PortfolioHeatmap />
    </div>
  );
}
```

---

#### 9. Salary Card EMI Context (Requirement 11)

**Purpose**: Display EMI affordability percentage with color-coded risk indicators in salary card.

**Location**: `frontend/components/student/SalaryRangeCard.tsx` (modify existing)

**Interface**:
```typescript
// frontend/components/student/SalaryRangeCard.tsx
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip';
import { Info } from 'lucide-react';

interface SalaryRangeCardProps {
  salaryMin: number;
  salaryMax: number;
  confidence: number;
  emiAffordability?: number;  // 0.0 to 1.0+
}

export function SalaryRangeCard({ 
  salaryMin, 
  salaryMax, 
  confidence,
  emiAffordability 
}: SalaryRangeCardProps) {
  // Format salary in lakhs
  const formatSalary = (amount: number) => {
    return `₹${(amount / 100000).toFixed(1)}L`;
  };

  // Determine EMI affordability status
  const getAffordabilityStatus = (affordability: number) => {
    if (affordability < 0.3) {
      return { label: 'Good', color: 'bg-green-100 text-green-800', textColor: 'text-green-600' };
    } else if (affordability <= 0.5) {
      return { label: 'Moderate', color: 'bg-amber-100 text-amber-800', textColor: 'text-amber-600' };
    } else {
      return { label: 'High Risk', color: 'bg-red-100 text-red-800', textColor: 'text-red-600' };
    }
  };

  const affordabilityPct = emiAffordability ? (emiAffordability * 100).toFixed(1) : null;
  const affordabilityStatus = emiAffordability ? getAffordabilityStatus(emiAffordability) : null;

  return (
    <Card>
      <CardHeader>
        <CardTitle>Expected Salary Range</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Salary Range */}
        <div className="flex items-baseline justify-between">
          <div className="text-3xl font-bold">
            {formatSalary(salaryMin)} - {formatSalary(salaryMax)}
          </div>
          <Badge variant="outline">{(confidence * 100).toFixed(0)}% confidence</Badge>
        </div>

        {/* EMI Affordability (Requirement 11) */}
        {affordabilityPct && affordabilityStatus && (
          <div className="pt-4 border-t">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span className="text-sm font-medium">EMI Affordability</span>
                <TooltipProvider>
                  <Tooltip>
                    <TooltipTrigger>
                      <Info className="h-4 w-4 text-muted-foreground" />
                    </TooltipTrigger>
                    <TooltipContent>
                      <p className="max-w-xs">
                        Percentage of expected salary required for loan repayment. 
                        Lower is better. &lt;30% is good, 30-50% is moderate, &gt;50% is high risk.
                      </p>
                    </TooltipContent>
                  </Tooltip>
                </TooltipProvider>
              </div>
              
              <div className="flex items-center gap-2">
                <span className={`text-2xl font-bold ${affordabilityStatus.textColor}`}>
                  {affordabilityPct}%
                </span>
                <Badge className={affordabilityStatus.color}>
                  {affordabilityStatus.label}
                </Badge>
              </div>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
```

---

#### 10. Risk Score Gauge Visualization (Requirement 12)

**Purpose**: Circular gauge showing risk score 0-100 with color zones and animation.

**Location**: `frontend/components/student/RiskScoreGauge.tsx` (new file)

**Interface**:
```typescript
// frontend/components/student/RiskScoreGauge.tsx
'use client';

import { useEffect, useState } from 'react';

interface RiskScoreGaugeProps {
  riskScore: number;  // 0-100
  size?: number;      // Diameter in pixels
}

export function RiskScoreGauge({ riskScore, size = 200 }: RiskScoreGaugeProps) {
  const [animatedScore, setAnimatedScore] = useState(0);

  // Animate from 0 to actual score on mount
  useEffect(() => {
    const duration = 1000; // 1 second
    const steps = 60;
    const increment = riskScore / steps;
    let current = 0;

    const timer = setInterval(() => {
      current += increment;
      if (current >= riskScore) {
        setAnimatedScore(riskScore);
        clearInterval(timer);
      } else {
        setAnimatedScore(Math.floor(current));
      }
    }, duration / steps);

    return () => clearInterval(timer);
  }, [riskScore]);

  // Determine color based on risk score
  const getColor = (score: number) => {
    if (score <= 33) return '#22c55e'; // green
    if (score <= 66) return '#f59e0b'; // amber
    return '#ef4444'; // red
  };

  // Calculate arc parameters
  const radius = (size - 20) / 2;
  const circumference = 2 * Math.PI * radius;
  const arcLength = (animatedScore / 100) * circumference * 0.75; // 270 degrees (0.75 of circle)
  const strokeDasharray = `${arcLength} ${circumference}`;

  return (
    <div className="relative" style={{ width: size, height: size }}>
      <svg width={size} height={size} className="transform -rotate-[135deg]">
        {/* Background arc */}
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke="#e5e7eb"
          strokeWidth="12"
          strokeDasharray={`${circumference * 0.75} ${circumference}`}
        />
        
        {/* Colored arc */}
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke={getColor(animatedScore)}
          strokeWidth="12"
          strokeDasharray={strokeDasharray}
          strokeLinecap="round"
          className="transition-all duration-100"
        />
      </svg>

      {/* Center text */}
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <div className="text-4xl font-bold" style={{ color: getColor(animatedScore) }}>
          {animatedScore}
        </div>
        <div className="text-sm text-muted-foreground">Risk Score</div>
      </div>
    </div>
  );
}
```

**Integration in RiskScoreDisplay**:
```typescript
// frontend/components/student/RiskScoreDisplay.tsx
import { RiskScoreGauge } from './RiskScoreGauge';

export function RiskScoreDisplay({ riskScore, riskLevel }: Props) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Risk Assessment</CardTitle>
      </CardHeader>
      <CardContent className="flex flex-col items-center space-y-4">
        <RiskScoreGauge riskScore={riskScore} size={200} />
        <Badge variant={getRiskVariant(riskLevel)}>
          {riskLevel.toUpperCase()} RISK
        </Badge>
      </CardContent>
    </Card>
  );
}
```

---

#### 11. Dashboard Empty State (Requirement 13)

**Purpose**: Friendly empty state with call-to-action when no students exist.

**Location**: `frontend/components/dashboard/EmptyState.tsx` (new file)

**Interface**:
```typescript
// frontend/components/dashboard/EmptyState.tsx
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { UserPlus, FileSpreadsheet } from 'lucide-react';
import Link from 'next/link';

export function EmptyState() {
  return (
    <Card className="border-dashed">
      <CardContent className="flex flex-col items-center justify-center py-16 space-y-6">
        {/* Icon */}
        <div className="rounded-full bg-muted p-6">
          <FileSpreadsheet className="h-12 w-12 text-muted-foreground" />
        </div>

        {/* Message */}
        <div className="text-center space-y-2">
          <h3 className="text-2xl font-semibold">No students yet</h3>
          <p className="text-muted-foreground max-w-md">
            Get started by adding your first student to assess their placement risk 
            and receive AI-powered recommendations.
          </p>
        </div>

        {/* Call to Action */}
        <div className="flex gap-4">
          <Link href="/student/new">
            <Button size="lg" className="gap-2">
              <UserPlus className="h-5 w-5" />
              Add Your First Student
            </Button>
          </Link>
          
          <Link href="/docs">
            <Button size="lg" variant="outline" className="gap-2">
              View API Documentation
            </Button>
          </Link>
        </div>
      </CardContent>
    </Card>
  );
}
```

**Integration in Dashboard**:
```typescript
// frontend/app/dashboard/page.tsx
import { EmptyState } from '@/components/dashboard/EmptyState';
import { StudentTable } from '@/components/dashboard/StudentTable';

export default async function DashboardPage() {
  const students = await fetchStudents();

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold">Dashboard</h1>
        <Link href="/student/new">
          <Button size="lg" className="gap-2">
            <Plus className="h-5 w-5" />
            Add Student
          </Button>
        </Link>
      </div>

      {/* Show empty state or student table */}
      {students.length === 0 ? (
        <EmptyState />
      ) : (
        <>
          <StudentTable students={students} />
          <PortfolioHeatmap />
        </>
      )}
    </div>
  );
}
```

---

#### 12. CSV Batch Upload UI (Requirement 14)

**Purpose**: File upload interface for batch scoring multiple students from CSV.

**Location**: `frontend/app/student/batch/page.tsx` (new file)

**Interface**:
```typescript
// frontend/app/student/batch/page.tsx
'use client';

import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Upload, CheckCircle, XCircle } from 'lucide-react';
import Papa from 'papaparse';

interface ParsedStudent {
  name: string;
  course_type: string;
  institute_tier: number;
  cgpa: number;
  year_of_grad: number;
  loan_amount: number;
  loan_emi: number;
}

interface BatchResult {
  success: boolean;
  student_name: string;
  prediction?: any;
  error?: string;
}

export default function BatchUploadPage() {
  const [file, setFile] = useState<File | null>(null);
  const [students, setStudents] = useState<ParsedStudent[]>([]);
  const [results, setResults] = useState<BatchResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0];
    if (!selectedFile) return;

    if (!selectedFile.name.endsWith('.csv')) {
      setError('Please select a CSV file');
      return;
    }

    setFile(selectedFile);
    setError(null);

    // Parse CSV
    Papa.parse(selectedFile, {
      header: true,
      skipEmptyLines: true,
      complete: (results) => {
        const parsed = results.data as ParsedStudent[];
        
        // Validate required columns
        const requiredColumns = ['name', 'course_type', 'institute_tier', 'cgpa', 
                                 'year_of_grad', 'loan_amount', 'loan_emi'];
        const hasAllColumns = requiredColumns.every(col => 
          parsed.length > 0 && col in parsed[0]
        );

        if (!hasAllColumns) {
          setError(`CSV must contain columns: ${requiredColumns.join(', ')}`);
          return;
        }

        if (parsed.length > 500) {
          setError('Maximum 500 students per batch');
          return;
        }

        setStudents(parsed);
      },
      error: (error) => {
        setError(`Failed to parse CSV: ${error.message}`);
      }
    });
  };

  const handleSubmit = async () => {
    if (students.length === 0) return;

    setLoading(true);
    setError(null);

    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/batch-score`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-API-Key': process.env.NEXT_PUBLIC_API_KEY || '',
        },
        body: JSON.stringify(students),
      });

      if (!response.ok) {
        throw new Error('Batch scoring failed');
      }

      const data = await response.json();
      setResults(data.results);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold">Batch Upload</h1>
        <p className="text-muted-foreground">
          Upload a CSV file to score multiple students at once
        </p>
      </div>

      {/* File Upload */}
      <Card>
        <CardHeader>
          <CardTitle>Upload CSV File</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center gap-4">
            <input
              type="file"
              accept=".csv"
              onChange={handleFileChange}
              className="hidden"
              id="csv-upload"
            />
            <label htmlFor="csv-upload">
              <Button variant="outline" className="gap-2" asChild>
                <span>
                  <Upload className="h-4 w-4" />
                  Select CSV File
                </span>
              </Button>
            </label>
            {file && <span className="text-sm text-muted-foreground">{file.name}</span>}
          </div>

          {error && (
            <div className="text-sm text-destructive">{error}</div>
          )}

          {students.length > 0 && (
            <div className="space-y-4">
              <div className="text-sm text-muted-foreground">
                {students.length} students ready to process
              </div>
              
              <Button 
                onClick={handleSubmit} 
                disabled={loading}
                className="gap-2"
              >
                {loading ? 'Processing...' : 'Submit Batch'}
              </Button>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Results */}
      {results.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Results</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              <div className="flex gap-4 text-sm">
                <span className="text-green-600 flex items-center gap-1">
                  <CheckCircle className="h-4 w-4" />
                  {results.filter(r => r.success).length} successful
                </span>
                <span className="text-red-600 flex items-center gap-1">
                  <XCircle className="h-4 w-4" />
                  {results.filter(r => !r.success).length} failed
                </span>
              </div>

              {/* Failed items */}
              {results.filter(r => !r.success).map((result, idx) => (
                <div key={idx} className="text-sm text-destructive">
                  {result.student_name}: {result.error}
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
```

**CSV Template**:
```csv
name,course_type,institute_tier,cgpa,year_of_grad,loan_amount,loan_emi,institute_name,cgpa_scale,internship_count,internship_months,internship_employer_type,certifications,region
John Doe,Engineering,1,8.5,2024,500000,10000,IIT Delhi,10,2,6,Startup,AWS Certified,North
Jane Smith,MBA,2,7.2,2024,800000,15000,IIM Bangalore,10,1,3,MNC,None,South
```

---

#### 13. Frontend Login Portal (Requirement 23)

**Purpose**: Secure login screen for user authentication before accessing the application.

**Location**: `frontend/app/login/page.tsx` (new file), `frontend/lib/auth.ts` (new file)

**Interface**:
```typescript
// frontend/app/login/page.tsx
'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { login } from '@/lib/auth';

export default function LoginPage() {
  const router = useRouter();
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    // Validate inputs (Requirement 23.8)
    if (!username.trim() || !password.trim()) {
      setError('Please enter both username and password');
      return;
    }

    setLoading(true);

    try {
      // Attempt login (Requirement 23.3, 23.4, 23.5)
      await login(username, password);
      
      // Redirect to dashboard on success
      router.push('/dashboard');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Login failed. Please check your credentials.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-50 to-indigo-100 p-4">
      <Card className="w-full max-w-md">
        <CardHeader className="space-y-4">
          {/* Logo and Branding (Requirement 23.7) */}
          <div className="flex justify-center">
            <div className="text-4xl font-bold text-primary">EduRisk AI</div>
          </div>
          <CardTitle className="text-2xl text-center">Welcome Back</CardTitle>
          <CardDescription className="text-center">
            Sign in to access your student risk assessment dashboard
          </CardDescription>
        </CardHeader>

        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            {/* Error Alert (Requirement 23.3) */}
            {error && (
              <Alert variant="destructive">
                <AlertDescription>{error}</AlertDescription>
              </Alert>
            )}

            {/* Username Field (Requirement 23.2) */}
            <div className="space-y-2">
              <Label htmlFor="username">Username</Label>
              <Input
                id="username"
                type="text"
                placeholder="Enter your username"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                disabled={loading}
                required
              />
            </div>

            {/* Password Field (Requirement 23.2) */}
            <div className="space-y-2">
              <Label htmlFor="password">Password</Label>
              <Input
                id="password"
                type="password"
                placeholder="Enter your password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                disabled={loading}
                required
              />
            </div>

            {/* Forgot Password Link (Requirement 23.6) */}
            <div className="text-right">
              <a href="#" className="text-sm text-primary hover:underline">
                Forgot password?
              </a>
            </div>

            {/* Submit Button */}
            <Button type="submit" className="w-full" disabled={loading}>
              {loading ? 'Signing in...' : 'Sign In'}
            </Button>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
```

---

#### 14. Frontend Auth State Management (Requirement 24)

**Purpose**: Centralized authentication state management with automatic token handling and route protection.

**Location**: `frontend/lib/auth.ts` (new file), `frontend/hooks/useAuth.ts` (new file), `frontend/middleware.ts` (new file)

**Interface**:
```typescript
// frontend/lib/auth.ts
/**
 * Authentication utilities for EduRisk AI frontend.
 * 
 * Requirements: 24.1, 24.2, 24.3, 24.4, 24.5, 24.6, 24.7
 */

const TOKEN_KEY = 'edurisk_auth_token';
const USER_KEY = 'edurisk_user';

interface AuthTokens {
  access_token: string;
  token_type: string;
}

interface User {
  username: string;
  email?: string;
  full_name?: string;
}

/**
 * Store JWT token securely.
 * 
 * Requirements: 24.1
 */
export function setAuthToken(token: string): void {
  if (typeof window !== 'undefined') {
    localStorage.setItem(TOKEN_KEY, token);
  }
}

/**
 * Retrieve stored JWT token.
 * 
 * Requirements: 24.1
 */
export function getAuthToken(): string | null {
  if (typeof window !== 'undefined') {
    return localStorage.getItem(TOKEN_KEY);
  }
  return null;
}

/**
 * Remove stored JWT token.
 * 
 * Requirements: 24.4
 */
export function clearAuthToken(): void {
  if (typeof window !== 'undefined') {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(USER_KEY);
  }
}

/**
 * Store user information.
 * 
 * Requirements: 24.5
 */
export function setUser(user: User): void {
  if (typeof window !== 'undefined') {
    localStorage.setItem(USER_KEY, JSON.stringify(user));
  }
}

/**
 * Retrieve stored user information.
 * 
 * Requirements: 24.5
 */
export function getUser(): User | null {
  if (typeof window !== 'undefined') {
    const userStr = localStorage.getItem(USER_KEY);
    return userStr ? JSON.parse(userStr) : null;
  }
  return null;
}

/**
 * Login with username and password.
 * 
 * Requirements: 24.1, 24.2
 */
export async function login(username: string, password: string): Promise<void> {
  const formData = new URLSearchParams();
  formData.append('username', username);
  formData.append('password', password);

  const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/auth/login`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/x-www-form-urlencoded',
    },
    body: formData,
  });

  if (!response.ok) {
    throw new Error('Invalid username or password');
  }

  const data: AuthTokens = await response.json();
  
  // Store token
  setAuthToken(data.access_token);
  
  // Fetch and store user info
  await fetchUserInfo();
}

/**
 * Logout and clear stored tokens.
 * 
 * Requirements: 24.4
 */
export function logout(): void {
  clearAuthToken();
  
  // Redirect to login
  if (typeof window !== 'undefined') {
    window.location.href = '/login';
  }
}

/**
 * Fetch current user information.
 * 
 * Requirements: 24.5
 */
async function fetchUserInfo(): Promise<void> {
  const token = getAuthToken();
  
  if (!token) {
    throw new Error('No authentication token');
  }

  const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/auth/me`, {
    headers: {
      'Authorization': `Bearer ${token}`,
    },
  });

  if (!response.ok) {
    throw new Error('Failed to fetch user info');
  }

  const user: User = await response.json();
  setUser(user);
}

/**
 * Create API client with automatic token injection.
 * 
 * Requirements: 24.2, 24.3
 */
export async function apiClient(
  endpoint: string,
  options: RequestInit = {}
): Promise<Response> {
  const token = getAuthToken();
  
  const headers = {
    'Content-Type': 'application/json',
    ...options.headers,
  };

  // Add Authorization header if token exists
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}${endpoint}`, {
    ...options,
    headers,
  });

  // Handle 401 Unauthorized (Requirement 24.3)
  if (response.status === 401) {
    clearAuthToken();
    if (typeof window !== 'undefined') {
      window.location.href = '/login';
    }
    throw new Error('Unauthorized');
  }

  return response;
}
```

**useAuth Hook**:
```typescript
// frontend/hooks/useAuth.ts
/**
 * React hook for accessing authentication state.
 * 
 * Requirements: 24.6
 */
'use client';

import { useState, useEffect } from 'react';
import { getAuthToken, getUser, logout as authLogout } from '@/lib/auth';

interface User {
  username: string;
  email?: string;
  full_name?: string;
}

export function useAuth() {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const [isAuthenticated, setIsAuthenticated] = useState(false);

  useEffect(() => {
    // Check for stored token and user
    const token = getAuthToken();
    const storedUser = getUser();

    if (token && storedUser) {
      setUser(storedUser);
      setIsAuthenticated(true);
    }

    setLoading(false);
  }, []);

  const logout = () => {
    authLogout();
    setUser(null);
    setIsAuthenticated(false);
  };

  return {
    user,
    loading,
    isAuthenticated,
    logout,
  };
}
```

**Route Protection Middleware**:
```typescript
// frontend/middleware.ts
/**
 * Middleware to protect routes requiring authentication.
 * 
 * Requirements: 24.7
 */
import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

const PUBLIC_ROUTES = ['/login', '/'];
const PROTECTED_ROUTES = ['/dashboard', '/alerts', '/student'];

export function middleware(request: NextRequest) {
  const token = request.cookies.get('edurisk_auth_token')?.value || 
                request.headers.get('authorization');

  const { pathname } = request.nextUrl;

  // Allow public routes
  if (PUBLIC_ROUTES.includes(pathname)) {
    return NextResponse.next();
  }

  // Check if route is protected
  const isProtectedRoute = PROTECTED_ROUTES.some(route => pathname.startsWith(route));

  if (isProtectedRoute && !token) {
    // Redirect to login if not authenticated
    const loginUrl = new URL('/login', request.url);
    return NextResponse.redirect(loginUrl);
  }

  return NextResponse.next();
}

export const config = {
  matcher: ['/((?!api|_next/static|_next/image|favicon.ico).*)'],
};
```

**Navigation Bar with User Info**:
```typescript
// frontend/components/layout/NavigationBar.tsx (updated)
import { useAuth } from '@/hooks/useAuth';
import { LogOut, User as UserIcon } from 'lucide-react';

export function NavigationBar() {
  const { user, logout } = useAuth();

  return (
    <nav className="border-b bg-white">
      <div className="container mx-auto px-4">
        <div className="flex h-16 items-center justify-between">
          {/* Logo */}
          <div className="text-2xl font-bold text-primary">EduRisk AI</div>

          {/* Navigation Links */}
          <div className="flex items-center space-x-4">
            {/* ... existing nav items ... */}

            {/* User Info (Requirement 24.5) */}
            {user && (
              <div className="flex items-center space-x-2 border-l pl-4">
                <UserIcon className="h-4 w-4" />
                <span className="text-sm font-medium">{user.username}</span>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={logout}
                  className="gap-2"
                >
                  <LogOut className="h-4 w-4" />
                  Logout
                </Button>
              </div>
            )}
          </div>
        </div>
      </div>
    </nav>
  );
}
```

**API Client Usage Example**:
```typescript
// Example: Using apiClient for authenticated requests
import { apiClient } from '@/lib/auth';

async function fetchStudents() {
  const response = await apiClient('/api/students');
  const students = await response.json();
  return students;
}

async function createPrediction(studentData: any) {
  const response = await apiClient('/api/predict', {
    method: 'POST',
    body: JSON.stringify(studentData),
  });
  const prediction = await response.json();
  return prediction;
}
```

---



```

---

#### 16. Real Kaggle Data Integration (Requirement 25)

**Purpose**: Support real Kaggle datasets for ML training alongside synthetic data, with validation and merging capabilities.

**Location**: `ml/data/kaggle_integration.py` (new file), `ml/data/README.md` (new file), `ml/data/download_kaggle.py` (new file)

**Interface**:
```python
# ml/data/kaggle_integration.py
"""
Kaggle dataset integration for EduRisk AI.

Requirements: 25.1, 25.2, 25.3, 25.4, 25.5, 25.6
"""
import pandas as pd
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# Expected schema for Kaggle datasets
REQUIRED_COLUMNS = [
    'name', 'course_type', 'institute_tier', 'cgpa', 'year_of_grad',
    'loan_amount', 'loan_emi', 'placed'
]

OPTIONAL_COLUMNS = [
    'institute_name', 'cgpa_scale', 'internship_count', 'internship_months',
    'internship_employer_type', 'certifications', 'region', 'salary'
]

def validate_kaggle_dataset(df: pd.DataFrame) -> tuple[bool, list[str]]:
    """
    Validate Kaggle dataset schema.
    
    Args:
        df: DataFrame to validate
    
    Returns:
        Tuple of (is_valid, list_of_errors)
    
    Requirements: 25.3
    """
    errors = []
    
    # Check required columns
    missing_cols = set(REQUIRED_COLUMNS) - set(df.columns)
    if missing_cols:
        errors.append(f"Missing required columns: {missing_cols}")
    
    # Check data types
    if 'cgpa' in df.columns and not pd.api.types.is_numeric_dtype(df['cgpa']):
        errors.append("Column 'cgpa' must be numeric")
    
    if 'institute_tier' in df.columns and not pd.api.types.is_integer_dtype(df['institute_tier']):
        errors.append("Column 'institute_tier' must be integer")
    
    # Check value ranges
    if 'cgpa' in df.columns:
        if (df['cgpa'] < 0).any() or (df['cgpa'] > 10).any():
            errors.append("Column 'cgpa' must be between 0 and 10")
    
    if 'institute_tier' in df.columns:
        if not df['institute_tier'].isin([1, 2, 3]).all():
            errors.append("Column 'institute_tier' must be 1, 2, or 3")
    
    is_valid = len(errors) == 0
    return is_valid, errors

def handle_missing_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add default values for missing optional columns.
    
    Args:
        df: DataFrame with potentially missing columns
    
    Returns:
        DataFrame with all columns filled
    
    Requirements: 25.6
    """
    defaults = {
        'institute_name': 'Unknown',
        'cgpa_scale': 10.0,
        'internship_count': 0,
        'internship_months': 0,
        'internship_employer_type': None,
        'certifications': None,
        'region': None,
        'salary': None
    }
    
    for col, default_value in defaults.items():
        if col not in df.columns:
            df[col] = default_value
            logger.info(f"Added missing column '{col}' with default value: {default_value}")
    
    return df

def merge_datasets(
    synthetic_df: pd.DataFrame,
    kaggle_df: Optional[pd.DataFrame] = None
) -> pd.DataFrame:
    """
    Merge synthetic and Kaggle datasets.
    
    Args:
        synthetic_df: Synthetic training data
        kaggle_df: Optional Kaggle dataset
    
    Returns:
        Merged DataFrame
    
    Requirements: 25.4
    """
    if kaggle_df is None:
        logger.info("No Kaggle data provided, using synthetic data only")
        return synthetic_df
    
    # Validate Kaggle dataset
    is_valid, errors = validate_kaggle_dataset(kaggle_df)
    if not is_valid:
        logger.error(f"Kaggle dataset validation failed: {errors}")
        logger.warning("Falling back to synthetic data only")
        return synthetic_df
    
    # Handle missing columns
    kaggle_df = handle_missing_columns(kaggle_df)
    
    # Merge datasets
    merged_df = pd.concat([synthetic_df, kaggle_df], ignore_index=True)
    
    logger.info(f"Merged datasets: {len(synthetic_df)} synthetic + {len(kaggle_df)} Kaggle = {len(merged_df)} total")
    
    return merged_df

def load_kaggle_dataset(dataset_path: str) -> Optional[pd.DataFrame]:
    """
    Load Kaggle dataset from CSV file.
    
    Args:
        dataset_path: Path to Kaggle CSV file
    
    Returns:
        DataFrame if successful, None otherwise
    
    Requirements: 25.1, 25.2
    """
    path = Path(dataset_path)
    
    if not path.exists():
        logger.warning(f"Kaggle dataset not found: {dataset_path}")
        return None
    
    try:
        df = pd.read_csv(path)
        logger.info(f"Loaded Kaggle dataset: {len(df)} rows from {dataset_path}")
        return df
    except Exception as e:
        logger.error(f"Failed to load Kaggle dataset: {e}")
        return None
```

**Download Script**:
```python
# ml/data/download_kaggle.py
"""
Script to download Kaggle datasets for EduRisk AI.

Requirements: 25.7
"""
import os
import sys
from pathlib import Path

def download_kaggle_dataset(dataset_name: str, output_dir: str = "ml/data/kaggle"):
    """
    Download dataset from Kaggle using Kaggle API.
    
    Prerequisites:
    - Install kaggle package: pip install kaggle
    - Configure Kaggle API credentials: ~/.kaggle/kaggle.json
    
    Args:
        dataset_name: Kaggle dataset identifier (e.g., "username/dataset-name")
        output_dir: Directory to save downloaded files
    """
    try:
        from kaggle.api.kaggle_api_extended import KaggleApi
    except ImportError:
        print("❌ Kaggle package not installed. Run: pip install kaggle")
        sys.exit(1)
    
    # Initialize Kaggle API
    api = KaggleApi()
    api.authenticate()
    
    # Create output directory
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    # Download dataset
    print(f"Downloading {dataset_name} to {output_dir}...")
    api.dataset_download_files(dataset_name, path=output_dir, unzip=True)
    
    print(f"✅ Dataset downloaded to {output_dir}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python download_kaggle.py <dataset-name>")
        print("Example: python download_kaggle.py username/student-placement-data")
        sys.exit(1)
    
    dataset_name = sys.argv[1]
    download_kaggle_dataset(dataset_name)
```

**Documentation**:
```markdown
# ml/data/README.md

# Kaggle Data Integration

## Expected Schema

### Required Columns
- `name` (string): Student name
- `course_type` (string): Engineering, MBA, Medicine, Law, Other
- `institute_tier` (int): 1, 2, or 3
- `cgpa` (float): 0.0 to 10.0
- `year_of_grad` (int): Graduation year
- `loan_amount` (float): Loan amount in currency
- `loan_emi` (float): Monthly EMI amount
- `placed` (int): 1 if placed, 0 if not placed

### Optional Columns
- `institute_name` (string): Name of institution
- `cgpa_scale` (float): CGPA scale (default: 10.0)
- `internship_count` (int): Number of internships
- `internship_months` (int): Total internship duration
- `internship_employer_type` (string): Startup, MNC, Government, etc.
- `certifications` (string): Comma-separated certifications
- `region` (string): Geographic region
- `salary` (float): Actual salary if placed

## Downloading Kaggle Datasets

1. Install Kaggle API:
   ```bash
   pip install kaggle
   ```

2. Configure API credentials:
   - Go to https://www.kaggle.com/account
   - Create new API token
   - Save `kaggle.json` to `~/.kaggle/`

3. Download dataset:
   ```bash
   python ml/data/download_kaggle.py username/dataset-name
   ```

## Recommended Datasets

- **Student Placement Data**: Search for "student placement" on Kaggle
- **Campus Recruitment**: Search for "campus recruitment" on Kaggle
- **Engineering Placement**: Search for "engineering placement" on Kaggle

## Usage in Training

```python
from ml.data.kaggle_integration import load_kaggle_dataset, merge_datasets
from ml.data.generate_synthetic import generate_synthetic_data

# Load datasets
synthetic_df = generate_synthetic_data(n_samples=1000)
kaggle_df = load_kaggle_dataset("ml/data/kaggle/placement_data.csv")

# Merge datasets
training_df = merge_datasets(synthetic_df, kaggle_df)

# Train models
# ...
```
```

**Integration in Training Pipeline**:
```python
# ml/pipeline/train_all.py
from ml.data.kaggle_integration import load_kaggle_dataset, merge_datasets
from ml.data.generate_synthetic import generate_synthetic_data

def prepare_training_data():
    """
    Prepare training data from synthetic and Kaggle sources.
    
    Requirements: 25.4, 25.5
    """
    # Generate synthetic data
    synthetic_df = generate_synthetic_data(n_samples=1000)
    
    # Try to load Kaggle data
    kaggle_df = load_kaggle_dataset("ml/data/kaggle/placement_data.csv")
    
    # Merge datasets
    training_df = merge_datasets(synthetic_df, kaggle_df)
    
    # Log data source
    if kaggle_df is not None:
        data_source = "mixed"
        logger.info(f"Training with mixed data: {len(synthetic_df)} synthetic + {len(kaggle_df)} Kaggle")
    else:
        data_source = "synthetic"
        logger.info(f"Training with synthetic data only: {len(synthetic_df)} samples")
    
    # Save data source to metrics
    metrics = {"data_source": data_source}
    with open("ml/models/training_metrics.json", "w") as f:
        json.dump(metrics, f)
    
    return training_df
```

---

#### 17. N+1 Query Optimization (Requirement 26)

**Purpose**: Optimize database queries to eliminate N+1 patterns and improve dashboard performance.

**Location**: `backend/routes/students.py` (modify), `backend/db/session.py` (modify)

**Interface**:
```python
# backend/routes/students.py
from sqlalchemy.orm import joinedload, selectinload
from sqlalchemy import select
from backend.models.student import Student
from backend.models.prediction import Prediction
from backend.models.audit_log import AuditLog

@router.get("/students", response_model=List[StudentResponse])
async def get_students(
    db: AsyncSession = Depends(get_db),
    limit: int = 100,
    offset: int = 0
):
    """
    Get all students with their latest predictions.
    
    Optimized to avoid N+1 queries using joinedload().
    
    Requirements: 26.1, 26.2, 26.4, 26.5
    """
    # Single query with eager loading
    stmt = (
        select(Student)
        .options(
            joinedload(Student.predictions)  # Eager load predictions
        )
        .limit(limit)
        .offset(offset)
    )
    
    result = await db.execute(stmt)
    students = result.unique().scalars().all()
    
    logger.info(f"Fetched {len(students)} students with predictions in single query")
    
    return students

@router.get("/dashboard/heatmap")
async def get_dashboard_heatmap(db: AsyncSession = Depends(get_db)):
    """
    Get heatmap data for dashboard.
    
    Optimized to execute at most 2 database queries.
    
    Requirements: 26.4
    """
    # Query 1: Get all students with latest predictions
    stmt = (
        select(Student)
        .options(joinedload(Student.predictions))
        .order_by(Student.created_at.desc())
    )
    
    result = await db.execute(stmt)
    students = result.unique().scalars().all()
    
    # Query 2: Get high-risk alert count
    alert_stmt = select(Prediction).where(Prediction.risk_level == "high")
    alert_result = await db.execute(alert_stmt)
    high_risk_count = len(alert_result.scalars().all())
    
    logger.info(f"Dashboard heatmap loaded with 2 queries: {len(students)} students, {high_risk_count} alerts")
    
    return {
        "students": students,
        "high_risk_count": high_risk_count
    }

@router.get("/students/{student_id}/audit-logs")
async def get_student_audit_logs(
    student_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """
    Get audit logs for a student.
    
    Uses selectinload() for related data.
    
    Requirements: 26.3
    """
    stmt = (
        select(AuditLog)
        .where(AuditLog.student_id == student_id)
        .options(selectinload(AuditLog.prediction))
        .order_by(AuditLog.created_at.desc())
    )
    
    result = await db.execute(stmt)
    audit_logs = result.scalars().all()
    
    return audit_logs
```

**Query Profiling Middleware**:
```python
# backend/middleware/query_profiler.py
"""
Middleware to log slow database queries.

Requirements: 26.6, 26.7
"""
import time
import logging
from starlette.middleware.base import BaseHTTPMiddleware
from backend.config import config

logger = logging.getLogger(__name__)

class QueryProfilerMiddleware(BaseHTTPMiddleware):
    """Log slow database queries for optimization."""
    
    SLOW_QUERY_THRESHOLD_MS = 100
    
    async def dispatch(self, request, call_next):
        start_time = time.time()
        
        response = await call_next(request)
        
        duration_ms = (time.time() - start_time) * 1000
        
        # Log slow requests (likely slow queries)
        if duration_ms > self.SLOW_QUERY_THRESHOLD_MS:
            logger.warning(
                f"Slow request: {request.method} {request.url.path} "
                f"took {duration_ms:.2f}ms (threshold: {self.SLOW_QUERY_THRESHOLD_MS}ms)"
            )
        
        return response
```

**Integration in main.py**:
```python
# backend/main.py
from backend.middleware.query_profiler import QueryProfilerMiddleware

# Add query profiler in DEBUG mode
if config.debug:
    app.add_middleware(QueryProfilerMiddleware)
    logger.info("Query profiling enabled (DEBUG=True)")
```

**Performance Testing**:
```python
# backend/tests/test_performance.py
"""
Performance tests for N+1 query optimization.

Requirements: 26.5
"""
import pytest
import time
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

def test_dashboard_loads_quickly_with_100_students():
    """Dashboard should load in under 500ms for 100 students."""
    # Create 100 test students
    for i in range(100):
        client.post("/api/students", json={
            "name": f"Student {i}",
            "course_type": "Engineering",
            "institute_tier": 1,
            "cgpa": 8.0,
            "year_of_grad": 2024
        })
    
    # Measure dashboard load time
    start_time = time.time()
    response = client.get("/api/students")
    duration_ms = (time.time() - start_time) * 1000
    
    assert response.status_code == 200
    assert duration_ms < 500, f"Dashboard took {duration_ms}ms (expected < 500ms)"
```

---

#### 18. Async SHAP Computation for Batch Requests (Requirement 27)

**Purpose**: Compute SHAP values asynchronously for batch requests to avoid timeouts and improve response times.

**Location**: `backend/routes/predict.py` (modify), `backend/services/shap_service.py` (new file)

**Interface**:
```python
# backend/services/shap_service.py
"""
Asynchronous SHAP computation service.

Requirements: 27.1, 27.2, 27.3, 27.4, 27.5, 27.6, 27.7
"""
import logging
import time
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from backend.models.prediction import Prediction
from ml.pipeline.explain import compute_shap_values

logger = logging.getLogger(__name__)

async def compute_shap_async(
    prediction_id: UUID,
    student_features: dict,
    db: AsyncSession
):
    """
    Compute SHAP values asynchronously and update prediction.
    
    Args:
        prediction_id: ID of prediction to update
        student_features: Feature dict for SHAP computation
        db: Database session
    
    Requirements: 27.1, 27.6
    """
    start_time = time.time()
    
    try:
        # Compute SHAP values
        shap_values = compute_shap_values(student_features)
        
        # Update prediction with SHAP values
        stmt = select(Prediction).where(Prediction.id == prediction_id)
        result = await db.execute(stmt)
        prediction = result.scalar_one_or_none()
        
        if prediction:
            prediction.shap_values = shap_values
            await db.commit()
            
            duration_ms = (time.time() - start_time) * 1000
            logger.info(f"SHAP computation completed for prediction {prediction_id} in {duration_ms:.2f}ms")
        else:
            logger.error(f"Prediction {prediction_id} not found for SHAP update")
    
    except Exception as e:
        logger.error(f"SHAP computation failed for prediction {prediction_id}: {e}")
        await db.rollback()
```

**Batch Prediction with Background Tasks**:
```python
# backend/routes/predict.py
from fastapi import BackgroundTasks
from backend.services.shap_service import compute_shap_async

@router.post("/batch-score", response_model=BatchPredictionResponse)
async def batch_score_students(
    students: List[StudentInput],
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """
    Score multiple students with async SHAP computation.
    
    Returns predictions immediately without waiting for SHAP values.
    SHAP values are computed in background and can be retrieved later.
    
    Requirements: 27.1, 27.2, 27.3, 27.4, 27.5
    """
    results = []
    
    for student_data in students:
        try:
            # Create prediction without SHAP values
            prediction = await prediction_service.predict_student(
                student_data=student_data,
                db=db,
                compute_shap=False  # Skip SHAP for now
            )
            
            # Schedule SHAP computation in background
            background_tasks.add_task(
                compute_shap_async,
                prediction_id=prediction.id,
                student_features=student_data.model_dump(),
                db=db
            )
            
            results.append({
                "success": True,
                "student_name": student_data.name,
                "prediction": prediction,
                "shap_values": None  # Will be computed asynchronously
            })
        
        except Exception as e:
            results.append({
                "success": False,
                "student_name": student_data.name,
                "error": str(e)
            })
    
    logger.info(f"Batch scoring completed: {len(results)} students processed")
    
    return BatchPredictionResponse(
        total=len(students),
        successful=len([r for r in results if r["success"]]),
        failed=len([r for r in results if not r["success"]]),
        results=results
    )

@router.get("/predictions/{prediction_id}/shap")
async def get_shap_values(
    prediction_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """
    Retrieve SHAP values for a prediction.
    
    Returns null if SHAP computation is still in progress.
    
    Requirements: 27.4
    """
    stmt = select(Prediction).where(Prediction.id == prediction_id)
    result = await db.execute(stmt)
    prediction = result.scalar_one_or_none()
    
    if not prediction:
        raise HTTPException(status_code=404, detail="Prediction not found")
    
    return {
        "prediction_id": prediction_id,
        "shap_values": prediction.shap_values,
        "computed": prediction.shap_values is not None
    }
```

**Performance Testing**:
```python
# backend/tests/test_batch_performance.py
"""
Performance tests for batch scoring.

Requirements: 27.5
"""
import pytest
import time
from fastapi.testclient import TestClient

def test_batch_score_completes_quickly():
    """Batch scoring 100 students should complete in under 5 seconds."""
    students = [
        {
            "name": f"Student {i}",
            "course_type": "Engineering",
            "institute_tier": 1,
            "cgpa": 8.0,
            "year_of_grad": 2024,
            "loan_amount": 500000,
            "loan_emi": 10000
        }
        for i in range(100)
    ]
    
    start_time = time.time()
    response = client.post("/api/batch-score", json=students)
    duration = time.time() - start_time
    
    assert response.status_code == 200
    assert duration < 5.0, f"Batch scoring took {duration}s (expected < 5s)"
    
    data = response.json()
    assert data["total"] == 100
    
    # SHAP values should be null initially
    for result in data["results"]:
        if result["success"]:
            assert result["prediction"]["shap_values"] is None
```

---

#### 19. Feature Engineering Configuration (Requirement 28)

**Purpose**: Make feature engineering weights configurable through external config files for easy tuning.

**Location**: `ml/pipeline/config.json` (new file), `ml/pipeline/feature_engineering.py` (modify)

**Interface**:
```json
// ml/pipeline/config.json
{
  "feature_weights": {
    "internship_score_weight": 0.4,
    "certification_score_weight": 0.3,
    "regional_adjustment_weight": 0.2,
    "cgpa_weight": 0.5,
    "tier_weight": 0.3
  },
  "internship_scoring": {
    "months_per_point": 3,
    "max_score": 10,
    "employer_type_bonus": {
      "MNC": 2.0,
      "Startup": 1.5,
      "Government": 1.0,
      "Other": 0.5
    }
  },
  "certification_scoring": {
    "per_certification": 1.5,
    "max_score": 10,
    "high_value_certs": ["AWS", "Azure", "GCP", "PMP", "CFA"]
  },
  "regional_adjustments": {
    "North": 1.0,
    "South": 1.2,
    "East": 0.9,
    "West": 1.1,
    "Central": 0.8
  }
}
```

**Feature Engineer with Config Loading**:
```python
# ml/pipeline/feature_engineering.py
"""
Feature engineering with configurable weights.

Requirements: 28.1, 28.2, 28.3, 28.4, 28.5, 28.6, 28.7
"""
import json
import logging
from pathlib import Path
from typing import Dict, Any

logger = logging.getLogger(__name__)

class FeatureEngineer:
    """Feature engineering with external configuration."""
    
    DEFAULT_CONFIG = {
        "feature_weights": {
            "internship_score_weight": 0.4,
            "certification_score_weight": 0.3,
            "regional_adjustment_weight": 0.2
        },
        "internship_scoring": {
            "months_per_point": 3,
            "max_score": 10
        },
        "certification_scoring": {
            "per_certification": 1.5,
            "max_score": 10
        }
    }
    
    def __init__(self, config_path: str = "ml/pipeline/config.json"):
        """
        Initialize feature engineer with configuration.
        
        Args:
            config_path: Path to configuration JSON file
        
        Requirements: 28.1, 28.4, 28.5, 28.6
        """
        self.config = self._load_config(config_path)
        logger.info(f"FeatureEngineer initialized with config: {self.config}")
    
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """
        Load configuration from JSON file.
        
        Falls back to default config if file is missing.
        
        Requirements: 28.1, 28.4
        """
        path = Path(config_path)
        
        if not path.exists():
            logger.warning(f"Config file not found: {config_path}, using defaults")
            return self.DEFAULT_CONFIG
        
        try:
            with open(path, 'r') as f:
                config = json.load(f)
            
            # Validate config schema
            self._validate_config(config)
            
            logger.info(f"Loaded configuration from {config_path}")
            return config
        
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in config file: {e}")
            logger.warning("Using default configuration")
            return self.DEFAULT_CONFIG
        
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            logger.warning("Using default configuration")
            return self.DEFAULT_CONFIG
    
    def _validate_config(self, config: Dict[str, Any]):
        """
        Validate configuration schema.
        
        Requirements: 28.5
        """
        required_keys = ["feature_weights", "internship_scoring", "certification_scoring"]
        
        for key in required_keys:
            if key not in config:
                raise ValueError(f"Missing required config key: {key}")
    
    def calculate_internship_score(self, internship_count: int, internship_months: int) -> float:
        """
        Calculate internship score using configured weights.
        
        Requirements: 28.2, 28.3
        """
        weight = self.config["feature_weights"]["internship_score_weight"]
        months_per_point = self.config["internship_scoring"]["months_per_point"]
        max_score = self.config["internship_scoring"]["max_score"]
        
        # Calculate base score
        score = (internship_count * weight) + (internship_months / months_per_point)
        
        # Cap at max score
        score = min(score, max_score)
        
        return score
    
    def calculate_certification_score(self, certifications: str) -> float:
        """
        Calculate certification score using configured weights.
        
        Requirements: 28.2, 28.3
        """
        if not certifications or certifications == "None":
            return 0.0
        
        weight = self.config["feature_weights"]["certification_score_weight"]
        per_cert = self.config["certification_scoring"]["per_certification"]
        max_score = self.config["certification_scoring"]["max_score"]
        
        # Count certifications
        cert_list = [c.strip() for c in certifications.split(',')]
        cert_count = len(cert_list)
        
        # Calculate score
        score = cert_count * per_cert * weight
        
        # Cap at max score
        score = min(score, max_score)
        
        return score
    
    def apply_regional_adjustment(self, base_score: float, region: str) -> float:
        """
        Apply regional adjustment using configured weights.
        
        Requirements: 28.2, 28.3
        """
        if not region or region not in self.config.get("regional_adjustments", {}):
            return base_score
        
        adjustment = self.config["regional_adjustments"][region]
        adjusted_score = base_score * adjustment
        
        return adjusted_score
```

**Usage in Training**:
```python
# ml/pipeline/train.py
from ml.pipeline.feature_engineering import FeatureEngineer

def train_model():
    """Train model with configurable feature engineering."""
    # Load feature engineer with config
    feature_engineer = FeatureEngineer(config_path="ml/pipeline/config.json")
    
    # Apply feature engineering
    for student in training_data:
        student['internship_score'] = feature_engineer.calculate_internship_score(
            student['internship_count'],
            student['internship_months']
        )
        student['certification_score'] = feature_engineer.calculate_certification_score(
            student['certifications']
        )
    
    # Train model...
```

---

## Data Models

### Database Schema Changes

**No schema changes required** - all improvements work with existing database schema. The audit_logs table already supports the EXPLAIN action type through its flexible `action` VARCHAR field.

### Existing Models Used

#### Student Model
```python
# backend/models/student.py
class Student(Base):
    __tablename__ = "students"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    course_type = Column(String, nullable=False)
    institute_name = Column(String, nullable=False)
    institute_tier = Column(Integer, nullable=False)
    cgpa = Column(Numeric(4, 2), nullable=False)
    cgpa_scale = Column(Numeric(4, 2), default=10.0)
    year_of_grad = Column(Integer, nullable=False)
    internship_count = Column(Integer, default=0)
    internship_months = Column(Integer, default=0)
    internship_employer_type = Column(String, nullable=True)
    certifications = Column(String, nullable=True)
    region = Column(String, nullable=True)
    loan_amount = Column(Numeric(12, 2), nullable=True)
    loan_emi = Column(Numeric(10, 2), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
```

#### Prediction Model
```python
# backend/models/prediction.py
class Prediction(Base):
    __tablename__ = "predictions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id = Column(UUID(as_uuid=True), ForeignKey("students.id"), nullable=False)
    model_version = Column(String, nullable=False)
    prob_placed_3m = Column(Numeric(5, 4), nullable=False)
    prob_placed_6m = Column(Numeric(5, 4), nullable=False)
    prob_placed_12m = Column(Numeric(5, 4), nullable=False)
    placement_label = Column(String, nullable=False)
    risk_score = Column(Integer, nullable=False)
    risk_level = Column(String, nullable=False)
    salary_min = Column(Numeric(12, 2), nullable=True)
    salary_max = Column(Numeric(12, 2), nullable=True)
    salary_confidence = Column(Numeric(5, 4), nullable=True)
    emi_affordability = Column(Numeric(5, 3), nullable=True)
    shap_values = Column(JSON, nullable=True)
    top_risk_drivers = Column(JSON, nullable=True)
    ai_summary = Column(Text, nullable=True)
    next_best_actions = Column(JSON, nullable=True)
    alert_triggered = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
```

#### Audit Log Model
```python
# backend/models/audit_log.py
class AuditLog(Base):
    __tablename__ = "audit_logs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    action = Column(String, nullable=False)  # "PREDICT", "EXPLAIN", "ALERT_SENT"
    student_id = Column(UUID(as_uuid=True), ForeignKey("students.id"), nullable=True)
    prediction_id = Column(UUID(as_uuid=True), ForeignKey("predictions.id"), nullable=True)
    performed_by = Column(String, nullable=False)
    details = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
```

### API Request/Response Models

#### Batch Prediction Request
```python
# backend/schemas/student.py
from typing import List
from pydantic import BaseModel, Field

class StudentInput(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    course_type: str = Field(..., pattern="^(Engineering|MBA|Medicine|Law|Other)$")
    institute_name: str = Field(..., min_length=1, max_length=200)
    institute_tier: int = Field(..., ge=1, le=3)
    cgpa: float = Field(..., ge=0.0, le=10.0)
    cgpa_scale: float = Field(default=10.0, ge=4.0, le=10.0)
    year_of_grad: int = Field(..., ge=2020, le=2030)
    internship_count: int = Field(default=0, ge=0, le=10)
    internship_months: int = Field(default=0, ge=0, le=60)
    internship_employer_type: str | None = None
    certifications: str | None = None
    region: str | None = None
    loan_amount: float | None = Field(default=None, ge=0)
    loan_emi: float | None = Field(default=None, ge=0)

class BatchPredictionRequest(BaseModel):
    students: List[StudentInput] = Field(..., max_length=500)
```

#### Batch Prediction Response
```python
# backend/schemas/prediction.py
from typing import List
from pydantic import BaseModel

class BatchPredictionResult(BaseModel):
    success: bool
    student_name: str
    prediction: PredictionResponse | None = None
    error: str | None = None

class BatchPredictionResponse(BaseModel):
    total: int
    successful: int
    failed: int
    results: List[BatchPredictionResult]
```

#### CSV Student Data
```python
# backend/schemas/csv_parser.py
from typing import List
from pydantic import BaseModel, ValidationError
import csv
from io import StringIO

class CSVStudentRow(BaseModel):
    """Single row from CSV file."""
    name: str
    course_type: str
    institute_tier: int
    cgpa: float
    year_of_grad: int
    loan_amount: float
    loan_emi: float
    institute_name: str = "Unknown"
    cgpa_scale: float = 10.0
    internship_count: int = 0
    internship_months: int = 0
    internship_employer_type: str | None = None
    certifications: str | None = None
    region: str | None = None

def parse_csv(csv_content: str) -> List[StudentInput]:
    """
    Parse CSV content into list of StudentInput objects.
    
    Args:
        csv_content: CSV file content as string
    
    Returns:
        List of validated StudentInput objects
    
    Raises:
        ValueError: If CSV is malformed or validation fails
    """
    reader = csv.DictReader(StringIO(csv_content))
    students = []
    
    for row_num, row in enumerate(reader, start=2):  # Start at 2 (header is row 1)
        try:
            csv_row = CSVStudentRow(**row)
            student = StudentInput(**csv_row.model_dump())
            students.append(student)
        except ValidationError as e:
            raise ValueError(f"Row {row_num}: {e.errors()[0]['msg']}")
    
    return students

def print_csv(students: List[StudentInput]) -> str:
    """
    Format list of StudentInput objects as CSV string.
    
    Args:
        students: List of StudentInput objects
    
    Returns:
        CSV string with header and data rows
    """
    if not students:
        return ""
    
    output = StringIO()
    fieldnames = list(students[0].model_dump().keys())
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    
    writer.writeheader()
    for student in students:
        writer.writerow(student.model_dump())
    
    return output.getvalue()
```

### Configuration Models

#### Environment Variables
```python
# backend/config.py (additions for new requirements)
class Configuration(BaseSettings):
    # Existing fields...
    
    # API Authentication (Requirement 2)
    api_key: Optional[str] = Field(
        default=None,
        description="API key for endpoint authentication"
    )
    
    # Debug Mode (Requirement 5)
    debug: bool = Field(
        default=False,
        description="Enable debug mode with detailed error traces"
    )
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
```

#### Docker Compose Environment
```yaml
# docker-compose.yml (additions)
services:
  backend:
    environment:
      # Existing vars...
      API_KEY: ${API_KEY:-}  # Optional API key
      DEBUG: ${DEBUG:-False}  # Default to False for production
```

### ML Model Files

**Required Model Files** (checked at startup):
```
ml/models/
├── placement_model_3m.pkl      # 3-month placement classifier
├── placement_model_6m.pkl      # 6-month placement classifier
├── placement_model_12m.pkl     # 12-month placement classifier
├── salary_model.pkl            # Salary range estimator
├── feature_names.json          # Feature column names
├── training_metrics.json       # Model performance metrics
└── version.json                # Model version metadata
```

**Model Metadata**:
```json
// ml/models/version.json
{
  "version": "1.0.0",
  "trained_at": "2024-01-15T10:30:00Z",
  "training_samples": 10000,
  "placement_3m_accuracy": 0.87,
  "placement_6m_accuracy": 0.89,
  "placement_12m_accuracy": 0.91,
  "salary_mae": 45000
}
```



## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property Reflection

After analyzing all acceptance criteria, the following properties were identified as suitable for property-based testing:

**Properties Identified:**
1. Risk score calculation maintains invariants (0 ≤ score ≤ 100) for all probability inputs
2. Risk score calculation is monotonic (higher placement probabilities → lower risk scores)
3. CSV parser error messages identify missing fields for any incomplete row
4. CSV parser error messages identify type mismatches for any invalid data
5. CSV parser round-trip preserves data (parse → print → parse = identity)
6. Batch processing results are independent of processing order (confluence)
7. Batch processing isolates failures (one failure doesn't affect others)

**Redundancy Analysis:**
- Properties 6 and 7 can be combined into a single comprehensive property about batch processing independence
- Properties 3 and 4 are both about error handling but test different aspects (missing vs invalid), so both should be kept
- Properties 1 and 2 are both about risk score calculation but test different aspects (range invariant vs monotonicity), so both should be kept

**Final Properties (after removing redundancy):**
1. Risk score range invariant
2. Risk score monotonicity
3. CSV parser error handling for missing fields
4. CSV parser error handling for type mismatches
5. CSV parser round-trip property
6. Batch processing independence and failure isolation

### Property 1: Risk Score Range Invariant

*For any* three placement probabilities (prob_3m, prob_6m, prob_12m) where each is between 0.0 and 1.0, the calculated risk score SHALL be an integer between 0 and 100 (inclusive).

**Validates: Requirements 10.2**

**Rationale**: The risk score is a composite metric that must always be in the valid range regardless of input probabilities. This property ensures the calculation never produces out-of-range values due to floating-point arithmetic or edge cases.

**Test Implementation**:
```python
from hypothesis import given, strategies as st
from backend.services.risk_calculator import calculate_risk_score

@given(
    prob_3m=st.floats(min_value=0.0, max_value=1.0),
    prob_6m=st.floats(min_value=0.0, max_value=1.0),
    prob_12m=st.floats(min_value=0.0, max_value=1.0)
)
def test_risk_score_range_invariant(prob_3m, prob_6m, prob_12m):
    """
    Feature: edurisk-submission-improvements, Property 1:
    Risk score range invariant
    """
    risk_score = calculate_risk_score(prob_3m, prob_6m, prob_12m)
    
    assert isinstance(risk_score, int), "Risk score must be an integer"
    assert 0 <= risk_score <= 100, f"Risk score {risk_score} out of range [0, 100]"
```

---

### Property 2: Risk Score Monotonicity

*For any* two sets of placement probabilities where all probabilities in set A are greater than or equal to the corresponding probabilities in set B, the risk score for set A SHALL be less than or equal to the risk score for set B.

**Validates: Requirements 10.2**

**Rationale**: Higher placement probabilities should always result in lower risk scores. This monotonicity property ensures the risk calculation is logically consistent with the definition of risk.

**Test Implementation**:
```python
from hypothesis import given, strategies as st, assume
from backend.services.risk_calculator import calculate_risk_score

@given(
    prob_3m_a=st.floats(min_value=0.0, max_value=1.0),
    prob_6m_a=st.floats(min_value=0.0, max_value=1.0),
    prob_12m_a=st.floats(min_value=0.0, max_value=1.0),
    prob_3m_b=st.floats(min_value=0.0, max_value=1.0),
    prob_6m_b=st.floats(min_value=0.0, max_value=1.0),
    prob_12m_b=st.floats(min_value=0.0, max_value=1.0)
)
def test_risk_score_monotonicity(prob_3m_a, prob_6m_a, prob_12m_a, 
                                  prob_3m_b, prob_6m_b, prob_12m_b):
    """
    Feature: edurisk-submission-improvements, Property 2:
    Risk score monotonicity
    """
    # Only test when A has higher or equal probabilities than B
    assume(prob_3m_a >= prob_3m_b)
    assume(prob_6m_a >= prob_6m_b)
    assume(prob_12m_a >= prob_12m_b)
    
    risk_score_a = calculate_risk_score(prob_3m_a, prob_6m_a, prob_12m_a)
    risk_score_b = calculate_risk_score(prob_3m_b, prob_6m_b, prob_12m_b)
    
    assert risk_score_a <= risk_score_b, \
        f"Higher probabilities should yield lower risk: {risk_score_a} > {risk_score_b}"
```

---

### Property 3: CSV Parser Error Handling for Missing Fields

*For any* CSV row with one or more required fields missing, the parser SHALL return a descriptive error message that identifies which field is missing.

**Validates: Requirements 19.2**

**Rationale**: Clear error messages are essential for users to correct CSV formatting issues. This property ensures the parser always provides actionable feedback for missing fields.

**Test Implementation**:
```python
from hypothesis import given, strategies as st
from backend.schemas.csv_parser import parse_csv
import pytest

REQUIRED_FIELDS = ['name', 'course_type', 'institute_tier', 'cgpa', 
                   'year_of_grad', 'loan_amount', 'loan_emi']

@given(
    missing_field=st.sampled_from(REQUIRED_FIELDS),
    name=st.text(min_size=1, max_size=50),
    course_type=st.sampled_from(['Engineering', 'MBA', 'Medicine']),
    institute_tier=st.integers(min_value=1, max_value=3),
    cgpa=st.floats(min_value=0.0, max_value=10.0),
    year_of_grad=st.integers(min_value=2020, max_value=2030),
    loan_amount=st.floats(min_value=0, max_value=10000000),
    loan_emi=st.floats(min_value=0, max_value=100000)
)
def test_csv_parser_missing_field_error(missing_field, name, course_type, 
                                         institute_tier, cgpa, year_of_grad,
                                         loan_amount, loan_emi):
    """
    Feature: edurisk-submission-improvements, Property 3:
    CSV parser error handling for missing fields
    """
    # Build CSV row with one field missing
    row_data = {
        'name': name,
        'course_type': course_type,
        'institute_tier': institute_tier,
        'cgpa': cgpa,
        'year_of_grad': year_of_grad,
        'loan_amount': loan_amount,
        'loan_emi': loan_emi
    }
    
    # Remove the randomly selected field
    del row_data[missing_field]
    
    # Build CSV string
    header = ','.join(row_data.keys())
    values = ','.join(str(v) for v in row_data.values())
    csv_content = f"{header}\n{values}"
    
    # Parse should raise error mentioning the missing field
    with pytest.raises(ValueError) as exc_info:
        parse_csv(csv_content)
    
    error_message = str(exc_info.value).lower()
    assert missing_field.lower() in error_message, \
        f"Error message should mention missing field '{missing_field}': {error_message}"
```

---

### Property 4: CSV Parser Error Handling for Type Mismatches

*For any* CSV row with a field containing data of the wrong type (e.g., text in a numeric field), the parser SHALL return a descriptive error message that identifies the type mismatch.

**Validates: Requirements 19.3**

**Rationale**: Type validation is critical for data integrity. This property ensures the parser catches type errors and provides clear feedback.

**Test Implementation**:
```python
from hypothesis import given, strategies as st
from backend.schemas.csv_parser import parse_csv
import pytest

NUMERIC_FIELDS = ['institute_tier', 'cgpa', 'year_of_grad', 'loan_amount', 'loan_emi']

@given(
    invalid_field=st.sampled_from(NUMERIC_FIELDS),
    invalid_value=st.text(min_size=1, max_size=20).filter(lambda x: not x.replace('.', '').isdigit())
)
def test_csv_parser_type_mismatch_error(invalid_field, invalid_value):
    """
    Feature: edurisk-submission-improvements, Property 4:
    CSV parser error handling for type mismatches
    """
    # Build valid CSV row
    row_data = {
        'name': 'John Doe',
        'course_type': 'Engineering',
        'institute_tier': '1',
        'cgpa': '8.5',
        'year_of_grad': '2024',
        'loan_amount': '500000',
        'loan_emi': '10000'
    }
    
    # Inject invalid value into randomly selected numeric field
    row_data[invalid_field] = invalid_value
    
    # Build CSV string
    header = ','.join(row_data.keys())
    values = ','.join(str(v) for v in row_data.values())
    csv_content = f"{header}\n{values}"
    
    # Parse should raise error mentioning type issue
    with pytest.raises(ValueError) as exc_info:
        parse_csv(csv_content)
    
    error_message = str(exc_info.value).lower()
    # Error should mention either the field name or type-related keywords
    assert (invalid_field.lower() in error_message or 
            any(keyword in error_message for keyword in ['type', 'invalid', 'number', 'integer', 'float'])), \
        f"Error message should indicate type mismatch: {error_message}"
```

---

### Property 5: CSV Parser Round-Trip Preservation

*For any* valid StudentInput object, serializing it to CSV format then parsing it back SHALL produce an equivalent StudentInput object with all fields preserved.

**Validates: Requirements 19.5**

**Rationale**: This is the gold standard for parser correctness. If serialization and deserialization are inverses, the parser is correct. This property ensures no data loss or corruption during CSV round-trips.

**Test Implementation**:
```python
from hypothesis import given, strategies as st
from backend.schemas.csv_parser import parse_csv, print_csv
from backend.schemas.student import StudentInput

@given(
    name=st.text(min_size=1, max_size=100),
    course_type=st.sampled_from(['Engineering', 'MBA', 'Medicine', 'Law', 'Other']),
    institute_tier=st.integers(min_value=1, max_value=3),
    cgpa=st.floats(min_value=0.0, max_value=10.0, allow_nan=False, allow_infinity=False),
    year_of_grad=st.integers(min_value=2020, max_value=2030),
    loan_amount=st.floats(min_value=0, max_value=10000000, allow_nan=False, allow_infinity=False),
    loan_emi=st.floats(min_value=0, max_value=100000, allow_nan=False, allow_infinity=False)
)
def test_csv_parser_round_trip(name, course_type, institute_tier, cgpa, 
                                year_of_grad, loan_amount, loan_emi):
    """
    Feature: edurisk-submission-improvements, Property 5:
    CSV parser round-trip preservation
    """
    # Create original student object
    original = StudentInput(
        name=name,
        course_type=course_type,
        institute_name="Test Institute",
        institute_tier=institute_tier,
        cgpa=cgpa,
        year_of_grad=year_of_grad,
        loan_amount=loan_amount,
        loan_emi=loan_emi
    )
    
    # Round trip: object → CSV → object
    csv_string = print_csv([original])
    parsed_students = parse_csv(csv_string)
    
    assert len(parsed_students) == 1, "Should parse exactly one student"
    parsed = parsed_students[0]
    
    # Verify all fields are preserved (with floating-point tolerance)
    assert parsed.name == original.name
    assert parsed.course_type == original.course_type
    assert parsed.institute_tier == original.institute_tier
    assert abs(parsed.cgpa - original.cgpa) < 0.01  # Floating-point tolerance
    assert parsed.year_of_grad == original.year_of_grad
    assert abs(parsed.loan_amount - original.loan_amount) < 0.01
    assert abs(parsed.loan_emi - original.loan_emi) < 0.01
```

---

### Property 6: Batch Processing Independence and Failure Isolation

*For any* batch of student prediction requests, the success or failure of processing one student SHALL NOT affect the success or failure of processing any other student in the batch, and the order of students in the batch SHALL NOT affect the results.

**Validates: Requirements 9.4, 9.5**

**Rationale**: Batch processing must be independent and confluent. One student's failure shouldn't cascade to others, and processing order shouldn't matter. This ensures reliable parallel processing.

**Test Implementation**:
```python
from hypothesis import given, strategies as st
from backend.schemas.student import StudentInput
import asyncio

def valid_student_strategy():
    """Strategy for generating valid students."""
    return st.builds(
        StudentInput,
        name=st.text(min_size=1, max_size=50),
        course_type=st.sampled_from(['Engineering', 'MBA']),
        institute_name=st.just("Test Institute"),
        institute_tier=st.integers(min_value=1, max_value=3),
        cgpa=st.floats(min_value=5.0, max_value=10.0),
        year_of_grad=st.integers(min_value=2024, max_value=2026),
        loan_amount=st.floats(min_value=100000, max_value=1000000),
        loan_emi=st.floats(min_value=5000, max_value=50000)
    )

def invalid_student_strategy():
    """Strategy for generating invalid students (will fail validation)."""
    return st.builds(
        StudentInput,
        name=st.just(""),  # Invalid: empty name
        course_type=st.sampled_from(['Engineering', 'MBA']),
        institute_name=st.just("Test Institute"),
        institute_tier=st.integers(min_value=1, max_value=3),
        cgpa=st.floats(min_value=0.0, max_value=10.0),
        year_of_grad=st.integers(min_value=2024, max_value=2026),
        loan_amount=st.floats(min_value=0, max_value=1000000),
        loan_emi=st.floats(min_value=0, max_value=50000)
    )

@given(
    valid_students=st.lists(valid_student_strategy(), min_size=1, max_size=5),
    invalid_students=st.lists(invalid_student_strategy(), min_size=1, max_size=2)
)
def test_batch_processing_independence(valid_students, invalid_students):
    """
    Feature: edurisk-submission-improvements, Property 6:
    Batch processing independence and failure isolation
    """
    # Mix valid and invalid students
    batch = valid_students + invalid_students
    
    # Process batch (mock implementation for testing)
    results = asyncio.run(process_batch_mock(batch))
    
    # Verify valid students succeeded
    valid_results = [r for r in results if r['student'] in valid_students]
    assert all(r['success'] for r in valid_results), \
        "All valid students should succeed"
    
    # Verify invalid students failed
    invalid_results = [r for r in results if r['student'] in invalid_students]
    assert all(not r['success'] for r in invalid_results), \
        "All invalid students should fail"
    
    # Verify count matches
    assert len(results) == len(batch), \
        "Should have one result per student"
    
    # Test confluence: process in different order
    shuffled_batch = batch.copy()
    import random
    random.shuffle(shuffled_batch)
    shuffled_results = asyncio.run(process_batch_mock(shuffled_batch))
    
    # Results should be the same regardless of order (when matched by student)
    for student in batch:
        original_result = next(r for r in results if r['student'] == student)
        shuffled_result = next(r for r in shuffled_results if r['student'] == student)
        assert original_result['success'] == shuffled_result['success'], \
            "Processing order should not affect results"
```



## Error Handling

### Error Categories

#### 1. Startup Errors (Requirement 1)

**ML Model Training Failure**:
- **Cause**: Model training exceeds 120s timeout or fails due to insufficient data
- **Handling**: Log error to stdout, exit with code 1, prevent FastAPI server from starting
- **User Impact**: Container fails to start, docker-compose shows error
- **Recovery**: Check logs, ensure sufficient disk space and memory

**Model File Corruption**:
- **Cause**: Existing model files are corrupted or incompatible
- **Handling**: Delete corrupted files, trigger retraining
- **User Impact**: Slightly longer startup time
- **Recovery**: Automatic retraining

#### 2. Authentication Errors (Requirement 2)

**Missing API Key**:
- **HTTP Status**: 401 Unauthorized
- **Response Body**:
  ```json
  {
    "detail": "Missing API key. Include X-API-Key header in your request."
  }
  ```
- **Logging**: Warning with client IP address
- **Recovery**: Add X-API-Key header to request

**Invalid API Key**:
- **HTTP Status**: 401 Unauthorized
- **Response Body**:
  ```json
  {
    "detail": "Invalid API key"
  }
  ```
- **Logging**: Warning with client IP address
- **Recovery**: Use correct API key from environment variable

#### 3. Database Errors

**Connection Failure**:
- **Cause**: PostgreSQL not ready, network issue, wrong credentials
- **Handling**: Retry with exponential backoff (wait-for-db.py), log error
- **User Impact**: Delayed startup or request failure
- **Recovery**: Automatic retry, check DATABASE_URL

**Session Corruption (Requirement 9)**:
- **Cause**: Shared session across concurrent batch operations
- **Handling**: Use independent sessions per student, rollback on error
- **User Impact**: Individual student failure doesn't affect batch
- **Recovery**: Automatic isolation via session factory

**Migration Failure (Requirement 4)**:
- **Cause**: Alembic can't connect to database, schema conflict
- **Handling**: Log error with DATABASE_URL (sanitized), exit with code 1
- **User Impact**: Container fails to start
- **Recovery**: Check DATABASE_URL, resolve schema conflicts

#### 4. Validation Errors

**Invalid Student Data**:
- **HTTP Status**: 422 Unprocessable Entity
- **Response Body**:
  ```json
  {
    "detail": [
      {
        "loc": ["body", "cgpa"],
        "msg": "ensure this value is less than or equal to 10.0",
        "type": "value_error.number.not_le"
      }
    ]
  }
  ```
- **Handling**: Pydantic validation, return detailed error
- **User Impact**: Request rejected with clear error message
- **Recovery**: Fix input data

**CSV Parsing Errors (Requirement 19)**:
- **Missing Required Field**:
  ```json
  {
    "error": "Row 3: Missing required field 'cgpa'"
  }
  ```
- **Type Mismatch**:
  ```json
  {
    "error": "Row 5: Invalid type for field 'institute_tier': expected integer, got 'abc'"
  }
  ```
- **Handling**: Descriptive error with row number and field name
- **User Impact**: CSV upload rejected with actionable feedback
- **Recovery**: Fix CSV file

#### 5. External Service Errors

**LLM API Failure**:
- **Cause**: Groq API timeout, rate limit, invalid key, network error
- **Handling**: Return fallback message, log warning, continue prediction
- **Fallback Message**: "AI summary unavailable - refer to SHAP values for risk drivers."
- **User Impact**: Prediction succeeds but AI summary is generic
- **Recovery**: Graceful degradation, no user action needed

**Redis Connection Failure**:
- **Cause**: Redis not available, network issue
- **Handling**: Disable rate limiting, log warning, continue without caching
- **User Impact**: Rate limiting disabled, slightly slower responses
- **Recovery**: Automatic fallback to no-cache mode

#### 6. Runtime Errors

**Debug Mode Errors (Requirement 5)**:
- **DEBUG=True**: Return full stack trace in HTTP response
  ```json
  {
    "error": "Internal Server Error",
    "detail": "Division by zero in risk_calculator.py:45",
    "traceback": ["File ...", "Line ..."]
  }
  ```
- **DEBUG=False**: Return generic error message
  ```json
  {
    "error": "Internal Server Error",
    "detail": "An unexpected error occurred. Please contact support."
  }
  ```
- **Logging**: Always log full stack trace to backend logs
- **User Impact**: Developers see details, production users see generic message
- **Recovery**: Check logs, fix bug

### Error Handling Patterns

#### Middleware Error Handling

```python
# backend/middleware/error_handler.py
from fastapi import Request, status
from fastapi.responses import JSONResponse
import logging

logger = logging.getLogger(__name__)

class ErrorHandlingMiddleware:
    async def __call__(self, request: Request, call_next):
        try:
            return await call_next(request)
        except Exception as e:
            logger.error(f"Unhandled exception: {e}", exc_info=True)
            
            # Check debug mode
            debug = os.getenv("DEBUG", "False").lower() == "true"
            
            if debug:
                # Return detailed error in debug mode
                return JSONResponse(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    content={
                        "error": "Internal Server Error",
                        "detail": str(e),
                        "type": type(e).__name__,
                        "traceback": traceback.format_exc()
                    }
                )
            else:
                # Return generic error in production
                return JSONResponse(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    content={
                        "error": "Internal Server Error",
                        "detail": "An unexpected error occurred. Please contact support."
                    }
                )
```

#### Batch Processing Error Isolation

```python
# backend/routes/predict.py
async def process_student(student_data: StudentInput) -> dict:
    """Process single student with error isolation."""
    async with get_async_session() as db:
        try:
            result = await prediction_service.predict_student(
                student_data=student_data,
                db=db,
                performed_by="batch_api"
            )
            await db.commit()
            
            return {
                "success": True,
                "student_name": student_data.name,
                "prediction": result
            }
        except ValidationError as e:
            # Validation error - return descriptive message
            await db.rollback()
            return {
                "success": False,
                "student_name": student_data.name,
                "error": f"Validation error: {e.errors()[0]['msg']}"
            }
        except Exception as e:
            # Unexpected error - log and return generic message
            logger.error(f"Batch processing error for {student_data.name}: {e}", exc_info=True)
            await db.rollback()
            return {
                "success": False,
                "student_name": student_data.name,
                "error": "Processing failed. Check logs for details."
            }
```

### Logging Strategy

#### Log Levels

- **DEBUG**: Detailed diagnostic information (only when DEBUG=True)
- **INFO**: General informational messages (startup, health checks, successful operations)
- **WARNING**: Potentially harmful situations (missing API keys, fallback to defaults, rate limit warnings)
- **ERROR**: Error events that might still allow the application to continue (LLM API failures, individual prediction failures)
- **CRITICAL**: Severe error events that might cause the application to abort (database connection failure, model loading failure)

#### Structured Logging

```python
# backend/middleware/logging_config.py
import logging
import json
from datetime import datetime

class StructuredFormatter(logging.Formatter):
    def format(self, record):
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }
        
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        return json.dumps(log_data)
```

#### Audit Logging (Requirement 6)

All PREDICT and EXPLAIN actions are logged to the audit_logs table:

```python
# Example audit log entries
{
  "action": "PREDICT",
  "student_id": "uuid",
  "prediction_id": "uuid",
  "performed_by": "api_user",
  "details": {
    "model_version": "1.0.0",
    "risk_level": "medium",
    "risk_score": 45,
    "alert_triggered": false
  },
  "created_at": "2024-01-15T10:30:00Z"
}

{
  "action": "EXPLAIN",
  "student_id": "uuid",
  "prediction_id": "uuid",
  "performed_by": "api_user",
  "details": {
    "explanation_type": "SHAP"
  },
  "created_at": "2024-01-15T10:35:00Z"
}
```



## Testing Strategy

### Overview

The testing strategy employs a multi-layered approach combining unit tests, property-based tests, integration tests, and smoke tests. Each layer targets different aspects of correctness and reliability.

### Testing Pyramid

```
                    ┌─────────────┐
                    │   Smoke     │  ← Startup checks, health endpoints
                    │   Tests     │
                    └─────────────┘
                  ┌─────────────────┐
                  │  Integration    │  ← API endpoints, database
                  │     Tests       │
                  └─────────────────┘
              ┌───────────────────────┐
              │   Property-Based      │  ← Risk calculator, CSV parser
              │       Tests           │
              └───────────────────────┘
          ┌─────────────────────────────┐
          │       Unit Tests            │  ← Pure functions, utilities
          └─────────────────────────────┘
```

### Test Categories

#### 1. Unit Tests (Requirements 10.2-10.5)

**Purpose**: Test pure functions in isolation with specific examples and edge cases.

**Scope**:
- Risk calculator functions (calculate_risk_score, assign_risk_level, calculate_emi_affordability)
- Action recommender rules
- Utility functions

**Framework**: pytest

**Location**: `backend/services/test_risk_calculator_unit.py`

**Coverage Target**: 100% code coverage for risk_calculator.py

**Example Tests**:
```python
# backend/services/test_risk_calculator_unit.py
import pytest
from backend.services.risk_calculator import (
    calculate_risk_score,
    assign_risk_level,
    calculate_emi_affordability
)

class TestCalculateRiskScore:
    """Unit tests for risk score calculation."""
    
    def test_high_placement_probs_low_risk(self):
        """High placement probabilities should yield low risk score."""
        score = calculate_risk_score(0.9, 0.95, 0.98)
        assert 0 <= score <= 33
    
    def test_medium_placement_probs_medium_risk(self):
        """Medium placement probabilities should yield medium risk score."""
        score = calculate_risk_score(0.5, 0.6, 0.7)
        assert 34 <= score <= 66
    
    def test_low_placement_probs_high_risk(self):
        """Low placement probabilities should yield high risk score."""
        score = calculate_risk_score(0.2, 0.3, 0.4)
        assert 67 <= score <= 100
    
    def test_zero_probs_maximum_risk(self):
        """Zero placement probabilities should yield maximum risk."""
        score = calculate_risk_score(0.0, 0.0, 0.0)
        assert score == 100
    
    def test_perfect_probs_minimum_risk(self):
        """Perfect placement probabilities should yield minimum risk."""
        score = calculate_risk_score(1.0, 1.0, 1.0)
        assert score == 0

class TestAssignRiskLevel:
    """Unit tests for risk level assignment with boundary values."""
    
    def test_zero_is_low(self):
        assert assign_risk_level(0) == "low"
    
    def test_boundary_33_is_low(self):
        assert assign_risk_level(33) == "low"
    
    def test_boundary_34_is_medium(self):
        assert assign_risk_level(34) == "medium"
    
    def test_boundary_66_is_medium(self):
        assert assign_risk_level(66) == "medium"
    
    def test_boundary_67_is_high(self):
        assert assign_risk_level(67) == "high"
    
    def test_hundred_is_high(self):
        assert assign_risk_level(100) == "high"

class TestCalculateEMIAffordability:
    """Unit tests for EMI affordability calculation with edge cases."""
    
    def test_good_affordability(self):
        """EMI < 30% of monthly salary is good."""
        affordability = calculate_emi_affordability(10000, 500000)
        assert affordability < 0.3
    
    def test_moderate_affordability(self):
        """EMI 30-50% of monthly salary is moderate."""
        affordability = calculate_emi_affordability(20000, 500000)
        assert 0.3 <= affordability <= 0.5
    
    def test_high_risk_affordability(self):
        """EMI > 50% of monthly salary is high risk."""
        affordability = calculate_emi_affordability(30000, 500000)
        assert affordability > 0.5
    
    def test_zero_salary_maximum_risk(self):
        """Zero salary should return maximum risk (1.0)."""
        affordability = calculate_emi_affordability(10000, 0)
        assert affordability == 1.0
    
    def test_zero_emi_zero_risk(self):
        """Zero EMI should return zero risk."""
        affordability = calculate_emi_affordability(0, 500000)
        assert affordability == 0.0
```

**Execution**:
```bash
pytest backend/services/test_risk_calculator_unit.py -v --cov=backend/services/risk_calculator
```

---

#### 2. Property-Based Tests (Requirements 10.2, 19.2, 19.3, 19.5, 9.4)

**Purpose**: Verify universal properties hold across all valid inputs using randomized testing.

**Scope**:
- Risk calculator invariants and monotonicity
- CSV parser round-trip property
- CSV parser error handling
- Batch processing independence

**Framework**: pytest + Hypothesis

**Location**: `backend/services/test_risk_calculator_properties.py`, `backend/schemas/test_csv_parser_properties.py`

**Iterations**: Minimum 100 iterations per property test

**Property Test Configuration**:
```python
# conftest.py
from hypothesis import settings, Verbosity

# Configure Hypothesis for all property tests
settings.register_profile("default", max_examples=100, verbosity=Verbosity.normal)
settings.register_profile("ci", max_examples=200, verbosity=Verbosity.verbose)
settings.load_profile("default")
```

**Example Property Tests** (see Correctness Properties section for full implementations):
- Property 1: Risk score range invariant (0 ≤ score ≤ 100)
- Property 2: Risk score monotonicity (higher probs → lower risk)
- Property 3: CSV parser missing field errors
- Property 4: CSV parser type mismatch errors
- Property 5: CSV parser round-trip preservation
- Property 6: Batch processing independence

**Execution**:
```bash
pytest backend/services/test_risk_calculator_properties.py -v
pytest backend/schemas/test_csv_parser_properties.py -v
```

---

#### 3. Integration Tests (Requirements 18.2-18.7)

**Purpose**: Test API endpoints end-to-end with database and external services.

**Scope**:
- POST /api/predict with valid and invalid data
- GET /api/students
- GET /api/alerts
- GET /api/explain/{student_id}
- GET /api/health
- Authentication middleware

**Framework**: pytest + FastAPI TestClient

**Location**: `backend/tests/test_api_integration.py`

**Test Database**: Use separate test database or in-memory SQLite

**Example Integration Tests**:
```python
# backend/tests/test_api_integration.py
import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.db.session import get_db
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Test database setup
SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)

class TestPredictEndpoint:
    """Integration tests for POST /api/predict."""
    
    def test_predict_with_valid_data(self):
        """Test prediction with valid student data returns 200."""
        student_data = {
            "name": "John Doe",
            "course_type": "Engineering",
            "institute_name": "IIT Delhi",
            "institute_tier": 1,
            "cgpa": 8.5,
            "year_of_grad": 2024,
            "loan_amount": 500000,
            "loan_emi": 10000
        }
        
        response = client.post(
            "/api/predict",
            json=student_data,
            headers={"X-API-Key": "test_api_key"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "risk_score" in data
        assert "risk_level" in data
        assert 0 <= data["risk_score"] <= 100
    
    def test_predict_with_invalid_data(self):
        """Test prediction with invalid data returns 422."""
        student_data = {
            "name": "",  # Invalid: empty name
            "course_type": "Engineering",
            "institute_tier": 1,
            "cgpa": 8.5
        }
        
        response = client.post(
            "/api/predict",
            json=student_data,
            headers={"X-API-Key": "test_api_key"}
        )
        
        assert response.status_code == 422

class TestAuthenticationMiddleware:
    """Integration tests for API key authentication."""
    
    def test_missing_api_key(self):
        """Test request without API key returns 401."""
        response = client.get("/api/students")
        assert response.status_code == 401
        assert "Missing API key" in response.json()["detail"]
    
    def test_invalid_api_key(self):
        """Test request with invalid API key returns 401."""
        response = client.get(
            "/api/students",
            headers={"X-API-Key": "wrong_key"}
        )
        assert response.status_code == 401
        assert "Invalid API key" in response.json()["detail"]
    
    def test_valid_api_key(self):
        """Test request with valid API key succeeds."""
        response = client.get(
            "/api/students",
            headers={"X-API-Key": "test_api_key"}
        )
        assert response.status_code == 200

class TestHealthEndpoint:
    """Integration tests for GET /api/health."""
    
    def test_health_check_returns_ml_models_status(self):
        """Test health check includes ML models status."""
        response = client.get("/api/health")
        assert response.status_code == 200
        data = response.json()
        assert "ml_models" in data
        assert data["ml_models"] in ["available", "unavailable"]
```

**Execution**:
```bash
pytest backend/tests/test_api_integration.py -v
```

---

#### 4. Smoke Tests (Requirements 1.1, 1.7)

**Purpose**: Verify critical system functionality with minimal test cases.

**Scope**:
- ML model startup check
- Health endpoint availability
- Database connectivity
- Redis connectivity

**Framework**: pytest

**Location**: `backend/tests/test_smoke.py`

**Example Smoke Tests**:
```python
# backend/tests/test_smoke.py
import pytest
from pathlib import Path
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

class TestStartupChecks:
    """Smoke tests for system startup."""
    
    def test_ml_models_exist(self):
        """Test that all required ML model files exist."""
        model_files = [
            "ml/models/placement_model_3m.pkl",
            "ml/models/placement_model_6m.pkl",
            "ml/models/placement_model_12m.pkl",
            "ml/models/salary_model.pkl"
        ]
        
        for model_file in model_files:
            assert Path(model_file).exists(), f"Missing model file: {model_file}"
    
    def test_health_endpoint_accessible(self):
        """Test that health endpoint is accessible without authentication."""
        response = client.get("/api/health")
        assert response.status_code == 200
    
    def test_health_endpoint_reports_ml_models(self):
        """Test that health endpoint reports ML models status."""
        response = client.get("/api/health")
        data = response.json()
        assert "ml_models" in data
        assert data["ml_models"] == "available"
```

**Execution**:
```bash
pytest backend/tests/test_smoke.py -v
```

---

#### 5. Mock LLM Response Tests (Requirement 29)

**Purpose**: Test graceful degradation when LLM service is unavailable by mocking API responses.

**Location**: `backend/tests/test_llm_service.py` (new file)

**Framework**: pytest + unittest.mock

**Scope**:
- LLM timeout scenarios
- LLM rate limit errors (HTTP 429)
- LLM API key errors (HTTP 401)
- Fallback message behavior
- Prediction success despite LLM failure

**Example Tests**:
```python
# backend/tests/test_llm_service.py
"""
Tests for LLM service graceful degradation.

Requirements: 29.1, 29.2, 29.3, 29.4, 29.5, 29.6, 29.7
"""
import pytest
from unittest.mock import patch, Mock
from backend.services.llm_service import LLMService
from backend.services.prediction_service import PredictionService

class TestLLMTimeout:
    """Test LLM timeout scenarios."""
    
    @patch('backend.services.llm_service.requests.post')
    def test_llm_timeout_returns_fallback(self, mock_post):
        """LLM timeout should return fallback message."""
        # Mock timeout
        mock_post.side_effect = TimeoutError("Request timed out")
        
        llm_service = LLMService()
        result = llm_service.generate_summary(
            risk_score=75,
            risk_level="high",
            top_drivers=["Low CGPA", "No internships"]
        )
        
        # Should return fallback message
        assert result is not None
        assert "unable to generate" in result.lower() or "fallback" in result.lower()
    
    @patch('backend.services.llm_service.requests.post')
    def test_llm_timeout_logs_warning(self, mock_post, caplog):
        """LLM timeout should log warning without exposing API key."""
        mock_post.side_effect = TimeoutError("Request timed out")
        
        llm_service = LLMService()
        llm_service.generate_summary(risk_score=75, risk_level="high", top_drivers=[])
        
        # Check logs
        assert any("timeout" in record.message.lower() for record in caplog.records)
        assert not any("api_key" in record.message.lower() for record in caplog.records)

class TestLLMRateLimiting:
    """Test LLM rate limit error handling."""
    
    @patch('backend.services.llm_service.requests.post')
    def test_rate_limit_returns_fallback(self, mock_post):
        """HTTP 429 rate limit should return fallback message."""
        # Mock rate limit response
        mock_response = Mock()
        mock_response.status_code = 429
        mock_response.headers = {'Retry-After': '60'}
        mock_post.return_value = mock_response
        
        llm_service = LLMService()
        result = llm_service.generate_summary(risk_score=75, risk_level="high", top_drivers=[])
        
        # Should return fallback message
        assert result is not None
        assert "unable to generate" in result.lower()
    
    @patch('backend.services.llm_service.requests.post')
    def test_rate_limit_logs_retry_after(self, mock_post, caplog):
        """Rate limit should log Retry-After header."""
        mock_response = Mock()
        mock_response.status_code = 429
        mock_response.headers = {'Retry-After': '60'}
        mock_post.return_value = mock_response
        
        llm_service = LLMService()
        llm_service.generate_summary(risk_score=75, risk_level="high", top_drivers=[])
        
        # Check logs
        assert any("rate limit" in record.message.lower() for record in caplog.records)
        assert any("60" in record.message for record in caplog.records)

class TestLLMAuthErrors:
    """Test LLM API key error handling."""
    
    @patch('backend.services.llm_service.requests.post')
    def test_invalid_api_key_returns_fallback(self, mock_post):
        """HTTP 401 auth error should return fallback message."""
        # Mock auth error
        mock_response = Mock()
        mock_response.status_code = 401
        mock_post.return_value = mock_response
        
        llm_service = LLMService()
        result = llm_service.generate_summary(risk_score=75, risk_level="high", top_drivers=[])
        
        # Should return fallback message
        assert result is not None
        assert "unable to generate" in result.lower()
    
    @patch('backend.services.llm_service.requests.post')
    def test_auth_error_does_not_expose_api_key(self, mock_post, caplog):
        """Auth error logs should not expose API key."""
        mock_response = Mock()
        mock_response.status_code = 401
        mock_post.return_value = mock_response
        
        llm_service = LLMService()
        llm_service.generate_summary(risk_score=75, risk_level="high", top_drivers=[])
        
        # Check logs don't contain API key
        for record in caplog.records:
            assert "api_key" not in record.message.lower()
            assert "groq" not in record.message.lower() or "failed" in record.message.lower()

class TestPredictionWithLLMFailure:
    """Test that predictions succeed even when LLM fails."""
    
    @patch('backend.services.llm_service.LLMService.generate_summary')
    async def test_prediction_succeeds_without_llm(self, mock_generate):
        """Prediction should succeed even if LLM fails."""
        # Mock LLM failure
        mock_generate.return_value = "Fallback: Unable to generate AI summary"
        
        prediction_service = PredictionService()
        
        student_data = {
            "name": "Test Student",
            "course_type": "Engineering",
            "institute_tier": 1,
            "cgpa": 8.5,
            "year_of_grad": 2024,
            "loan_amount": 500000,
            "loan_emi": 10000
        }
        
        # Should not raise exception
        result = await prediction_service.predict_student(student_data)
        
        # Prediction should have all required fields
        assert result.risk_score is not None
        assert result.risk_level is not None
        assert result.ai_summary is not None
        assert "fallback" in result.ai_summary.lower()

class TestLLMFallbackMessages:
    """Test fallback message generation."""
    
    def test_fallback_message_is_informative(self):
        """Fallback message should provide useful information."""
        llm_service = LLMService()
        fallback = llm_service.get_fallback_summary(
            risk_score=75,
            risk_level="high"
        )
        
        assert fallback is not None
        assert len(fallback) > 20  # Should be informative
        assert "high" in fallback.lower() or "75" in fallback
```

**Execution**:
```bash
pytest backend/tests/test_llm_service.py -v
```

---

#### 6. Groq API Rate Limiting Tests (Requirement 30)

**Purpose**: Test exponential backoff and retry logic for Groq API rate limits.

**Location**: `backend/services/llm_service.py` (modify), `backend/tests/test_groq_rate_limiting.py` (new file)

**Implementation**:
```python
# backend/services/llm_service.py (enhanced with rate limiting)
"""
LLM service with exponential backoff for rate limiting.

Requirements: 30.1, 30.2, 30.3, 30.4, 30.5, 30.6, 30.7
"""
import time
import logging
from typing import Optional
import requests

logger = logging.getLogger(__name__)

class LLMService:
    """LLM service with graceful degradation and rate limit handling."""
    
    MAX_RETRIES = 3
    BASE_DELAY = 1  # seconds
    
    def generate_summary(
        self,
        risk_score: int,
        risk_level: str,
        top_drivers: list[str],
        retry_count: int = 0
    ) -> str:
        """
        Generate AI summary with exponential backoff for rate limits.
        
        Requirements: 30.1, 30.2, 30.3, 30.4, 30.5, 30.6
        """
        try:
            response = requests.post(
                f"{self.api_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "mixtral-8x7b-32768",
                    "messages": [
                        {
                            "role": "user",
                            "content": f"Generate risk summary for student with risk score {risk_score}"
                        }
                    ]
                },
                timeout=10
            )
            
            # Handle rate limiting (Requirement 30.1, 30.2)
            if response.status_code == 429:
                if retry_count >= self.MAX_RETRIES:
                    logger.warning(f"Max retries ({self.MAX_RETRIES}) exhausted for LLM request")
                    return self.get_fallback_summary(risk_score, risk_level)
                
                # Get retry delay from header or use exponential backoff
                retry_after = response.headers.get('Retry-After')
                if retry_after:
                    delay = int(retry_after)
                    logger.info(f"Rate limited, retrying after {delay}s (from Retry-After header)")
                else:
                    delay = self.BASE_DELAY * (2 ** retry_count)
                    logger.info(f"Rate limited, retrying after {delay}s (exponential backoff)")
                
                # Log rate limit event (Requirement 30.5)
                logger.warning(
                    f"Groq API rate limit hit (attempt {retry_count + 1}/{self.MAX_RETRIES}), "
                    f"waiting {delay}s before retry"
                )
                
                time.sleep(delay)
                
                # Retry with incremented count
                return self.generate_summary(
                    risk_score,
                    risk_level,
                    top_drivers,
                    retry_count=retry_count + 1
                )
            
            # Don't retry on auth errors (Requirement 30.7)
            if response.status_code == 401:
                logger.error("Groq API authentication failed (invalid API key)")
                return self.get_fallback_summary(risk_score, risk_level)
            
            # Success
            if response.status_code == 200:
                data = response.json()
                return data['choices'][0]['message']['content']
            
            # Other errors
            logger.warning(f"LLM request failed with status {response.status_code}")
            return self.get_fallback_summary(risk_score, risk_level)
        
        except Exception as e:
            logger.error(f"LLM service error: {e}")
            return self.get_fallback_summary(risk_score, risk_level)
    
    def get_fallback_summary(self, risk_score: int, risk_level: str) -> str:
        """
        Generate fallback summary when LLM is unavailable.
        
        Requirements: 30.4
        """
        return (
            f"Risk Assessment: {risk_level.upper()} (Score: {risk_score}/100). "
            f"AI-powered insights are temporarily unavailable. "
            f"Please review the risk drivers and SHAP values for detailed analysis."
        )
```

**Rate Limiting Tests**:
```python
# backend/tests/test_groq_rate_limiting.py
"""
Tests for Groq API rate limiting with exponential backoff.

Requirements: 30.1, 30.2, 30.3, 30.4, 30.5, 30.6, 30.7
"""
import pytest
from unittest.mock import patch, Mock
from backend.services.llm_service import LLMService
import time

class TestExponentialBackoff:
    """Test exponential backoff for rate limits."""
    
    @patch('backend.services.llm_service.requests.post')
    @patch('backend.services.llm_service.time.sleep')
    def test_exponential_backoff_delays(self, mock_sleep, mock_post):
        """Delays should increase exponentially: 1s, 2s, 4s."""
        # Mock rate limit responses
        mock_response = Mock()
        mock_response.status_code = 429
        mock_response.headers = {}
        mock_post.return_value = mock_response
        
        llm_service = LLMService()
        llm_service.generate_summary(risk_score=75, risk_level="high", top_drivers=[])
        
        # Check sleep was called with exponential delays
        assert mock_sleep.call_count == 3
        delays = [call[0][0] for call in mock_sleep.call_args_list]
        assert delays == [1, 2, 4]  # Exponential backoff
    
    @patch('backend.services.llm_service.requests.post')
    def test_max_retries_returns_fallback(self, mock_post):
        """After max retries, should return fallback message."""
        mock_response = Mock()
        mock_response.status_code = 429
        mock_response.headers = {}
        mock_post.return_value = mock_response
        
        llm_service = LLMService()
        result = llm_service.generate_summary(risk_score=75, risk_level="high", top_drivers=[])
        
        # Should return fallback after 3 retries
        assert "temporarily unavailable" in result.lower()
        assert mock_post.call_count == 4  # Initial + 3 retries

class TestRetryAfterHeader:
    """Test Retry-After header handling."""
    
    @patch('backend.services.llm_service.requests.post')
    @patch('backend.services.llm_service.time.sleep')
    def test_retry_after_header_respected(self, mock_sleep, mock_post):
        """Should use Retry-After header value if present."""
        # Mock rate limit with Retry-After header
        mock_response = Mock()
        mock_response.status_code = 429
        mock_response.headers = {'Retry-After': '30'}
        mock_post.return_value = mock_response
        
        llm_service = LLMService()
        llm_service.generate_summary(risk_score=75, risk_level="high", top_drivers=[])
        
        # First retry should use Retry-After value
        assert mock_sleep.call_args_list[0][0][0] == 30

class TestAuthErrorNoRetry:
    """Test that auth errors are not retried."""
    
    @patch('backend.services.llm_service.requests.post')
    def test_auth_error_no_retry(self, mock_post):
        """HTTP 401 should not trigger retries."""
        mock_response = Mock()
        mock_response.status_code = 401
        mock_post.return_value = mock_response
        
        llm_service = LLMService()
        result = llm_service.generate_summary(risk_score=75, risk_level="high", top_drivers=[])
        
        # Should only make one request (no retries)
        assert mock_post.call_count == 1
        assert "temporarily unavailable" in result.lower()

class TestRateLimitMetrics:
    """Test rate limit event logging."""
    
    @patch('backend.services.llm_service.requests.post')
    def test_rate_limit_events_logged(self, mock_post, caplog):
        """Rate limit events should be logged with retry count."""
        mock_response = Mock()
        mock_response.status_code = 429
        mock_response.headers = {}
        mock_post.return_value = mock_response
        
        llm_service = LLMService()
        llm_service.generate_summary(risk_score=75, risk_level="high", top_drivers=[])
        
        # Check logs contain rate limit info
        rate_limit_logs = [r for r in caplog.records if "rate limit" in r.message.lower()]
        assert len(rate_limit_logs) == 3  # One for each retry
        
        # Check retry counts are logged
        assert any("attempt 1/3" in r.message for r in rate_limit_logs)
        assert any("attempt 2/3" in r.message for r in rate_limit_logs)
        assert any("attempt 3/3" in r.message for r in rate_limit_logs)
```

**Execution**:
```bash
pytest backend/tests/test_groq_rate_limiting.py -v
```

---

### Frontend Testing

#### Component Tests

**Framework**: Jest + React Testing Library

**Scope**:
- NavigationBar component (Requirement 7)
- EmptyState component (Requirement 13)
- RiskScoreGauge component (Requirement 12)
- SalaryRangeCard component (Requirement 11)

**Location**: `frontend/components/**/__tests__/`

**Example Component Test**:
```typescript
// frontend/components/layout/__tests__/NavigationBar.test.tsx
import { render, screen } from '@testing-library/react';
import { NavigationBar } from '../NavigationBar';

describe('NavigationBar', () => {
  it('renders all navigation links', () => {
    render(<NavigationBar />);
    
    expect(screen.getByText('Dashboard')).toBeInTheDocument();
    expect(screen.getByText('Alerts')).toBeInTheDocument();
    expect(screen.getByText('New Student')).toBeInTheDocument();
    expect(screen.getByText('API Docs')).toBeInTheDocument();
  });
  
  it('highlights active page', () => {
    // Mock usePathname to return '/dashboard'
    jest.mock('next/navigation', () => ({
      usePathname: () => '/dashboard'
    }));
    
    render(<NavigationBar />);
    
    const dashboardLink = screen.getByText('Dashboard').closest('a');
    expect(dashboardLink).toHaveClass('bg-primary');
  });
  
  it('displays alert badge when alerts exist', async () => {
    // Mock fetch to return alerts
    global.fetch = jest.fn(() =>
      Promise.resolve({
        json: () => Promise.resolve([
          { risk_level: 'high' },
          { risk_level: 'high' },
          { risk_level: 'medium' }
        ])
      })
    );
    
    render(<NavigationBar />);
    
    // Wait for alert count to load
    const badge = await screen.findByText('2');
    expect(badge).toBeInTheDocument();
  });
});
```

**Execution**:
```bash
cd frontend
npm test
```

---

### Test Execution Strategy

#### Local Development

```bash
# Backend unit tests
pytest backend/services/test_risk_calculator_unit.py -v

# Backend property tests
pytest backend/services/test_risk_calculator_properties.py -v
pytest backend/schemas/test_csv_parser_properties.py -v

# Backend integration tests
pytest backend/tests/test_api_integration.py -v

# Backend smoke tests
pytest backend/tests/test_smoke.py -v

# All backend tests with coverage
pytest --cov=backend --cov-report=html

# Frontend tests
cd frontend && npm test
```

#### CI/CD Pipeline

```yaml
# .github/workflows/test.yml
name: Test Suite

on: [push, pull_request]

jobs:
  backend-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: 3.11
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Run unit tests
        run: pytest backend/services/test_risk_calculator_unit.py -v
      - name: Run property tests
        run: pytest backend/services/test_risk_calculator_properties.py -v --hypothesis-profile=ci
      - name: Run integration tests
        run: pytest backend/tests/test_api_integration.py -v
      - name: Run smoke tests
        run: pytest backend/tests/test_smoke.py -v
      - name: Generate coverage report
        run: pytest --cov=backend --cov-report=xml
      - name: Upload coverage
        uses: codecov/codecov-action@v2
  
  frontend-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Node.js
        uses: actions/setup-node@v2
        with:
          node-version: 18
      - name: Install dependencies
        run: cd frontend && npm ci
      - name: Run tests
        run: cd frontend && npm test
```

---

### Test Coverage Goals

| Component | Unit Tests | Property Tests | Integration Tests | Target Coverage |
|-----------|-----------|----------------|-------------------|-----------------|
| Risk Calculator | ✅ | ✅ | - | 100% |
| CSV Parser | ✅ | ✅ | - | 100% |
| API Endpoints | - | - | ✅ | 90% |
| Middleware | - | - | ✅ | 85% |
| Services | ✅ | - | ✅ | 85% |
| Frontend Components | ✅ | - | - | 80% |

---

### Manual Testing Checklist

**Phase 1 (Critical)**:
- [ ] Docker compose up completes successfully on first boot
- [ ] ML models are trained automatically if missing
- [ ] Health endpoint returns ml_models: available
- [ ] API requests without X-API-Key header return 401
- [ ] API requests with valid X-API-Key succeed
- [ ] Alembic migrations run successfully in Docker
- [ ] DEBUG=False hides stack traces in production
- [ ] EXPLAIN actions appear in audit logs

**Phase 2 (Important)**:
- [ ] Navigation bar appears on all pages
- [ ] Active page is highlighted in navigation
- [ ] Alert badge shows correct count
- [ ] Dashboard shows "Add Student" button
- [ ] Batch scoring handles failures independently
- [ ] Salary card shows EMI affordability with color coding
- [ ] Risk gauge animates from 0 to actual score
- [ ] Empty state appears when no students exist

**Phase 3 (Optional)**:
- [ ] CSV upload accepts valid files
- [ ] CSV upload rejects invalid files with clear errors
- [ ] Batch results show success/failure counts
- [ ] Risk trend chart displays historical data
- [ ] Docker image size is under 1 GB
- [ ] Student table pagination works correctly




## Documentation and Deployment

### Vercel Deployment Guide (Requirement 31)

**Purpose**: Provide clear instructions for deploying the frontend to Vercel for live demo.

**Location**: `DEPLOYMENT_GUIDE.md` (modify/append)

**Content**:
```markdown
# Vercel Deployment Guide

## Overview

Deploy the EduRisk AI frontend to Vercel for a live demo accessible to hackathon judges.

**Estimated Time**: 5 minutes

**Requirements**: 31.1, 31.2, 31.3, 31.4, 31.5, 31.6, 31.7

---

## Prerequisites

- GitHub account with EduRisk AI repository
- Vercel account (free tier is sufficient)
- Backend API deployed and accessible (e.g., on Railway, Render, or AWS)

---

## Step-by-Step Deployment

### 1. Connect GitHub Repository to Vercel

1. Go to [vercel.com](https://vercel.com) and sign in
2. Click "Add New Project"
3. Select "Import Git Repository"
4. Choose your EduRisk AI repository
5. Vercel will auto-detect Next.js configuration

### 2. Configure Environment Variables

In the Vercel project settings, add the following environment variables:

**Required Variables**:
```bash
NEXT_PUBLIC_API_URL=https://your-backend-api.com
NEXT_PUBLIC_API_KEY=your_api_key_here
```

**How to add**:
1. Go to Project Settings → Environment Variables
2. Add each variable with its value
3. Select "Production", "Preview", and "Development" environments

### 3. Configure Build Settings

Vercel should auto-detect these settings, but verify:

- **Framework Preset**: Next.js
- **Root Directory**: `frontend`
- **Build Command**: `npm run build`
- **Output Directory**: `.next`
- **Install Command**: `npm install`

### 4. Deploy

1. Click "Deploy"
2. Wait 2-3 minutes for build to complete
3. Vercel will provide a live URL: `https://your-project.vercel.app`

### 5. Verify Deployment

1. Visit the deployed URL
2. Test login functionality
3. Create a test prediction
4. Verify API connectivity

---

## Environment Variables Reference

| Variable | Description | Example |
|----------|-------------|---------|
| `NEXT_PUBLIC_API_URL` | Backend API base URL | `https://api.edurisk.com` |
| `NEXT_PUBLIC_API_KEY` | API key for backend authentication | `your_secret_key` |

**Important**: 
- Variables prefixed with `NEXT_PUBLIC_` are exposed to the browser
- Never commit real API keys to version control
- Use different API keys for production vs development

---

## Troubleshooting

### Issue: Build fails with "Module not found"

**Solution**:
```bash
# Ensure all dependencies are in package.json
cd frontend
npm install
npm run build  # Test locally first
```

### Issue: API requests fail with CORS error

**Solution**:
- Add your Vercel domain to `CORS_ORIGINS` in backend `.env`:
  ```bash
  CORS_ORIGINS=https://your-project.vercel.app,http://localhost:3000
  ```
- Redeploy backend with updated CORS configuration

### Issue: Environment variables not working

**Solution**:
- Verify variables are prefixed with `NEXT_PUBLIC_`
- Redeploy after adding/changing environment variables
- Check browser console for actual API URL being used

### Issue: 404 on page refresh

**Solution**:
- Vercel automatically handles Next.js routing
- If issue persists, check `next.config.js` for custom routing

---

## Custom Domain (Optional)

1. Go to Project Settings → Domains
2. Add your custom domain
3. Update DNS records as instructed by Vercel
4. SSL certificate is automatically provisioned

---

## Continuous Deployment

Vercel automatically deploys on every push to your main branch:

- **Production**: Deploys from `main` branch
- **Preview**: Deploys from pull requests
- **Development**: Local development with `npm run dev`

---

## Performance Optimization

Vercel provides automatic optimizations:
- ✅ Edge caching
- ✅ Image optimization
- ✅ Automatic HTTPS
- ✅ Global CDN

---

## Monitoring

View deployment logs and analytics:
1. Go to Vercel Dashboard
2. Select your project
3. View "Deployments" tab for build logs
4. View "Analytics" tab for performance metrics

---

## Additional Resources

- [Vercel Next.js Documentation](https://vercel.com/docs/frameworks/nextjs)
- [Environment Variables Guide](https://vercel.com/docs/concepts/projects/environment-variables)
- [Custom Domains Guide](https://vercel.com/docs/concepts/projects/domains)

---

## Quick Reference Commands

```bash
# Install Vercel CLI (optional)
npm install -g vercel

# Deploy from command line
cd frontend
vercel

# Deploy to production
vercel --prod
```
```

---

### Mock Alert Notification System (Requirement 32)

**Purpose**: Demonstrate alert notification capabilities with mock SMS/email functions.

**Location**: `backend/services/alert_service.py` (new file)

**Implementation**:
```python
# backend/services/alert_service.py
"""
Mock alert notification system for EduRisk AI.

Demonstrates how the system would notify loan officers of high-risk students.
In production, integrate with Twilio (SMS) and SendGrid (email).

Requirements: 32.1, 32.2, 32.3, 32.4, 32.5, 32.6, 32.7, 32.8
"""
import logging
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from backend.models.student import Student
from backend.models.prediction import Prediction
from backend.models.audit_log import AuditLog

logger = logging.getLogger(__name__)

class AlertService:
    """Service for sending alert notifications."""
    
    # Mock phone numbers for demo (Requirement 32.5)
    DEMO_PHONE_NUMBERS = {
        "loan_officer_1": "+1-555-0101",
        "loan_officer_2": "+1-555-0102",
        "manager": "+1-555-0199"
    }
    
    async def send_high_risk_alert(
        self,
        student: Student,
        prediction: Prediction,
        db: AsyncSession
    ):
        """
        Send alert notification for high-risk student.
        
        Triggers when risk_score >= 67.
        
        Requirements: 32.2, 32.3, 32.4
        """
        if prediction.risk_score < 67:
            return  # Only alert for high-risk students
        
        # Mock SMS notification (Requirement 32.6)
        await self.mock_send_sms(
            to_phone=self.DEMO_PHONE_NUMBERS["loan_officer_1"],
            student_name=student.name,
            risk_score=prediction.risk_score
        )
        
        # Mock email notification (Requirement 32.7)
        await self.mock_send_email(
            to_email="loan.officer@edurisk.ai",
            student_name=student.name,
            risk_score=prediction.risk_score,
            risk_level=prediction.risk_level
        )
        
        # Log alert to audit trail (Requirement 32.4)
        audit_entry = AuditLog(
            action="ALERT_SENT",
            student_id=student.id,
            prediction_id=prediction.id,
            performed_by="system",
            details={
                "alert_type": "high_risk",
                "risk_score": prediction.risk_score,
                "notification_channels": ["sms", "email"]
            }
        )
        db.add(audit_entry)
        await db.flush()
    
    async def mock_send_sms(
        self,
        to_phone: str,
        student_name: str,
        risk_score: int
    ):
        """
        Mock SMS notification function.
        
        In production, replace with Twilio integration:
        ```python
        from twilio.rest import Client
        
        client = Client(account_sid, auth_token)
        message = client.messages.create(
            body=f"ALERT: High-risk student {student_name} (Risk: {risk_score})",
            from_='+1-555-EDURISK',
            to=to_phone
        )
        ```
        
        Requirements: 32.3, 32.6, 32.8
        """
        # Log mock SMS (Requirement 32.3)
        logger.info(
            f"📱 ALERT: SMS sent to {to_phone} for student {student_name} "
            f"(Risk: {risk_score})"
        )
        
        # In production, this would make actual Twilio API call
        # See Requirement 32.8 for integration points
    
    async def mock_send_email(
        self,
        to_email: str,
        student_name: str,
        risk_score: int,
        risk_level: str
    ):
        """
        Mock email notification function.
        
        In production, replace with SendGrid integration:
        ```python
        from sendgrid import SendGridAPIClient
        from sendgrid.helpers.mail import Mail
        
        message = Mail(
            from_email='alerts@edurisk.ai',
            to_emails=to_email,
            subject=f'High Risk Alert: {student_name}',
            html_content=f'<p>Student {student_name} has been flagged as {risk_level} risk...</p>'
        )
        
        sg = SendGridAPIClient(os.environ.get('SENDGRID_API_KEY'))
        response = sg.send(message)
        ```
        
        Requirements: 32.3, 32.7, 32.8
        """
        # Log mock email (Requirement 32.3)
        logger.info(
            f"📧 ALERT: Email sent to {to_email} for student {student_name} "
            f"(Risk: {risk_score}, Level: {risk_level})"
        )
        
        # In production, this would make actual SendGrid API call
        # See Requirement 32.8 for integration points
```

**Integration in Prediction Service**:
```python
# backend/services/prediction_service.py
from backend.services.alert_service import AlertService

class PredictionService:
    """Service for student risk predictions."""
    
    def __init__(self):
        self.alert_service = AlertService()
    
    async def predict_student(
        self,
        student_data: StudentInput,
        db: AsyncSession
    ) -> Prediction:
        """Create prediction and trigger alerts if high-risk."""
        # ... existing prediction logic ...
        
        # Trigger alert for high-risk students (Requirement 32.2)
        if prediction.risk_score >= 67:
            await self.alert_service.send_high_risk_alert(
                student=student,
                prediction=prediction,
                db=db
            )
        
        await db.commit()
        return prediction
```

**Testing**:
```python
# backend/tests/test_alert_service.py
"""
Tests for alert notification system.

Requirements: 32.1, 32.2, 32.3, 32.4
"""
import pytest
from backend.services.alert_service import AlertService
from backend.models.student import Student
from backend.models.prediction import Prediction

class TestHighRiskAlerts:
    """Test high-risk alert triggering."""
    
    async def test_high_risk_triggers_alert(self, caplog):
        """Risk score >= 67 should trigger alert."""
        alert_service = AlertService()
        
        student = Student(name="Test Student")
        prediction = Prediction(risk_score=75, risk_level="high")
        
        await alert_service.send_high_risk_alert(student, prediction, db=mock_db)
        
        # Check logs for SMS and email
        assert any("SMS sent" in record.message for record in caplog.records)
        assert any("Email sent" in record.message for record in caplog.records)
    
    async def test_medium_risk_no_alert(self, caplog):
        """Risk score < 67 should not trigger alert."""
        alert_service = AlertService()
        
        student = Student(name="Test Student")
        prediction = Prediction(risk_score=50, risk_level="medium")
        
        await alert_service.send_high_risk_alert(student, prediction, db=mock_db)
        
        # No alerts should be sent
        assert not any("SMS sent" in record.message for record in caplog.records)
        assert not any("Email sent" in record.message for record in caplog.records)

class TestAuditLogging:
    """Test alert audit logging."""
    
    async def test_alert_logged_to_audit_trail(self):
        """Alert should be logged to audit_logs table."""
        alert_service = AlertService()
        
        student = Student(id=uuid4(), name="Test Student")
        prediction = Prediction(id=uuid4(), risk_score=75, risk_level="high")
        
        await alert_service.send_high_risk_alert(student, prediction, db=mock_db)
        
        # Check audit log was created
        audit_logs = await db.execute(
            select(AuditLog).where(AuditLog.action == "ALERT_SENT")
        )
        assert len(audit_logs.scalars().all()) == 1
```

**Production Integration Guide**:
```markdown
# Production Alert Integration

## Twilio SMS Integration

1. Sign up for Twilio account
2. Get Account SID and Auth Token
3. Purchase phone number
4. Add to `.env`:
   ```bash
   TWILIO_ACCOUNT_SID=your_account_sid
   TWILIO_AUTH_TOKEN=your_auth_token
   TWILIO_PHONE_NUMBER=+1-555-EDURISK
   ```
5. Replace `mock_send_sms()` with actual Twilio code

## SendGrid Email Integration

1. Sign up for SendGrid account
2. Create API key
3. Verify sender email
4. Add to `.env`:
   ```bash
   SENDGRID_API_KEY=your_api_key
   SENDGRID_FROM_EMAIL=alerts@edurisk.ai
   ```
5. Replace `mock_send_email()` with actual SendGrid code

## Testing

```bash
# Test with mock notifications
pytest backend/tests/test_alert_service.py -v

# Test with real Twilio/SendGrid (staging environment)
TWILIO_ACCOUNT_SID=xxx SENDGRID_API_KEY=yyy pytest backend/tests/test_alert_integration.py -v
```
```

---

## Implementation Plan

### Phase 1: Critical Fixes (Requirements 1-6)

**Priority**: MUST complete before submission
**Estimated Effort**: 4-6 hours
**Dependencies**: None

#### Task 1.1: ML Model Startup Check (Requirement 1)
- **Files**: `docker/start-backend.sh`, `ml/pipeline/train_all.py`
- **Steps**:
  1. Modify `start-backend.sh` to check for model files before starting server
  2. If models missing, call `python -m ml.pipeline.train_all` with 120s timeout
  3. Log success/failure to stdout
  4. Exit with code 1 if training fails
  5. Update health endpoint to report ml_models status
- **Testing**: Smoke test with fresh Docker volume
- **Acceptance**: `docker-compose up` works on first boot without manual steps

#### Task 1.2: API Key Authentication Middleware (Requirement 2)
- **Files**: `backend/middleware/api_key_auth.py` (new), `backend/main.py`, `.env.example`
- **Steps**:
  1. Create `ApiKeyMiddleware` class with public path whitelist
  2. Check X-API-Key header against API_KEY environment variable
  3. Return 401 for missing/invalid keys with descriptive messages
  4. Log authentication failures with client IP
  5. Add middleware to FastAPI app
  6. Update `.env.example` with API_KEY
- **Testing**: Integration tests for auth scenarios
- **Acceptance**: Protected endpoints require valid API key

#### Task 1.3: Environment Variable Documentation (Requirement 3)
- **Files**: `README.md`, `.env.example`
- **Steps**:
  1. Remove all references to ANTHROPIC_API_KEY from README
  2. Document LLM_API_KEY and LLM_PROVIDER variables
  3. Document API_KEY variable
  4. Document DEBUG variable with usage guidance
  5. Ensure .env.example matches README
  6. Add note about optional LLM integration
- **Testing**: Manual review of documentation
- **Acceptance**: README accurately reflects actual environment variables

#### Task 1.4: Alembic Environment Configuration (Requirement 4)
- **Files**: `backend/alembic/env.py`
- **Steps**:
  1. Read DATABASE_URL from os.getenv()
  2. Override alembic.ini sqlalchemy.url if DATABASE_URL exists
  3. Log which database URL is being used
  4. Add fallback warning if DATABASE_URL not found
- **Testing**: Run `alembic upgrade head` in Docker container
- **Acceptance**: Migrations work in Docker without hardcoded URLs

#### Task 1.5: Production Debug Mode Configuration (Requirement 5)
- **Files**: `.env.example`, `docker-compose.yml`, `backend/middleware/error_handler.py`
- **Steps**:
  1. Set DEBUG=False in `.env.example`
  2. Set DEBUG=${DEBUG:-False} in `docker-compose.yml`
  3. Add comment explaining DEBUG usage
  4. Verify error handler respects DEBUG flag
  5. Test stack trace visibility in both modes
- **Testing**: Manual testing with DEBUG=True and DEBUG=False
- **Acceptance**: Production defaults to DEBUG=False, no stack traces exposed

#### Task 1.6: Audit Logging for Explanations (Requirement 6)
- **Files**: `backend/services/audit_logger.py`, `backend/routes/explain.py`
- **Steps**:
  1. Add `log_explain()` method to AuditLogger
  2. Call `log_explain()` in explain endpoint after generating explanation
  3. Record student_id, prediction_id, performed_by, timestamp
  4. Verify EXPLAIN actions appear in audit_logs table
- **Testing**: Integration test for explain endpoint
- **Acceptance**: EXPLAIN actions logged alongside PREDICT actions

---

### Phase 2: Important Improvements (Requirements 7-13)

**Priority**: SHOULD complete for polished submission
**Estimated Effort**: 5-8 hours
**Dependencies**: Phase 1 complete

#### Task 2.1: Navigation Bar Component (Requirement 7)
- **Files**: `frontend/components/layout/NavigationBar.tsx` (new), `frontend/app/layout.tsx`
- **Steps**:
  1. Create NavigationBar component with links to Dashboard, Alerts, New Student, API Docs
  2. Implement active page highlighting using usePathname()
  3. Fetch alert count and display badge on Alerts link
  4. Add responsive mobile menu with hamburger icon
  5. Integrate NavigationBar into root layout
- **Testing**: Component tests + manual testing on desktop/mobile
- **Acceptance**: Navigation works on all pages with active highlighting

#### Task 2.2: Dashboard Add Student Button (Requirement 8)
- **Files**: `frontend/app/dashboard/page.tsx`
- **Steps**:
  1. Add Button component in dashboard header
  2. Link to /student/new
  3. Add Plus icon
  4. Style as primary button
  5. Position in top-right of header
- **Testing**: Manual testing
- **Acceptance**: Button visible and navigates to student form

#### Task 2.3: Batch Scoring Session Safety (Requirement 9)
- **Files**: `backend/routes/predict.py`, `backend/db/session.py`
- **Steps**:
  1. Create `get_async_session()` context manager
  2. Refactor batch endpoint to use independent sessions per student
  3. Use asyncio.gather() for parallel processing
  4. Implement error isolation (one failure doesn't affect others)
  5. Return success/failure status for each student
- **Testing**: Property test for batch independence
- **Acceptance**: Batch processing handles failures independently

#### Task 2.4: Risk Calculator Unit Tests (Requirement 10)
- **Files**: `backend/services/test_risk_calculator_unit.py` (new)
- **Steps**:
  1. Write tests for calculate_risk_score() with high/medium/low probs
  2. Write tests for assign_risk_level() with boundary values
  3. Write tests for calculate_emi_affordability() with edge cases
  4. Write tests for action recommender rules
  5. Achieve 100% coverage for risk_calculator.py
- **Testing**: Run pytest with coverage report
- **Acceptance**: All tests pass, 100% coverage achieved

#### Task 2.5: Salary Card EMI Context (Requirement 11)
- **Files**: `frontend/components/student/SalaryRangeCard.tsx`
- **Steps**:
  1. Add EMI affordability display below salary range
  2. Implement color coding (green < 30%, amber 30-50%, red > 50%)
  3. Add tooltip explaining EMI affordability
  4. Format percentage with one decimal place
  5. Add status labels (Good, Moderate, High Risk)
- **Testing**: Component tests + manual testing
- **Acceptance**: EMI affordability visible with correct color coding

#### Task 2.6: Risk Score Gauge Visualization (Requirement 12)
- **Files**: `frontend/components/student/RiskScoreGauge.tsx` (new), `frontend/components/student/RiskScoreDisplay.tsx`
- **Steps**:
  1. Create RiskScoreGauge component with SVG circular gauge
  2. Implement color zones (green 0-33, amber 34-66, red 67-100)
  3. Add animation from 0 to actual score on mount
  4. Display numeric score in center
  5. Make responsive for mobile
  6. Integrate into RiskScoreDisplay component
- **Testing**: Component tests + manual testing
- **Acceptance**: Gauge animates and displays correct colors

#### Task 2.7: Dashboard Empty State (Requirement 13)
- **Files**: `frontend/components/dashboard/EmptyState.tsx` (new), `frontend/app/dashboard/page.tsx`
- **Steps**:
  1. Create EmptyState component with icon, message, CTA button
  2. Add "Add Your First Student" button linking to /student/new
  3. Add secondary button linking to API docs
  4. Center component in dashboard
  5. Conditionally render EmptyState when students.length === 0
- **Testing**: Manual testing with empty database
- **Acceptance**: Empty state appears when no students exist

---

### Phase 3: Optional Enhancements (Requirements 14-18)

**Priority**: OPTIONAL for advanced features
**Estimated Effort**: 3-5 hours
**Dependencies**: Phase 2 complete

#### Task 3.1: CSV Batch Upload UI (Requirement 14)
- **Files**: `frontend/app/student/batch/page.tsx` (new)
- **Steps**:
  1. Create batch upload page with file input
  2. Parse CSV using Papa Parse library
  3. Validate required columns and row count (max 500)
  4. Display preview table of parsed students
  5. Submit batch to POST /api/batch-score
  6. Display progress indicator during processing
  7. Show results summary with success/failure counts
- **Testing**: Manual testing with valid/invalid CSV files
- **Acceptance**: CSV upload works with clear error messages

#### Task 3.2: Risk Score Trend Chart (Requirement 15)
- **Files**: `frontend/components/student/RiskScoreTrendChart.tsx` (new), `frontend/app/student/[id]/page.tsx`
- **Steps**:
  1. Create RiskScoreTrendChart component using Recharts
  2. Fetch prediction history from GET /api/students/{id}/predictions
  3. Plot risk_score vs created_at
  4. Color line green for improving trend, red for declining
  5. Handle "No historical data" case
  6. Add axis labels
- **Testing**: Manual testing with multiple predictions
- **Acceptance**: Trend chart displays historical risk scores

#### Task 3.3: Docker Multi-Stage Build (Requirement 16)
- **Files**: `docker/Dockerfile.backend`
- **Steps**:
  1. Create builder stage with gcc, g++, libpq-dev
  2. Install Python dependencies in builder stage
  3. Create runtime stage with python:3.11-slim
  4. Copy installed packages from builder to runtime
  5. Install only runtime dependencies (libpq5)
  6. Verify final image size < 1 GB
- **Testing**: Build image and check size with `docker images`
- **Acceptance**: Image size under 1 GB, all functionality works

#### Task 3.4: Student Table Pagination (Requirement 17)
- **Files**: `frontend/components/dashboard/StudentTable.tsx`, `backend/routes/students.py`
- **Steps**:
  1. Add pagination controls below table
  2. Add Previous/Next buttons
  3. Add page size selector (20, 50, 100)
  4. Display current page and total pages
  5. Display total student count
  6. Fetch paginated data from API with limit/offset
  7. Reset to page 1 when page size changes
- **Testing**: Manual testing with > 100 students
- **Acceptance**: Pagination works smoothly with large datasets

#### Task 3.5: API Integration Tests (Requirement 18)
- **Files**: `backend/tests/test_api_integration.py` (new)
- **Steps**:
  1. Set up test database with TestClient
  2. Write tests for POST /api/predict (valid and invalid data)
  3. Write tests for GET /api/students
  4. Write tests for GET /api/alerts
  5. Write tests for GET /api/explain/{student_id}
  6. Write tests for GET /api/health
  7. Write tests for authentication middleware
- **Testing**: Run pytest on integration test suite
- **Acceptance**: All integration tests pass

#### Task 3.6: CSV Parser Property Tests (Requirement 19)
- **Files**: `backend/schemas/test_csv_parser_properties.py` (new), `backend/schemas/csv_parser.py` (new)
- **Steps**:
  1. Implement parse_csv() and print_csv() functions
  2. Write property test for missing field errors
  3. Write property test for type mismatch errors
  4. Write property test for round-trip preservation
  5. Run tests with 100+ iterations
- **Testing**: Run pytest with Hypothesis
- **Acceptance**: All property tests pass with 100+ examples

---

### Implementation Order

```mermaid
gantt
    title Implementation Timeline
    dateFormat  YYYY-MM-DD
    section Phase 1 (Critical)
    ML Model Startup Check           :p1t1, 2024-01-15, 2h
    API Key Authentication           :p1t2, after p1t1, 2h
    Environment Docs                 :p1t3, after p1t2, 1h
    Alembic Configuration            :p1t4, after p1t3, 1h
    Debug Mode Config                :p1t5, after p1t4, 1h
    Audit Logging                    :p1t6, after p1t5, 1h
    
    section Phase 2 (Important)
    Navigation Bar                   :p2t1, after p1t6, 3h
    Dashboard Button                 :p2t2, after p2t1, 1h
    Batch Session Safety             :p2t3, after p2t2, 2h
    Risk Calculator Tests            :p2t4, after p2t3, 2h
    Salary EMI Context               :p2t5, after p2t4, 2h
    Risk Score Gauge                 :p2t6, after p2t5, 3h
    Dashboard Empty State            :p2t7, after p2t6, 1h
    
    section Phase 3 (Optional)
    CSV Batch Upload                 :p3t1, after p2t7, 3h
    Risk Trend Chart                 :p3t2, after p3t1, 2h
    Docker Multi-Stage               :p3t3, after p3t2, 2h
    Table Pagination                 :p3t4, after p3t3, 2h
    API Integration Tests            :p3t5, after p3t4, 2h
    CSV Parser Properties            :p3t6, after p3t5, 2h
```

---

### Rollback Strategy

Each phase can be rolled back independently:

**Phase 1 Rollback**:
- Revert `start-backend.sh` to original version
- Remove `ApiKeyMiddleware` from middleware stack
- Restore original README and .env.example
- Revert `alembic/env.py` changes
- Restore original DEBUG defaults

**Phase 2 Rollback**:
- Remove NavigationBar from layout
- Remove dashboard button
- Revert batch endpoint to original implementation
- Delete test files
- Revert frontend component changes

**Phase 3 Rollback**:
- Delete batch upload page
- Delete trend chart component
- Revert Dockerfile to single-stage build
- Remove pagination controls
- Delete integration test files

---

### Success Criteria

**Phase 1 Complete When**:
- ✅ Docker compose up works on first boot
- ✅ All endpoints require API key authentication
- ✅ README matches actual environment variables
- ✅ Alembic migrations work in Docker
- ✅ DEBUG=False by default
- ✅ EXPLAIN actions logged to audit trail

**Phase 2 Complete When**:
- ✅ Navigation bar on all pages
- ✅ Dashboard has "Add Student" button
- ✅ Batch scoring handles failures independently
- ✅ Risk calculator has 100% test coverage
- ✅ Salary card shows EMI affordability
- ✅ Risk gauge animates correctly
- ✅ Empty state appears when no students

**Phase 3 Complete When**:
- ✅ CSV batch upload works
- ✅ Risk trend chart displays history
- ✅ Docker image under 1 GB
- ✅ Table pagination works
- ✅ Integration tests pass
- ✅ CSV parser property tests pass

**Submission Ready When**:
- ✅ Phase 1 complete (100%)
- ✅ Phase 2 at least 5/7 tasks complete (71%+)
- ✅ All tests passing
- ✅ No critical security issues
- ✅ Documentation accurate and complete



## Appendix

### A. Environment Variables Reference

Complete list of environment variables used by the system:

#### Backend Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `DATABASE_URL` | Yes | - | PostgreSQL connection URL (format: `postgresql+asyncpg://user:pass@host:port/db`) |
| `REDIS_URL` | No | - | Redis connection URL (format: `redis://host:port/db`) |
| `ML_MODEL_PATH` | Yes | `ml/models` | Path to ML model files directory |
| `API_KEY` | No | - | API key for endpoint authentication (if not set, auth disabled) |
| `LLM_API_KEY` | No | - | API key for LLM provider (Groq or Anthropic) |
| `LLM_PROVIDER` | No | `groq` | LLM provider: `groq` or `anthropic` |
| `SECRET_KEY` | No | `dev_secret_key` | Secret key for JWT signing (future use) |
| `CORS_ORIGINS` | No | `http://localhost:3000` | Comma-separated list of allowed CORS origins |
| `DEBUG` | No | `False` | Enable debug mode with detailed error traces |
| `LOG_LEVEL` | No | `INFO` | Logging level: `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL` |
| `LOG_JSON_FORMAT` | No | `True` | Use JSON format for structured logging |
| `RATE_LIMIT_ENABLED` | No | `True` | Enable rate limiting middleware |
| `RATE_LIMIT_PREDICT_PER_MINUTE` | No | `100` | Rate limit for POST /api/predict |
| `RATE_LIMIT_BATCH_PER_MINUTE` | No | `10` | Rate limit for POST /api/batch-score |
| `RATE_LIMIT_GET_PER_MINUTE` | No | `300` | Rate limit for GET requests |

#### Frontend Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `NEXT_PUBLIC_API_URL` | Yes | - | Backend API base URL (e.g., `http://localhost:8000`) |
| `NEXT_PUBLIC_API_KEY` | No | - | API key for backend authentication (if required) |

#### Docker Compose Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `POSTGRES_USER` | Yes | `edurisk` | PostgreSQL username |
| `POSTGRES_PASSWORD` | Yes | `edurisk_password` | PostgreSQL password |
| `POSTGRES_DB` | Yes | `edurisk_db` | PostgreSQL database name |

---

### B. API Endpoints Reference

Complete list of API endpoints with authentication requirements:

#### Public Endpoints (No Authentication Required)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Root endpoint - API information |
| GET | `/api/health` | Health check with system status |
| GET | `/docs` | OpenAPI documentation (Swagger UI) |
| GET | `/redoc` | OpenAPI documentation (ReDoc) |
| GET | `/openapi.json` | OpenAPI schema JSON |

#### Protected Endpoints (Require X-API-Key Header)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/predict` | Create student and generate risk prediction |
| POST | `/api/batch-score` | Batch prediction for multiple students |
| GET | `/api/students` | List all students with pagination |
| GET | `/api/students/{id}` | Get student details by ID |
| GET | `/api/students/{id}/predictions` | Get prediction history for student |
| GET | `/api/alerts` | List high-risk alerts |
| GET | `/api/explain/{student_id}` | Get SHAP explanation for latest prediction |
| GET | `/api/audit-logs` | List audit trail entries |

---

### C. Database Schema Reference

#### Students Table

```sql
CREATE TABLE students (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR NOT NULL,
    course_type VARCHAR NOT NULL,
    institute_name VARCHAR NOT NULL,
    institute_tier INTEGER NOT NULL CHECK (institute_tier BETWEEN 1 AND 3),
    cgpa NUMERIC(4, 2) NOT NULL CHECK (cgpa >= 0 AND cgpa <= 10),
    cgpa_scale NUMERIC(4, 2) DEFAULT 10.0,
    year_of_grad INTEGER NOT NULL,
    internship_count INTEGER DEFAULT 0,
    internship_months INTEGER DEFAULT 0,
    internship_employer_type VARCHAR,
    certifications VARCHAR,
    region VARCHAR,
    loan_amount NUMERIC(12, 2),
    loan_emi NUMERIC(10, 2),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE
);
```

#### Predictions Table

```sql
CREATE TABLE predictions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    student_id UUID NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    model_version VARCHAR NOT NULL,
    prob_placed_3m NUMERIC(5, 4) NOT NULL,
    prob_placed_6m NUMERIC(5, 4) NOT NULL,
    prob_placed_12m NUMERIC(5, 4) NOT NULL,
    placement_label VARCHAR NOT NULL,
    risk_score INTEGER NOT NULL CHECK (risk_score BETWEEN 0 AND 100),
    risk_level VARCHAR NOT NULL CHECK (risk_level IN ('low', 'medium', 'high')),
    salary_min NUMERIC(12, 2),
    salary_max NUMERIC(12, 2),
    salary_confidence NUMERIC(5, 4),
    emi_affordability NUMERIC(5, 3),
    shap_values JSONB,
    top_risk_drivers JSONB,
    ai_summary TEXT,
    next_best_actions JSONB,
    alert_triggered BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_predictions_student_id ON predictions(student_id);
CREATE INDEX idx_predictions_risk_level ON predictions(risk_level);
CREATE INDEX idx_predictions_alert_triggered ON predictions(alert_triggered);
```

#### Audit Logs Table

```sql
CREATE TABLE audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    action VARCHAR NOT NULL CHECK (action IN ('PREDICT', 'EXPLAIN', 'ALERT_SENT')),
    student_id UUID REFERENCES students(id) ON DELETE SET NULL,
    prediction_id UUID REFERENCES predictions(id) ON DELETE SET NULL,
    performed_by VARCHAR NOT NULL,
    details JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_audit_logs_action ON audit_logs(action);
CREATE INDEX idx_audit_logs_student_id ON audit_logs(student_id);
CREATE INDEX idx_audit_logs_created_at ON audit_logs(created_at DESC);
```

---

### D. Docker Commands Reference

#### Development Commands

```bash
# Start all services
docker-compose up

# Start in detached mode
docker-compose up -d

# Rebuild images
docker-compose up --build

# Stop all services
docker-compose down

# Stop and remove volumes (clean slate)
docker-compose down -v

# View logs
docker-compose logs -f backend
docker-compose logs -f frontend

# Execute command in container
docker exec -it edurisk-backend bash
docker exec -it edurisk-frontend sh

# Run database migrations
docker exec -it edurisk-backend alembic upgrade head

# Train ML models manually
docker exec -it edurisk-backend python -m ml.pipeline.train_all

# Check container health
docker ps
docker inspect edurisk-backend | grep Health
```

#### Production Commands

```bash
# Build production images
docker-compose -f docker-compose.prod.yml build

# Start production services
docker-compose -f docker-compose.prod.yml up -d

# View production logs
docker-compose -f docker-compose.prod.yml logs -f

# Scale backend service
docker-compose -f docker-compose.prod.yml up -d --scale backend=3

# Check image sizes
docker images | grep edurisk
```

---

### E. Testing Commands Reference

#### Backend Testing

```bash
# Run all tests
pytest

# Run specific test file
pytest backend/services/test_risk_calculator_unit.py

# Run with coverage
pytest --cov=backend --cov-report=html

# Run property tests with verbose output
pytest backend/services/test_risk_calculator_properties.py -v

# Run integration tests
pytest backend/tests/test_api_integration.py -v

# Run smoke tests
pytest backend/tests/test_smoke.py -v

# Run tests matching pattern
pytest -k "test_risk_score"

# Run tests with specific marker
pytest -m "unit"

# Generate coverage report
pytest --cov=backend --cov-report=term-missing
```

#### Frontend Testing

```bash
# Run all tests
cd frontend && npm test

# Run tests in watch mode
cd frontend && npm test -- --watch

# Run tests with coverage
cd frontend && npm test -- --coverage

# Run specific test file
cd frontend && npm test -- NavigationBar.test.tsx

# Update snapshots
cd frontend && npm test -- -u
```

#### Property-Based Testing

```bash
# Run with default profile (100 examples)
pytest backend/services/test_risk_calculator_properties.py

# Run with CI profile (200 examples)
pytest backend/services/test_risk_calculator_properties.py --hypothesis-profile=ci

# Run with verbose Hypothesis output
pytest backend/services/test_risk_calculator_properties.py -v --hypothesis-verbosity=verbose

# Find minimal failing example
pytest backend/services/test_risk_calculator_properties.py --hypothesis-seed=12345
```

---

### F. Troubleshooting Guide

#### Issue: Docker container fails to start

**Symptoms**: Container exits immediately after `docker-compose up`

**Possible Causes**:
1. ML model training timeout
2. Database connection failure
3. Missing environment variables

**Solutions**:
```bash
# Check container logs
docker-compose logs backend

# Check if database is ready
docker-compose logs postgres | grep "ready to accept connections"

# Verify environment variables
docker exec -it edurisk-backend env | grep DATABASE_URL

# Manually train models
docker exec -it edurisk-backend python -m ml.pipeline.train_all

# Restart with clean volumes
docker-compose down -v && docker-compose up
```

---

#### Issue: API returns 401 Unauthorized

**Symptoms**: All API requests return 401 even with valid data

**Possible Causes**:
1. Missing X-API-Key header
2. Invalid API key
3. API_KEY environment variable not set

**Solutions**:
```bash
# Check if API_KEY is configured
docker exec -it edurisk-backend env | grep API_KEY

# Test with curl
curl -H "X-API-Key: your_api_key" http://localhost:8000/api/health

# Disable authentication temporarily (for debugging)
# Set API_KEY="" in docker-compose.yml
```

---

#### Issue: ML models not found

**Symptoms**: Health endpoint returns `ml_models: unavailable`

**Possible Causes**:
1. Models not trained on first boot
2. Volume mount issue
3. Model files corrupted

**Solutions**:
```bash
# Check if model files exist
docker exec -it edurisk-backend ls -la ml/models/

# Manually train models
docker exec -it edurisk-backend python -m ml.pipeline.train_all

# Check volume mounts
docker inspect edurisk-backend | grep Mounts -A 10

# Remove and retrain
docker exec -it edurisk-backend rm -rf ml/models/*.pkl
docker-compose restart backend
```

---

#### Issue: Frontend can't connect to backend

**Symptoms**: Frontend shows network errors, API calls fail

**Possible Causes**:
1. Wrong NEXT_PUBLIC_API_URL
2. CORS configuration issue
3. Backend not running

**Solutions**:
```bash
# Check backend is running
curl http://localhost:8000/api/health

# Check frontend environment
docker exec -it edurisk-frontend env | grep NEXT_PUBLIC_API_URL

# Check CORS origins in backend
docker exec -it edurisk-backend env | grep CORS_ORIGINS

# Test from frontend container
docker exec -it edurisk-frontend curl http://backend:8000/api/health
```

---

#### Issue: Database migrations fail

**Symptoms**: Alembic upgrade fails with connection error

**Possible Causes**:
1. Wrong DATABASE_URL
2. Database not ready
3. Schema conflict

**Solutions**:
```bash
# Check DATABASE_URL
docker exec -it edurisk-backend env | grep DATABASE_URL

# Wait for database
docker exec -it edurisk-backend python /app/wait-for-db.py

# Check database connectivity
docker exec -it edurisk-postgres psql -U edurisk -d edurisk_db -c "SELECT 1"

# Reset database (WARNING: deletes all data)
docker-compose down -v
docker-compose up -d postgres
docker-compose up backend
```

---

### G. Performance Optimization Notes

#### Backend Optimization

1. **Database Connection Pooling**:
   - Use SQLAlchemy async engine with pool size 20
   - Set pool_recycle to 3600 seconds
   - Enable pool_pre_ping for connection health checks

2. **Redis Caching**:
   - Cache student predictions for 5 minutes
   - Cache ML model metadata for 1 hour
   - Use Redis for rate limiting state

3. **Async Processing**:
   - Use asyncio.gather() for parallel batch processing
   - Implement async database queries
   - Use async LLM API calls with timeout

#### Frontend Optimization

1. **Code Splitting**:
   - Use Next.js dynamic imports for heavy components
   - Lazy load chart libraries (Recharts)
   - Split vendor bundles

2. **Data Fetching**:
   - Use React Server Components for initial data
   - Implement SWR for client-side caching
   - Prefetch navigation targets

3. **Image Optimization**:
   - Use Next.js Image component
   - Serve images in WebP format
   - Implement lazy loading

#### Docker Optimization

1. **Multi-Stage Builds** (Requirement 16):
   - Separate builder and runtime stages
   - Copy only necessary files to runtime
   - Use slim base images

2. **Layer Caching**:
   - Copy requirements.txt before code
   - Install dependencies in separate layer
   - Minimize layer count

3. **Image Size**:
   - Remove build tools from runtime
   - Clean apt cache after installs
   - Use .dockerignore to exclude unnecessary files

---

### H. Security Considerations

#### Authentication

- API key authentication for all protected endpoints
- Store API keys in environment variables, never in code
- Use strong, randomly generated API keys (min 32 characters)
- Rotate API keys periodically

#### Data Protection

- Use HTTPS in production (configure reverse proxy)
- Sanitize all user inputs (Pydantic validation)
- Prevent SQL injection (use parameterized queries)
- Limit request payload size (FastAPI default: 16MB)

#### Rate Limiting

- Implement per-IP rate limiting with Redis
- Different limits for different endpoints
- Return 429 with Retry-After header
- Log rate limit violations

#### Error Handling

- Never expose stack traces in production (DEBUG=False)
- Sanitize error messages (no sensitive data)
- Log all errors with context
- Use generic error messages for users

#### Dependency Security

- Regularly update dependencies (npm audit, pip-audit)
- Use dependabot for automated updates
- Pin dependency versions in production
- Scan Docker images for vulnerabilities

---

### I. Deployment Checklist

#### Pre-Deployment

- [ ] All Phase 1 requirements complete
- [ ] All tests passing (unit, property, integration)
- [ ] Code coverage > 85%
- [ ] No critical security vulnerabilities
- [ ] Documentation up to date
- [ ] Environment variables documented
- [ ] API key generated and secured
- [ ] DEBUG=False in production
- [ ] CORS origins configured correctly

#### Deployment

- [ ] Build Docker images
- [ ] Push images to registry
- [ ] Configure production environment variables
- [ ] Set up PostgreSQL database
- [ ] Set up Redis cache
- [ ] Run database migrations
- [ ] Train ML models (or copy from dev)
- [ ] Start backend service
- [ ] Start frontend service
- [ ] Configure reverse proxy (nginx)
- [ ] Set up SSL certificates
- [ ] Configure monitoring and logging

#### Post-Deployment

- [ ] Verify health endpoint returns 200
- [ ] Test API authentication
- [ ] Test prediction endpoint
- [ ] Test batch scoring
- [ ] Verify ML models loaded
- [ ] Check application logs
- [ ] Monitor error rates
- [ ] Test frontend navigation
- [ ] Verify CORS working
- [ ] Load test critical endpoints

---

### J. Future Enhancements

**Beyond Submission Scope** (not part of current requirements):

1. **User Authentication**:
   - JWT-based user authentication
   - Role-based access control (admin, analyst, viewer)
   - User management UI

2. **Advanced Analytics**:
   - Portfolio risk dashboard with aggregated metrics
   - Risk distribution histograms
   - Cohort analysis by institute/course

3. **Model Improvements**:
   - A/B testing for model versions
   - Model retraining pipeline
   - Feature importance tracking over time

4. **Notifications**:
   - Email alerts for high-risk students
   - Webhook integrations
   - Slack/Teams notifications

5. **Export Features**:
   - PDF report generation
   - Excel export for batch results
   - API for third-party integrations

6. **Performance**:
   - Implement caching layer with Redis
   - Add database read replicas
   - Optimize SHAP computation

