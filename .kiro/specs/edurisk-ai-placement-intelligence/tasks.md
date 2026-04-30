# Implementation Plan: EduRisk AI - Placement Risk Intelligence

## Overview

This implementation plan breaks down the EduRisk AI system into discrete coding tasks. The system consists of three main layers: ML Pipeline (Python), Backend API (FastAPI/Python), and Frontend (Next.js/TypeScript). Tasks are organized to build incrementally, with early validation through testing and checkpoints.

## Tasks

- [x] 1. Set up project structure and core infrastructure
  - Create directory structure: `ml/`, `backend/`, `frontend/`, `docker/`
  - Set up Python virtual environment and install core dependencies (FastAPI, SQLAlchemy, XGBoost, SHAP, Pydantic, Anthropic)
  - Set up Next.js project with TypeScript, Tailwind CSS, and shadcn/ui
  - Create `.env.example` files for configuration
  - _Requirements: 24.1, 24.5_

- [x] 2. Implement database schema and ORM models
  - [x] 2.1 Create SQLAlchemy base configuration and async session management
    - Implement `backend/db/session.py` with async engine, connection pooling (pool_size=20, max_overflow=10)
    - Implement `get_db()` dependency for FastAPI
    - _Requirements: 18.1, 18.5, 18.6_

  - [x] 2.2 Create Student ORM model
    - Implement `backend/models/student.py` with all fields from requirements
    - Add constraints: institute_tier (1-3), cgpa validation, year_of_grad (2020-2030)
    - Add relationships to predictions and audit_logs
    - _Requirements: 18.1_

  - [x] 2.3 Create Prediction ORM model
    - Implement `backend/models/prediction.py` with all fields including JSONB columns
    - Add constraints: probabilities (0-1), risk_score (0-100), risk_level enum
    - Add foreign key to students with CASCADE delete
    - _Requirements: 18.2, 18.4_

  - [x] 2.4 Create AuditLog ORM model
    - Implement `backend/models/audit_log.py` with action tracking
    - Add foreign keys with SET NULL on delete
    - _Requirements: 18.3, 18.4_

  - [x] 2.5 Create Alembic migration for initial schema
    - Generate migration with all tables, indexes, and constraints
    - Add indexes: students(tier, course, created_at), predictions(student_id, risk_level, created_at), audit_logs(student_id, action, created_at)
    - _Requirements: 18.1, 18.2, 18.3_

- [x] 3. Implement Pydantic schemas for API validation
  - [x] 3.1 Create request schemas
    - Implement `backend/schemas/student.py` with StudentInput and BatchScoreRequest
    - Add field validators: institute_tier (1-3), cgpa <= cgpa_scale, year_of_grad (2020-2030), non-negative values
    - _Requirements: 20.1, 20.2, 20.3, 20.4, 20.5, 20.6_

  - [x] 3.2 Create response schemas
    - Implement `backend/schemas/prediction.py` with PredictionResponse, BatchScoreResponse, ShapExplanationResponse
    - Include nested models: RiskDriver, NextBestAction
    - _Requirements: 8.5, 9.5, 10.3_

  - [ ]* 3.3 Write unit tests for schema validation
    - Test validation errors for out-of-range values
    - Test required field enforcement
    - _Requirements: 20.7_

- [x] 4. Implement ML feature engineering pipeline
  - [x] 4.1 Create FeatureEngineer class
    - Implement `ml/pipeline/feature_engineering.py` with transform() and get_feature_names()
    - Implement transformations: cgpa_normalized, internship_score, employer_type_score, skill_gap_score, emi_stress_ratio, placement_momentum
    - Implement one-hot encoding for institute_tier, label encoding for course_type
    - Create `ml/models/feature_names.json` with 16 feature names
    - _Requirements: 17.1, 17.2, 17.3, 17.4, 17.5, 17.6, 17.7_

  - [ ]* 4.2 Write property test for demographic feature exclusion
    - **Property 3: Demographic Feature Exclusion**
    - **Validates: Requirements 1.5, 2.7, 16.1, 16.2, 16.3**
    - Test that feature vector never contains gender, religion, caste, state_of_origin
    - Test that feature_names.json does not list demographic features

  - [ ]* 4.3 Write unit tests for feature engineering edge cases
    - Test missing optional fields use defaults
    - Test CGPA normalization with different scales
    - Test internship_score calculation with zero internships
    - _Requirements: 17.1, 17.2, 17.3_

- [x] 5. Implement ML model training pipeline
  - [x] 5.1 Create synthetic data generation script
    - Implement `ml/data/generate_synthetic.py` with distributions from requirements
    - Generate 5000 records with CGPA (normal), institute_tier (multinomial), internship_count (Poisson)
    - Generate placement labels using logistic function
    - Save to `ml/data/synthetic/students.csv`
    - _Requirements: 30.1, 30.2, 30.3, 30.4, 30.5, 30.6, 30.7_

  - [x] 5.2 Create model training script
    - Implement `ml/pipeline/train.py` with XGBoost training for 3 time windows
    - Implement 80/20 train-test split, 5-fold cross-validation
    - Implement hyperparameter tuning with Optuna (50 trials)
    - Save models: placement_model_3m.pkl, placement_model_6m.pkl, placement_model_12m.pkl
    - Log metrics: AUC-ROC, F1, Precision, Recall
    - _Requirements: 1.3_

  - [x] 5.3 Create salary model training script
    - Implement Ridge regression training with StandardScaler pipeline
    - Save model: salary_model.pkl
    - _Requirements: 2.6_

  - [x] 5.4 Create model version tracking
    - Implement `ml/models/version.json` generation with semantic version, training date, metrics
    - _Requirements: 15.1, 15.2, 15.3_

- [x] 6. Checkpoint - Verify ML pipeline and data setup
  - Ensure all tests pass, ask the user if questions arise.

- [x] 7. Implement ML prediction components
  - [x] 7.1 Create PlacementPredictor class
    - Implement `ml/pipeline/predict.py` with model loading and predict()
    - Implement placement label assignment logic (prob >= 0.5 thresholds)
    - Implement get_model_version() reading from version.json
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.6_

  - [ ]* 7.2 Write property test for placement probability validity
    - **Property 1: Placement Probability Validity**
    - **Validates: Requirements 1.1, 1.4**
    - Test that all probabilities are in [0, 1] with 4 decimal places

  - [ ]* 7.3 Write property test for placement label assignment
    - **Property 2: Placement Label Assignment Correctness**
    - **Validates: Requirements 1.2, 1.6**
    - Test label assignment follows threshold rules

  - [x] 7.4 Create SalaryEstimator class
    - Implement `ml/pipeline/salary_model.py` with predict()
    - Calculate salary_min, salary_max using 1.5 * std formula
    - Calculate salary_confidence percentage
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5_

  - [ ]* 7.5 Write property test for salary range relationship
    - **Property 4: Salary Range Relationship**
    - **Validates: Requirements 2.1, 2.3, 2.4**
    - Test that salary_min < predicted < salary_max
    - Test formula: min = predicted - 1.5*std, max = predicted + 1.5*std

  - [ ]* 7.6 Write property test for salary confidence calculation
    - **Property 5: Salary Confidence Calculation**
    - **Validates: Requirements 2.2, 2.5**
    - Test confidence = ((max - min) / predicted) * 100

- [x] 8. Implement risk calculation and scoring
  - [x] 8.1 Create risk calculation functions
    - Implement `backend/services/risk_calculator.py` with calculate_risk_score()
    - Implement formula: 100 - (prob_3m * 50 + prob_6m * 30 + prob_12m * 20)
    - Implement assign_risk_level() with thresholds: 0-33 low, 34-66 medium, 67-100 high
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6_

  - [ ]* 8.2 Write property test for risk score calculation
    - **Property 6: Risk Score Calculation Formula**
    - **Validates: Requirements 3.1, 3.2, 3.3**
    - Test risk score formula with various probability combinations

  - [ ]* 8.3 Write property test for risk level assignment
    - **Property 7: Risk Level Assignment**
    - **Validates: Requirements 3.4, 3.5, 3.6**
    - Test risk level thresholds

  - [x] 8.4 Implement EMI affordability calculation
    - Add calculate_emi_affordability() function
    - Implement formula: loan_emi / ((salary_lpa * 100000) / 12)
    - _Requirements: 4.1, 4.2, 4.3, 4.4_

  - [ ]* 8.5 Write property test for EMI affordability
    - **Property 8: EMI Affordability Calculation**
    - **Validates: Requirements 4.1, 4.2, 4.3, 4.4**
    - Test EMI affordability formula

  - [ ]* 8.6 Write property test for high risk alert triggering
    - **Property 9: High Risk Alert Triggering**
    - **Validates: Requirements 4.5**
    - Test alert_triggered = (risk_level == "high" OR emi_affordability > 0.5)

- [-] 9. Implement SHAP explainability engine
  - [x] 9.1 Create ShapExplainer class
    - Implement `ml/pipeline/explain.py` with TreeExplainer initialization
    - Implement explain() method returning SHAP values dictionary, base_value, top_drivers
    - Implement select_top_drivers() sorting by absolute value, taking top 5
    - _Requirements: 5.1, 5.2, 5.3, 5.5_

  - [ ]* 9.2 Write property test for SHAP values completeness
    - **Property 10: SHAP Values Completeness**
    - **Validates: Requirements 5.1**
    - Test SHAP dictionary contains exactly all features from feature_names.json

  - [ ]* 9.3 Write property test for top risk drivers selection
    - **Property 11: Top Risk Drivers Selection**
    - **Validates: Requirements 5.3, 5.5**
    - Test top 5 drivers sorted by absolute value
    - Test direction field ("positive" or "negative")

  - [ ]* 9.4 Write property test for SHAP storage round-trip
    - **Property 12: SHAP Values Storage Round-Trip**
    - **Validates: Requirements 5.4**
    - Test JSONB storage and retrieval preserves SHAP values

- [x] 10. Implement LLM integration for AI summaries
  - [x] 10.1 Create LLMService class
    - Implement `backend/services/llm_service.py` with Anthropic client
    - Implement generate_summary() with Claude Sonnet 4 API call
    - Implement prompt template including course_type, institute_tier, cgpa, internship_count, risk_score, risk_level, top_risk_drivers
    - Set timeout to 5 seconds, max_tokens to 200, temperature to 0.3
    - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5_

  - [x] 10.2 Implement fallback for API failures
    - Add try-catch for timeout and API errors
    - Return "AI summary unavailable - refer to SHAP values for risk drivers." on failure
    - _Requirements: 6.7_

  - [ ]* 10.3 Write property test for LLM prompt completeness
    - **Property 13: LLM Prompt Completeness**
    - **Validates: Requirements 6.3**
    - Test prompt contains all required fields

  - [ ]* 10.4 Write unit test for LLM fallback behavior
    - Test timeout returns fallback message
    - Test API error returns fallback message
    - _Requirements: 6.7_

- [x] 11. Implement action recommendation engine
  - [x] 11.1 Create action recommendation functions
    - Implement `backend/services/action_recommender.py` with generate_actions()
    - Implement rule 1: skill_up when job_demand_score in bottom 3 SHAP features
    - Implement rule 2: internship when count=0 or score<0.3 (priority high)
    - Implement rule 3: resume when risk_score>60
    - Implement rule 4: mock_interview when prob_3m<0.5 (priority high)
    - Implement rule 5: recruiter_match when risk_level low/medium and tier<=2 (priority low)
    - _Requirements: 7.2, 7.3, 7.4, 7.5, 7.6, 7.7_

  - [ ]* 11.2 Write property tests for action recommendations
    - **Property 14: Action Recommendation - Skill Gap**
    - **Property 15: Action Recommendation - Internship Gap**
    - **Property 16: Action Recommendation - High Risk Resume**
    - **Property 17: Action Recommendation - Mock Interview**
    - **Property 18: Action Recommendation - Recruiter Match**
    - **Validates: Requirements 7.2, 7.3, 7.4, 7.5, 7.6**
    - Test each rule triggers appropriate action

  - [ ]* 11.3 Write property test for action structure validity
    - **Property 19: Action Structure Validity**
    - **Validates: Requirements 7.7**
    - Test all actions have type, title, description, priority fields

- [x] 12. Checkpoint - Verify ML components and business logic
  - Ensure all tests pass, ask the user if questions arise.

- [x] 13. Implement core prediction service
  - [x] 13.1 Create PredictionService class
    - Implement `backend/services/prediction_service.py` with predict_student()
    - Orchestrate: feature engineering → placement prediction → salary prediction → risk calculation → SHAP explanation → LLM summary → action recommendations
    - Store student record, prediction record, audit log entry
    - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5_

  - [ ]* 13.2 Write property test for prediction response completeness
    - **Property 20: Prediction Response Completeness**
    - **Validates: Requirements 8.5**
    - Test response contains all required fields

  - [ ]* 13.3 Write integration test for complete prediction flow
    - Test end-to-end: POST student data → verify DB records → verify response
    - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5_

- [-] 14. Implement configuration management
  - [x] 14.1 Create configuration schema
    - Implement `backend/config.py` with Pydantic Settings
    - Add fields: database_url, redis_url, anthropic_api_key, ml_model_path, secret_key, cors_origins
    - Add validation for required fields
    - _Requirements: 19.1, 19.2, 19.3, 19.4_

  - [x] 14.2 Create configuration file parser and printer
    - Implement parse_config() reading from JSON
    - Implement print_config() with 2-space indentation and sorted keys
    - _Requirements: 19.5, 19.7_

  - [ ]* 14.3 Write property test for configuration round-trip
    - **Property 21: Configuration Round-Trip Preservation**
    - **Validates: Requirements 19.6**
    - Test parse(print(parse(json))) == parse(json)

  - [ ]* 14.4 Write property test for JSON formatting
    - **Property 22: Configuration JSON Formatting**
    - **Validates: Requirements 19.7**
    - Test 2-space indentation and sorted keys

- [x] 15. Implement audit logging
  - [x] 15.1 Create AuditLogger service
    - Implement `backend/services/audit_logger.py` with log_action()
    - Support action types: PREDICT, EXPLAIN, ALERT_SENT
    - Store metadata including model_version for PREDICT actions
    - _Requirements: 14.1, 14.2, 14.3, 14.4, 14.5, 14.6, 14.7_

  - [ ]* 15.2 Write integration test for audit logging
    - Test audit log created for each action type
    - Test metadata includes model_version
    - _Requirements: 14.1, 14.2, 14.3, 14.5_

- [x] 16. Implement FastAPI endpoints
  - [x] 16.1 Create API router and middleware
    - Implement `backend/api/router.py` with all endpoint routes
    - Add CORS middleware with configurable origins
    - Add request logging middleware
    - Add exception handling middleware
    - _Requirements: 21.1, 21.2, 21.3, 21.4, 21.5_

  - [x] 16.2 Implement POST /api/predict endpoint
    - Implement `backend/routes/predict.py` with predict_single()
    - Validate StudentInput schema
    - Call PredictionService.predict_student()
    - Return PredictionResponse
    - Handle errors with appropriate HTTP status codes
    - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5, 8.6, 8.7_

  - [ ]* 16.3 Write property tests for API validation
    - **Property 23: Required Field Validation**
    - **Property 24: Institute Tier Validation**
    - **Property 25: CGPA Validation**
    - **Property 26: Year of Graduation Validation**
    - **Property 27: Non-Negative Value Validation**
    - **Property 28: Validation Error Response Format**
    - **Validates: Requirements 20.1, 20.2, 20.3, 20.4, 20.5, 20.6, 20.7**
    - Test validation errors return HTTP 422 with field-specific messages

  - [x] 16.4 Implement POST /api/batch-score endpoint
    - Implement predict_batch() processing array of students
    - Reject batches > 500 students with HTTP 400
    - Process predictions in parallel with asyncio.gather()
    - Return BatchScoreResponse with results array and summary
    - _Requirements: 9.1, 9.2, 9.3, 9.4, 9.5, 9.6, 9.7_

  - [ ]* 16.5 Write integration test for batch scoring
    - Test batch of 100 students processed correctly
    - Test batch > 500 rejected
    - Test summary statistics correct
    - _Requirements: 9.1, 9.2, 9.5, 9.6_

  - [x] 16.6 Implement GET /api/explain/{student_id} endpoint
    - Implement `backend/routes/explain.py` with get_explanation()
    - Retrieve most recent prediction for student
    - Format SHAP values into waterfall data structure
    - Return ShapExplanationResponse
    - Return HTTP 404 if student not found
    - _Requirements: 10.1, 10.2, 10.3, 10.4, 10.5, 10.6_

  - [x] 16.7 Implement GET /api/alerts endpoint
    - Implement `backend/routes/alerts.py` with get_alerts()
    - Filter by threshold parameter (default "high")
    - Support pagination with limit/offset
    - Return students where risk_level="high" OR emi_affordability>0.5
    - Sort by risk_score descending
    - _Requirements: 11.1, 11.2, 11.3, 11.4, 11.5, 11.6, 11.7_

  - [x] 16.8 Implement GET /api/students endpoint
    - Implement `backend/routes/students.py` with list_students()
    - Support search, sort, order, limit, offset parameters
    - Join with predictions to include latest prediction
    - Return array of students with total_count
    - _Requirements: 12.1, 12.2, 12.3, 12.4, 12.5, 12.6, 12.7_

  - [x] 16.9 Implement GET /api/health endpoint
    - Implement `backend/routes/health.py` with health_check()
    - Verify database connectivity
    - Verify ML model files exist
    - Return HTTP 200 with status "ok" if all checks pass
    - Return HTTP 503 with status "degraded" if any check fails
    - _Requirements: 13.1, 13.2, 13.3, 13.4, 13.5, 13.6_

- [x] 17. Implement rate limiting
  - [x] 17.1 Create rate limiting middleware
    - Implement `backend/middleware/rate_limit.py` using Redis
    - Set limits: POST /api/predict (100/min), POST /api/batch-score (10/min), GET (300/min)
    - Return HTTP 429 when limit exceeded
    - Add X-RateLimit-* headers to all responses
    - _Requirements: 23.1, 23.2, 23.3, 23.4, 23.5, 23.6_

  - [ ]* 17.2 Write integration test for rate limiting
    - Test 101st request returns HTTP 429
    - Test X-RateLimit headers present
    - _Requirements: 23.2, 23.3, 23.5, 23.6_

- [x] 18. Implement error handling and logging
  - [x] 18.1 Create error handling middleware
    - Implement global exception handler returning consistent JSON error format
    - Implement validation exception handler for HTTP 422
    - Add error types: ValidationError, InternalServerError, etc.
    - _Requirements: 22.1, 22.2, 22.3, 22.4, 22.5, 22.6_

  - [x] 18.2 Configure structured logging
    - Set up JSON logging with timestamp, level, logger, message, context
    - Log all API requests with method, path, status, response time
    - Log errors with stack traces
    - _Requirements: 22.1, 22.2, 22.3, 22.4, 22.5, 22.6_

  - [ ]* 18.3 Write unit tests for error handling
    - Test database failure returns HTTP 503
    - Test validation error returns HTTP 422 with field details
    - _Requirements: 8.7_

- [x] 19. Checkpoint - Verify backend API complete
  - Ensure all tests pass, ask the user if questions arise.

- [x] 20. Implement frontend dashboard page
  - [x] 20.1 Create dashboard layout and components
    - Implement `frontend/app/dashboard/page.tsx` with server-side data fetching
    - Create PortfolioHeatmap component (grid with color-coded risk levels)
    - Create RiskScoreCard component (aggregate statistics)
    - Create StudentTable component (sortable, paginated)
    - Create AlertBanner component (red notification for high-risk alerts)
    - _Requirements: 25.1, 25.2, 25.3, 25.5_

  - [x] 20.2 Implement auto-refresh for dashboard
    - Add useEffect with 30-second interval polling /api/students
    - _Requirements: 25.4_

- [x] 21. Implement frontend student detail page
  - [x] 21.1 Create student detail layout and components
    - Implement `frontend/app/student/[id]/page.tsx` with dynamic routing
    - Create RiskScoreCard component (large score with color badge)
    - Create PlacementProbChart component (bar chart with Recharts)
    - Create SalaryRangeCard component (min-max with confidence)
    - _Requirements: 26.1, 26.2, 26.3_

  - [x] 21.2 Create SHAP waterfall visualization
    - Implement ShapWaterfallChart component using Recharts BarChart
    - Color bars: green for positive, red for negative SHAP values
    - Horizontal layout with feature names on Y-axis
    - _Requirements: 26.4_

  - [x] 21.3 Create AI summary and actions panels
    - Implement AISummaryCard component displaying ai_summary text
    - Implement NextBestActionsPanel component with action cards (icon, title, description, priority badge)
    - Implement AuditTrailTimeline component showing historical predictions
    - _Requirements: 26.5, 26.6, 26.7_

- [x] 22. Implement frontend new prediction form
  - [x] 22.1 Create multi-step form
    - Implement `frontend/app/student/new/page.tsx` with 3-step form
    - Step 1: Academic Info (name, course_type, institute_tier, institute_name, cgpa, cgpa_scale, year_of_grad)
    - Step 2: Internship & Skills (internship_count, internship_months, internship_employer_type, certifications, region)
    - Step 3: Loan Details (loan_amount, loan_emi)
    - _Requirements: 27.1_

  - [x] 22.2 Implement form validation and submission
    - Add Zod schema matching Pydantic backend schemas
    - Validate required fields before step progression
    - Display inline validation errors
    - POST to /api/predict on submit
    - Navigate to student detail page on success
    - _Requirements: 27.2, 27.3, 27.4, 27.5, 27.6_

- [x] 23. Implement frontend alerts page
  - [x] 23.1 Create alerts page and components
    - Implement `frontend/app/alerts/page.tsx` with filter bar
    - Create AlertCard component (name, risk badge, risk score, top driver, recommended action)
    - Add acknowledge button functionality
    - _Requirements: 28.1, 28.2, 28.3, 28.4, 28.5_

  - [x] 23.2 Implement auto-refresh for alerts
    - Use SWR with 10-second refresh interval
    - Display unacknowledged alert count badge
    - _Requirements: 28.6_

- [x] 24. Implement Docker containerization
  - [x] 24.1 Create Dockerfiles
    - Create `backend/Dockerfile` with Python 3.11, install dependencies, copy code
    - Create `frontend/Dockerfile` with Node.js 20, build Next.js app
    - Create `docker/postgres/Dockerfile` for PostgreSQL 16
    - _Requirements: 24.1_

  - [x] 24.2 Create docker-compose.yml
    - Define services: postgres, redis, backend, frontend
    - Configure networks and volumes
    - Mount ML models as read-only volume in backend
    - Set environment variables from .env file
    - Configure backend to wait for database availability
    - Expose backend on port 8000, frontend on port 3000
    - _Requirements: 24.1, 24.2, 24.3, 24.4, 24.5_

  - [ ]* 24.3 Write integration test for Docker deployment
    - Test docker-compose up starts all services
    - Test health check endpoint returns 200
    - _Requirements: 24.6_

- [x] 25. Implement bias audit tooling
  - [x] 25.1 Create bias audit script
    - Implement `ml/pipeline/bias_audit.py` with run_bias_audit()
    - Use Fairlearn to compute demographic parity metrics
    - Compute accuracy and selection rate by gender and region groups
    - Flag model if demographic_parity_difference > 0.1
    - Generate report with metric breakdowns
    - _Requirements: 29.1, 29.2, 29.3, 29.4, 29.5, 29.6_

  - [ ]* 25.2 Write unit test for bias audit
    - Test demographic parity calculation
    - Test flagging when threshold exceeded
    - _Requirements: 29.5_

- [x] 26. Final integration and wiring
  - [x] 26.1 Wire all components together
    - Ensure all services communicate correctly
    - Verify database migrations run on startup
    - Verify ML models load correctly
    - Test end-to-end flow: form submission → prediction → display
    - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5_

  - [x] 26.2 Create README and documentation
    - Document setup instructions
    - Document API endpoints
    - Document environment variables
    - Document deployment process

  - [ ]* 26.3 Write end-to-end integration tests
    - Test complete user journey: dashboard → new prediction → student detail → alerts
    - Test batch scoring workflow
    - Test error scenarios

- [x] 27. Final checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation
- Property tests validate universal correctness properties (minimum 100 iterations each)
- Unit tests validate specific examples and edge cases
- Integration tests validate end-to-end workflows
- The system uses Python for backend/ML and TypeScript for frontend
- All property tests must include comment tags: `# Feature: edurisk-ai-placement-intelligence, Property {number}: {property_text}`
