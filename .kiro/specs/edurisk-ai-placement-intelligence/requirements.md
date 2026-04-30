# Requirements Document: EduRisk AI - Placement Risk Intelligence

## Introduction

EduRisk AI is a Placement Risk Intelligence engine for education loan lenders participating in the TenzorX 2026 Poonawalla Fincorp National AI Hackathon. The system predicts student placement probability within 3, 6, and 12 months post-graduation, estimates expected starting salary ranges, calculates placement risk scores, and suggests actionable interventions to improve student outcomes. The system supports lending decisions and portfolio monitoring but does NOT automate credit approvals. All predictions are logged for audit compliance with RBI regulations.

## Glossary

- **System**: The EduRisk AI Placement Risk Intelligence engine
- **Placement_Predictor**: The ML component that predicts placement timeline probabilities
- **Salary_Estimator**: The ML component that predicts salary ranges
- **Risk_Calculator**: The component that computes composite risk scores
- **Explainability_Engine**: The SHAP-based component that generates feature attributions
- **LLM_Summarizer**: The Claude API integration that generates natural language risk summaries
- **Action_Recommender**: The rule-based engine that suggests next-best actions
- **Audit_Logger**: The component that records all predictions and actions for compliance
- **Student_Profile**: A record containing academic, internship, and loan data for a student
- **Loan_Officer**: A user who reviews individual student risk before loan disbursement
- **Portfolio_Manager**: A user who monitors batches of students and views risk distributions
- **Risk_Score**: A composite score from 0-100 where higher values indicate higher placement risk
- **Risk_Level**: A categorical classification (Low/Medium/High) derived from Risk_Score
- **SHAP_Values**: Feature attribution values explaining model predictions
- **LPA**: Lakhs Per Annum, the Indian convention for expressing annual salary
- **Placement_Timeline**: The predicted time window (3/6/12 months) for student placement
- **High_Risk_Student**: A student with Risk_Level = "high" or EMI-to-salary ratio > 0.5
- **Model_Version**: A version identifier for the ML model used in prediction
- **Demographic_Features**: Gender, religion, caste, and state of origin (EXCLUDED from ML models)
- **Institute_Tier**: A classification (1/2/3) indicating institute quality and placement track record
- **Internship_Score**: A derived metric combining internship count, duration, and employer type
- **EMI_Affordability**: The ratio of loan EMI to predicted salary
- **Batch_Scoring**: Processing multiple student predictions in a single API request (max 500)
- **Confidence_Interval**: The range around salary prediction indicating uncertainty
- **Next_Best_Action**: A recommended intervention (skill-up, resume coaching, mock interview, recruiter match)

## Requirements

### Requirement 1: Placement Timeline Prediction

**User Story:** As a Loan Officer, I want to know when a student is likely to get placed after graduation, so that I can assess loan repayment risk.

#### Acceptance Criteria

1. WHEN a Student_Profile is provided, THE Placement_Predictor SHALL generate probability scores for placement within 3 months, 6 months, and 12 months post-graduation
2. THE Placement_Predictor SHALL assign a Placement_Timeline label of "placed_3m", "placed_6m", "placed_12m", or "high_risk" based on the highest probability threshold
3. THE Placement_Predictor SHALL use three separate XGBoost classifiers trained for 3-month, 6-month, and 12-month placement windows
4. THE Placement_Predictor SHALL output probability values as decimals between 0.0000 and 1.0000 with four decimal precision
5. THE Placement_Predictor SHALL exclude Demographic_Features (gender, religion, caste, state of origin) from all model inputs
6. WHEN probability scores for all three time windows are below 0.50, THE Placement_Predictor SHALL assign the label "high_risk"

### Requirement 2: Salary Range Estimation

**User Story:** As a Loan Officer, I want to know the expected salary range for a student, so that I can evaluate their loan repayment capacity.

#### Acceptance Criteria

1. WHEN a Student_Profile is provided, THE Salary_Estimator SHALL predict a minimum salary, maximum salary, and confidence percentage
2. THE Salary_Estimator SHALL express all salary values in LPA (Lakhs Per Annum) with two decimal precision
3. THE Salary_Estimator SHALL calculate salary_min as predicted_salary minus 1.5 times the standard deviation
4. THE Salary_Estimator SHALL calculate salary_max as predicted_salary plus 1.5 times the standard deviation
5. THE Salary_Estimator SHALL calculate salary_confidence as the Confidence_Interval width expressed as a percentage of the predicted salary
6. THE Salary_Estimator SHALL use a Ridge Regression model with StandardScaler preprocessing
7. THE Salary_Estimator SHALL exclude Demographic_Features from all model inputs

### Requirement 3: Placement Risk Score Calculation

**User Story:** As a Portfolio Manager, I want a single risk score for each student, so that I can quickly prioritize high-risk cases.

#### Acceptance Criteria

1. WHEN placement probabilities are generated, THE Risk_Calculator SHALL compute a Risk_Score as an integer from 0 to 100
2. THE Risk_Calculator SHALL derive Risk_Score using the formula: 100 minus (weighted average of placement probabilities times 100)
3. THE Risk_Calculator SHALL apply weights of 0.5 for 3-month probability, 0.3 for 6-month probability, and 0.2 for 12-month probability
4. WHEN Risk_Score is between 0 and 33, THE Risk_Calculator SHALL assign Risk_Level as "low"
5. WHEN Risk_Score is between 34 and 66, THE Risk_Calculator SHALL assign Risk_Level as "medium"
6. WHEN Risk_Score is between 67 and 100, THE Risk_Calculator SHALL assign Risk_Level as "high"

### Requirement 4: EMI Affordability Assessment

**User Story:** As a Loan Officer, I want to know if the student's predicted salary can support their loan EMI, so that I can assess repayment risk.

#### Acceptance Criteria

1. WHEN a Student_Profile includes loan_emi and a salary prediction is available, THE Risk_Calculator SHALL compute EMI_Affordability ratio
2. THE Risk_Calculator SHALL calculate EMI_Affordability as monthly loan_emi divided by monthly predicted salary
3. THE Risk_Calculator SHALL convert annual salary in LPA to monthly salary by dividing by 12 and multiplying by 100000
4. THE Risk_Calculator SHALL express EMI_Affordability as a decimal with two decimal precision
5. WHEN EMI_Affordability exceeds 0.50, THE Risk_Calculator SHALL flag the student as High_Risk_Student regardless of Risk_Score

### Requirement 5: SHAP-Based Explainability

**User Story:** As a Loan Officer, I want to understand which factors drive a student's risk score, so that I can make informed lending decisions.

#### Acceptance Criteria

1. WHEN a prediction is generated, THE Explainability_Engine SHALL compute SHAP_Values for all input features
2. THE Explainability_Engine SHALL use TreeExplainer for XGBoost models to generate exact SHAP values
3. THE Explainability_Engine SHALL identify the top 5 risk drivers by sorting features by absolute SHAP value in descending order
4. THE Explainability_Engine SHALL store the complete SHAP_Values dictionary as JSONB in the predictions table
5. THE Explainability_Engine SHALL store top_risk_drivers as a JSONB array containing feature name, SHAP value, and direction (positive/negative)
6. THE Explainability_Engine SHALL include base_value (model baseline prediction) in the explanation output

### Requirement 6: AI-Generated Risk Summary

**User Story:** As a Loan Officer, I want a plain-English explanation of a student's risk profile, so that I can quickly understand the assessment without technical jargon.

#### Acceptance Criteria

1. WHEN a prediction is generated, THE LLM_Summarizer SHALL generate a natural language risk summary using the Claude API
2. THE LLM_Summarizer SHALL use the claude-sonnet-4-20250514 model for summary generation
3. THE LLM_Summarizer SHALL include student course type, Institute_Tier, CGPA, internship count, Risk_Score, Risk_Level, and top risk drivers in the prompt
4. THE LLM_Summarizer SHALL limit the summary to 2 sentences maximum
5. THE LLM_Summarizer SHALL start the summary with the Risk_Level and primary risk driver
6. THE LLM_Summarizer SHALL store the generated summary as TEXT in the predictions table ai_summary column
7. WHEN the Claude API call fails, THE LLM_Summarizer SHALL store a fallback summary stating "AI summary unavailable - refer to SHAP values"

### Requirement 7: Next-Best Action Recommendations

**User Story:** As a Loan Officer, I want actionable recommendations to help students improve their placement prospects, so that I can guide them toward better outcomes.

#### Acceptance Criteria

1. WHEN a prediction is generated, THE Action_Recommender SHALL generate a list of Next_Best_Action recommendations
2. WHEN job_demand_score is among the bottom 3 SHAP contributors, THE Action_Recommender SHALL recommend a "skill_up" action with course-specific certification suggestions
3. WHEN internship_count is zero or Internship_Score is below 0.3, THE Action_Recommender SHALL recommend an "internship" action with high priority
4. WHEN Risk_Score exceeds 60, THE Action_Recommender SHALL recommend a "resume" action for resume improvement
5. WHEN prob_placed_3m is below 0.5, THE Action_Recommender SHALL recommend a "mock_interview" action with high priority
6. WHEN Risk_Level is "low" or "medium" AND Institute_Tier is 1 or 2, THE Action_Recommender SHALL recommend a "recruiter_match" action with low priority
7. THE Action_Recommender SHALL store recommendations as a JSONB array with fields: type, title, description, and priority

### Requirement 8: Single Student Prediction API

**User Story:** As a Loan Officer, I want to submit a single student's data and receive a complete risk assessment, so that I can evaluate loan applications.

#### Acceptance Criteria

1. THE System SHALL expose a POST endpoint at /api/predict accepting a Student_Profile in JSON format
2. WHEN a valid Student_Profile is received, THE System SHALL create a student record in the students table
3. WHEN a student record is created, THE System SHALL invoke Placement_Predictor, Salary_Estimator, Risk_Calculator, Explainability_Engine, LLM_Summarizer, and Action_Recommender in sequence
4. WHEN all components complete, THE System SHALL store the complete prediction in the predictions table
5. WHEN the prediction is stored, THE System SHALL return a JSON response containing student_id, prediction_id, all probability scores, Risk_Score, Risk_Level, salary range, EMI_Affordability, top_risk_drivers, ai_summary, and next_best_actions
6. THE System SHALL complete the prediction request within 5 seconds for 95% of requests
7. WHEN any component fails, THE System SHALL return an HTTP 500 error with a descriptive error message

### Requirement 9: Batch Student Scoring API

**User Story:** As a Portfolio Manager, I want to score multiple students at once, so that I can efficiently assess portfolio risk.

#### Acceptance Criteria

1. THE System SHALL expose a POST endpoint at /api/batch-score accepting an array of Student_Profile objects
2. THE System SHALL reject batch requests containing more than 500 students with an HTTP 400 error
3. WHEN a valid batch request is received, THE System SHALL process each Student_Profile using the same pipeline as single predictions
4. THE System SHALL process batch predictions in parallel using asynchronous processing
5. WHEN all predictions complete, THE System SHALL return a JSON response containing an array of prediction results and a summary object
6. THE summary object SHALL include counts of high_risk_count, medium_risk_count, and low_risk_count students
7. THE System SHALL complete batch scoring within 60 seconds for batches of 500 students

### Requirement 10: SHAP Explanation Retrieval API

**User Story:** As a Loan Officer, I want to retrieve detailed SHAP explanations for a student, so that I can understand the model's reasoning in depth.

#### Acceptance Criteria

1. THE System SHALL expose a GET endpoint at /api/explain/{student_id} accepting a student UUID
2. WHEN a valid student_id is provided, THE System SHALL retrieve the most recent prediction record for that student
3. WHEN a prediction record exists, THE System SHALL return a JSON response containing student_id, complete SHAP_Values dictionary, base_value, prediction probability, and waterfall_data array
4. THE waterfall_data array SHALL contain objects with feature name, SHAP value, and cumulative prediction value for visualization
5. WHEN no prediction exists for the student_id, THE System SHALL return an HTTP 404 error
6. THE System SHALL complete explanation retrieval within 1 second

### Requirement 11: High-Risk Student Alerts API

**User Story:** As a Portfolio Manager, I want to see a list of high-risk students requiring immediate attention, so that I can prioritize interventions.

#### Acceptance Criteria

1. THE System SHALL expose a GET endpoint at /api/alerts accepting optional query parameters: threshold, limit, and offset
2. WHEN threshold parameter is "high", THE System SHALL return students where Risk_Level equals "high" OR EMI_Affordability exceeds 0.5
3. WHEN threshold parameter is omitted, THE System SHALL default to "high"
4. THE System SHALL support pagination using limit (default 50) and offset (default 0) parameters
5. THE System SHALL return a JSON array of student predictions sorted by Risk_Score in descending order
6. THE System SHALL include student name, course type, Institute_Tier, Risk_Score, Risk_Level, EMI_Affordability, and top risk driver in each alert record
7. THE System SHALL complete alert retrieval within 2 seconds

### Requirement 12: Student List API

**User Story:** As a Portfolio Manager, I want to view all students with their latest predictions, so that I can monitor portfolio health.

#### Acceptance Criteria

1. THE System SHALL expose a GET endpoint at /api/students accepting optional query parameters: search, sort, order, limit, and offset
2. WHEN search parameter is provided, THE System SHALL filter students by name using case-insensitive partial matching
3. WHEN sort parameter is provided, THE System SHALL sort results by the specified column (risk_score, name, course_type, institute_tier, created_at)
4. WHEN order parameter is "desc", THE System SHALL sort in descending order; otherwise ascending
5. THE System SHALL support pagination using limit (default 20) and offset (default 0) parameters
6. THE System SHALL join students table with predictions table to include the most recent prediction for each student
7. THE System SHALL return a JSON response containing an array of student records and a total_count field

### Requirement 13: System Health Check API

**User Story:** As a DevOps Engineer, I want to check if the system is operational, so that I can monitor service availability.

#### Acceptance Criteria

1. THE System SHALL expose a GET endpoint at /api/health
2. THE System SHALL verify database connectivity by executing a simple query
3. THE System SHALL verify ML model availability by checking if model files exist at the configured path
4. WHEN all checks pass, THE System SHALL return HTTP 200 with a JSON response containing status "ok", Model_Version, database status "connected", and current timestamp
5. WHEN any check fails, THE System SHALL return HTTP 503 with status "degraded" and details of the failed component
6. THE System SHALL complete health checks within 3 seconds

### Requirement 14: Audit Logging for Compliance

**User Story:** As a Compliance Officer, I want all predictions and actions logged, so that I can demonstrate RBI compliance during audits.

#### Acceptance Criteria

1. WHEN a prediction is generated, THE Audit_Logger SHALL create a record in the audit_logs table with action "PREDICT"
2. WHEN a SHAP explanation is retrieved, THE Audit_Logger SHALL create a record with action "EXPLAIN"
3. WHEN a high-risk alert is triggered, THE Audit_Logger SHALL create a record with action "ALERT_SENT"
4. THE Audit_Logger SHALL store student_id, prediction_id, action type, performed_by user identifier, and metadata JSONB in each log record
5. THE Audit_Logger SHALL include Model_Version in the metadata for all PREDICT actions
6. THE Audit_Logger SHALL record timestamp automatically using database default NOW()
7. THE Audit_Logger SHALL never delete audit log records (append-only table)

### Requirement 15: Model Version Tracking

**User Story:** As a Data Scientist, I want to track which model version generated each prediction, so that I can analyze model performance over time.

#### Acceptance Criteria

1. WHEN a prediction is generated, THE System SHALL record the Model_Version string in the predictions table
2. THE System SHALL read Model_Version from a version.json file stored alongside model artifacts
3. THE Model_Version string SHALL follow semantic versioning format (e.g., "1.0.0", "1.2.3")
4. WHEN Model_Version file is missing, THE System SHALL use "unknown" as the version and log a warning
5. THE System SHALL include Model_Version in all API responses containing prediction data

### Requirement 16: Demographic Feature Exclusion

**User Story:** As a Compliance Officer, I want to ensure demographic features are never used in ML models, so that we comply with fair lending regulations.

#### Acceptance Criteria

1. THE Placement_Predictor SHALL exclude gender, religion, caste, and state_of_origin from all training and inference feature sets
2. THE Salary_Estimator SHALL exclude gender, religion, caste, and state_of_origin from all training and inference feature sets
3. THE System SHALL validate that Demographic_Features are not present in the feature_names.json file used by models
4. WHEN a Student_Profile includes Demographic_Features, THE System SHALL accept them for storage but SHALL NOT pass them to ML models
5. THE System SHALL use Demographic_Features only for post-hoc bias auditing with Fairlearn

### Requirement 17: Feature Engineering Pipeline

**User Story:** As a Data Scientist, I want consistent feature engineering across training and inference, so that model predictions are accurate.

#### Acceptance Criteria

1. THE System SHALL normalize CGPA by dividing by cgpa_scale to produce cgpa_normalized between 0.0 and 1.0
2. THE System SHALL compute Internship_Score as: (internship_count × 0.4) + (internship_months/24 × 0.3) + (employer_type_score × 0.3)
3. THE System SHALL map internship_employer_type to employer_type_score: MNC=4, Startup=3, PSU=2, NGO=1, None=0
4. THE System SHALL compute skill_gap_score as: job_demand_score minus (cgpa_normalized × 5 + Internship_Score × 5)
5. THE System SHALL compute emi_stress_ratio as: loan_emi divided by salary_benchmark
6. THE System SHALL compute placement_momentum as: placement_rate_3m divided by placement_rate_12m
7. THE System SHALL one-hot encode Institute_Tier and label encode course_type

### Requirement 18: Database Schema Compliance

**User Story:** As a Backend Developer, I want a well-defined database schema, so that data integrity is maintained.

#### Acceptance Criteria

1. THE System SHALL create a students table with columns: id (UUID primary key), name, course_type, institute_name, Institute_Tier, cgpa, cgpa_scale, year_of_grad, internship_count, internship_months, internship_employer_type, certifications, region, loan_amount, loan_emi, created_at, updated_at
2. THE System SHALL create a predictions table with columns: id (UUID primary key), student_id (foreign key), Model_Version, prob_placed_3m, prob_placed_6m, prob_placed_12m, placement_label, Risk_Score, Risk_Level, salary_min, salary_max, salary_confidence, EMI_Affordability, SHAP_Values (JSONB), top_risk_drivers (JSONB), ai_summary (TEXT), next_best_actions (JSONB), alert_triggered (BOOLEAN), created_at
3. THE System SHALL create an audit_logs table with columns: id (UUID primary key), student_id (foreign key), prediction_id (foreign key), action, performed_by, metadata (JSONB), created_at
4. THE System SHALL enforce foreign key constraints with ON DELETE CASCADE for student_id references
5. THE System SHALL use TIMESTAMPTZ for all timestamp columns with DEFAULT NOW()
6. THE System SHALL use gen_random_uuid() for UUID primary key defaults

### Requirement 19: Configuration File Parser and Pretty Printer

**User Story:** As a DevOps Engineer, I want to load system configuration from files, so that I can deploy the system with different settings.

#### Acceptance Criteria

1. WHEN a configuration file path is provided, THE System SHALL parse the file into a Configuration object
2. WHEN an invalid configuration file is provided, THE System SHALL return a descriptive error indicating the line and issue
3. THE System SHALL support configuration files in JSON format with fields: database_url, redis_url, anthropic_api_key, ml_model_path, secret_key, cors_origins
4. THE System SHALL validate that required fields (database_url, ml_model_path) are present
5. THE System SHALL provide a Pretty_Printer that formats Configuration objects back into valid JSON configuration files
6. FOR ALL valid Configuration objects, parsing then printing then parsing SHALL produce an equivalent Configuration object (round-trip property)
7. THE Pretty_Printer SHALL format JSON with 2-space indentation and sorted keys

### Requirement 20: API Request Validation

**User Story:** As a Backend Developer, I want all API requests validated, so that invalid data is rejected before processing.

#### Acceptance Criteria

1. WHEN a POST /api/predict request is received, THE System SHALL validate that required fields (name, course_type, Institute_Tier, cgpa, year_of_grad) are present
2. THE System SHALL validate that Institute_Tier is an integer between 1 and 3
3. THE System SHALL validate that cgpa is a decimal between 0.0 and cgpa_scale
4. THE System SHALL validate that year_of_grad is an integer between 2020 and 2030
5. THE System SHALL validate that internship_count is a non-negative integer
6. THE System SHALL validate that loan_amount and loan_emi are non-negative decimals
7. WHEN validation fails, THE System SHALL return HTTP 422 with a JSON response containing field-specific error messages

### Requirement 21: CORS Configuration

**User Story:** As a Frontend Developer, I want the API to accept requests from the frontend domain, so that the web application can communicate with the backend.

#### Acceptance Criteria

1. THE System SHALL configure CORS middleware to accept requests from origins specified in the CORS_ORIGINS environment variable
2. THE System SHALL allow HTTP methods: GET, POST, PUT, DELETE, OPTIONS
3. THE System SHALL allow headers: Content-Type, Authorization, Accept
4. THE System SHALL include Access-Control-Allow-Credentials header set to true
5. WHEN CORS_ORIGINS is not configured, THE System SHALL default to allowing http://localhost:3000

### Requirement 22: Error Handling and Logging

**User Story:** As a DevOps Engineer, I want detailed error logs, so that I can troubleshoot production issues.

#### Acceptance Criteria

1. WHEN an unhandled exception occurs, THE System SHALL log the full stack trace with ERROR level
2. WHEN a prediction request fails, THE System SHALL log the student_id, error type, and error message
3. WHEN the Claude API call fails, THE System SHALL log the API response status and error message
4. WHEN a database query fails, THE System SHALL log the SQL statement and error details
5. THE System SHALL use structured logging with JSON format including timestamp, level, message, and context fields
6. THE System SHALL log all API requests with INFO level including method, path, status code, and response time

### Requirement 23: Rate Limiting

**User Story:** As a DevOps Engineer, I want to prevent API abuse, so that the system remains available for legitimate users.

#### Acceptance Criteria

1. THE System SHALL implement rate limiting using Redis as the backend store
2. THE System SHALL limit POST /api/predict requests to 100 requests per minute per IP address
3. THE System SHALL limit POST /api/batch-score requests to 10 requests per minute per IP address
4. THE System SHALL limit GET requests to 300 requests per minute per IP address
5. WHEN rate limit is exceeded, THE System SHALL return HTTP 429 with a JSON response containing retry_after seconds
6. THE System SHALL include X-RateLimit-Limit, X-RateLimit-Remaining, and X-RateLimit-Reset headers in all responses

### Requirement 24: Docker Containerization

**User Story:** As a DevOps Engineer, I want the entire system containerized, so that I can deploy it consistently across environments.

#### Acceptance Criteria

1. THE System SHALL provide a docker-compose.yml file that orchestrates PostgreSQL, Redis, backend, and frontend services
2. THE System SHALL configure the backend service to wait for database availability before starting
3. THE System SHALL mount ML model artifacts as a read-only volume in the backend container
4. THE System SHALL expose backend on port 8000 and frontend on port 3000
5. THE System SHALL configure environment variables via .env file
6. WHEN docker-compose up is executed, THE System SHALL start all services and complete health checks within 60 seconds

### Requirement 25: Frontend Dashboard Overview

**User Story:** As a Portfolio Manager, I want a dashboard showing portfolio risk distribution, so that I can monitor overall portfolio health.

#### Acceptance Criteria

1. THE Frontend SHALL display a portfolio heatmap showing all students color-coded by Risk_Level
2. THE Frontend SHALL display aggregate statistics: total students, high-risk count, medium-risk count, low-risk count
3. THE Frontend SHALL display a sortable table of students with columns: name, course type, Institute_Tier, Risk_Score, alert status
4. THE Frontend SHALL refresh dashboard data every 30 seconds automatically
5. WHEN a student row is clicked, THE Frontend SHALL navigate to the student detail page

### Requirement 26: Frontend Student Detail Page

**User Story:** As a Loan Officer, I want to view comprehensive risk details for a student, so that I can make informed lending decisions.

#### Acceptance Criteria

1. THE Frontend SHALL display the student's Risk_Score as a large number with color-coded badge (green for low, yellow for medium, red for high)
2. THE Frontend SHALL display a bar chart showing prob_placed_3m, prob_placed_6m, and prob_placed_12m
3. THE Frontend SHALL display salary range as a card showing salary_min to salary_max in LPA with confidence percentage
4. THE Frontend SHALL display a SHAP waterfall chart with horizontal bars (green for positive, red for negative contributions)
5. THE Frontend SHALL display the ai_summary text in a prominent card
6. THE Frontend SHALL display next_best_actions as a list of cards with icons, titles, descriptions, and priority badges
7. THE Frontend SHALL display an audit trail timeline showing all predictions for the student

### Requirement 27: Frontend New Prediction Form

**User Story:** As a Loan Officer, I want to input a new student's data and get a risk assessment, so that I can evaluate loan applications.

#### Acceptance Criteria

1. THE Frontend SHALL provide a multi-step form with three steps: Academic Info, Internship & Skills, Loan Details
2. THE Frontend SHALL validate required fields in each step before allowing progression to the next step
3. THE Frontend SHALL display field-level validation errors inline below each input
4. WHEN the form is submitted, THE Frontend SHALL call POST /api/predict with the Student_Profile
5. WHEN the prediction succeeds, THE Frontend SHALL navigate to the student detail page for the new student
6. WHEN the prediction fails, THE Frontend SHALL display an error message and allow the user to retry

### Requirement 28: Frontend Alerts Page

**User Story:** As a Portfolio Manager, I want to see high-risk students requiring attention, so that I can prioritize interventions.

#### Acceptance Criteria

1. THE Frontend SHALL display a filter bar with options: All, High Risk, Medium Risk
2. THE Frontend SHALL call GET /api/alerts with the selected threshold parameter
3. THE Frontend SHALL display each alert as a card showing student name, Risk_Level badge, Risk_Score, top risk driver, and recommended action
4. THE Frontend SHALL provide an "Acknowledge" button on each alert card
5. WHEN an alert is acknowledged, THE Frontend SHALL mark it as read and remove it from the active alerts view
6. THE Frontend SHALL display a count badge on the alerts navigation item showing unacknowledged alert count

### Requirement 29: Bias Audit Reporting

**User Story:** As a Compliance Officer, I want to audit model fairness across demographic groups, so that I can ensure fair lending practices.

#### Acceptance Criteria

1. THE System SHALL provide a bias audit script that runs Fairlearn demographic parity analysis on test data
2. THE bias audit script SHALL compute accuracy and selection rate metrics grouped by gender and region
3. THE bias audit script SHALL compute demographic_parity_difference for gender groups
4. THE bias audit script SHALL generate a report showing metric disparities across groups
5. WHEN demographic_parity_difference exceeds 0.1, THE bias audit script SHALL flag the model as potentially biased
6. THE bias audit report SHALL be saved as a JSON file with timestamp in the ml/reports/ directory

### Requirement 30: Synthetic Data Generation

**User Story:** As a Data Scientist, I want to generate synthetic student data, so that I can train models without relying solely on limited real data.

#### Acceptance Criteria

1. THE System SHALL provide a script that generates 5000 synthetic student records
2. THE script SHALL generate CGPA values from a normal distribution with mean 7.5 and standard deviation 1.2, clipped to [4.0, 10.0]
3. THE script SHALL generate Institute_Tier values from a multinomial distribution with probabilities [0.2, 0.5, 0.3] for tiers 1, 2, 3
4. THE script SHALL generate internship_count values from a Poisson distribution with lambda 1.5, capped at 6
5. THE script SHALL generate placement_3m labels using a logistic function of (Institute_Tier=1, cgpa>8, internship_count>2)
6. THE script SHALL generate salary values from a lognormal distribution based on Institute_Tier and course_type
7. THE script SHALL save synthetic data as CSV in ml/data/synthetic/ directory
