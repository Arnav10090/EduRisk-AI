# EduRisk AI — Kiro Technical Specification
### TenzorX 2026 | Poonawalla Fincorp National AI Hackathon | Round 2
**Problem Statement:** PS1 — Linking Study-Abroad Education Loan to Career Success Using AI  
**Solution Name:** EduRisk AI  
**Version:** 1.0  

---

## 1. PROJECT OVERVIEW

EduRisk AI is a Placement Risk Intelligence engine for education loan lenders. It predicts a student's probability of getting placed within 3, 6, and 12 months post-graduation, estimates their expected starting salary range, flags early repayment risk, and suggests actionable student interventions. The system supports lending decisions and portfolio monitoring — it does NOT automate credit approvals.

### 1.1 Core Outputs (from Problem Statement)
1. **Placement timeline prediction** — Placed within 3 / 6 / 12 months, or High Risk of delay
2. **Predicted salary range** — Min–Max CTC with confidence intervals
3. **Placement-risk score** — Low / Medium / High (0–100 composite score)
4. **AI-generated explanation** — Natural language summary of risk drivers
5. **Suggested next-best actions** — Skill-up, resume coaching, mock interviews, recruiter matches

### 1.2 Users
- **Loan Officers** — Review individual student risk before disbursement
- **Portfolio Managers** — Monitor batch of students, view risk distribution heatmap
- **Students** (future scope) — Receive personalised intervention nudges

---

## 2. TECH STACK

| Layer | Technology | Reason |
|---|---|---|
| ML Model | Python 3.11, XGBoost, LightGBM | Best-in-class tabular classification |
| Explainability | SHAP 0.44 | Industry-standard feature attribution |
| Salary Prediction | Scikit-learn Ridge Regression | Salary is continuous — regression task |
| Bias Audit | Fairlearn | Demographic parity testing |
| API Backend | FastAPI 0.111 | Async, fast, auto-generates OpenAPI docs |
| Data Validation | Pydantic v2 | Request/response schema enforcement |
| Database | PostgreSQL 16 | Student records, predictions, audit logs |
| ORM | SQLAlchemy 2.0 + Alembic | Migrations |
| Cache | Redis 7 | Rate limiting, session cache |
| Frontend | React 18 + Next.js 14 (App Router) | SSR, fast dashboard |
| UI Components | shadcn/ui + Tailwind CSS | Clean, accessible, professional |
| Charts | Recharts | SHAP waterfall, salary chart, portfolio heatmap |
| LLM Integration | Anthropic Claude API (claude-sonnet-4-20250514) | AI-generated risk summaries |
| Containerisation | Docker + Docker Compose | Single-command local setup |
| Dataset | Kaggle placement datasets (synthetic + real) | Training data source |

---

## 3. PROJECT FOLDER STRUCTURE

```
edurisk-ai/
├── README.md
├── docker-compose.yml
├── .env.example
│
├── backend/                          # FastAPI application
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── main.py                       # FastAPI app entry point
│   ├── config.py                     # Environment config (Pydantic settings)
│   │
│   ├── api/
│   │   ├── __init__.py
│   │   ├── router.py                 # Main API router
│   │   └── routes/
│   │       ├── predict.py            # POST /api/predict, POST /api/batch-score
│   │       ├── explain.py            # GET /api/explain/{student_id}
│   │       ├── alerts.py             # GET /api/alerts
│   │       ├── students.py           # CRUD for student records
│   │       └── health.py             # GET /api/health
│   │
│   ├── models/
│   │   ├── __init__.py
│   │   ├── student.py                # SQLAlchemy Student ORM model
│   │   ├── prediction.py             # SQLAlchemy Prediction ORM model
│   │   └── audit_log.py              # Audit log ORM model
│   │
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── student.py                # Pydantic input/output schemas
│   │   ├── prediction.py             # Prediction response schemas
│   │   └── alert.py                  # Alert schemas
│   │
│   ├── services/
│   │   ├── __init__.py
│   │   ├── prediction_service.py     # Orchestrates ML pipeline calls
│   │   ├── explanation_service.py    # SHAP explanation generation
│   │   ├── alert_service.py          # High-risk student alert logic
│   │   └── llm_service.py            # Claude API — AI summary generation
│   │
│   └── db/
│       ├── __init__.py
│       ├── session.py                # DB session factory
│       └── migrations/               # Alembic migrations
│           └── versions/
│
├── ml/                               # ML pipeline (separate from API)
│   ├── Dockerfile
│   ├── requirements.txt
│   │
│   ├── data/
│   │   ├── raw/                      # Raw Kaggle datasets (gitignored)
│   │   ├── processed/                # Cleaned, feature-engineered CSVs
│   │   └── synthetic/                # Synthetically generated student profiles
│   │
│   ├── notebooks/
│   │   ├── 01_eda.ipynb              # Exploratory data analysis
│   │   ├── 02_feature_engineering.ipynb
│   │   ├── 03_model_training.ipynb
│   │   └── 04_shap_analysis.ipynb
│   │
│   ├── pipeline/
│   │   ├── __init__.py
│   │   ├── feature_engineering.py    # All feature transforms
│   │   ├── train.py                  # XGBoost + LightGBM training
│   │   ├── predict.py                # Inference wrapper
│   │   ├── explain.py                # SHAP wrapper
│   │   ├── salary_model.py           # Salary regression pipeline
│   │   └── bias_audit.py             # Fairlearn bias testing
│   │
│   ├── models/                       # Saved model artifacts (gitignored)
│   │   ├── placement_model_3m.pkl
│   │   ├── placement_model_6m.pkl
│   │   ├── placement_model_12m.pkl
│   │   ├── salary_model.pkl
│   │   └── feature_names.json
│   │
│   └── scripts/
│       ├── generate_synthetic_data.py
│       ├── train_all_models.py
│       └── evaluate_models.py
│
└── frontend/                         # Next.js 14 application
    ├── Dockerfile
    ├── package.json
    ├── next.config.js
    ├── tailwind.config.js
    │
    ├── app/
    │   ├── layout.tsx                # Root layout with sidebar
    │   ├── page.tsx                  # Dashboard home → redirect to /dashboard
    │   ├── dashboard/
    │   │   └── page.tsx              # Portfolio overview heatmap
    │   ├── student/
    │   │   ├── [id]/
    │   │   │   └── page.tsx          # Individual student risk profile
    │   │   └── new/
    │   │       └── page.tsx          # Add new student / run prediction
    │   └── alerts/
    │       └── page.tsx              # High-risk alert management
    │
    ├── components/
    │   ├── layout/
    │   │   ├── Sidebar.tsx
    │   │   └── TopBar.tsx
    │   ├── dashboard/
    │   │   ├── RiskScoreCard.tsx     # Score + badge (Low/Medium/High)
    │   │   ├── PlacementProbChart.tsx # 3/6/12-month probability bar chart
    │   │   ├── SalaryRangeCard.tsx   # Salary band with CI display
    │   │   ├── ShapWaterfallChart.tsx # SHAP feature contribution chart
    │   │   ├── PortfolioHeatmap.tsx  # Risk distribution across students
    │   │   ├── StudentTable.tsx      # Paginated sortable student table
    │   │   └── AlertBanner.tsx       # Red alert strip for high-risk
    │   ├── forms/
    │   │   └── StudentInputForm.tsx  # Multi-step form to input student data
    │   └── ui/                       # shadcn/ui re-exports
    │
    └── lib/
        ├── api.ts                    # Axios API client
        ├── types.ts                  # TypeScript types
        └── utils.ts                  # Helpers
```

---

## 4. DATABASE SCHEMA

### 4.1 students table
```sql
CREATE TABLE students (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name            VARCHAR(255) NOT NULL,
    course_type     VARCHAR(100) NOT NULL,       -- Engineering, MBA, Nursing, Law, etc.
    institute_name  VARCHAR(255),
    institute_tier  INTEGER NOT NULL,             -- 1, 2, or 3
    cgpa            DECIMAL(4,2),                 -- e.g. 8.50
    cgpa_scale      DECIMAL(4,2) DEFAULT 10.0,
    year_of_grad    INTEGER NOT NULL,
    internship_count INTEGER DEFAULT 0,
    internship_months INTEGER DEFAULT 0,
    internship_employer_type VARCHAR(100),        -- MNC, Startup, PSU, NGO, None
    certifications  INTEGER DEFAULT 0,
    region          VARCHAR(100),                 -- North, South, East, West, Abroad
    loan_amount     DECIMAL(12,2),
    loan_emi        DECIMAL(10,2),
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);
```

### 4.2 predictions table
```sql
CREATE TABLE predictions (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    student_id          UUID REFERENCES students(id) ON DELETE CASCADE,
    model_version       VARCHAR(50) NOT NULL,
    prob_placed_3m      DECIMAL(5,4) NOT NULL,    -- e.g. 0.6123
    prob_placed_6m      DECIMAL(5,4) NOT NULL,
    prob_placed_12m     DECIMAL(5,4) NOT NULL,
    placement_label     VARCHAR(50) NOT NULL,      -- placed_3m / placed_6m / placed_12m / high_risk
    risk_score          INTEGER NOT NULL,          -- 0–100 (higher = more risk)
    risk_level          VARCHAR(20) NOT NULL,      -- low / medium / high
    salary_min          DECIMAL(10,2),             -- in LPA (Lakhs Per Annum)
    salary_max          DECIMAL(10,2),
    salary_confidence   DECIMAL(4,2),              -- CI width %
    emi_affordability   DECIMAL(5,2),              -- EMI-to-salary ratio
    shap_values         JSONB,                     -- Full SHAP feature dict
    top_risk_drivers    JSONB,                     -- Top 5 features + SHAP values
    ai_summary          TEXT,                      -- LLM-generated explanation
    next_best_actions   JSONB,                     -- List of recommended actions
    alert_triggered     BOOLEAN DEFAULT FALSE,
    created_at          TIMESTAMPTZ DEFAULT NOW()
);
```

### 4.3 audit_logs table
```sql
CREATE TABLE audit_logs (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    student_id      UUID REFERENCES students(id),
    prediction_id   UUID REFERENCES predictions(id),
    action          VARCHAR(100) NOT NULL,         -- PREDICT / EXPLAIN / ALERT_SENT
    performed_by    VARCHAR(100),                  -- loan_officer / system
    metadata        JSONB,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);
```

---

## 5. ML PIPELINE — DETAILED SPEC

### 5.1 Feature Engineering (`ml/pipeline/feature_engineering.py`)

**Input features from student record:**

| Feature | Type | Transform |
|---|---|---|
| institute_tier | int (1/2/3) | One-hot encode |
| course_type | categorical | Label encode (Engineering=0, MBA=1, ...) |
| cgpa_normalized | float | cgpa / cgpa_scale → 0.0–1.0 |
| internship_score | float | internship_count × 0.4 + internship_months/24 × 0.3 + employer_score × 0.3 |
| employer_type_score | int | MNC=4, Startup=3, PSU=2, NGO=1, None=0 |
| certifications | int | Raw count, capped at 5 |
| placement_rate_3m | float | Institute historic 3m placement rate |
| placement_rate_6m | float | Institute historic 6m placement rate |
| salary_benchmark | float | Institute historic median salary (LPA) |
| job_demand_score | float | Sector hiring demand index (1–10) |
| region_job_density | float | Region-wise job posting density index |
| macro_hiring_index | float | Macro labor market composite (0–1) |
| sector_growth_rate | float | YoY sector hiring growth % |

**Derived/engineered features:**
- `skill_gap_score` = job_demand_score - (cgpa_normalized × 5 + internship_score × 5)
- `emi_stress_ratio` = loan_emi / salary_benchmark (risk proxy)
- `placement_momentum` = placement_rate_3m / placement_rate_12m (institute velocity)

### 5.2 Model Training (`ml/pipeline/train.py`)

**Three classifiers — one per time window:**

```python
# For each: placed_3m, placed_6m, placed_12m
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

**Training strategy:**
- 80/20 train-test split, stratified by placement label
- 5-fold cross-validation
- Hyperparameter tuning with Optuna (50 trials)
- Save best model as `.pkl` with joblib
- Log AUC-ROC, F1, Precision, Recall per fold

**Target variable:**
- Binary for each model: 1 = placed within Nm months, 0 = not placed
- Use the Kaggle placement dataset + synthetic data generated by `generate_synthetic_data.py`

### 5.3 Salary Model (`ml/pipeline/salary_model.py`)

```python
# Pipeline: preprocessing + Ridge regression
Pipeline([
    ('scaler', StandardScaler()),
    ('model', Ridge(alpha=1.0))
])
```

**Outputs:**
- `salary_predicted` — point estimate in LPA
- `salary_min` = predicted - 1.5 × std
- `salary_max` = predicted + 1.5 × std
- `salary_confidence` = CI width as % of predicted

### 5.4 SHAP Explainability (`ml/pipeline/explain.py`)

```python
import shap

# Use TreeExplainer for XGBoost (fast, exact)
explainer = shap.TreeExplainer(model)
shap_values = explainer.shap_values(X_instance)  # shape: (1, n_features)

# Top 5 risk drivers (sorted by abs SHAP value)
top_drivers = sorted(
    zip(feature_names, shap_values[0]),
    key=lambda x: abs(x[1]),
    reverse=True
)[:5]
```

**Response format:**
```json
{
  "shap_values": {
    "internship_score": 0.34,
    "institute_tier": 0.22,
    "cgpa_normalized": 0.11,
    "job_demand_score": -0.09,
    "course_type": -0.17
  },
  "base_value": 0.45,
  "prediction": 0.78
}
```

### 5.5 AI Summary Generation (`backend/services/llm_service.py`)

**Anthropic Claude API call:**
```python
import anthropic

client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)

def generate_risk_summary(student_data: dict, prediction: dict, shap_drivers: list) -> str:
    prompt = f"""
You are a credit risk analyst at an Indian NBFC. Given this student's placement risk assessment, 
write a 2-sentence plain-English summary for a loan officer.

Student: {course_type} from Tier-{institute_tier} institute, CGPA {cgpa}, {internship_count} internships
Risk score: {risk_score}/100 ({risk_level} risk)
Top risk drivers: {shap_drivers}
Placement probability: 3m={prob_3m:.0%}, 6m={prob_6m:.0%}, 12m={prob_12m:.0%}

Write a concise, professional 2-sentence assessment. Start with the risk level and key reason.
"""
    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=200,
        messages=[{"role": "user", "content": prompt}]
    )
    return message.content[0].text
```

### 5.6 Next-Best Actions (`backend/services/prediction_service.py`)

**Rule-based action engine:**
```python
def generate_next_best_actions(risk_level, shap_drivers, student_data):
    actions = []
    
    # Skill gap action
    if "job_demand_score" in low_shap_features:
        actions.append({
            "type": "skill_up",
            "title": "Skill-Up Recommendation",
            "description": f"Enroll in {course_type}-specific certification. "
                          f"Demand for your field is {job_demand_score:.1f}/10 — below average.",
            "priority": "high" if risk_level == "high" else "medium"
        })
    
    # Internship gap action
    if internship_count == 0 or internship_score < 0.3:
        actions.append({
            "type": "internship",
            "title": "Internship / Project Experience",
            "description": "No internship history detected. Complete at least 1 industry internship "
                          "or capstone project to improve placement score by ~18 points.",
            "priority": "high"
        })
    
    # Resume action
    if risk_score > 60:
        actions.append({
            "type": "resume",
            "title": "Resume Improvement",
            "description": "Resume review recommended. Highlight certifications, "
                          "projects, and quantifiable outcomes.",
            "priority": "medium"
        })
    
    # Mock interview
    if prob_placed_3m < 0.5:
        actions.append({
            "type": "mock_interview",
            "title": "Mock Interview Coaching",
            "description": "3-month placement probability is below 50%. "
                          "Mock interview preparation improves offer conversion by ~22%.",
            "priority": "high"
        })
    
    # Recruiter match
    if risk_level in ["low", "medium"] and institute_tier <= 2:
        actions.append({
            "type": "recruiter_match",
            "title": "Recruiter Matches Available",
            "description": f"3 active recruiters hiring {course_type} graduates "
                          f"in {region}. Profile flagged for outreach.",
            "priority": "low"
        })
    
    return actions
```

### 5.7 Bias Audit (`ml/pipeline/bias_audit.py`)

```python
from fairlearn.metrics import MetricFrame, demographic_parity_difference

# Sensitive features explicitly excluded from model features
EXCLUDED_FEATURES = ["gender", "religion", "caste", "state_of_origin"]

# Audit runs separately on test set
metric_frame = MetricFrame(
    metrics={"accuracy": accuracy_score, "selection_rate": selection_rate},
    y_true=y_test,
    y_pred=y_pred,
    sensitive_features=sensitive_test_df[["gender", "region_tier"]]
)
demographic_parity_diff = demographic_parity_difference(y_test, y_pred, 
                          sensitive_features=sensitive_test_df["gender"])
```

---

## 6. API ENDPOINTS — COMPLETE SPEC

### 6.1 POST /api/predict
Predict placement risk for a single student.

**Request body:**
```json
{
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
```

**Response:**
```json
{
  "student_id": "uuid-here",
  "prediction_id": "uuid-here",
  "prob_placed_3m": 0.61,
  "prob_placed_6m": 0.79,
  "prob_placed_12m": 0.93,
  "placement_label": "placed_6m",
  "risk_score": 42,
  "risk_level": "medium",
  "salary_min": 5.2,
  "salary_max": 7.8,
  "salary_confidence": 85.0,
  "emi_affordability": 0.31,
  "top_risk_drivers": [
    {"feature": "internship_score", "shap_value": 0.22, "direction": "positive"},
    {"feature": "job_demand_score", "shap_value": -0.14, "direction": "negative"}
  ],
  "ai_summary": "This student presents medium placement risk...",
  "next_best_actions": [...],
  "alert_triggered": false
}
```

### 6.2 POST /api/batch-score
Score an array of students — portfolio view.

**Request:** `{ "students": [StudentInput, ...] }` (max 500)  
**Response:** `{ "results": [PredictionResult, ...], "summary": { "high_risk_count": 12, "medium_risk_count": 45, "low_risk_count": 143 } }`

### 6.3 GET /api/explain/{student_id}
Returns full SHAP breakdown for a student.

**Response:**
```json
{
  "student_id": "uuid",
  "shap_values": { "feature": value, ... },
  "base_value": 0.45,
  "prediction": 0.78,
  "waterfall_data": [
    { "feature": "internship_score", "value": 0.34, "cumulative": 0.79 },
    ...
  ]
}
```

### 6.4 GET /api/alerts
Returns list of high-risk students that need immediate attention.

**Query params:** `?threshold=high&limit=50&offset=0`  
**Response:** Paginated list of student predictions where `risk_level == "high"` or `emi_affordability > 0.5`

### 6.5 GET /api/students
List all students with latest prediction.  
**Query params:** `?search=&sort=risk_score&order=desc&limit=20&offset=0`

### 6.6 GET /api/health
```json
{ "status": "ok", "model_version": "1.0.0", "db": "connected", "timestamp": "..." }
```

---

## 7. FRONTEND — COMPONENT SPEC

### 7.1 Dashboard (`/dashboard`)
**Layout:** Sidebar + main content  
**Components rendered:**
- `RiskScoreCard` — large number (risk score/100) with coloured badge
- `PlacementProbChart` — 3-bar chart: 3m / 6m / 12m probability
- `SalaryRangeCard` — shows ₹X.X L – ₹Y.Y L CTC with CI
- `AlertBanner` — red strip if `alert_triggered === true`
- `StudentTable` — sortable table with columns: Name, Course, Tier, Risk Score, Flag, Actions
- `PortfolioHeatmap` — grid/heatmap of all students colour-coded by risk

### 7.2 Student Detail (`/student/[id]`)
**Components:**
- `RiskScoreCard` (large)
- `PlacementProbChart`
- `SalaryRangeCard`
- `ShapWaterfallChart` — horizontal bar chart, green bars = positive, red = negative
- `AISummaryCard` — LLM-generated explanation text
- `NextBestActionsPanel` — card list of recommended actions with icons
- `AuditTrailTimeline` — history of predictions for this student

### 7.3 New Prediction (`/student/new`)
**Multi-step form (3 steps):**
- Step 1: Student Academic Info (course, CGPA, institute, year)
- Step 2: Internship & Skills (count, duration, employer type, certifications)
- Step 3: Loan Details (amount, EMI, region)
- Submit → calls POST /api/predict → redirect to `/student/[new_id]`

### 7.4 Alerts (`/alerts`)
**Components:**
- Filter bar (All / High / Medium)
- `AlertCard` per student — shows name, risk level, top driver, recommended action button

### 7.5 ShapWaterfallChart — implementation detail
```tsx
// Uses Recharts BarChart with custom cell rendering
// Positive SHAP → teal (#1D9E75)  
// Negative SHAP → red (#E24B4A)
// Baseline line → dashed at base_value
// Sorted by absolute SHAP value descending
```

---

## 8. DOCKER COMPOSE SETUP

```yaml
# docker-compose.yml
version: '3.9'
services:
  db:
    image: postgres:16-alpine
    environment:
      POSTGRES_DB: edurisk
      POSTGRES_USER: edurisk
      POSTGRES_PASSWORD: edurisk123
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

  backend:
    build: ./backend
    command: uvicorn main:app --host 0.0.0.0 --port 8000 --reload
    environment:
      DATABASE_URL: postgresql://edurisk:edurisk123@db:5432/edurisk
      REDIS_URL: redis://redis:6379
      ANTHROPIC_API_KEY: ${ANTHROPIC_API_KEY}
      ML_MODEL_PATH: /app/models
    volumes:
      - ./backend:/app
      - ./ml/models:/app/models:ro
    ports:
      - "8000:8000"
    depends_on:
      - db
      - redis

  frontend:
    build: ./frontend
    command: npm run dev
    environment:
      NEXT_PUBLIC_API_URL: http://localhost:8000
    volumes:
      - ./frontend:/app
      - /app/node_modules
    ports:
      - "3000:3000"
    depends_on:
      - backend

volumes:
  postgres_data:
```

---

## 9. ENVIRONMENT VARIABLES

```bash
# .env.example
# Backend
DATABASE_URL=postgresql://edurisk:edurisk123@localhost:5432/edurisk
REDIS_URL=redis://localhost:6379
ANTHROPIC_API_KEY=your_anthropic_api_key_here
ML_MODEL_PATH=./ml/models
SECRET_KEY=your_secret_key_here
CORS_ORIGINS=http://localhost:3000

# Frontend
NEXT_PUBLIC_API_URL=http://localhost:8000
```

---

## 10. DATASET & SYNTHETIC DATA

### 10.1 Kaggle Datasets to download
1. `https://www.kaggle.com/datasets/benroshan/factors-affecting-campus-placement` — Primary dataset
2. `https://www.kaggle.com/datasets/ahsan81/student-placement-dataset`
3. `https://www.kaggle.com/datasets/tejashvi14/engineering-placements-prediction`

### 10.2 Synthetic Data Generator (`ml/scripts/generate_synthetic_data.py`)
Generate 5,000 synthetic student records using numpy/faker with realistic distributions:
- CGPA: Normal(7.5, 1.2), clipped to [4.0, 10.0]
- Institute tier: Multinomial([0.2, 0.5, 0.3]) for tiers 1, 2, 3
- Internship count: Poisson(1.5), capped at 6
- Placement at 3m: Logistic function of (tier=1, CGPA>8, internship>2)
- Salary: Lognormal based on tier and course type

---

## 11. STEP-BY-STEP BUILD ORDER FOR KIRO

Build in this exact order to avoid dependency issues:

```
Phase 1 — Data & ML (Days 1–2)
  1. Create ml/ folder structure
  2. Download Kaggle datasets → ml/data/raw/
  3. Run generate_synthetic_data.py
  4. Implement feature_engineering.py
  5. Train 3 XGBoost classifiers (train.py)
  6. Train salary Ridge model (salary_model.py)
  7. Implement explain.py (SHAP)
  8. Run bias_audit.py
  9. Save all .pkl files to ml/models/

Phase 2 — Backend API (Days 2–3)
  10. Set up FastAPI app (main.py, config.py)
  11. Set up PostgreSQL + run Alembic migrations
  12. Implement Pydantic schemas
  13. Implement SQLAlchemy models
  14. Implement prediction_service.py (loads .pkl, runs inference)
  15. Implement explanation_service.py
  16. Implement llm_service.py (Claude API)
  17. Implement all API routes
  18. Add CORS middleware
  19. Test all endpoints with curl / Postman

Phase 3 — Frontend (Days 3–4)
  20. Set up Next.js 14 with shadcn/ui + Tailwind
  21. Create layout (Sidebar + TopBar)
  22. Implement StudentInputForm (multi-step)
  23. Implement RiskScoreCard
  24. Implement PlacementProbChart (Recharts)
  25. Implement ShapWaterfallChart (Recharts)
  26. Implement SalaryRangeCard
  27. Implement StudentTable with sorting
  28. Implement PortfolioHeatmap
  29. Implement AlertBanner + Alerts page
  30. Wire all components to API via lib/api.ts

Phase 4 — Polish & Docker (Day 5)
  31. Write docker-compose.yml
  32. Write Dockerfiles for backend + frontend
  33. Test full stack with docker-compose up
  34. Write README.md with setup instructions
  35. Create GitHub repo, push all code
```

---

## 12. README.md STRUCTURE

```markdown
# EduRisk AI — Placement Risk Intelligence for Education Lending

## Quick Start (Docker)
\`\`\`bash
git clone https://github.com/your-username/edurisk-ai
cd edurisk-ai
cp .env.example .env
# Add your ANTHROPIC_API_KEY to .env
docker-compose up --build
\`\`\`
- Frontend: http://localhost:3000
- Backend API docs: http://localhost:8000/docs

## Architecture
[Architecture diagram or description]

## ML Models
- Placement classifier: XGBoost (AUC: ~0.87)
- Salary predictor: Ridge Regression (MAE: ~0.8 LPA)
- Explainability: SHAP TreeExplainer
- Bias audit: Fairlearn demographic parity

## Tech Stack
[Table from Section 2]

## API Reference
[Summary of endpoints from Section 6]
```

---

## 13. KEY CONSTRAINTS & NOTES FOR KIRO

1. **Do NOT automate credit approvals** — the system must always say "Recommend for review" not "Auto-approve". This is a hard requirement from the problem statement.
2. **Demographic features EXCLUDED from model** — gender, religion, caste must never be input features to the ML model. Only used in bias audit post-hoc.
3. **Salary in LPA** — all salary figures in Lakhs Per Annum (Indian convention).
4. **Risk score 0–100** — 0 = lowest risk, 100 = highest risk (invert placement probability).
5. **All predictions logged to audit_logs** — every inference must be traceable (RBI compliance).
6. **SHAP values must be stored** — save full SHAP dict as JSONB in predictions table for auditability.
7. **Model version must be recorded** — store model version string with every prediction.
8. **No real student PII in the GitHub repo** — only synthetic or Kaggle data.