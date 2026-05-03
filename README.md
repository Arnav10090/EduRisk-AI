# EduRisk AI - Placement Risk Intelligence

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.111.0-009688.svg)](https://fastapi.tiangolo.com)
[![Next.js 14](https://img.shields.io/badge/Next.js-14-black.svg)](https://nextjs.org/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

AI-powered placement risk assessment system for education loan lenders. Built for the TenzorX 2026 Poonawalla Fincorp National AI Hackathon.

## 🎯 Overview

EduRisk AI predicts student placement outcomes and generates actionable risk assessments for education loan lenders. The system provides:

- **Placement Timeline Predictions**: 3-month, 6-month, and 12-month placement probabilities
- **Salary Range Estimates**: Expected starting salary with confidence intervals
- **Risk Scoring**: Composite risk scores (0-100) with categorical levels (Low/Medium/High)
- **SHAP Explainability**: Transparent feature attributions for every prediction
- **AI-Generated Summaries**: Optional natural language risk explanations via Groq or Anthropic
- **Actionable Recommendations**: Personalized intervention suggestions
- **Compliance Audit Trails**: Complete logging for RBI regulatory requirements

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Frontend (Next.js 14)                     │
│  Dashboard • Student Detail • New Prediction • Alerts        │
└────────────────────────┬────────────────────────────────────┘
                         │ HTTP/REST API
┌────────────────────────┴────────────────────────────────────┐
│                  Backend API (FastAPI)                       │
│  Prediction Service • LLM Service • Action Recommender       │
└────────────────────────┬────────────────────────────────────┘
                         │
        ┌────────────────┴────────────────┐
        │                                 │
┌───────▼────────┐              ┌─────────▼────────┐
│ PostgreSQL 16  │              │    Redis 7       │
│ + Alembic      │              │  Rate Limiting   │
└────────────────┘              └──────────────────┘

┌─────────────────────────────────────────────────────────────┐
│              ML Pipeline (XGBoost + SHAP)                    │
│  Feature Engineering • Placement Models • Salary Model       │
└─────────────────────────────────────────────────────────────┘
```

### Technology Stack

| Component | Technology | Version |
|-----------|-----------|---------|
| ML Models | XGBoost | 2.0.3 |
| Explainability | SHAP | 0.44.1 |
| Backend API | FastAPI | 0.111.0 |
| Database | PostgreSQL | 16 |
| ORM | SQLAlchemy | 2.0.30 |
| Cache | Redis | 7 |
| LLM | Optional Groq / Anthropic integration | Latest |
| Frontend | Next.js | 14 |
| UI Components | shadcn/ui + Tailwind CSS | Latest |
| Containerization | Docker + Docker Compose | Latest |

## 🚀 Quick Start

### Prerequisites

- **Docker** (20.10+) and **Docker Compose** (2.0+)
- **LLM API Key** (optional - for AI summaries, system works without it)
- **8GB RAM** minimum
- **10GB disk space** for Docker images and data

### Quick Demo Access

After the stack starts:

- **Frontend**: http://localhost:3000
- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/api/health
- **Demo login**: `demo` / `demo@1234`
- **Admin login**: `admin` / `admin123`
- These are intentional seeded demo credentials for hackathon evaluation only.

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd edurisk-ai
   ```

2. **Set up environment variables**
   ```bash
   cp .env.example .env
   ```
   
   Edit `.env` and configure:
   ```env
   # Security
   SECRET_KEY=your_secret_key_here_change_in_production
   
   # Leave API_KEY empty for the frontend demo flow.
   # If you set it, manual API requests must include X-API-Key.
   API_KEY=
   
   # Optional LLM integration
   # LLM_API_KEY=your_provider_key_here
   # LLM_PROVIDER=anthropic
   
   # Application settings
   DEBUG=False  # Set to True only for local development
   LOG_LEVEL=INFO
   
   # Docker defaults
   POSTGRES_USER=edurisk
   POSTGRES_PASSWORD=edurisk_password
   POSTGRES_DB=edurisk_db
   ```
   
   Notes:
   - The LLM integration is optional. If `LLM_API_KEY` is not configured, the system still serves predictions, risk scores, and SHAP explanations.
   - This repo currently does not include the trained `.pkl` model binaries. On first backend startup, the container auto-trains models if they are missing. That can add 1-2 minutes to first boot.

3. **Start the application**
   ```bash
   docker-compose up -d
   ```
   
   This will:
   - Start PostgreSQL database
   - Start Redis cache
   - Start the FastAPI backend on port 8000
   - Start the Next.js frontend on port 3000
   - Train ML models automatically on first boot if model binaries are missing
   - Initialize database tables during backend startup

4. **Verify deployment**
   ```bash
   # Check service health
   curl http://localhost:8000/api/health
   ```

5. **Access the application**
   - **Frontend**: http://localhost:3000
   - **API Documentation**: http://localhost:8000/docs
   - **API Alternative Docs**: http://localhost:8000/redoc

### API Endpoints

#### Prediction Endpoints

**POST /api/predict** - Single student prediction
```bash
curl -X POST http://localhost:8000/api/predict \
  -H "Content-Type: application/json" \
  -d '{
    "name": "John Doe",
    "course_type": "Engineering",
    "institute_tier": 2,
    "institute_name": "ABC Institute",
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
  }'
```

**Response:**
```json
{
  "student_id": "uuid",
  "prediction_id": "uuid",
  "risk_score": 45,
  "risk_level": "medium",
  "prob_placed_3m": 0.6234,
  "prob_placed_6m": 0.7891,
  "prob_placed_12m": 0.8567,
  "placement_label": "placed_3m",
  "salary_min": 4.5,
  "salary_max": 6.8,
  "salary_confidence": 85.5,
  "emi_affordability": 0.32,
  "top_risk_drivers": [...],
  "ai_summary": "Medium risk student...",
  "next_best_actions": [...]
}
```

**POST /api/batch-score** - Batch prediction (max 500 students)
```bash
curl -X POST http://localhost:8000/api/batch-score \
  -H "Content-Type: application/json" \
  -d '{
    "students": [
      { "name": "Student 1", ... },
      { "name": "Student 2", ... }
    ]
  }'
```

#### Query Endpoints

**GET /api/explain/{student_id}** - Get SHAP explanation
```bash
curl http://localhost:8000/api/explain/{student_id}
```

**GET /api/students** - List all students
```bash
# With pagination and search
curl "http://localhost:8000/api/students?search=John&limit=20&offset=0&sort=risk_score&order=desc"
```

**GET /api/alerts** - Get high-risk alerts
```bash
curl "http://localhost:8000/api/alerts?threshold=high&limit=50"
```

**GET /api/health** - Health check
```bash
curl http://localhost:8000/api/health
```

### Environment Variables

#### Backend Configuration

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `DATABASE_URL` | PostgreSQL connection string | `postgresql+asyncpg://...` | Yes |
| `REDIS_URL` | Redis connection string | `redis://redis:6379/0` | Yes |
| `LLM_API_KEY` | API key for LLM provider (Groq or Anthropic) | - | No* |
| `LLM_PROVIDER` | LLM provider to use when `LLM_API_KEY` is set | `groq` | No* |
| `API_KEY` | Optional API key for manual API protection via `X-API-Key` | empty | No |
| `ML_MODEL_PATH` | Path to ML models directory | `/app/ml/models` | Yes |
| `SECRET_KEY` | Secret key for JWT tokens and encryption | - | Yes |
| `CORS_ORIGINS` | Allowed CORS origins | `http://localhost:3000` | No |
| `DEBUG` | Enable debug mode with detailed error traces | `False` | No |
| `LOG_LEVEL` | Logging level (DEBUG, INFO, WARNING, ERROR) | `INFO` | No |
| `LOG_JSON_FORMAT` | Use JSON logging format | `True` | No |

**\*LLM Integration Note**: The `LLM_API_KEY` and `LLM_PROVIDER` are optional. If not configured, the system will gracefully degrade and provide predictions without AI-generated summaries. All core functionality (predictions, risk scoring, SHAP explanations) works without LLM integration.

**DEBUG Usage**: 
- Set `DEBUG=False` for production deployments to hide stack traces and sensitive error details
- Set `DEBUG=True` only for local development to see detailed error information
- Default is `False` for security

**API_KEY Usage**:
- For the hackathon UI demo, leave `API_KEY` unset so the frontend can authenticate with JWT only.
- If you set `API_KEY`, manual API requests must include it via `X-API-Key`.
- Public endpoints remain accessible without it: `/`, `/api/health`, `/api/auth/login`, `/api/auth/refresh`, `/docs`, `/redoc`, `/openapi.json`

**Authentication Flow**:
- Frontend users log in at `/login` with the demo credentials listed above.
- Protected UI/API flows use JWT bearer authentication after login.

#### Frontend Configuration

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `NEXT_PUBLIC_API_URL` | Backend API URL | `http://localhost:8000` | Yes |

### Database Schema

#### students Table
```sql
CREATE TABLE students (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    course_type VARCHAR(100) NOT NULL,
    institute_name VARCHAR(255),
    institute_tier INTEGER NOT NULL CHECK (institute_tier BETWEEN 1 AND 3),
    cgpa DECIMAL(4,2) CHECK (cgpa >= 0),
    cgpa_scale DECIMAL(4,2) DEFAULT 10.0,
    year_of_grad INTEGER NOT NULL CHECK (year_of_grad BETWEEN 2020 AND 2030),
    internship_count INTEGER DEFAULT 0,
    internship_months INTEGER DEFAULT 0,
    internship_employer_type VARCHAR(100),
    certifications INTEGER DEFAULT 0,
    region VARCHAR(100),
    loan_amount DECIMAL(12,2),
    loan_emi DECIMAL(10,2),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

#### predictions Table
```sql
CREATE TABLE predictions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    student_id UUID NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    model_version VARCHAR(50) NOT NULL,
    prob_placed_3m DECIMAL(5,4) NOT NULL,
    prob_placed_6m DECIMAL(5,4) NOT NULL,
    prob_placed_12m DECIMAL(5,4) NOT NULL,
    placement_label VARCHAR(50) NOT NULL,
    risk_score INTEGER NOT NULL CHECK (risk_score BETWEEN 0 AND 100),
    risk_level VARCHAR(20) NOT NULL,
    salary_min DECIMAL(10,2),
    salary_max DECIMAL(10,2),
    salary_confidence DECIMAL(4,2),
    emi_affordability DECIMAL(5,2),
    shap_values JSONB NOT NULL,
    top_risk_drivers JSONB NOT NULL,
    ai_summary TEXT,
    next_best_actions JSONB NOT NULL,
    alert_triggered BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

#### audit_logs Table
```sql
CREATE TABLE audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    student_id UUID REFERENCES students(id) ON DELETE SET NULL,
    prediction_id UUID REFERENCES predictions(id) ON DELETE SET NULL,
    action VARCHAR(50) NOT NULL,
    performed_by VARCHAR(255),
    metadata JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

## 🔧 Development

### Running Tests

```bash
# Backend and API tests
pytest backend/tests -v

# ML pipeline tests
pytest ml -v

# Frontend checks
cd frontend
npm run lint
npm run type-check
```

### Database Migrations

```bash
# Create a new migration
cd backend
alembic revision --autogenerate -m "Description"

# Apply migrations
alembic upgrade head

# Rollback migration
alembic downgrade -1
```

### ML Model Training

```bash
# Generate synthetic data
python ml/data/generate_synthetic.py

# Train all models
python -m ml.pipeline.train_all

# Faster local bootstrap option
python -m ml.pipeline.train_quick

# Run bias audit
python ml/pipeline/bias_audit.py
```

## 📊 ML Pipeline

### Feature Engineering

The system uses 16 engineered features:

1. **cgpa_normalized**: CGPA scaled to 0-1 range
2. **internship_score**: Composite score from count, duration, employer type
3. **employer_type_score**: MNC=4, Startup=3, PSU=2, NGO=1
4. **certifications**: Number of certifications (capped at 5)
5-7. **institute_tier_1/2/3**: One-hot encoded tier
8. **course_type_encoded**: Label encoded course type
9-11. **placement_rate_3m/6m/12m**: Historical institute rates
12. **salary_benchmark**: Institute historical salary
13. **job_demand_score**: Sector demand index (1-10)
14. **region_job_density**: Regional job market density
15. **macro_hiring_index**: Economic hiring indicator (0-1)
16. **skill_gap_score**: Derived gap metric

**Excluded Features**: gender, religion, caste, state_of_origin (for fairness)

### Models

- **Placement Models**: 3 XGBoost classifiers (3m, 6m, 12m windows)
- **Salary Model**: Ridge regression with StandardScaler
- **Explainability**: SHAP TreeExplainer for feature attributions

### Risk Calculation

```python
risk_score = 100 - (prob_3m * 50 + prob_6m * 30 + prob_12m * 20)

risk_level = {
    0-33: "low",
    34-66: "medium",
    67-100: "high"
}
```

## 🔒 Security & Compliance

### Rate Limiting

- **POST /api/predict**: 100 requests/minute per IP
- **POST /api/batch-score**: 10 requests/minute per IP
- **GET endpoints**: 300 requests/minute per IP

### Audit Logging

All predictions, explanations, and alerts are logged to the `audit_logs` table with:
- Action type (PREDICT, EXPLAIN, ALERT_SENT)
- Student ID and Prediction ID
- Model version
- Timestamp
- User identifier (if authenticated)

### Fairness

- Demographic features (gender, religion, caste, state) are **excluded** from all ML models
- Post-hoc bias auditing with Fairlearn
- Demographic parity monitoring

## 🐛 Troubleshooting

### Common Issues

**1. Database connection failed**
```bash
# Check if PostgreSQL is running
docker-compose ps postgres

# Check logs
docker-compose logs postgres

# Restart database
docker-compose restart postgres
```

**2. ML models not found**
```bash
# Train models first
python ml/pipeline/train.py

# Or check if models directory is mounted correctly
docker-compose exec backend ls -la /app/ml/models
```

**3. Frontend can't connect to backend**
```bash
# Check if backend is running
curl http://localhost:8000/api/health

# Check NEXT_PUBLIC_API_URL in frontend/.env.local
cat frontend/.env.local
```

**4. Rate limit exceeded**
```bash
# Clear Redis cache
docker-compose exec redis redis-cli FLUSHALL
```

**5. Alembic migration failed**
```bash
# Check current migration version
cd backend && alembic current

# Reset database (WARNING: deletes all data)
docker-compose down -v
docker-compose up -d
```

### Logs

```bash
# View all logs
docker-compose logs -f

# View specific service logs
docker-compose logs -f backend
docker-compose logs -f frontend
docker-compose logs -f postgres
docker-compose logs -f redis
```

## 📈 Performance

- **Single Prediction**: < 5 seconds (95th percentile)
- **Batch Prediction (500 students)**: < 60 seconds
- **Health Check**: < 3 seconds
- **Explanation Retrieval**: < 1 second
- **Alert Query**: < 2 seconds

## 🤝 Contributing

This project was built for the TenzorX 2026 Poonawalla Fincorp National AI Hackathon.

## 📞 Support

For issues and questions:
- Check the [Troubleshooting](#troubleshooting) section
- Review API documentation at http://localhost:8000/docs
- Check Docker logs: `docker-compose logs -f`

---

**Built with ❤️ for better education loan decisions**
