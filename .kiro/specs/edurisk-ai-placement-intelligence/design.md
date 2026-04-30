# Design Document: EduRisk AI - Placement Risk Intelligence

## Overview

EduRisk AI is a three-tier Placement Risk Intelligence system that predicts student placement outcomes and generates actionable risk assessments for education loan lenders. The system processes student academic and internship data through machine learning models to produce placement timeline predictions (3/6/12 months), salary estimates, composite risk scores, SHAP-based explanations, AI-generated summaries, and personalized intervention recommendations.

### System Goals

1. **Predictive Accuracy**: Achieve AUC-ROC ≥ 0.85 for placement classification across all time windows
2. **Explainability**: Provide transparent, auditable feature attributions for every prediction using SHAP values
3. **Fairness**: Exclude demographic features (gender, religion, caste, state of origin) from all ML models
4. **Performance**: Process single predictions in <5 seconds and batch predictions (500 students) in <60 seconds
5. **Compliance**: Maintain complete audit trails for RBI regulatory requirements
6. **Actionability**: Generate contextual intervention recommendations to improve student outcomes

### Key Design Principles

- **Separation of Concerns**: ML pipeline, API backend, and frontend are independently deployable
- **Async-First**: FastAPI with async database operations for high concurrency
- **Model Versioning**: All predictions tagged with model version for reproducibility
- **Fail-Safe Defaults**: Graceful degradation when external services (Claude API) fail
- **Data Integrity**: Foreign key constraints with cascading deletes, JSONB for flexible schema evolution

### Technology Stack Summary

| Layer | Technology | Justification |
|-------|-----------|---------------|
| ML Models | XGBoost 2.0 | Best-in-class for tabular data; TreeExplainer provides exact SHAP values |
| Salary Model | Ridge Regression | Linear model appropriate for continuous salary prediction with regularization |
| Explainability | SHAP 0.44 | Industry standard; TreeExplainer is fast and exact for tree models |
| API Framework | FastAPI 0.111 | Native async support, automatic OpenAPI docs, Pydantic validation |
| Database | PostgreSQL 16 | JSONB support for flexible SHAP storage, strong ACID guarantees |
| ORM | SQLAlchemy 2.0 | Async support, mature migration tooling with Alembic |
| Cache/Rate Limiting | Redis 7 | In-memory performance for rate limit counters |
| LLM Integration | Anthropic Claude Sonnet 4 | High-quality natural language generation for risk summaries |
| Frontend | Next.js 14 (App Router) | Server-side rendering, React Server Components, optimal performance |
| UI Components | shadcn/ui + Tailwind | Accessible, customizable, professional design system |
| Visualization | Recharts | React-native charting for SHAP waterfalls, probability bars, heatmaps |
| Containerization | Docker Compose | Single-command local development environment |


## Architecture

### System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                         Frontend (Next.js 14)                    │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │  Dashboard   │  │ Student      │  │   Alerts     │          │
│  │  Portfolio   │  │ Detail Page  │  │   Page       │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
│         │                  │                  │                  │
│         └──────────────────┴──────────────────┘                 │
│                            │                                     │
│                    HTTP/REST API                                 │
└────────────────────────────┼────────────────────────────────────┘
                             │
┌────────────────────────────┼────────────────────────────────────┐
│                    FastAPI Backend                               │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                    API Layer                              │   │
│  │  /predict  /batch-score  /explain  /alerts  /students    │   │
│  └────────────────┬─────────────────────────────────────────┘   │
│                   │                                              │
│  ┌────────────────┴─────────────────────────────────────────┐   │
│  │                  Service Layer                            │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐   │   │
│  │  │ Prediction   │  │ Explanation  │  │    Alert     │   │   │
│  │  │   Service    │  │   Service    │  │   Service    │   │   │
│  │  └──────────────┘  └──────────────┘  └──────────────┘   │   │
│  │  ┌──────────────┐                                        │   │
│  │  │     LLM      │  ← Anthropic Claude API               │   │
│  │  │   Service    │                                        │   │
│  │  └──────────────┘                                        │   │
│  └────────────────┬─────────────────────────────────────────┘   │
│                   │                                              │
│  ┌────────────────┴─────────────────────────────────────────┐   │
│  │                  Data Layer                               │   │
│  │  SQLAlchemy ORM + Async Session Management               │   │
│  └────────────────┬─────────────────────────────────────────┘   │
└───────────────────┼──────────────────────────────────────────────┘
                    │
        ┌───────────┴───────────┐
        │                       │
┌───────▼────────┐    ┌─────────▼────────┐
│  PostgreSQL 16 │    │    Redis 7       │
│                │    │                  │
│  - students    │    │  - Rate limits   │
│  - predictions │    │  - Session cache │
│  - audit_logs  │    │                  │
└────────────────┘    └──────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                    ML Pipeline (Offline)                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │   Feature    │→ │   Model      │→ │    SHAP      │          │
│  │ Engineering  │  │  Training    │  │  Analysis    │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
│                                                                  │
│  Outputs: placement_model_3m.pkl, placement_model_6m.pkl,       │
│           placement_model_12m.pkl, salary_model.pkl,            │
│           feature_names.json, version.json                      │
└──────────────────────────────────────────────────────────────────┘
```

### Component Interactions

#### Prediction Flow

1. **Frontend** submits Student_Profile via POST /api/predict
2. **API Layer** validates request with Pydantic schemas
3. **Prediction Service**:
   - Loads ML models from disk (cached in memory)
   - Applies feature engineering transformations
   - Invokes 3 XGBoost classifiers (3m, 6m, 12m)
   - Invokes Ridge regression for salary
   - Computes risk score and EMI affordability
4. **Explanation Service**:
   - Computes SHAP values using TreeExplainer
   - Identifies top 5 risk drivers
5. **LLM Service**:
   - Generates natural language summary via Claude API
   - Falls back to template if API fails
6. **Action Recommender** (within Prediction Service):
   - Applies rule-based logic to generate interventions
7. **Data Layer**:
   - Inserts student record
   - Inserts prediction record with JSONB fields
   - Inserts audit log entry
8. **API Layer** returns complete prediction response

#### Batch Scoring Flow

- Same as single prediction but processes array in parallel using `asyncio.gather()`
- Limits batch size to 500 to prevent memory exhaustion
- Returns aggregated summary statistics

#### Explanation Retrieval Flow

1. Frontend requests GET /api/explain/{student_id}
2. API Layer queries most recent prediction for student
3. Explanation Service formats SHAP values into waterfall data structure
4. Returns JSON with base_value, SHAP dictionary, and cumulative values

### Deployment Architecture

**Development Environment (Docker Compose)**:
- All services run in containers on single host
- Shared Docker network for inter-service communication
- Volume mounts for hot-reload during development
- ML models mounted as read-only volume

**Production Considerations** (out of scope for hackathon):
- Backend: Multiple FastAPI instances behind load balancer
- Database: PostgreSQL with read replicas for analytics queries
- Redis: Redis Cluster for high availability
- ML Models: Versioned artifacts in S3/GCS, loaded at startup
- Frontend: Static export deployed to CDN


## Components and Interfaces

### ML Pipeline Components

#### Feature Engineering Module (`ml/pipeline/feature_engineering.py`)

**Purpose**: Transform raw student data into model-ready features with consistent preprocessing.

**Interface**:
```python
class FeatureEngineer:
    def __init__(self, feature_config: dict):
        """Initialize with feature configuration including scaling params."""
        
    def transform(self, student_data: dict) -> np.ndarray:
        """
        Transform raw student data into feature vector.
        
        Args:
            student_data: Dictionary with keys matching Student_Profile schema
            
        Returns:
            numpy array of shape (1, n_features) ready for model inference
            
        Raises:
            ValueError: If required fields missing or invalid values
        """
        
    def get_feature_names(self) -> List[str]:
        """Return ordered list of feature names matching transform output."""
```

**Key Transformations**:
- `cgpa_normalized = cgpa / cgpa_scale` (0.0 to 1.0 range)
- `internship_score = (count × 0.4) + (months/24 × 0.3) + (employer_score × 0.3)`
- `employer_type_score`: MNC=4, Startup=3, PSU=2, NGO=1, None=0
- `skill_gap_score = job_demand_score - (cgpa_normalized × 5 + internship_score × 5)`
- `emi_stress_ratio = loan_emi / salary_benchmark`
- `placement_momentum = placement_rate_3m / placement_rate_12m`
- One-hot encoding for `institute_tier` (3 binary features)
- Label encoding for `course_type` (Engineering=0, MBA=1, etc.)

**Feature Set** (16 features total):
1. cgpa_normalized
2. internship_score
3. employer_type_score
4. certifications (capped at 5)
5. institute_tier_1 (one-hot)
6. institute_tier_2 (one-hot)
7. institute_tier_3 (one-hot)
8. course_type_encoded
9. placement_rate_3m (institute historical)
10. placement_rate_6m (institute historical)
11. salary_benchmark (institute historical)
12. job_demand_score (sector index 1-10)
13. region_job_density (region index)
14. macro_hiring_index (0-1 composite)
15. skill_gap_score (derived)
16. emi_stress_ratio (derived)

**Excluded Features**: gender, religion, caste, state_of_origin (stored but never passed to models)

#### Placement Prediction Module (`ml/pipeline/predict.py`)

**Purpose**: Load trained XGBoost models and generate placement probability predictions.

**Interface**:
```python
class PlacementPredictor:
    def __init__(self, model_dir: Path):
        """Load 3 XGBoost models from disk."""
        
    def predict(self, features: np.ndarray) -> PlacementPrediction:
        """
        Generate placement predictions for all time windows.
        
        Args:
            features: Feature vector from FeatureEngineer (1, 16)
            
        Returns:
            PlacementPrediction with prob_3m, prob_6m, prob_12m, label
        """
        
    def get_model_version(self) -> str:
        """Return semantic version string from version.json."""
```

**Model Configuration**:
```python
XGBClassifier(
    n_estimators=300,
    max_depth=6,
    learning_rate=0.05,
    subsample=0.8,
    colsample_bytree=0.8,
    use_label_encoder=False,
    eval_metric='auc',
    random_state=42
)
```

**Placement Label Logic**:
- If `prob_3m >= 0.50`: label = "placed_3m"
- Elif `prob_6m >= 0.50`: label = "placed_6m"
- Elif `prob_12m >= 0.50`: label = "placed_12m"
- Else: label = "high_risk"

#### Salary Estimation Module (`ml/pipeline/salary_model.py`)

**Purpose**: Predict salary range using Ridge regression.

**Interface**:
```python
class SalaryEstimator:
    def __init__(self, model_path: Path):
        """Load Ridge regression pipeline (scaler + model)."""
        
    def predict(self, features: np.ndarray) -> SalaryPrediction:
        """
        Predict salary range in LPA.
        
        Args:
            features: Same feature vector as placement models
            
        Returns:
            SalaryPrediction with min, max, predicted, confidence
        """
```

**Salary Calculation**:
- `predicted_salary = model.predict(features)[0]`
- `std = model.std_residuals_` (from training)
- `salary_min = predicted - 1.5 × std`
- `salary_max = predicted + 1.5 × std`
- `confidence = ((salary_max - salary_min) / predicted) × 100`

**Model Pipeline**:
```python
Pipeline([
    ('scaler', StandardScaler()),
    ('model', Ridge(alpha=1.0))
])
```

#### SHAP Explanation Module (`ml/pipeline/explain.py`)

**Purpose**: Generate feature attributions using SHAP TreeExplainer.

**Interface**:
```python
class ShapExplainer:
    def __init__(self, model: XGBClassifier):
        """Initialize TreeExplainer for given model."""
        
    def explain(self, features: np.ndarray, feature_names: List[str]) -> ShapExplanation:
        """
        Compute SHAP values for prediction.
        
        Args:
            features: Feature vector (1, 16)
            feature_names: Ordered list of feature names
            
        Returns:
            ShapExplanation with values dict, base_value, top_drivers
        """
```

**SHAP Output Structure**:
```python
{
    "shap_values": {
        "internship_score": 0.34,
        "institute_tier_1": 0.22,
        "cgpa_normalized": 0.11,
        "job_demand_score": -0.09,
        "course_type_encoded": -0.17,
        ...
    },
    "base_value": 0.45,  # Model baseline on training data
    "prediction": 0.78,   # base_value + sum(shap_values)
    "top_drivers": [
        {"feature": "internship_score", "value": 0.34, "direction": "positive"},
        {"feature": "institute_tier_1", "value": 0.22, "direction": "positive"},
        {"feature": "course_type_encoded", "value": -0.17, "direction": "negative"},
        {"feature": "cgpa_normalized", "value": 0.11, "direction": "positive"},
        {"feature": "job_demand_score", "value": -0.09, "direction": "negative"}
    ]
}
```

**Top Drivers Selection**: Sort by `abs(shap_value)` descending, take top 5.

#### Model Training Module (`ml/pipeline/train.py`)

**Purpose**: Train XGBoost classifiers with hyperparameter optimization.

**Training Strategy**:
1. Load processed training data (synthetic + Kaggle datasets)
2. 80/20 train-test split, stratified by placement label
3. 5-fold cross-validation for each model
4. Hyperparameter tuning with Optuna (50 trials)
5. Save best model as `.pkl` with joblib
6. Log metrics: AUC-ROC, F1, Precision, Recall per fold

**Hyperparameter Search Space**:
```python
{
    'n_estimators': [100, 200, 300, 500],
    'max_depth': [3, 4, 5, 6, 7],
    'learning_rate': [0.01, 0.05, 0.1],
    'subsample': [0.7, 0.8, 0.9],
    'colsample_bytree': [0.7, 0.8, 0.9],
    'min_child_weight': [1, 3, 5],
    'gamma': [0, 0.1, 0.2]
}
```

**Target Variables**:
- `placed_3m`: Binary (1 if placed within 3 months, else 0)
- `placed_6m`: Binary (1 if placed within 6 months, else 0)
- `placed_12m`: Binary (1 if placed within 12 months, else 0)

#### Bias Audit Module (`ml/pipeline/bias_audit.py`)

**Purpose**: Post-hoc fairness testing using Fairlearn.

**Interface**:
```python
def run_bias_audit(
    model: XGBClassifier,
    X_test: pd.DataFrame,
    y_test: pd.Series,
    sensitive_features: pd.DataFrame
) -> BiasReport:
    """
    Compute demographic parity metrics.
    
    Args:
        model: Trained XGBoost model
        X_test: Test features (WITHOUT sensitive features)
        y_test: True labels
        sensitive_features: DataFrame with gender, region columns
        
    Returns:
        BiasReport with parity differences and metric breakdowns
    """
```

**Metrics Computed**:
- Accuracy by gender group
- Selection rate by gender group
- Demographic parity difference (max difference in selection rates)
- Equalized odds difference

**Bias Threshold**: Flag model if `demographic_parity_difference > 0.1`

### Backend API Components

#### API Router (`backend/api/router.py`)

**Purpose**: Central routing configuration for all endpoints.

**Endpoints**:
- `POST /api/predict` → `routes.predict.predict_single`
- `POST /api/batch-score` → `routes.predict.predict_batch`
- `GET /api/explain/{student_id}` → `routes.explain.get_explanation`
- `GET /api/alerts` → `routes.alerts.get_alerts`
- `GET /api/students` → `routes.students.list_students`
- `GET /api/health` → `routes.health.health_check`

**Middleware Stack**:
1. CORS middleware (configured from env)
2. Rate limiting middleware (Redis-backed)
3. Request logging middleware
4. Exception handling middleware

#### Prediction Service (`backend/services/prediction_service.py`)

**Purpose**: Orchestrate ML pipeline and business logic for predictions.

**Interface**:
```python
class PredictionService:
    def __init__(
        self,
        feature_engineer: FeatureEngineer,
        placement_predictor: PlacementPredictor,
        salary_estimator: SalaryEstimator,
        shap_explainer: ShapExplainer,
        llm_service: LLMService
    ):
        """Initialize with all ML components."""
        
    async def predict_student(
        self,
        student_data: StudentInput,
        db: AsyncSession
    ) -> PredictionResponse:
        """
        Generate complete prediction for student.
        
        Flow:
        1. Create student record in DB
        2. Transform features
        3. Get placement predictions
        4. Get salary prediction
        5. Compute risk score
        6. Compute EMI affordability
        7. Generate SHAP explanation
        8. Generate AI summary (async)
        9. Generate next-best actions
        10. Store prediction in DB
        11. Log audit entry
        12. Return response
        """
```

**Risk Score Calculation**:
```python
risk_score = 100 - (
    prob_3m * 50 +
    prob_6m * 30 +
    prob_12m * 20
)
```

**Risk Level Assignment**:
- 0-33: "low"
- 34-66: "medium"
- 67-100: "high"

**EMI Affordability**:
```python
monthly_salary = (predicted_salary_lpa * 100000) / 12
emi_affordability = loan_emi / monthly_salary
```

**High Risk Flag**: Set `alert_triggered = True` if `risk_level == "high"` OR `emi_affordability > 0.5`

#### Action Recommender (within Prediction Service)

**Purpose**: Generate contextual intervention recommendations.

**Rule Engine**:
```python
def generate_actions(
    risk_level: str,
    risk_score: int,
    shap_drivers: List[dict],
    student_data: dict,
    placement_probs: dict
) -> List[Action]:
    actions = []
    
    # Rule 1: Skill gap
    if "job_demand_score" in bottom_3_shap_features:
        actions.append({
            "type": "skill_up",
            "title": "Skill-Up Recommendation",
            "description": f"Enroll in {course_type}-specific certification...",
            "priority": "high" if risk_level == "high" else "medium"
        })
    
    # Rule 2: Internship gap
    if internship_count == 0 or internship_score < 0.3:
        actions.append({
            "type": "internship",
            "title": "Internship / Project Experience",
            "description": "Complete at least 1 industry internship...",
            "priority": "high"
        })
    
    # Rule 3: Resume improvement
    if risk_score > 60:
        actions.append({
            "type": "resume",
            "title": "Resume Improvement",
            "description": "Resume review recommended...",
            "priority": "medium"
        })
    
    # Rule 4: Mock interviews
    if placement_probs["prob_3m"] < 0.5:
        actions.append({
            "type": "mock_interview",
            "title": "Mock Interview Coaching",
            "description": "3-month placement probability below 50%...",
            "priority": "high"
        })
    
    # Rule 5: Recruiter matching
    if risk_level in ["low", "medium"] and institute_tier <= 2:
        actions.append({
            "type": "recruiter_match",
            "title": "Recruiter Matches Available",
            "description": f"3 active recruiters hiring {course_type}...",
            "priority": "low"
        })
    
    return actions
```

#### LLM Service (`backend/services/llm_service.py`)

**Purpose**: Generate natural language risk summaries using Claude API.

**Interface**:
```python
class LLMService:
    def __init__(self, api_key: str):
        self.client = anthropic.Anthropic(api_key=api_key)
        
    async def generate_summary(
        self,
        student_data: dict,
        prediction: dict,
        shap_drivers: List[dict]
    ) -> str:
        """
        Generate 2-sentence risk summary.
        
        Returns:
            Natural language summary or fallback message if API fails
        """
```

**Prompt Template**:
```
You are a credit risk analyst at an Indian NBFC. Given this student's placement risk assessment, write a 2-sentence plain-English summary for a loan officer.

Student: {course_type} from Tier-{institute_tier} institute, CGPA {cgpa}, {internship_count} internships
Risk score: {risk_score}/100 ({risk_level} risk)
Top risk drivers: {shap_drivers}
Placement probability: 3m={prob_3m:.0%}, 6m={prob_6m:.0%}, 12m={prob_12m:.0%}

Write a concise, professional 2-sentence assessment. Start with the risk level and key reason.
```

**API Configuration**:
- Model: `claude-sonnet-4-20250514`
- Max tokens: 200
- Temperature: 0.3 (deterministic)
- Timeout: 5 seconds

**Fallback**: If API fails, return `"AI summary unavailable - refer to SHAP values for risk drivers."`

#### Database Session Management (`backend/db/session.py`)

**Purpose**: Provide async database sessions with connection pooling.

**Configuration**:
```python
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    pool_size=20,          # Max connections in pool
    max_overflow=10,       # Additional connections beyond pool_size
    pool_pre_ping=True,    # Verify connections before use
    pool_recycle=3600      # Recycle connections after 1 hour
)

async_session_maker = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)

async def get_db() -> AsyncSession:
    """FastAPI dependency for database sessions."""
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
```

**Connection Pool Sizing**: Based on research, `pool_size=20` with `max_overflow=10` supports ~30 concurrent requests, suitable for hackathon scale. Production would scale based on load testing.

### Frontend Components

#### Dashboard Page (`frontend/app/dashboard/page.tsx`)

**Purpose**: Portfolio overview with risk distribution and student table.

**Components Used**:
- `PortfolioHeatmap`: Grid visualization of all students color-coded by risk level
- `RiskScoreCard`: Aggregate statistics (total, high/medium/low counts)
- `StudentTable`: Sortable, paginated table with columns: name, course, tier, risk score, alert status
- `AlertBanner`: Red notification strip if any high-risk alerts exist

**Data Fetching**:
```typescript
async function getDashboardData() {
  const [students, alerts] = await Promise.all([
    fetch('/api/students?limit=100'),
    fetch('/api/alerts?threshold=high')
  ]);
  return { students, alerts };
}
```

**Auto-refresh**: Poll `/api/students` every 30 seconds using `useEffect` with interval.

#### Student Detail Page (`frontend/app/student/[id]/page.tsx`)

**Purpose**: Comprehensive risk profile for individual student.

**Components Used**:
- `RiskScoreCard`: Large risk score with color-coded badge
- `PlacementProbChart`: Bar chart (3m/6m/12m probabilities)
- `SalaryRangeCard`: Salary min-max with confidence interval
- `ShapWaterfallChart`: Horizontal waterfall showing SHAP contributions
- `AISummaryCard`: LLM-generated explanation
- `NextBestActionsPanel`: List of recommended interventions
- `AuditTrailTimeline`: Historical predictions for student

**SHAP Waterfall Implementation**:
```typescript
// Uses Recharts BarChart with custom cell coloring
<BarChart data={waterfallData} layout="vertical">
  <XAxis type="number" />
  <YAxis type="category" dataKey="feature" />
  <Bar dataKey="value">
    {waterfallData.map((entry, index) => (
      <Cell
        key={index}
        fill={entry.value > 0 ? '#1D9E75' : '#E24B4A'}
      />
    ))}
  </Bar>
</BarChart>
```

#### New Prediction Form (`frontend/app/student/new/page.tsx`)

**Purpose**: Multi-step form for inputting new student data.

**Form Steps**:
1. **Academic Info**: name, course_type, institute_tier, institute_name, cgpa, cgpa_scale, year_of_grad
2. **Internship & Skills**: internship_count, internship_months, internship_employer_type, certifications, region
3. **Loan Details**: loan_amount, loan_emi

**Validation**: Client-side validation with Zod schema matching Pydantic backend schemas.

**Submission Flow**:
```typescript
async function handleSubmit(data: StudentInput) {
  const response = await fetch('/api/predict', {
    method: 'POST',
    body: JSON.stringify(data)
  });
  const result = await response.json();
  router.push(`/student/${result.student_id}`);
}
```

#### Alerts Page (`frontend/app/alerts/page.tsx`)

**Purpose**: High-risk student management interface.

**Components Used**:
- Filter bar (All / High / Medium)
- `AlertCard` per student: name, risk badge, risk score, top driver, recommended action
- Acknowledge button (marks alert as read)

**Data Fetching**:
```typescript
const { data } = useSWR(
  `/api/alerts?threshold=${filter}`,
  fetcher,
  { refreshInterval: 10000 } // Refresh every 10 seconds
);
```


## Data Models

### Database Schema

#### students Table

**Purpose**: Store student academic and loan information.

```sql
CREATE TABLE students (
    id                      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name                    VARCHAR(255) NOT NULL,
    course_type             VARCHAR(100) NOT NULL,
    institute_name          VARCHAR(255),
    institute_tier          INTEGER NOT NULL CHECK (institute_tier BETWEEN 1 AND 3),
    cgpa                    DECIMAL(4,2) CHECK (cgpa >= 0),
    cgpa_scale              DECIMAL(4,2) DEFAULT 10.0,
    year_of_grad            INTEGER NOT NULL CHECK (year_of_grad BETWEEN 2020 AND 2030),
    internship_count        INTEGER DEFAULT 0 CHECK (internship_count >= 0),
    internship_months       INTEGER DEFAULT 0 CHECK (internship_months >= 0),
    internship_employer_type VARCHAR(100),
    certifications          INTEGER DEFAULT 0 CHECK (certifications >= 0),
    region                  VARCHAR(100),
    loan_amount             DECIMAL(12,2) CHECK (loan_amount >= 0),
    loan_emi                DECIMAL(10,2) CHECK (loan_emi >= 0),
    created_at              TIMESTAMPTZ DEFAULT NOW(),
    updated_at              TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_students_tier ON students(institute_tier);
CREATE INDEX idx_students_course ON students(course_type);
CREATE INDEX idx_students_created ON students(created_at DESC);
```

**Constraints**:
- `institute_tier` must be 1, 2, or 3
- `cgpa` must be non-negative
- `year_of_grad` must be between 2020 and 2030
- All count/amount fields must be non-negative

#### predictions Table

**Purpose**: Store prediction results with SHAP explanations and AI summaries.

```sql
CREATE TABLE predictions (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    student_id          UUID NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    model_version       VARCHAR(50) NOT NULL,
    prob_placed_3m      DECIMAL(5,4) NOT NULL CHECK (prob_placed_3m BETWEEN 0 AND 1),
    prob_placed_6m      DECIMAL(5,4) NOT NULL CHECK (prob_placed_6m BETWEEN 0 AND 1),
    prob_placed_12m     DECIMAL(5,4) NOT NULL CHECK (prob_placed_12m BETWEEN 0 AND 1),
    placement_label     VARCHAR(50) NOT NULL,
    risk_score          INTEGER NOT NULL CHECK (risk_score BETWEEN 0 AND 100),
    risk_level          VARCHAR(20) NOT NULL CHECK (risk_level IN ('low', 'medium', 'high')),
    salary_min          DECIMAL(10,2),
    salary_max          DECIMAL(10,2),
    salary_confidence   DECIMAL(4,2),
    emi_affordability   DECIMAL(5,2),
    shap_values         JSONB NOT NULL,
    top_risk_drivers    JSONB NOT NULL,
    ai_summary          TEXT,
    next_best_actions   JSONB NOT NULL,
    alert_triggered     BOOLEAN DEFAULT FALSE,
    created_at          TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_predictions_student ON predictions(student_id);
CREATE INDEX idx_predictions_risk_level ON predictions(risk_level);
CREATE INDEX idx_predictions_alert ON predictions(alert_triggered) WHERE alert_triggered = TRUE;
CREATE INDEX idx_predictions_created ON predictions(created_at DESC);
```

**JSONB Field Structures**:

`shap_values`:
```json
{
  "internship_score": 0.34,
  "institute_tier_1": 0.22,
  "cgpa_normalized": 0.11,
  "job_demand_score": -0.09,
  "course_type_encoded": -0.17,
  ...
}
```

`top_risk_drivers`:
```json
[
  {
    "feature": "internship_score",
    "value": 0.34,
    "direction": "positive"
  },
  {
    "feature": "institute_tier_1",
    "value": 0.22,
    "direction": "positive"
  },
  ...
]
```

`next_best_actions`:
```json
[
  {
    "type": "skill_up",
    "title": "Skill-Up Recommendation",
    "description": "Enroll in Engineering-specific certification...",
    "priority": "high"
  },
  {
    "type": "internship",
    "title": "Internship / Project Experience",
    "description": "Complete at least 1 industry internship...",
    "priority": "high"
  }
]
```

**Constraints**:
- All probability fields must be between 0 and 1
- `risk_score` must be between 0 and 100
- `risk_level` must be 'low', 'medium', or 'high'
- `placement_label` must be 'placed_3m', 'placed_6m', 'placed_12m', or 'high_risk'

#### audit_logs Table

**Purpose**: Maintain compliance audit trail for all predictions and actions.

```sql
CREATE TABLE audit_logs (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    student_id      UUID REFERENCES students(id) ON DELETE SET NULL,
    prediction_id   UUID REFERENCES predictions(id) ON DELETE SET NULL,
    action          VARCHAR(100) NOT NULL,
    performed_by    VARCHAR(100),
    metadata        JSONB,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_audit_logs_student ON audit_logs(student_id);
CREATE INDEX idx_audit_logs_action ON audit_logs(action);
CREATE INDEX idx_audit_logs_created ON audit_logs(created_at DESC);
```

**Action Types**:
- `PREDICT`: Prediction generated
- `EXPLAIN`: SHAP explanation retrieved
- `ALERT_SENT`: High-risk alert triggered

**Metadata Structure** (for PREDICT action):
```json
{
  "model_version": "1.0.0",
  "risk_score": 42,
  "risk_level": "medium",
  "processing_time_ms": 1234
}
```

**Audit Policy**: Append-only table, no deletes allowed. Foreign keys use `ON DELETE SET NULL` to preserve audit trail even if student/prediction deleted.

### SQLAlchemy ORM Models

#### Student Model (`backend/models/student.py`)

```python
from sqlalchemy import Column, String, Integer, Numeric, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

class Student(Base):
    __tablename__ = "students"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    course_type = Column(String(100), nullable=False)
    institute_name = Column(String(255))
    institute_tier = Column(Integer, nullable=False)
    cgpa = Column(Numeric(4, 2))
    cgpa_scale = Column(Numeric(4, 2), default=10.0)
    year_of_grad = Column(Integer, nullable=False)
    internship_count = Column(Integer, default=0)
    internship_months = Column(Integer, default=0)
    internship_employer_type = Column(String(100))
    certifications = Column(Integer, default=0)
    region = Column(String(100))
    loan_amount = Column(Numeric(12, 2))
    loan_emi = Column(Numeric(10, 2))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    predictions = relationship("Prediction", back_populates="student", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="student")
```

#### Prediction Model (`backend/models/prediction.py`)

```python
from sqlalchemy import Column, String, Integer, Numeric, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

class Prediction(Base):
    __tablename__ = "predictions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id = Column(UUID(as_uuid=True), ForeignKey("students.id", ondelete="CASCADE"), nullable=False)
    model_version = Column(String(50), nullable=False)
    prob_placed_3m = Column(Numeric(5, 4), nullable=False)
    prob_placed_6m = Column(Numeric(5, 4), nullable=False)
    prob_placed_12m = Column(Numeric(5, 4), nullable=False)
    placement_label = Column(String(50), nullable=False)
    risk_score = Column(Integer, nullable=False)
    risk_level = Column(String(20), nullable=False)
    salary_min = Column(Numeric(10, 2))
    salary_max = Column(Numeric(10, 2))
    salary_confidence = Column(Numeric(4, 2))
    emi_affordability = Column(Numeric(5, 2))
    shap_values = Column(JSONB, nullable=False)
    top_risk_drivers = Column(JSONB, nullable=False)
    ai_summary = Column(Text)
    next_best_actions = Column(JSONB, nullable=False)
    alert_triggered = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    student = relationship("Student", back_populates="predictions")
    audit_logs = relationship("AuditLog", back_populates="prediction")
```

#### AuditLog Model (`backend/models/audit_log.py`)

```python
from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

class AuditLog(Base):
    __tablename__ = "audit_logs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id = Column(UUID(as_uuid=True), ForeignKey("students.id", ondelete="SET NULL"))
    prediction_id = Column(UUID(as_uuid=True), ForeignKey("predictions.id", ondelete="SET NULL"))
    action = Column(String(100), nullable=False)
    performed_by = Column(String(100))
    metadata = Column(JSONB)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    student = relationship("Student", back_populates="audit_logs")
    prediction = relationship("Prediction", back_populates="audit_logs")
```

### Pydantic Schemas

#### Request Schemas (`backend/schemas/student.py`)

```python
from pydantic import BaseModel, Field, validator
from typing import Optional
from decimal import Decimal

class StudentInput(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    course_type: str = Field(..., min_length=1, max_length=100)
    institute_name: Optional[str] = Field(None, max_length=255)
    institute_tier: int = Field(..., ge=1, le=3)
    cgpa: Decimal = Field(..., ge=0, decimal_places=2)
    cgpa_scale: Decimal = Field(default=10.0, ge=0, decimal_places=2)
    year_of_grad: int = Field(..., ge=2020, le=2030)
    internship_count: int = Field(default=0, ge=0)
    internship_months: int = Field(default=0, ge=0)
    internship_employer_type: Optional[str] = Field(None, max_length=100)
    certifications: int = Field(default=0, ge=0)
    region: Optional[str] = Field(None, max_length=100)
    loan_amount: Optional[Decimal] = Field(None, ge=0, decimal_places=2)
    loan_emi: Optional[Decimal] = Field(None, ge=0, decimal_places=2)
    
    @validator('cgpa')
    def validate_cgpa(cls, v, values):
        if 'cgpa_scale' in values and v > values['cgpa_scale']:
            raise ValueError('cgpa cannot exceed cgpa_scale')
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "Rahul Sharma",
                "course_type": "Engineering",
                "institute_tier": 2,
                "cgpa": 7.8,
                "cgpa_scale": 10.0,
                "year_of_grad": 2025,
                "internship_count": 2,
                "internship_months": 6,
                "internship_employer_type": "Startup",
                "certifications": 3,
                "region": "South",
                "loan_amount": 1500000,
                "loan_emi": 18000
            }
        }

class BatchScoreRequest(BaseModel):
    students: list[StudentInput] = Field(..., max_length=500)
```

#### Response Schemas (`backend/schemas/prediction.py`)

```python
from pydantic import BaseModel, Field
from typing import List, Dict, Any
from decimal import Decimal
from uuid import UUID

class RiskDriver(BaseModel):
    feature: str
    value: float
    direction: str  # "positive" or "negative"

class NextBestAction(BaseModel):
    type: str
    title: str
    description: str
    priority: str  # "low", "medium", "high"

class PredictionResponse(BaseModel):
    student_id: UUID
    prediction_id: UUID
    prob_placed_3m: Decimal = Field(..., decimal_places=4)
    prob_placed_6m: Decimal = Field(..., decimal_places=4)
    prob_placed_12m: Decimal = Field(..., decimal_places=4)
    placement_label: str
    risk_score: int = Field(..., ge=0, le=100)
    risk_level: str
    salary_min: Optional[Decimal] = Field(None, decimal_places=2)
    salary_max: Optional[Decimal] = Field(None, decimal_places=2)
    salary_confidence: Optional[Decimal] = Field(None, decimal_places=2)
    emi_affordability: Optional[Decimal] = Field(None, decimal_places=2)
    top_risk_drivers: List[RiskDriver]
    ai_summary: str
    next_best_actions: List[NextBestAction]
    alert_triggered: bool

class BatchScoreResponse(BaseModel):
    results: List[PredictionResponse]
    summary: Dict[str, int]  # {"high_risk_count": 12, "medium_risk_count": 45, "low_risk_count": 143}

class ShapExplanationResponse(BaseModel):
    student_id: UUID
    shap_values: Dict[str, float]
    base_value: float
    prediction: float
    waterfall_data: List[Dict[str, Any]]  # [{"feature": "...", "value": 0.34, "cumulative": 0.79}, ...]
```

### Configuration Schema

#### Configuration File Format (`config.json`)

```json
{
  "database_url": "postgresql+asyncpg://user:pass@localhost:5432/edurisk",
  "redis_url": "redis://localhost:6379",
  "anthropic_api_key": "sk-ant-...",
  "ml_model_path": "./ml/models",
  "secret_key": "your-secret-key-here",
  "cors_origins": ["http://localhost:3000"]
}
```

#### Configuration Pydantic Model (`backend/config.py`)

```python
from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    database_url: str
    redis_url: str = "redis://localhost:6379"
    anthropic_api_key: str
    ml_model_path: str = "./ml/models"
    secret_key: str
    cors_origins: List[str] = ["http://localhost:3000"]
    
    # Connection pool settings
    db_pool_size: int = 20
    db_max_overflow: int = 10
    
    # Rate limiting
    rate_limit_predict: int = 100  # per minute per IP
    rate_limit_batch: int = 10     # per minute per IP
    rate_limit_get: int = 300      # per minute per IP
    
    # LLM settings
    llm_timeout: int = 5  # seconds
    llm_max_tokens: int = 200
    
    class Config:
        env_file = ".env"
        case_sensitive = False

settings = Settings()
```

### Model Artifact Files

**Directory Structure**:
```
ml/models/
├── placement_model_3m.pkl      # XGBoost classifier for 3-month placement
├── placement_model_6m.pkl      # XGBoost classifier for 6-month placement
├── placement_model_12m.pkl     # XGBoost classifier for 12-month placement
├── salary_model.pkl            # Ridge regression pipeline
├── feature_names.json          # Ordered list of feature names
└── version.json                # {"version": "1.0.0"}
```

**feature_names.json**:
```json
[
  "cgpa_normalized",
  "internship_score",
  "employer_type_score",
  "certifications",
  "institute_tier_1",
  "institute_tier_2",
  "institute_tier_3",
  "course_type_encoded",
  "placement_rate_3m",
  "placement_rate_6m",
  "salary_benchmark",
  "job_demand_score",
  "region_job_density",
  "macro_hiring_index",
  "skill_gap_score",
  "emi_stress_ratio"
]
```

**version.json**:
```json
{
  "version": "1.0.0",
  "trained_at": "2025-01-15T10:30:00Z",
  "training_samples": 8000,
  "auc_3m": 0.87,
  "auc_6m": 0.89,
  "auc_12m": 0.91
}
```


## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Placement Probability Validity

*For any* Student_Profile input, all three placement probability outputs (prob_placed_3m, prob_placed_6m, prob_placed_12m) SHALL be decimal values between 0.0000 and 1.0000 with exactly four decimal places.

**Validates: Requirements 1.1, 1.4**

### Property 2: Placement Label Assignment Correctness

*For any* set of placement probabilities, the assigned placement_label SHALL be "placed_3m" if prob_3m >= 0.50, else "placed_6m" if prob_6m >= 0.50, else "placed_12m" if prob_12m >= 0.50, else "high_risk".

**Validates: Requirements 1.2, 1.6**

### Property 3: Demographic Feature Exclusion

*For any* prediction execution, the feature vector passed to ML models SHALL NOT contain any demographic features (gender, religion, caste, state_of_origin), and the feature_names.json file SHALL NOT list any demographic features.

**Validates: Requirements 1.5, 2.7, 16.1, 16.2, 16.3**

### Property 4: Salary Range Relationship

*For any* salary prediction, the relationship salary_min < predicted_salary < salary_max SHALL hold, and salary_min SHALL equal predicted_salary minus 1.5 times the standard deviation, and salary_max SHALL equal predicted_salary plus 1.5 times the standard deviation.

**Validates: Requirements 2.1, 2.3, 2.4**

### Property 5: Salary Confidence Calculation

*For any* salary prediction with min, max, and predicted values, the salary_confidence SHALL equal ((salary_max - salary_min) / predicted_salary) × 100, expressed with two decimal precision.

**Validates: Requirements 2.2, 2.5**

### Property 6: Risk Score Calculation Formula

*For any* set of placement probabilities, the risk_score SHALL equal 100 minus (prob_3m × 50 + prob_6m × 30 + prob_12m × 20), rounded to an integer between 0 and 100.

**Validates: Requirements 3.1, 3.2, 3.3**

### Property 7: Risk Level Assignment

*For any* risk_score value, the risk_level SHALL be "low" when risk_score is in [0, 33], "medium" when risk_score is in [34, 66], and "high" when risk_score is in [67, 100].

**Validates: Requirements 3.4, 3.5, 3.6**

### Property 8: EMI Affordability Calculation

*For any* student with loan_emi and predicted_salary_lpa, the emi_affordability SHALL equal loan_emi divided by ((predicted_salary_lpa × 100000) / 12), expressed with two decimal precision.

**Validates: Requirements 4.1, 4.2, 4.3, 4.4**

### Property 9: High Risk Alert Triggering

*For any* prediction, alert_triggered SHALL be true if and only if risk_level equals "high" OR emi_affordability exceeds 0.50.

**Validates: Requirements 4.5**

### Property 10: SHAP Values Completeness

*For any* prediction, the shap_values dictionary SHALL contain exactly one entry for each feature name in the feature_names.json file, with no additional or missing features.

**Validates: Requirements 5.1**

### Property 11: Top Risk Drivers Selection

*For any* SHAP values dictionary, the top_risk_drivers array SHALL contain exactly 5 elements, each SHALL be the features with the 5 highest absolute SHAP values in descending order, and each SHALL include feature name, SHAP value, and direction ("positive" if value > 0, else "negative").

**Validates: Requirements 5.3, 5.5**

### Property 12: SHAP Values Storage Round-Trip

*For any* SHAP values dictionary stored as JSONB in the predictions table, retrieving and parsing the stored value SHALL produce a dictionary equivalent to the original SHAP values.

**Validates: Requirements 5.4**

### Property 13: LLM Prompt Completeness

*For any* student data and prediction, the generated Claude API prompt SHALL contain the student's course_type, institute_tier, cgpa, internship_count, risk_score, risk_level, and all top risk drivers.

**Validates: Requirements 6.3**

### Property 14: Action Recommendation - Skill Gap

*For any* prediction where job_demand_score is among the bottom 3 SHAP contributors, the next_best_actions array SHALL contain an action with type "skill_up".

**Validates: Requirements 7.2**

### Property 15: Action Recommendation - Internship Gap

*For any* student where internship_count equals 0 OR internship_score is below 0.3, the next_best_actions array SHALL contain an action with type "internship" and priority "high".

**Validates: Requirements 7.3**

### Property 16: Action Recommendation - High Risk Resume

*For any* prediction where risk_score exceeds 60, the next_best_actions array SHALL contain an action with type "resume".

**Validates: Requirements 7.4**

### Property 17: Action Recommendation - Mock Interview

*For any* prediction where prob_placed_3m is below 0.5, the next_best_actions array SHALL contain an action with type "mock_interview" and priority "high".

**Validates: Requirements 7.5**

### Property 18: Action Recommendation - Recruiter Match

*For any* prediction where risk_level is "low" or "medium" AND institute_tier is 1 or 2, the next_best_actions array SHALL contain an action with type "recruiter_match" and priority "low".

**Validates: Requirements 7.6**

### Property 19: Action Structure Validity

*For any* action in the next_best_actions array, the action SHALL contain exactly four fields: type (string), title (string), description (string), and priority (string with value "low", "medium", or "high").

**Validates: Requirements 7.7**

### Property 20: Prediction Response Completeness

*For any* successful prediction API response, the response SHALL contain all required fields: student_id, prediction_id, prob_placed_3m, prob_placed_6m, prob_placed_12m, placement_label, risk_score, risk_level, salary_min, salary_max, salary_confidence, emi_affordability, top_risk_drivers, ai_summary, next_best_actions, and alert_triggered.

**Validates: Requirements 8.5**

### Property 21: Configuration Round-Trip Preservation

*For any* valid Configuration object, the sequence of operations parse(print(parse(json_string))) SHALL produce a Configuration object equivalent to parse(json_string), where parse converts JSON to Configuration and print converts Configuration to JSON.

**Validates: Requirements 19.6**

### Property 22: Configuration JSON Formatting

*For any* Configuration object, the printed JSON output SHALL use 2-space indentation and SHALL have keys sorted alphabetically.

**Validates: Requirements 19.7**

### Property 23: Required Field Validation

*For any* POST /api/predict request missing one or more required fields (name, course_type, institute_tier, cgpa, year_of_grad), the API SHALL return HTTP status 422 with a JSON response containing field-specific error messages.

**Validates: Requirements 20.1**

### Property 24: Institute Tier Validation

*For any* POST /api/predict request where institute_tier is not an integer in the range [1, 3], the API SHALL return HTTP status 422 with a validation error.

**Validates: Requirements 20.2**

### Property 25: CGPA Validation

*For any* POST /api/predict request where cgpa is negative OR cgpa exceeds cgpa_scale, the API SHALL return HTTP status 422 with a validation error.

**Validates: Requirements 20.3**

### Property 26: Year of Graduation Validation

*For any* POST /api/predict request where year_of_grad is not an integer in the range [2020, 2030], the API SHALL return HTTP status 422 with a validation error.

**Validates: Requirements 20.4**

### Property 27: Non-Negative Value Validation

*For any* POST /api/predict request where internship_count, loan_amount, or loan_emi is negative, the API SHALL return HTTP status 422 with a validation error.

**Validates: Requirements 20.5, 20.6**

### Property 28: Validation Error Response Format

*For any* validation failure on POST /api/predict, the API SHALL return HTTP status 422 AND the response body SHALL be valid JSON containing an array or object with field-specific error messages.

**Validates: Requirements 20.7**


## Error Handling

### Error Handling Strategy

The system implements a layered error handling approach with graceful degradation for non-critical failures and fail-fast behavior for critical errors.

#### Error Categories

**Critical Errors** (Fail-Fast):
- Database connection failures
- ML model file not found or corrupted
- Invalid feature vector dimensions
- Database constraint violations

**Recoverable Errors** (Graceful Degradation):
- Claude API timeout or failure → Use fallback summary
- Redis connection failure → Disable rate limiting, log warning
- Individual prediction failure in batch → Continue with remaining predictions, report failures

**Validation Errors** (User-Facing):
- Invalid input data → HTTP 422 with field-specific errors
- Missing required fields → HTTP 422 with clear error messages
- Out-of-range values → HTTP 422 with acceptable range information

#### Error Response Format

All API errors follow a consistent JSON structure:

```json
{
  "error": {
    "type": "ValidationError",
    "message": "Request validation failed",
    "details": [
      {
        "field": "institute_tier",
        "message": "Value must be between 1 and 3",
        "received": 5
      }
    ],
    "timestamp": "2025-01-15T10:30:00Z",
    "request_id": "uuid-here"
  }
}
```

#### Component-Specific Error Handling

**ML Pipeline**:
```python
class PredictionError(Exception):
    """Base exception for prediction failures."""
    pass

class ModelLoadError(PredictionError):
    """Raised when model files cannot be loaded."""
    pass

class FeatureEngineeringError(PredictionError):
    """Raised when feature transformation fails."""
    pass

# Usage
try:
    features = feature_engineer.transform(student_data)
except ValueError as e:
    raise FeatureEngineeringError(f"Invalid student data: {e}") from e
```

**Database Operations**:
```python
from sqlalchemy.exc import IntegrityError, OperationalError

async def create_prediction(db: AsyncSession, prediction_data: dict):
    try:
        prediction = Prediction(**prediction_data)
        db.add(prediction)
        await db.commit()
        return prediction
    except IntegrityError as e:
        await db.rollback()
        logger.error(f"Database integrity error: {e}")
        raise HTTPException(status_code=409, detail="Duplicate prediction")
    except OperationalError as e:
        await db.rollback()
        logger.error(f"Database operational error: {e}")
        raise HTTPException(status_code=503, detail="Database unavailable")
```

**LLM Service**:
```python
async def generate_summary(self, student_data, prediction, shap_drivers):
    try:
        response = await asyncio.wait_for(
            self.client.messages.create(...),
            timeout=self.timeout
        )
        return response.content[0].text
    except asyncio.TimeoutError:
        logger.warning("Claude API timeout, using fallback")
        return "AI summary unavailable - refer to SHAP values for risk drivers."
    except anthropic.APIError as e:
        logger.error(f"Claude API error: {e}")
        return "AI summary unavailable - refer to SHAP values for risk drivers."
```

**API Endpoints**:
```python
from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "type": "InternalServerError",
                "message": "An unexpected error occurred",
                "request_id": str(uuid.uuid4()),
                "timestamp": datetime.utcnow().isoformat()
            }
        }
    )

@app.exception_handler(ValidationError)
async def validation_exception_handler(request: Request, exc: ValidationError):
    return JSONResponse(
        status_code=422,
        content={
            "error": {
                "type": "ValidationError",
                "message": "Request validation failed",
                "details": exc.errors(),
                "timestamp": datetime.utcnow().isoformat()
            }
        }
    )
```

#### Logging Strategy

**Log Levels**:
- **ERROR**: Critical failures requiring immediate attention (DB down, model load failure)
- **WARNING**: Recoverable issues (Claude API timeout, Redis unavailable)
- **INFO**: Normal operations (prediction created, API request completed)
- **DEBUG**: Detailed diagnostic information (feature values, SHAP computation)

**Structured Logging Format**:
```json
{
  "timestamp": "2025-01-15T10:30:00.123Z",
  "level": "ERROR",
  "logger": "prediction_service",
  "message": "Prediction failed for student",
  "context": {
    "student_id": "uuid-here",
    "error_type": "FeatureEngineeringError",
    "error_message": "Invalid CGPA value",
    "request_id": "uuid-here"
  },
  "stack_trace": "..."
}
```

**Log Aggregation**: All logs written to stdout in JSON format for collection by Docker logging drivers or external log aggregators (CloudWatch, ELK, etc.).

#### Retry Logic

**Database Operations**:
- Retry transient errors (connection timeout) up to 3 times with exponential backoff
- Do not retry integrity constraint violations

**Claude API**:
- Single attempt with 5-second timeout
- No retries (use fallback immediately to maintain <5s response time SLA)

**Redis Rate Limiting**:
- Single attempt
- If Redis unavailable, log warning and allow request (fail-open for availability)

#### Circuit Breaker Pattern

For external dependencies (Claude API), implement circuit breaker to prevent cascading failures:

```python
class CircuitBreaker:
    def __init__(self, failure_threshold=5, timeout=60):
        self.failure_count = 0
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.last_failure_time = None
        self.state = "closed"  # closed, open, half-open
    
    async def call(self, func, *args, **kwargs):
        if self.state == "open":
            if time.time() - self.last_failure_time > self.timeout:
                self.state = "half-open"
            else:
                raise CircuitBreakerOpenError("Circuit breaker is open")
        
        try:
            result = await func(*args, **kwargs)
            if self.state == "half-open":
                self.state = "closed"
                self.failure_count = 0
            return result
        except Exception as e:
            self.failure_count += 1
            self.last_failure_time = time.time()
            if self.failure_count >= self.failure_threshold:
                self.state = "open"
            raise
```


## Testing Strategy

### Overview

The testing strategy employs a dual approach combining property-based testing for universal correctness guarantees with example-based unit tests for specific scenarios and integration tests for end-to-end workflows.

### Property-Based Testing

**Framework**: [fast-check](https://fast-check.dev/) for TypeScript/JavaScript, [Hypothesis](https://hypothesis.readthedocs.io/) for Python

**Configuration**:
- Minimum 100 iterations per property test (due to randomization)
- Each property test tagged with comment referencing design document property
- Tag format: `# Feature: edurisk-ai-placement-intelligence, Property {number}: {property_text}`

**Property Test Categories**:

#### 1. ML Pipeline Properties

**Feature Engineering Properties**:
```python
# Feature: edurisk-ai-placement-intelligence, Property 3: Demographic Feature Exclusion
@given(student_profile=student_profiles())
def test_demographic_features_excluded(student_profile):
    """For any student profile, feature vector must not contain demographic features."""
    feature_engineer = FeatureEngineer(config)
    features = feature_engineer.transform(student_profile)
    feature_names = feature_engineer.get_feature_names()
    
    # Verify no demographic features in names
    demographic_features = {'gender', 'religion', 'caste', 'state_of_origin'}
    assert demographic_features.isdisjoint(set(feature_names))
    
    # Verify feature vector length matches non-demographic features
    assert len(features[0]) == len(feature_names)
```

**Placement Prediction Properties**:
```python
# Feature: edurisk-ai-placement-intelligence, Property 1: Placement Probability Validity
@given(student_profile=student_profiles())
def test_placement_probabilities_valid_range(student_profile):
    """For any student profile, all probabilities must be in [0, 1] with 4 decimal places."""
    predictor = PlacementPredictor(model_dir)
    features = feature_engineer.transform(student_profile)
    prediction = predictor.predict(features)
    
    assert 0.0 <= prediction.prob_3m <= 1.0
    assert 0.0 <= prediction.prob_6m <= 1.0
    assert 0.0 <= prediction.prob_12m <= 1.0
    
    # Check 4 decimal precision
    assert len(str(prediction.prob_3m).split('.')[-1]) <= 4
    assert len(str(prediction.prob_6m).split('.')[-1]) <= 4
    assert len(str(prediction.prob_12m).split('.')[-1]) <= 4

# Feature: edurisk-ai-placement-intelligence, Property 2: Placement Label Assignment Correctness
@given(prob_3m=floats(0, 1), prob_6m=floats(0, 1), prob_12m=floats(0, 1))
def test_placement_label_assignment(prob_3m, prob_6m, prob_12m):
    """For any probabilities, label assignment follows specified rules."""
    label = assign_placement_label(prob_3m, prob_6m, prob_12m)
    
    if prob_3m >= 0.5:
        assert label == "placed_3m"
    elif prob_6m >= 0.5:
        assert label == "placed_6m"
    elif prob_12m >= 0.5:
        assert label == "placed_12m"
    else:
        assert label == "high_risk"
```

**Salary Prediction Properties**:
```python
# Feature: edurisk-ai-placement-intelligence, Property 4: Salary Range Relationship
@given(student_profile=student_profiles())
def test_salary_range_relationship(student_profile):
    """For any prediction, salary_min < predicted < salary_max."""
    estimator = SalaryEstimator(model_path)
    features = feature_engineer.transform(student_profile)
    prediction = estimator.predict(features)
    
    assert prediction.salary_min < prediction.predicted < prediction.salary_max
    
    # Verify formula: min = predicted - 1.5*std, max = predicted + 1.5*std
    std = (prediction.salary_max - prediction.salary_min) / 3.0
    assert abs(prediction.salary_min - (prediction.predicted - 1.5 * std)) < 0.01
    assert abs(prediction.salary_max - (prediction.predicted + 1.5 * std)) < 0.01

# Feature: edurisk-ai-placement-intelligence, Property 5: Salary Confidence Calculation
@given(salary_min=floats(3.0, 10.0), salary_max=floats(10.0, 30.0))
def test_salary_confidence_calculation(salary_min, salary_max):
    """For any salary range, confidence calculation is correct."""
    assume(salary_min < salary_max)
    predicted = (salary_min + salary_max) / 2.0
    
    confidence = calculate_salary_confidence(salary_min, salary_max, predicted)
    expected = ((salary_max - salary_min) / predicted) * 100
    
    assert abs(confidence - expected) < 0.01
    assert round(confidence, 2) == confidence  # 2 decimal precision
```

**Risk Calculation Properties**:
```python
# Feature: edurisk-ai-placement-intelligence, Property 6: Risk Score Calculation Formula
@given(prob_3m=floats(0, 1), prob_6m=floats(0, 1), prob_12m=floats(0, 1))
def test_risk_score_formula(prob_3m, prob_6m, prob_12m):
    """For any probabilities, risk score follows formula."""
    risk_score = calculate_risk_score(prob_3m, prob_6m, prob_12m)
    expected = 100 - (prob_3m * 50 + prob_6m * 30 + prob_12m * 20)
    
    assert abs(risk_score - round(expected)) <= 1  # Allow rounding difference
    assert 0 <= risk_score <= 100
    assert isinstance(risk_score, int)

# Feature: edurisk-ai-placement-intelligence, Property 7: Risk Level Assignment
@given(risk_score=integers(0, 100))
def test_risk_level_assignment(risk_score):
    """For any risk score, level assignment is correct."""
    risk_level = assign_risk_level(risk_score)
    
    if 0 <= risk_score <= 33:
        assert risk_level == "low"
    elif 34 <= risk_score <= 66:
        assert risk_level == "medium"
    elif 67 <= risk_score <= 100:
        assert risk_level == "high"

# Feature: edurisk-ai-placement-intelligence, Property 8: EMI Affordability Calculation
@given(loan_emi=floats(5000, 50000), salary_lpa=floats(3.0, 30.0))
def test_emi_affordability_calculation(loan_emi, salary_lpa):
    """For any loan EMI and salary, affordability calculation is correct."""
    emi_affordability = calculate_emi_affordability(loan_emi, salary_lpa)
    
    monthly_salary = (salary_lpa * 100000) / 12
    expected = loan_emi / monthly_salary
    
    assert abs(emi_affordability - expected) < 0.001
    assert round(emi_affordability, 2) == emi_affordability  # 2 decimal precision

# Feature: edurisk-ai-placement-intelligence, Property 9: High Risk Alert Triggering
@given(risk_level=sampled_from(["low", "medium", "high"]), 
       emi_affordability=floats(0, 1))
def test_alert_triggering(risk_level, emi_affordability):
    """For any risk level and EMI affordability, alert logic is correct."""
    alert_triggered = should_trigger_alert(risk_level, emi_affordability)
    
    expected = (risk_level == "high") or (emi_affordability > 0.5)
    assert alert_triggered == expected
```

**SHAP Explanation Properties**:
```python
# Feature: edurisk-ai-placement-intelligence, Property 10: SHAP Values Completeness
@given(student_profile=student_profiles())
def test_shap_values_completeness(student_profile):
    """For any prediction, SHAP values cover all features."""
    explainer = ShapExplainer(model)
    features = feature_engineer.transform(student_profile)
    feature_names = feature_engineer.get_feature_names()
    
    explanation = explainer.explain(features, feature_names)
    
    assert set(explanation.shap_values.keys()) == set(feature_names)
    assert len(explanation.shap_values) == len(feature_names)

# Feature: edurisk-ai-placement-intelligence, Property 11: Top Risk Drivers Selection
@given(shap_values=dictionaries(text(), floats(-1, 1), min_size=10, max_size=20))
def test_top_risk_drivers_selection(shap_values):
    """For any SHAP values, top 5 drivers are correctly selected."""
    top_drivers = select_top_drivers(shap_values, n=5)
    
    assert len(top_drivers) == min(5, len(shap_values))
    
    # Verify sorted by absolute value descending
    abs_values = [abs(d['value']) for d in top_drivers]
    assert abs_values == sorted(abs_values, reverse=True)
    
    # Verify direction is correct
    for driver in top_drivers:
        expected_direction = "positive" if driver['value'] > 0 else "negative"
        assert driver['direction'] == expected_direction
```

**Action Recommendation Properties**:
```python
# Feature: edurisk-ai-placement-intelligence, Property 14-18: Action Recommendations
@given(risk_score=integers(0, 100),
       prob_3m=floats(0, 1),
       internship_count=integers(0, 6),
       internship_score=floats(0, 1),
       institute_tier=integers(1, 3),
       risk_level=sampled_from(["low", "medium", "high"]),
       shap_drivers=lists(text(), min_size=5, max_size=5))
def test_action_recommendations(risk_score, prob_3m, internship_count, 
                                internship_score, institute_tier, 
                                risk_level, shap_drivers):
    """For any prediction data, action recommendations follow rules."""
    actions = generate_actions(
        risk_score=risk_score,
        prob_3m=prob_3m,
        internship_count=internship_count,
        internship_score=internship_score,
        institute_tier=institute_tier,
        risk_level=risk_level,
        shap_drivers=shap_drivers
    )
    
    # Property 15: Internship gap
    if internship_count == 0 or internship_score < 0.3:
        assert any(a['type'] == 'internship' and a['priority'] == 'high' 
                  for a in actions)
    
    # Property 16: High risk resume
    if risk_score > 60:
        assert any(a['type'] == 'resume' for a in actions)
    
    # Property 17: Mock interview
    if prob_3m < 0.5:
        assert any(a['type'] == 'mock_interview' and a['priority'] == 'high' 
                  for a in actions)
    
    # Property 18: Recruiter match
    if risk_level in ["low", "medium"] and institute_tier <= 2:
        assert any(a['type'] == 'recruiter_match' and a['priority'] == 'low' 
                  for a in actions)
    
    # Property 19: Action structure
    for action in actions:
        assert set(action.keys()) == {'type', 'title', 'description', 'priority'}
        assert action['priority'] in ['low', 'medium', 'high']
```

#### 2. Configuration Properties

```python
# Feature: edurisk-ai-placement-intelligence, Property 21: Configuration Round-Trip
@given(config_dict=dictionaries(
    keys=sampled_from(['database_url', 'redis_url', 'anthropic_api_key', 
                       'ml_model_path', 'secret_key', 'cors_origins']),
    values=text() | lists(text())
))
def test_config_round_trip(config_dict):
    """For any valid config, parse(print(parse(json))) == parse(json)."""
    # Ensure required fields present
    config_dict['database_url'] = config_dict.get('database_url', 'postgresql://...')
    config_dict['ml_model_path'] = config_dict.get('ml_model_path', './models')
    
    json_str = json.dumps(config_dict)
    config1 = parse_config(json_str)
    printed = print_config(config1)
    config2 = parse_config(printed)
    
    assert config1 == config2

# Feature: edurisk-ai-placement-intelligence, Property 22: Configuration JSON Formatting
@given(config=configurations())
def test_config_json_formatting(config):
    """For any config, printed JSON has 2-space indents and sorted keys."""
    printed = print_config(config)
    parsed = json.loads(printed)
    
    # Check indentation (2 spaces)
    lines = printed.split('\n')
    for line in lines[1:-1]:  # Skip first and last braces
        if line.strip():
            indent = len(line) - len(line.lstrip())
            assert indent % 2 == 0
    
    # Check sorted keys
    keys = list(parsed.keys())
    assert keys == sorted(keys)
```

#### 3. API Validation Properties

```python
# Feature: edurisk-ai-placement-intelligence, Property 23-28: Input Validation
@given(student_input=student_inputs())
def test_api_validation_properties(student_input):
    """For any input, validation follows all rules."""
    
    # Property 24: Institute tier validation
    if student_input.get('institute_tier') not in [1, 2, 3]:
        with pytest.raises(ValidationError):
            StudentInput(**student_input)
    
    # Property 25: CGPA validation
    cgpa = student_input.get('cgpa', 0)
    cgpa_scale = student_input.get('cgpa_scale', 10.0)
    if cgpa < 0 or cgpa > cgpa_scale:
        with pytest.raises(ValidationError):
            StudentInput(**student_input)
    
    # Property 26: Year validation
    year = student_input.get('year_of_grad', 2025)
    if year < 2020 or year > 2030:
        with pytest.raises(ValidationError):
            StudentInput(**student_input)
    
    # Property 27: Non-negative validation
    if (student_input.get('internship_count', 0) < 0 or
        student_input.get('loan_amount', 0) < 0 or
        student_input.get('loan_emi', 0) < 0):
        with pytest.raises(ValidationError):
            StudentInput(**student_input)
```

### Unit Testing

**Purpose**: Test specific scenarios, edge cases, and error conditions not covered by property tests.

**Framework**: pytest for Python, Jest for TypeScript

**Coverage Target**: 80% code coverage minimum

**Example Unit Tests**:

```python
def test_placement_label_all_below_threshold():
    """Specific case: all probabilities below 0.5 should yield high_risk."""
    label = assign_placement_label(0.3, 0.4, 0.45)
    assert label == "high_risk"

def test_salary_prediction_with_missing_features():
    """Edge case: missing optional features should use defaults."""
    student_data = {
        'name': 'Test Student',
        'course_type': 'Engineering',
        'institute_tier': 2,
        'cgpa': 7.5,
        'year_of_grad': 2025
        # Missing: internship_count, certifications, etc.
    }
    features = feature_engineer.transform(student_data)
    assert features is not None

def test_llm_service_fallback_on_timeout():
    """Error case: Claude API timeout should return fallback message."""
    with patch('anthropic.Anthropic.messages.create', side_effect=TimeoutError):
        summary = llm_service.generate_summary(student_data, prediction, shap_drivers)
        assert summary == "AI summary unavailable - refer to SHAP values for risk drivers."

def test_database_integrity_error_handling():
    """Error case: duplicate prediction should raise 409."""
    # Create prediction
    response1 = client.post('/api/predict', json=student_data)
    assert response1.status_code == 200
    
    # Attempt duplicate (same student_id, same timestamp)
    with patch('uuid.uuid4', return_value=response1.json()['prediction_id']):
        response2 = client.post('/api/predict', json=student_data)
        assert response2.status_code == 409
```

### Integration Testing

**Purpose**: Test end-to-end workflows with real database and mocked external services.

**Framework**: pytest with testcontainers for PostgreSQL, fakeredis for Redis

**Test Scenarios**:

1. **Complete Prediction Flow**:
   - POST student data → verify student record created
   - Verify prediction record created with all fields
   - Verify audit log entry created
   - Verify response contains all required fields

2. **Batch Scoring Flow**:
   - POST 100 students → verify all processed
   - Verify summary statistics correct
   - Verify database contains 100 student and prediction records

3. **SHAP Explanation Retrieval**:
   - Create prediction → GET /api/explain/{student_id}
   - Verify waterfall data structure correct
   - Verify SHAP values match stored values

4. **High-Risk Alerts**:
   - Create mix of low/medium/high risk predictions
   - GET /api/alerts?threshold=high
   - Verify only high-risk students returned
   - Verify sorting by risk_score descending

5. **Rate Limiting**:
   - Send 101 requests in 1 minute → verify 101st returns 429
   - Verify X-RateLimit headers present
   - Wait 1 minute → verify requests allowed again

6. **Error Handling**:
   - Mock database failure → verify 503 response
   - Mock model load failure → verify 500 response
   - Send invalid JSON → verify 400 response

### Performance Testing

**Purpose**: Verify system meets performance requirements.

**Tools**: Locust for load testing, pytest-benchmark for micro-benchmarks

**Performance Requirements**:
- Single prediction: <5 seconds for 95th percentile
- Batch prediction (500 students): <60 seconds
- SHAP explanation retrieval: <1 second
- Alert retrieval: <2 seconds
- Health check: <3 seconds

**Load Test Scenarios**:
```python
from locust import HttpUser, task, between

class PredictionUser(HttpUser):
    wait_time = between(1, 3)
    
    @task(3)
    def predict_single(self):
        self.client.post("/api/predict", json=sample_student_data())
    
    @task(1)
    def get_alerts(self):
        self.client.get("/api/alerts?threshold=high")
    
    @task(2)
    def get_explanation(self):
        student_id = random.choice(self.student_ids)
        self.client.get(f"/api/explain/{student_id}")
```

**Performance Test Execution**:
- Ramp up to 50 concurrent users over 2 minutes
- Sustain 50 users for 5 minutes
- Measure response times, error rates, throughput
- Verify 95th percentile response times meet requirements

### Bias Audit Testing

**Purpose**: Verify model fairness across demographic groups.

**Framework**: Fairlearn with custom test harness

**Test Execution**:
```python
def test_demographic_parity():
    """Verify demographic parity difference < 0.1."""
    model = load_model('placement_model_3m.pkl')
    X_test, y_test, sensitive_features = load_test_data()
    
    y_pred = model.predict(X_test)
    
    metric_frame = MetricFrame(
        metrics={'accuracy': accuracy_score, 'selection_rate': selection_rate},
        y_true=y_test,
        y_pred=y_pred,
        sensitive_features=sensitive_features['gender']
    )
    
    dpd = demographic_parity_difference(y_test, y_pred, 
                                       sensitive_features=sensitive_features['gender'])
    
    assert dpd < 0.1, f"Demographic parity difference {dpd} exceeds threshold"
    
    # Log metrics by group
    logger.info(f"Metrics by gender:\n{metric_frame.by_group}")
```

**Bias Test Frequency**: Run on every model retrain before deployment.

### Test Execution Strategy

**CI/CD Pipeline**:
1. **Pre-commit**: Run linters (black, flake8, mypy, eslint)
2. **On PR**: Run unit tests + property tests (100 iterations)
3. **On merge to main**: Run full test suite (unit + property + integration)
4. **Nightly**: Run extended property tests (1000 iterations) + performance tests + bias audit
5. **Pre-deployment**: Run smoke tests against staging environment

**Test Data Management**:
- Use synthetic data generators for property tests (Hypothesis strategies)
- Use fixed seed for reproducibility in CI
- Maintain separate test database with known fixtures for integration tests
- Never use production data in tests

**Test Isolation**:
- Each test gets fresh database transaction (rollback after test)
- Mock external services (Claude API, Redis) by default
- Use testcontainers for integration tests requiring real services

