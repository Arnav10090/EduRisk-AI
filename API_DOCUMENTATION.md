# EduRisk AI - API Documentation

Complete API reference for the EduRisk AI Placement Risk Intelligence system.

## Base URL

```
http://localhost:8000
```

For production deployments, replace with your production URL.

## Authentication

Currently, the API does not require authentication. For production deployments, implement JWT-based authentication using the `SECRET_KEY` environment variable.

## Rate Limits

| Endpoint | Limit |
|----------|-------|
| POST /api/predict | 100 requests/minute per IP |
| POST /api/batch-score | 10 requests/minute per IP |
| GET endpoints | 300 requests/minute per IP |

Rate limit headers are included in all responses:
- `X-RateLimit-Limit`: Maximum requests allowed
- `X-RateLimit-Remaining`: Remaining requests in current window
- `X-RateLimit-Reset`: Unix timestamp when limit resets

## Response Format

### Success Response
```json
{
  "data": { ... },
  "status": "success"
}
```

### Error Response
```json
{
  "detail": "Error message",
  "status": "error",
  "error_type": "ValidationError"
}
```

## Endpoints

### 1. Health Check

Check system health and availability.

**Endpoint:** `GET /api/health`

**Response:** `200 OK`
```json
{
  "status": "ok",
  "model_version": "1.0.0",
  "database": "connected",
  "timestamp": "2025-01-15T10:30:00Z"
}
```

**Response:** `503 Service Unavailable` (if degraded)
```json
{
  "status": "degraded",
  "model_version": "unknown",
  "database": "disconnected",
  "timestamp": "2025-01-15T10:30:00Z"
}
```

---

### 2. Single Student Prediction

Generate placement risk prediction for a single student.

**Endpoint:** `POST /api/predict`

**Request Body:**
```json
{
  "name": "John Doe",
  "course_type": "Engineering",
  "institute_name": "ABC Institute of Technology",
  "institute_tier": 2,
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
}
```

**Field Descriptions:**

| Field | Type | Required | Constraints | Description |
|-------|------|----------|-------------|-------------|
| name | string | Yes | 1-255 chars | Student's full name |
| course_type | string | Yes | - | Course type (Engineering, MBA, etc.) |
| institute_name | string | No | 1-255 chars | Name of educational institute |
| institute_tier | integer | Yes | 1-3 | Institute tier (1=top, 2=mid, 3=lower) |
| cgpa | decimal | Yes | >= 0 | Student's CGPA |
| cgpa_scale | decimal | No | > 0 | CGPA scale (default: 10.0) |
| year_of_grad | integer | Yes | 2020-2030 | Expected graduation year |
| internship_count | integer | No | >= 0 | Number of internships completed |
| internship_months | integer | No | >= 0 | Total months of internship experience |
| internship_employer_type | string | No | - | Type: MNC, Startup, PSU, NGO, or null |
| certifications | integer | No | >= 0 | Number of certifications |
| region | string | No | - | Geographic region |
| loan_amount | decimal | No | >= 0 | Total loan amount in INR |
| loan_emi | decimal | No | >= 0 | Monthly EMI in INR |

**Response:** `200 OK`
```json
{
  "student_id": "550e8400-e29b-41d4-a716-446655440000",
  "prediction_id": "660e8400-e29b-41d4-a716-446655440001",
  "model_version": "1.0.0",
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
  "alert_triggered": false,
  "top_risk_drivers": [
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
    {
      "feature": "cgpa_normalized",
      "value": 0.11,
      "direction": "positive"
    },
    {
      "feature": "job_demand_score",
      "value": -0.09,
      "direction": "negative"
    },
    {
      "feature": "course_type_encoded",
      "value": -0.17,
      "direction": "negative"
    }
  ],
  "ai_summary": "Medium risk student with strong academic performance (CGPA 8.5) and good internship experience. Primary risk driver is moderate job demand in the chosen field. Placement probability within 3 months is 62%, improving to 86% within 12 months.",
  "next_best_actions": [
    {
      "type": "skill_up",
      "title": "Skill-Up Recommendation",
      "description": "Enroll in Engineering-specific certification courses to improve job demand score. Focus on in-demand technologies like Cloud Computing, Data Science, or Full-Stack Development.",
      "priority": "medium"
    },
    {
      "type": "mock_interview",
      "title": "Mock Interview Coaching",
      "description": "3-month placement probability is below 70%. Schedule mock interviews to improve interview performance and confidence.",
      "priority": "high"
    }
  ],
  "created_at": "2025-01-15T10:30:00Z"
}
```

**Response Field Descriptions:**

| Field | Type | Description |
|-------|------|-------------|
| student_id | UUID | Unique identifier for the student |
| prediction_id | UUID | Unique identifier for this prediction |
| model_version | string | ML model version used |
| risk_score | integer | Composite risk score (0-100, higher = riskier) |
| risk_level | string | Risk category: "low", "medium", or "high" |
| prob_placed_3m | decimal | Probability of placement within 3 months (0-1) |
| prob_placed_6m | decimal | Probability of placement within 6 months (0-1) |
| prob_placed_12m | decimal | Probability of placement within 12 months (0-1) |
| placement_label | string | Predicted timeline: "placed_3m", "placed_6m", "placed_12m", or "high_risk" |
| salary_min | decimal | Minimum expected salary in LPA |
| salary_max | decimal | Maximum expected salary in LPA |
| salary_confidence | decimal | Confidence percentage for salary range |
| emi_affordability | decimal | EMI-to-salary ratio (0-1) |
| alert_triggered | boolean | True if high-risk alert triggered |
| top_risk_drivers | array | Top 5 SHAP feature attributions |
| ai_summary | string | Natural language risk explanation |
| next_best_actions | array | Recommended interventions |
| created_at | timestamp | Prediction timestamp |

**Error Responses:**

`422 Unprocessable Entity` - Validation error
```json
{
  "detail": [
    {
      "loc": ["body", "institute_tier"],
      "msg": "ensure this value is less than or equal to 3",
      "type": "value_error.number.not_le"
    }
  ]
}
```

`500 Internal Server Error` - Processing error
```json
{
  "detail": "Failed to generate prediction: Model file not found",
  "status": "error"
}
```

---

### 3. Batch Student Scoring

Generate predictions for multiple students in a single request.

**Endpoint:** `POST /api/batch-score`

**Request Body:**
```json
{
  "students": [
    {
      "name": "Student 1",
      "course_type": "Engineering",
      "institute_tier": 2,
      "cgpa": 8.5,
      "year_of_grad": 2025,
      ...
    },
    {
      "name": "Student 2",
      "course_type": "MBA",
      "institute_tier": 1,
      "cgpa": 9.0,
      "year_of_grad": 2025,
      ...
    }
  ]
}
```

**Constraints:**
- Maximum 500 students per batch
- Each student must have the same fields as single prediction

**Response:** `200 OK`
```json
{
  "results": [
    {
      "student_id": "...",
      "prediction_id": "...",
      "risk_score": 45,
      "risk_level": "medium",
      ...
    },
    {
      "student_id": "...",
      "prediction_id": "...",
      "risk_score": 25,
      "risk_level": "low",
      ...
    }
  ],
  "summary": {
    "total_count": 2,
    "high_risk_count": 0,
    "medium_risk_count": 1,
    "low_risk_count": 1,
    "avg_risk_score": 35.0,
    "processing_time_seconds": 12.5
  }
}
```

**Error Responses:**

`400 Bad Request` - Batch too large
```json
{
  "detail": "Batch size exceeds maximum of 500 students",
  "status": "error"
}
```

---

### 4. Get SHAP Explanation

Retrieve detailed SHAP explanation for a student's prediction.

**Endpoint:** `GET /api/explain/{student_id}`

**Path Parameters:**
- `student_id` (UUID): Student identifier

**Response:** `200 OK`
```json
{
  "student_id": "550e8400-e29b-41d4-a716-446655440000",
  "prediction_id": "660e8400-e29b-41d4-a716-446655440001",
  "base_value": 0.45,
  "prediction": 0.78,
  "shap_values": {
    "internship_score": 0.34,
    "institute_tier_1": 0.22,
    "cgpa_normalized": 0.11,
    "job_demand_score": -0.09,
    "course_type_encoded": -0.17,
    "certifications": 0.05,
    "placement_rate_3m": 0.08,
    "placement_rate_6m": 0.06,
    "salary_benchmark": 0.03,
    "region_job_density": -0.02,
    "macro_hiring_index": 0.01,
    "skill_gap_score": -0.04,
    "emi_stress_ratio": -0.01,
    "placement_momentum": 0.02,
    "employer_type_score": 0.12,
    "institute_tier_2": 0.0,
    "institute_tier_3": 0.0
  },
  "waterfall_data": [
    {
      "feature": "base_value",
      "value": 0.45,
      "cumulative": 0.45
    },
    {
      "feature": "internship_score",
      "value": 0.34,
      "cumulative": 0.79
    },
    {
      "feature": "institute_tier_1",
      "value": 0.22,
      "cumulative": 1.01
    },
    ...
  ]
}
```

**Error Responses:**

`404 Not Found` - Student not found
```json
{
  "detail": "No prediction found for student",
  "status": "error"
}
```

---

### 5. List Students

Retrieve paginated list of all students with their latest predictions.

**Endpoint:** `GET /api/students`

**Query Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| search | string | - | Search by student name (case-insensitive) |
| sort | string | created_at | Sort field: risk_score, name, course_type, institute_tier, created_at |
| order | string | desc | Sort order: asc or desc |
| limit | integer | 20 | Results per page (max 100) |
| offset | integer | 0 | Pagination offset |

**Example Request:**
```
GET /api/students?search=John&sort=risk_score&order=desc&limit=20&offset=0
```

**Response:** `200 OK`
```json
{
  "students": [
    {
      "student_id": "550e8400-e29b-41d4-a716-446655440000",
      "name": "John Doe",
      "course_type": "Engineering",
      "institute_name": "ABC Institute",
      "institute_tier": 2,
      "cgpa": 8.5,
      "year_of_grad": 2025,
      "latest_prediction": {
        "prediction_id": "660e8400-e29b-41d4-a716-446655440001",
        "risk_score": 45,
        "risk_level": "medium",
        "placement_label": "placed_3m",
        "alert_triggered": false,
        "created_at": "2025-01-15T10:30:00Z"
      },
      "created_at": "2025-01-15T10:00:00Z"
    },
    ...
  ],
  "total_count": 150,
  "limit": 20,
  "offset": 0
}
```

---

### 6. Get High-Risk Alerts

Retrieve students requiring immediate attention.

**Endpoint:** `GET /api/alerts`

**Query Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| threshold | string | high | Risk threshold: "high", "medium", or "all" |
| limit | integer | 50 | Results per page (max 100) |
| offset | integer | 0 | Pagination offset |

**Alert Criteria:**
- `threshold=high`: Students with risk_level="high" OR emi_affordability > 0.5
- `threshold=medium`: Students with risk_level="medium" or "high"
- `threshold=all`: All students with alerts

**Example Request:**
```
GET /api/alerts?threshold=high&limit=50&offset=0
```

**Response:** `200 OK`
```json
{
  "alerts": [
    {
      "student_id": "550e8400-e29b-41d4-a716-446655440000",
      "prediction_id": "660e8400-e29b-41d4-a716-446655440001",
      "name": "Jane Smith",
      "course_type": "MBA",
      "institute_tier": 3,
      "risk_score": 78,
      "risk_level": "high",
      "emi_affordability": 0.65,
      "alert_triggered": true,
      "top_risk_driver": {
        "feature": "institute_tier_3",
        "value": -0.25,
        "direction": "negative"
      },
      "recommended_action": {
        "type": "resume",
        "title": "Resume Improvement",
        "priority": "high"
      },
      "created_at": "2025-01-15T10:30:00Z"
    },
    ...
  ],
  "total_count": 25,
  "limit": 50,
  "offset": 0
}
```

---

## Data Models

### Student Input Schema

```typescript
interface StudentInput {
  name: string;                      // Required
  course_type: string;               // Required
  institute_name?: string;           // Optional
  institute_tier: 1 | 2 | 3;        // Required
  cgpa: number;                      // Required, >= 0
  cgpa_scale?: number;               // Optional, default 10.0
  year_of_grad: number;              // Required, 2020-2030
  internship_count?: number;         // Optional, >= 0
  internship_months?: number;        // Optional, >= 0
  internship_employer_type?: string; // Optional: MNC, Startup, PSU, NGO
  certifications?: number;           // Optional, >= 0
  region?: string;                   // Optional
  loan_amount?: number;              // Optional, >= 0
  loan_emi?: number;                 // Optional, >= 0
}
```

### Prediction Response Schema

```typescript
interface PredictionResponse {
  student_id: string;                // UUID
  prediction_id: string;             // UUID
  model_version: string;             // Semantic version
  risk_score: number;                // 0-100
  risk_level: "low" | "medium" | "high";
  prob_placed_3m: number;            // 0-1
  prob_placed_6m: number;            // 0-1
  prob_placed_12m: number;           // 0-1
  placement_label: string;           // placed_3m, placed_6m, placed_12m, high_risk
  salary_min: number;                // LPA
  salary_max: number;                // LPA
  salary_confidence: number;         // Percentage
  emi_affordability: number;         // 0-1 ratio
  alert_triggered: boolean;
  top_risk_drivers: RiskDriver[];
  ai_summary: string;
  next_best_actions: Action[];
  created_at: string;                // ISO 8601 timestamp
}

interface RiskDriver {
  feature: string;
  value: number;
  direction: "positive" | "negative";
}

interface Action {
  type: string;                      // skill_up, internship, resume, mock_interview, recruiter_match
  title: string;
  description: string;
  priority: "low" | "medium" | "high";
}
```

## Error Codes

| Status Code | Description |
|-------------|-------------|
| 200 | Success |
| 400 | Bad Request - Invalid input |
| 404 | Not Found - Resource doesn't exist |
| 422 | Unprocessable Entity - Validation error |
| 429 | Too Many Requests - Rate limit exceeded |
| 500 | Internal Server Error - Server-side error |
| 503 | Service Unavailable - System degraded |

## Best Practices

### 1. Error Handling

Always check the response status code and handle errors appropriately:

```javascript
try {
  const response = await fetch('/api/predict', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(studentData)
  });
  
  if (!response.ok) {
    const error = await response.json();
    console.error('Prediction failed:', error.detail);
    return;
  }
  
  const prediction = await response.json();
  // Process prediction...
} catch (error) {
  console.error('Network error:', error);
}
```

### 2. Rate Limiting

Monitor rate limit headers and implement exponential backoff:

```javascript
const rateLimitRemaining = response.headers.get('X-RateLimit-Remaining');
const rateLimitReset = response.headers.get('X-RateLimit-Reset');

if (rateLimitRemaining === '0') {
  const resetTime = new Date(parseInt(rateLimitReset) * 1000);
  console.log(`Rate limit exceeded. Resets at ${resetTime}`);
}
```

### 3. Batch Processing

For large datasets, split into batches of 500 or fewer:

```javascript
const batchSize = 500;
for (let i = 0; i < students.length; i += batchSize) {
  const batch = students.slice(i, i + batchSize);
  const response = await fetch('/api/batch-score', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ students: batch })
  });
  // Process batch results...
}
```

### 4. Pagination

Use pagination for large result sets:

```javascript
let offset = 0;
const limit = 100;
let allStudents = [];

while (true) {
  const response = await fetch(
    `/api/students?limit=${limit}&offset=${offset}`
  );
  const data = await response.json();
  
  allStudents = allStudents.concat(data.students);
  
  if (data.students.length < limit) {
    break; // No more results
  }
  
  offset += limit;
}
```

## Support

For API issues:
- Check the interactive documentation at http://localhost:8000/docs
- Review error messages in the response
- Check backend logs: `docker-compose logs backend`
- Verify environment variables are set correctly

---

**Last Updated:** January 2025
