# EduRisk AI - Placement Risk Intelligence

AI-powered placement risk assessment platform for education loan lenders. Built for the TenzorX 2026 Poonawalla Fincorp National AI Hackathon.

## Overview

EduRisk AI predicts student placement probability within 3, 6, and 12 months post-graduation, estimates salary ranges, calculates composite risk scores, and provides actionable intervention recommendations. The system uses XGBoost classifiers, SHAP explainability, and Claude AI for natural language summaries.

## Architecture

- **ML Pipeline**: Python-based feature engineering, XGBoost models, SHAP explanations
- **Backend API**: FastAPI with async SQLAlchemy, PostgreSQL, Redis
- **Frontend**: Next.js 14 with TypeScript, Tailwind CSS, shadcn/ui
- **Deployment**: Docker Compose orchestration

## Technology Stack

### Backend & ML
- FastAPI 0.111 - Async API framework
- SQLAlchemy 2.0 - Async ORM
- PostgreSQL 16 - Primary database
- Redis 7 - Caching and rate limiting
- XGBoost 2.0 - Placement prediction models
- SHAP 0.44 - Model explainability
- Anthropic Claude API - AI summaries
- Fairlearn - Bias auditing

### Frontend
- Next.js 14 (App Router) - React framework
- TypeScript - Type safety
- Tailwind CSS - Styling
- shadcn/ui - UI components
- Recharts - Data visualization
- SWR - Data fetching

## Project Structure

```
edurisk-ai/
├── ml/                          # ML Pipeline
│   ├── pipeline/                # Feature engineering, training, prediction
│   ├── models/                  # Trained model artifacts
│   └── data/                    # Training data
├── backend/                     # FastAPI Backend
│   ├── api/                     # API routes
│   ├── models/                  # SQLAlchemy ORM models
│   ├── schemas/                 # Pydantic schemas
│   ├── services/                # Business logic
│   ├── db/                      # Database configuration
│   └── middleware/              # Rate limiting, CORS
├── frontend/                    # Next.js Frontend
│   ├── app/                     # App router pages
│   ├── components/              # React components
│   └── lib/                     # Utilities
├── docker/                      # Docker configuration
│   ├── Dockerfile.backend
│   └── Dockerfile.frontend
├── docker-compose.yml           # Service orchestration
└── requirements.txt             # Python dependencies
```

## Setup Instructions

### Prerequisites

- Python 3.11+
- Node.js 20+
- Docker & Docker Compose (for containerized setup)
- PostgreSQL 16 (for local development)
- Redis 7 (for local development)

### Option 1: Docker Setup (Recommended)

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd edurisk-ai
   ```

2. **Configure environment variables**
   ```bash
   # Backend
   cp backend/.env.example backend/.env
   # Edit backend/.env and add your ANTHROPIC_API_KEY
   
   # Frontend
   cp frontend/.env.example frontend/.env
   ```

3. **Start all services**
   ```bash
   docker-compose up -d
   ```

4. **Run database migrations**
   ```bash
   docker-compose exec backend alembic upgrade head
   ```

5. **Access the application**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Docs: http://localhost:8000/docs

### Option 2: Local Development Setup

#### Backend Setup

1. **Create Python virtual environment**
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
   cp backend/.env.example backend/.env
   # Edit backend/.env with your database and API credentials
   ```

4. **Start PostgreSQL and Redis**
   ```bash
   # Using Docker
   docker run -d -p 5432:5432 -e POSTGRES_USER=edurisk -e POSTGRES_PASSWORD=edurisk_password -e POSTGRES_DB=edurisk_db postgres:16-alpine
   docker run -d -p 6379:6379 redis:7-alpine
   ```

5. **Run database migrations**
   ```bash
   cd backend
   alembic upgrade head
   ```

6. **Start the backend server**
   ```bash
   uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
   ```

#### Frontend Setup

1. **Install dependencies**
   ```bash
   cd frontend
   npm install
   ```

2. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env if needed (default points to localhost:8000)
   ```

3. **Start the development server**
   ```bash
   npm run dev
   ```

4. **Access the application**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000/docs

## ML Model Training

Before running predictions, you need to train the ML models:

```bash
# Generate synthetic training data
python ml/data/generate_synthetic.py

# Train placement models (3m, 6m, 12m)
python ml/pipeline/train.py

# Train salary model
python ml/pipeline/salary_model.py

# Run bias audit
python ml/pipeline/bias_audit.py
```

Models will be saved to `ml/models/` directory.

## API Endpoints

### Prediction
- `POST /api/predict` - Single student prediction
- `POST /api/batch-score` - Batch student scoring (max 500)

### Retrieval
- `GET /api/explain/{student_id}` - SHAP explanation
- `GET /api/alerts` - High-risk student alerts
- `GET /api/students` - Student list with filters

### System
- `GET /api/health` - Health check

See full API documentation at http://localhost:8000/docs

## Configuration

### Backend Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | Required |
| `REDIS_URL` | Redis connection string | Required |
| `ANTHROPIC_API_KEY` | Claude API key | Required |
| `ML_MODEL_PATH` | Path to ML models | `../ml/models` |
| `SECRET_KEY` | JWT secret key | Required |
| `CORS_ORIGINS` | Allowed CORS origins | `http://localhost:3000` |

### Frontend Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `NEXT_PUBLIC_API_URL` | Backend API URL | `http://localhost:8000` |

## Testing

### Backend Tests
```bash
pytest backend/tests/ -v --cov=backend
```

### Frontend Tests
```bash
cd frontend
npm run test
```

## Development Workflow

1. **Feature Development**: Create feature branches from `main`
2. **Code Quality**: Run linters and type checks before committing
3. **Testing**: Write unit tests for new features
4. **Documentation**: Update README and API docs

## Deployment

### Production Considerations

- Use environment-specific `.env` files
- Set `DEBUG=False` in production
- Use strong `SECRET_KEY` values
- Configure proper CORS origins
- Set up SSL/TLS certificates
- Use managed PostgreSQL and Redis services
- Implement proper logging and monitoring
- Set up CI/CD pipelines

## License

Proprietary - TenzorX 2026 Hackathon Submission

## Support

For questions or issues, contact the development team.
