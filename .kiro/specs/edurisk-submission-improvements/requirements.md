# Requirements Document: EduRisk AI Submission Improvements

## Introduction

This document specifies requirements for implementing critical improvements to the EduRisk AI project based on a comprehensive code review by Claude Sonnet 4.6. The EduRisk AI system is an AI-powered placement risk assessment platform for education loan lenders, built for the TenzorX 2026 Poonawalla Fincorp National AI Hackathon.

**Current State**: The project is functionally complete with good architecture (rated 7.5/10) but has critical issues preventing submission readiness.

**Target State**: Submission-ready, portfolio-worthy project (target 9.5/10) with all critical security, functionality, and UX issues resolved.

**Tech Stack**: FastAPI (Python), Next.js 14 (TypeScript), PostgreSQL, Redis, Docker, Groq API for LLM

**Improvement Scope**: 32 tasks across 3 phases (Critical, Important, Optional) addressing ML model availability, authentication, documentation accuracy, UX improvements, testing, performance optimization, and data integration.

## Glossary

- **Backend**: The FastAPI Python application providing REST API endpoints
- **Frontend**: The Next.js 14 TypeScript application providing the user interface
- **ML_Pipeline**: The machine learning training and inference system using XGBoost and SHAP
- **Docker_Container**: A containerized service (backend, frontend, postgres, redis)
- **Health_Check**: The `/api/health` endpoint that verifies system readiness
- **API_Key**: A secret token used for authenticating API requests via X-API-Key header
- **Audit_Logger**: The service that records all prediction and explanation actions to the audit_logs table
- **SHAP_Explainer**: The service that computes feature attributions for ML predictions
- **Risk_Score**: A 0-100 composite score indicating loan default risk (higher = riskier)
- **Placement_Model**: XGBoost classifier predicting student placement probability at 3m, 6m, 12m windows
- **Alembic**: The database migration tool for PostgreSQL schema management
- **Navigation_Bar**: The persistent UI component providing links between application pages
- **Batch_Scoring**: The parallel processing of multiple student predictions in a single API request
- **Empty_State**: The UI displayed when no data exists, providing guidance to users
- **EMI_Affordability**: The ratio of expected loan EMI to predicted salary (lower = better)
- **Risk_Gauge**: A circular visualization showing risk score from 0-100 with color zones
- **JWT_Token**: JSON Web Token used for stateless authentication in OAuth2 Password Flow
- **OAuth2_Flow**: Authentication mechanism using username/password to obtain JWT tokens
- **N+1_Query**: Database anti-pattern where multiple queries are executed instead of a single optimized query
- **Kaggle_Dataset**: Real-world datasets from Kaggle used for training ML models
- **Feature_Weights**: Hyperparameters in FeatureEngineer controlling feature importance calculations
- **Rate_Limiting**: Mechanism to prevent API abuse by limiting requests per time window
- **Background_Task**: Asynchronous task execution that doesn't block API response

## Requirements

### Requirement 1: ML Model Availability at Startup

**User Story:** As a hackathon judge, I want the system to work immediately after running `docker-compose up`, so that I can evaluate the project without manual setup steps.

#### Acceptance Criteria

1. WHEN THE Docker_Container starts for the first time, THE ML_Pipeline SHALL check for the existence of all required model files
2. IF placement_model_3m.pkl does not exist, THEN THE ML_Pipeline SHALL automatically generate synthetic training data
3. IF placement_model_3m.pkl does not exist, THEN THE ML_Pipeline SHALL train all four models (placement_model_3m.pkl, placement_model_6m.pkl, placement_model_12m.pkl, salary_model.pkl)
4. THE ML_Pipeline SHALL complete model training within 120 seconds
5. WHEN model training completes successfully, THE Backend SHALL log "✅ ML models trained successfully" to stdout
6. WHEN all model files exist, THE Backend SHALL log "✅ ML models found and ready" to stdout
7. WHEN THE Health_Check endpoint is called after startup, THE Backend SHALL return `ml_models: available` in the response
8. THE Backend SHALL NOT start the FastAPI server until all model files are confirmed to exist

### Requirement 2: API Key Authentication

**User Story:** As a security-conscious lender, I want all API endpoints to require authentication, so that unauthorized users cannot access sensitive student data or trigger predictions.

#### Acceptance Criteria

1. THE Backend SHALL require an X-API-Key header for all API requests except public endpoints
2. THE Backend SHALL define public endpoints as: /api/health, /docs, /redoc, /openapi.json, /
3. WHEN a request to a protected endpoint lacks an X-API-Key header, THE Backend SHALL return HTTP 401 with message "Missing API key. Include X-API-Key header in your request."
4. WHEN a request provides an X-API-Key header that does not match the configured API_KEY environment variable, THE Backend SHALL return HTTP 401 with message "Invalid API key"
5. WHEN a request provides a valid X-API-Key header, THE Backend SHALL process the request normally
6. IF the API_KEY environment variable is not configured, THEN THE Backend SHALL log a warning "API_KEY not configured - authentication disabled" and allow all requests
7. THE Backend SHALL implement authentication using a middleware class named ApiKeyMiddleware
8. WHEN an invalid API key is attempted, THE Backend SHALL log a warning including the client IP address

### Requirement 3: Environment Variable Documentation Accuracy

**User Story:** As a developer setting up the project, I want the README instructions to match the actual environment variables used by the code, so that I can configure the system correctly on the first attempt.

#### Acceptance Criteria

1. THE README SHALL NOT reference ANTHROPIC_API_KEY in any setup instructions
2. THE README SHALL document LLM_API_KEY as the environment variable for LLM integration
3. THE README SHALL document LLM_PROVIDER as the environment variable for selecting the LLM provider (groq or anthropic)
4. THE README SHALL document that LLM integration is optional and the system degrades gracefully without an API key
5. THE README SHALL provide an example .env snippet that exactly matches the .env.example file
6. THE README SHALL document the API_KEY environment variable for API authentication
7. THE README SHALL document the DEBUG environment variable and explain when to use DEBUG=True vs DEBUG=False

### Requirement 4: Database Migration Configuration

**User Story:** As a developer running database migrations inside Docker, I want Alembic to use the correct database URL from environment variables, so that migrations succeed without manual configuration.

#### Acceptance Criteria

1. WHEN Alembic runs inside the Docker_Container, THE Backend SHALL read the DATABASE_URL from environment variables
2. THE Backend SHALL override the alembic.ini sqlalchemy.url setting with the DATABASE_URL from environment
3. IF the DATABASE_URL cannot be loaded from environment, THEN THE Backend SHALL log a warning and fall back to the alembic.ini value
4. WHEN `alembic upgrade head` is executed inside Docker, THE Backend SHALL successfully apply migrations to the postgres service
5. THE Backend SHALL NOT contain any hardcoded localhost database URLs in alembic configuration

### Requirement 5: Production Debug Mode Configuration

**User Story:** As a production deployer, I want the system to default to DEBUG=False, so that stack traces and sensitive error details are not exposed to API clients.

#### Acceptance Criteria

1. THE .env.example file SHALL set DEBUG=False as the default value
2. THE docker-compose.yml file SHALL default DEBUG to False when the environment variable is not provided
3. THE .env.example file SHALL include a comment explaining "Set to True only for local development"
4. WHEN DEBUG=False, THE Backend SHALL NOT include stack traces in HTTP error responses
5. WHEN DEBUG=True, THE Backend SHALL include detailed stack traces in HTTP error responses for debugging

### Requirement 6: Audit Logging for Explanation Requests

**User Story:** As a compliance officer, I want all SHAP explanation requests to be logged to the audit trail, so that I can track which predictions were reviewed and when.

#### Acceptance Criteria

1. WHEN a request is made to /api/explain/{student_id}, THE Audit_Logger SHALL record an EXPLAIN action to the audit_logs table
2. THE Audit_Logger SHALL record the student_id associated with the explanation request
3. THE Audit_Logger SHALL record the prediction_id associated with the explanation request
4. THE Audit_Logger SHALL record the performed_by field (initially "api_user", to be replaced with actual user ID when authentication is implemented)
5. THE Audit_Logger SHALL record the timestamp of the explanation request
6. WHEN querying the audit_logs table, THE Backend SHALL return EXPLAIN actions alongside PREDICT and ALERT_SENT actions

### Requirement 7: Navigation Bar Component

**User Story:** As a loan officer using the application, I want a persistent navigation bar on all pages, so that I can easily move between Dashboard, Alerts, New Student, and API Documentation without using browser back buttons.

#### Acceptance Criteria

1. THE Frontend SHALL display a navigation bar at the top of all pages
2. THE Navigation_Bar SHALL include links to: Dashboard (/dashboard), Alerts (/alerts), New Student (/student/new), API Docs (/docs)
3. THE Navigation_Bar SHALL highlight the currently active page with a distinct visual style
4. WHEN the Alerts page has high-risk alerts, THE Navigation_Bar SHALL display a badge showing the count of high-risk alerts
5. THE Navigation_Bar SHALL be responsive and display correctly on mobile devices (viewport width < 768px)
6. THE Frontend SHALL wrap all page components with a Layout component that includes the Navigation_Bar
7. THE Navigation_Bar SHALL include the EduRisk AI logo or title on the left side

### Requirement 8: Dashboard New Prediction Button

**User Story:** As a loan officer viewing the dashboard, I want a prominent button to add a new student prediction, so that I can discover and access the student creation form without guessing the URL.

#### Acceptance Criteria

1. THE Frontend SHALL display an "Add Student" button in the dashboard header
2. WHEN the "Add Student" button is clicked, THE Frontend SHALL navigate to /student/new
3. THE "Add Student" button SHALL include an appropriate icon (e.g., plus icon)
4. THE "Add Student" button SHALL be visually prominent with primary button styling
5. THE "Add Student" button SHALL be positioned in the top-right area of the dashboard header

### Requirement 9: Batch Scoring Database Session Safety

**User Story:** As a system administrator processing batch predictions, I want each student in a batch to use an independent database session, so that concurrent processing does not corrupt data or cause race conditions.

#### Acceptance Criteria

1. WHEN processing a batch prediction request, THE Backend SHALL create a separate database session for each student in the batch
2. THE Backend SHALL NOT share a single database session across multiple concurrent student predictions
3. THE Backend SHALL use asyncio.gather() to process batch items in parallel
4. WHEN a batch item fails, THE Backend SHALL return success=False for that item without affecting other items in the batch
5. WHEN a batch item succeeds, THE Backend SHALL return success=True with the prediction data
6. THE Backend SHALL close each database session after processing its corresponding student

### Requirement 10: Risk Calculator Unit Tests

**User Story:** As a developer maintaining the risk calculation logic, I want comprehensive unit tests for all risk calculator functions, so that I can confidently refactor code and catch regressions.

#### Acceptance Criteria

1. THE Backend SHALL include a test file backend/services/test_risk_calculator_unit.py
2. THE Backend SHALL test calculate_risk_score() with various probability combinations (high, medium, low placement probabilities)
3. THE Backend SHALL test assign_risk_level() with boundary values (0, 33, 34, 66, 67, 100)
4. THE Backend SHALL test calculate_emi_affordability() with edge cases (zero salary, zero EMI, very high EMI)
5. THE Backend SHALL test action recommender rules for each risk level (low, medium, high)
6. WHEN pytest is executed, THE Backend SHALL run all risk calculator tests and report pass/fail status
7. THE Backend SHALL achieve 100% code coverage for risk_calculator.py functions

### Requirement 11: Salary Card EMI Context

**User Story:** As a loan officer reviewing a student's predicted salary, I want to see the EMI affordability percentage alongside the salary range, so that I can immediately assess loan repayment feasibility.

#### Acceptance Criteria

1. THE Frontend SHALL display the EMI affordability percentage below the salary range in the SalaryRangeCard component
2. WHEN EMI affordability is less than 30%, THE Frontend SHALL display the percentage in green with a "Good" label
3. WHEN EMI affordability is between 30% and 50%, THE Frontend SHALL display the percentage in amber with a "Moderate" label
4. WHEN EMI affordability is greater than 50%, THE Frontend SHALL display the percentage in red with a "High Risk" label
5. THE Frontend SHALL include a tooltip explaining "EMI Affordability: Percentage of expected salary required for loan repayment. Lower is better."
6. THE Frontend SHALL format the affordability percentage with one decimal place (e.g., "32.5%")

### Requirement 12: Risk Score Gauge Visualization

**User Story:** As a loan officer viewing a student's risk assessment, I want a visual gauge showing the risk score from 0-100, so that I can intuitively understand the risk level without reading numbers.

#### Acceptance Criteria

1. THE Frontend SHALL display a circular gauge visualization in the RiskScoreDisplay component
2. THE Risk_Gauge SHALL show the risk score from 0 to 100 on a circular arc
3. THE Risk_Gauge SHALL use green color for scores 0-33 (low risk zone)
4. THE Risk_Gauge SHALL use amber color for scores 34-66 (medium risk zone)
5. THE Risk_Gauge SHALL use red color for scores 67-100 (high risk zone)
6. THE Risk_Gauge SHALL animate from 0 to the actual score when the component loads
7. THE Risk_Gauge SHALL be responsive and display correctly on mobile devices
8. THE Risk_Gauge SHALL display the numeric risk score in the center of the gauge

### Requirement 13: Dashboard Empty State

**User Story:** As a first-time user viewing an empty dashboard, I want a helpful message and call-to-action button, so that I understand how to get started with the system.

#### Acceptance Criteria

1. WHEN no students exist in the database, THE Frontend SHALL display an Empty_State component instead of an empty table
2. THE Empty_State SHALL include a friendly message such as "No students yet. Add your first student to get started."
3. THE Empty_State SHALL include an "Add Your First Student" button that links to /student/new
4. THE Empty_State SHALL include an icon or illustration representing an empty state
5. THE Empty_State SHALL be centered vertically and horizontally in the dashboard content area
6. WHEN at least one student exists, THE Frontend SHALL display the normal student table instead of the Empty_State

### Requirement 14: CSV Batch Upload UI

**User Story:** As a loan officer with a spreadsheet of student applications, I want to upload a CSV file for batch scoring, so that I can process multiple students efficiently without manual data entry.

#### Acceptance Criteria

1. THE Frontend SHALL provide a page at /student/batch for CSV batch upload
2. THE Frontend SHALL include a file upload component accepting .csv files
3. WHEN a CSV file is selected, THE Frontend SHALL parse the file and display a preview table of students
4. THE Frontend SHALL validate that the CSV contains required columns (name, course_type, institute_tier, cgpa, year_of_grad, loan_amount, loan_emi)
5. THE Frontend SHALL include a "Submit Batch" button that calls POST /api/batch-score with the parsed students
6. WHILE the batch is processing, THE Frontend SHALL display a progress indicator
7. WHEN the batch completes, THE Frontend SHALL display a results summary showing success count, failure count, and any error messages
8. THE Frontend SHALL limit batch uploads to 500 students per request

### Requirement 15: Risk Score Trend Chart

**User Story:** As a loan officer monitoring a student over time, I want to see a line chart of risk score history, so that I can identify whether the student's risk is improving or declining.

#### Acceptance Criteria

1. THE Frontend SHALL display a line chart on the student detail page showing risk score over time
2. THE Frontend SHALL fetch prediction history from GET /api/students/{id}/predictions
3. THE Frontend SHALL plot risk_score on the Y-axis and created_at timestamp on the X-axis
4. THE Frontend SHALL use green line color when the trend is improving (risk decreasing)
5. THE Frontend SHALL use red line color when the trend is declining (risk increasing)
6. THE Frontend SHALL display a message "No historical data" when only one prediction exists
7. THE Frontend SHALL include axis labels "Risk Score" and "Date"

### Requirement 16: Docker Multi-Stage Build Optimization

**User Story:** As a DevOps engineer deploying the application, I want the backend Docker image to be under 1 GB, so that deployments are faster and storage costs are reduced.

#### Acceptance Criteria

1. THE Docker_Container SHALL use a multi-stage build with separate builder and runtime stages
2. THE builder stage SHALL install gcc, g++, libpq-dev, and all Python dependencies
3. THE runtime stage SHALL copy only the installed Python packages from the builder stage
4. THE runtime stage SHALL install only runtime dependencies (libpq5) without build tools
5. THE Docker_Container SHALL produce a final image size less than 1 GB
6. THE Docker_Container SHALL cache Python dependency layers to speed up rebuilds
7. WHEN the Dockerfile is rebuilt without code changes, THE Docker_Container SHALL reuse cached dependency layers

### Requirement 17: Student Table Pagination

**User Story:** As a loan officer managing a portfolio of more than 100 students, I want pagination controls on the student table, so that I can view all students without performance degradation.

#### Acceptance Criteria

1. THE Frontend SHALL display pagination controls below the student table
2. THE Frontend SHALL include "Previous" and "Next" buttons for navigating pages
3. THE Frontend SHALL include a page size selector with options: 20, 50, 100 students per page
4. THE Frontend SHALL display the current page number and total page count (e.g., "Page 2 of 5")
5. THE Frontend SHALL display the total student count (e.g., "Showing 21-40 of 237 students")
6. WHEN the "Next" button is clicked, THE Frontend SHALL fetch the next page of students from the API
7. WHEN the page size is changed, THE Frontend SHALL reset to page 1 and fetch students with the new limit

### Requirement 18: API Integration Tests

**User Story:** As a developer ensuring API reliability, I want automated integration tests for all endpoints, so that I can detect breaking changes before deployment.

#### Acceptance Criteria

1. THE Backend SHALL include a test file backend/tests/test_api_integration.py
2. THE Backend SHALL test POST /api/predict with valid student data and verify HTTP 200 response
3. THE Backend SHALL test POST /api/predict with invalid student data and verify HTTP 400 response
4. THE Backend SHALL test GET /api/students and verify the response contains a list of students
5. THE Backend SHALL test GET /api/alerts and verify the response contains high-risk alerts
6. THE Backend SHALL test GET /api/explain/{student_id} and verify the response contains SHAP values
7. THE Backend SHALL test GET /api/health and verify ml_models status is "available"
8. THE Backend SHALL use FastAPI TestClient for all integration tests
9. WHEN pytest is executed, THE Backend SHALL run all integration tests against a test database

## Parser and Serializer Requirements

### Requirement 19: CSV Student Data Parser

**User Story:** As a developer implementing batch upload, I want a robust CSV parser for student data, so that users can upload spreadsheets without format errors causing silent failures.

#### Acceptance Criteria

1. WHEN a CSV file is provided to the Parser, THE Backend SHALL parse each row into a StudentCreate object
2. WHEN a CSV row has missing required fields, THE Parser SHALL return a descriptive error indicating which field is missing
3. WHEN a CSV row has invalid data types (e.g., text in cgpa field), THE Parser SHALL return a descriptive error indicating the type mismatch
4. THE Backend SHALL include a Pretty_Printer that formats StudentCreate objects back into CSV rows
5. FOR ALL valid StudentCreate objects, parsing the CSV then printing then parsing SHALL produce an equivalent object (round-trip property)
6. THE Parser SHALL handle CSV files with or without a header row
7. THE Parser SHALL handle CSV files with quoted fields containing commas

## Property-Based Testing Guidance

The following requirements are well-suited for property-based testing:

- **Requirement 10 (Risk Calculator)**: Use property-based tests to verify invariants like `0 <= risk_score <= 100` and `risk_level` matches score ranges for all possible probability combinations
- **Requirement 19 (CSV Parser)**: Use property-based tests for the round-trip property (parse → print → parse produces equivalent object)
- **Requirement 9 (Batch Scoring)**: Use property-based tests to verify that batch results are independent of processing order (confluence property)

The following requirements should use integration tests with representative examples:

- **Requirement 1 (ML Model Availability)**: Integration test with 1-2 examples (first boot, subsequent boot)
- **Requirement 2 (API Authentication)**: Integration test with 3 examples (valid key, invalid key, missing key)
- **Requirement 7 (Navigation Bar)**: Manual UI testing or E2E test with 1 example per page

## Security and Authentication Requirements

### Requirement 20: JWT OAuth2 Authentication

**User Story:** As a fintech platform operator, I want robust user authentication with JWT tokens, so that only authorized users can access sensitive student risk data and predictions.

#### Acceptance Criteria

1. THE Backend SHALL implement OAuth2 Password Flow with JWT token generation
2. THE Backend SHALL provide a POST /api/auth/login endpoint accepting username and password
3. WHEN valid credentials are provided, THE Backend SHALL return an access_token (JWT) and token_type "bearer"
4. THE Backend SHALL sign JWT tokens with a SECRET_KEY from environment variables
5. THE Backend SHALL set JWT token expiration to 24 hours
6. THE Backend SHALL provide a POST /api/auth/refresh endpoint for token renewal
7. THE Backend SHALL validate JWT tokens on all protected endpoints using a dependency
8. WHEN an invalid or expired JWT is provided, THE Backend SHALL return HTTP 401 with message "Invalid or expired token"
9. THE Backend SHALL extract user information from JWT payload and pass it to route handlers
10. THE Backend SHALL NOT log JWT tokens or passwords in any log output

### Requirement 21: Secure Database Credentials

**User Story:** As a security engineer, I want all database credentials to be managed through environment variables, so that no secrets are hardcoded in version control.

#### Acceptance Criteria

1. THE docker-compose.yml file SHALL NOT contain any hardcoded passwords
2. THE docker-compose.yml file SHALL reference ${POSTGRES_PASSWORD} from environment variables
3. THE docker-compose.yml file SHALL reference ${POSTGRES_USER} from environment variables
4. THE docker-compose.yml file SHALL reference ${POSTGRES_DB} from environment variables
5. THE .env.example file SHALL include placeholder values for all database credentials
6. THE .env.example file SHALL include comments warning against committing real credentials
7. THE .gitignore file SHALL include .env to prevent accidental credential commits

### Requirement 22: Strict CORS Configuration

**User Story:** As a security engineer, I want CORS to be strictly configured for known frontend domains, so that unauthorized origins cannot access the API.

#### Acceptance Criteria

1. THE Backend SHALL configure CORS_ORIGINS from environment variables
2. THE Backend SHALL NOT use wildcard (*) CORS origins in production
3. THE Backend SHALL validate CORS_ORIGINS is a comma-separated list of full URLs
4. THE Backend SHALL log a warning if CORS_ORIGINS contains a wildcard
5. THE .env.example file SHALL provide example CORS_ORIGINS with production and development URLs
6. WHEN a request comes from an unauthorized origin, THE Backend SHALL reject it with CORS error

### Requirement 23: Frontend Login Portal

**User Story:** As a loan officer, I want a secure login screen to access the application, so that my credentials protect sensitive student data.

#### Acceptance Criteria

1. THE Frontend SHALL display a login page at /login as the default route for unauthenticated users
2. THE Frontend SHALL include username and password input fields with appropriate validation
3. WHEN invalid credentials are submitted, THE Frontend SHALL display a user-friendly error message
4. WHEN valid credentials are submitted, THE Frontend SHALL store the JWT token securely
5. THE Frontend SHALL redirect authenticated users to /dashboard
6. THE Frontend SHALL include a "Forgot Password" link (can be non-functional for MVP)
7. THE Frontend SHALL display the EduRisk AI logo and branding on the login page
8. THE Frontend SHALL validate form inputs before submission (non-empty fields)

### Requirement 24: Frontend Auth State Management

**User Story:** As a frontend developer, I want centralized authentication state management, so that all API requests include valid JWT tokens automatically.

#### Acceptance Criteria

1. THE Frontend SHALL store JWT tokens in httpOnly cookies OR secure localStorage
2. THE Frontend SHALL create an API client with an interceptor that attaches Authorization: Bearer {token} to all requests
3. WHEN a 401 response is received, THE Frontend SHALL redirect to /login and clear stored tokens
4. THE Frontend SHALL provide a logout function that clears tokens and redirects to /login
5. THE Frontend SHALL display user information (username) in the navigation bar when authenticated
6. THE Frontend SHALL implement a useAuth hook for accessing authentication state
7. THE Frontend SHALL protect routes by redirecting unauthenticated users to /login

## Data and Performance Requirements

### Requirement 25: Real Kaggle Data Integration

**User Story:** As a data scientist, I want the ML pipeline to support real Kaggle datasets, so that predictions are based on actual placement and salary data rather than purely synthetic data.

#### Acceptance Criteria

1. THE ML_Pipeline SHALL accept CSV files from Kaggle datasets as training input
2. THE ML_Pipeline SHALL document the expected Kaggle dataset schemas in ml/data/README.md
3. THE ML_Pipeline SHALL validate incoming CSV files match the expected schema
4. THE ML_Pipeline SHALL merge synthetic data with real Kaggle data when both are available
5. THE ML_Pipeline SHALL log the data source (synthetic, kaggle, or mixed) in training metrics
6. THE ML_Pipeline SHALL handle missing columns in Kaggle data with appropriate defaults
7. THE ML_Pipeline SHALL provide a script ml/data/download_kaggle.py for automated dataset download

### Requirement 26: N+1 Query Optimization

**User Story:** As a system administrator, I want the dashboard to load quickly even with 100+ students, so that loan officers have a responsive user experience.

#### Acceptance Criteria

1. THE Backend SHALL use SQLAlchemy joinedload() for fetching students with their predictions
2. THE Backend SHALL NOT execute separate queries for each student's predictions (N+1 pattern)
3. THE Backend SHALL use selectinload() for loading related audit logs when needed
4. WHEN fetching the dashboard heatmap data, THE Backend SHALL execute at most 2 database queries
5. THE Backend SHALL complete GET /api/students requests in under 500ms for 100 students
6. THE Backend SHALL log slow queries (>100ms) with query details for optimization
7. THE Backend SHALL include database query profiling in DEBUG mode

### Requirement 27: Async SHAP Computation for Batch Requests

**User Story:** As a loan officer uploading a batch of 100 students, I want the API to respond quickly, so that I don't experience timeouts waiting for SHAP explanations.

#### Acceptance Criteria

1. WHEN processing POST /api/batch-score, THE Backend SHALL compute SHAP values asynchronously using BackgroundTasks
2. THE Backend SHALL return prediction results immediately without waiting for SHAP computation
3. THE Backend SHALL set shap_values to null in the initial response for batch requests
4. THE Backend SHALL provide a GET /api/predictions/{id}/shap endpoint to retrieve SHAP values once computed
5. THE Backend SHALL complete POST /api/batch-score in under 5 seconds for 100 students
6. THE Backend SHALL log SHAP computation time separately from prediction time
7. THE Backend SHALL handle SHAP computation failures gracefully without affecting prediction results

### Requirement 28: Feature Engineering Configuration

**User Story:** As a data scientist, I want feature engineering weights to be configurable, so that I can tune hyperparameters without modifying Python code.

#### Acceptance Criteria

1. THE ML_Pipeline SHALL load feature weights from ml/pipeline/config.json
2. THE config.json file SHALL include weights for internship_score, certification_score, and regional_adjustment
3. THE FeatureEngineer class SHALL NOT contain hardcoded weight values (e.g., count * 0.4)
4. WHEN config.json is missing, THE ML_Pipeline SHALL use default weights and log a warning
5. THE ML_Pipeline SHALL validate config.json schema on startup
6. THE ML_Pipeline SHALL log the loaded configuration values at INFO level
7. THE config.json file SHALL include comments explaining each weight parameter

## Testing and Quality Requirements

### Requirement 29: Mock LLM Response Tests

**User Story:** As a developer, I want tests that mock LLM API responses, so that I can verify the system degrades gracefully when the LLM provider is unavailable.

#### Acceptance Criteria

1. THE Backend SHALL include test file backend/tests/test_llm_service.py
2. THE Backend SHALL test LLM timeout scenarios with mocked responses
3. THE Backend SHALL test LLM rate limit errors (HTTP 429) with appropriate backoff
4. THE Backend SHALL test LLM API key errors (HTTP 401) with fallback behavior
5. WHEN LLM service fails, THE Backend SHALL return a generic fallback message
6. THE Backend SHALL NOT fail prediction requests when LLM service is unavailable
7. THE Backend SHALL log LLM failures at WARNING level without exposing API keys

### Requirement 30: Groq API Rate Limiting

**User Story:** As a system administrator, I want the application to handle Groq API rate limits gracefully, so that temporary rate limit errors don't cause prediction failures.

#### Acceptance Criteria

1. THE Backend SHALL implement exponential backoff for Groq API rate limit errors (HTTP 429)
2. THE Backend SHALL retry failed Groq requests up to 3 times with increasing delays
3. THE Backend SHALL wait for the duration specified in Retry-After header if present
4. WHEN all retries are exhausted, THE Backend SHALL return a fallback AI summary
5. THE Backend SHALL log rate limit events with timestamp and retry count
6. THE Backend SHALL track rate limit metrics for monitoring
7. THE Backend SHALL NOT retry on authentication errors (HTTP 401)

## Documentation and Deployment Requirements

### Requirement 31: Vercel Deployment Guide

**User Story:** As a hackathon participant, I want clear instructions for deploying the frontend to Vercel, so that I can provide a live demo URL to judges.

#### Acceptance Criteria

1. THE DEPLOYMENT_GUIDE.md file SHALL include a "Vercel Deployment" section
2. THE guide SHALL provide step-by-step instructions for connecting a GitHub repository to Vercel
3. THE guide SHALL document required environment variables for Vercel (NEXT_PUBLIC_API_URL, NEXT_PUBLIC_API_KEY)
4. THE guide SHALL explain how to configure the backend API URL for production
5. THE guide SHALL include troubleshooting steps for common Vercel deployment issues
6. THE guide SHALL provide an estimated deployment time (5 minutes)
7. THE guide SHALL include a link to Vercel's official Next.js deployment documentation

### Requirement 32: Mock Alert Notification System

**User Story:** As a product manager, I want to demonstrate alert notification capabilities, so that judges can see how the system would notify loan officers of high-risk students.

#### Acceptance Criteria

1. THE Backend SHALL include a service backend/services/alert_service.py
2. WHEN a high-risk prediction is created (risk_score >= 67), THE Backend SHALL trigger an alert notification
3. THE Backend SHALL log alert notifications to stdout in format: "ALERT: SMS sent to [PHONE] for student [NAME] (Risk: [SCORE])"
4. THE Backend SHALL log alert notifications to the audit_logs table with action "ALERT_SENT"
5. THE Backend SHALL include placeholder phone numbers in student records for demo purposes
6. THE Backend SHALL provide a mock_send_sms() function with Twilio-compatible signature
7. THE Backend SHALL provide a mock_send_email() function with SendGrid-compatible signature
8. THE Backend SHALL include comments indicating where real Twilio/SendGrid integration would be added

## Implementation Notes

### Phase 1: Critical Fixes (Requirements 1-6, 20-22, 25-26)
These requirements MUST be completed before submission. They address broken functionality, security vulnerabilities, documentation accuracy, authentication, and performance issues.

**Estimated Effort**: 8-12 hours

### Phase 2: Important Improvements (Requirements 7-13, 23-24, 27-30)
These requirements SHOULD be completed for a polished submission. They address UX issues, testing gaps, feature discoverability, auth UI, and performance optimization.

**Estimated Effort**: 10-14 hours

### Phase 3: Optional Enhancements (Requirements 14-19, 31-32)
These requirements are OPTIONAL but significantly improve the project's professionalism and scalability demonstration.

**Estimated Effort**: 6-9 hours

### Technology Constraints

1. MUST use Groq API (not OpenAI or Anthropic) for LLM integration
2. MUST maintain Docker Compose setup for all services
3. MUST use FastAPI for backend (no framework changes)
4. MUST use Next.js 14 for frontend (no framework changes)
5. MUST use PostgreSQL for database (no database changes)
6. MUST use XGBoost for ML models (no model framework changes)

### Success Criteria

The project is submission-ready when:
- All Phase 1 requirements (1-6, 20-22, 25-26) are complete
- At least 7 of 11 Phase 2 requirements (7-13, 23-24, 27-30) are complete
- Health check passes on first boot without manual intervention
- JWT authentication protects all endpoints
- Login portal works with secure token management
- README setup instructions are accurate and complete
- Navigation works across all pages
- Dashboard loads in <500ms for 100+ students (N+1 queries fixed)
- Batch scoring completes in <5 seconds for 100 students
- No hardcoded secrets in docker-compose.yml
- CORS is strictly configured
- No critical security issues remain
- Code quality demonstrates professional best practices
- All tests pass (unit, property-based, integration, mock LLM)
