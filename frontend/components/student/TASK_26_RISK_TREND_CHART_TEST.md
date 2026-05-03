# Task 26: Risk Score Trend Chart - Test Plan

## Implementation Summary

### Components Created
1. **RiskTrendChart.tsx** - Line chart component showing risk score history over time
   - Location: `frontend/components/student/RiskTrendChart.tsx`
   - Uses Recharts LineChart for visualization
   - Fetches data from GET /api/students/{id}/predictions

### Integration
- Added RiskTrendChart to student detail page (`frontend/app/student/[id]/page.tsx`)
- Positioned below the risk score display section
- Passes studentId as prop to fetch prediction history

## Test Cases

### Test 26.1: Create RiskTrendChart Component ✅

**Verification Steps:**
1. ✅ Component file created at `frontend/components/student/RiskTrendChart.tsx`
2. ✅ Uses Recharts LineChart component
3. ✅ Fetches prediction history from GET /api/students/{id}/predictions endpoint
4. ✅ Component accepts studentId prop

**Expected Behavior:**
- Component renders without errors
- API call is made on component mount
- Loading state displays spinner

---

### Test 26.2: Implement Chart Visualization ✅

**Verification Steps:**
1. ✅ Risk score plotted on Y-axis (0-100 range)
2. ✅ Created_at timestamp plotted on X-axis (formatted as "Mon DD")
3. ✅ Axis labels added: "Risk Score" (Y-axis) and "Date" (X-axis)
4. ✅ Green line color (#10b981) when trend improving (risk decreasing)
5. ✅ Red line color (#ef4444) when trend declining (risk increasing)
6. ✅ Gray line color (#6b7280) when trend stable

**Expected Behavior:**
- Chart displays with proper axis labels
- Line color changes based on trend direction
- Tooltip shows full date and risk score on hover
- Chart is responsive and fits container

**Test Data:**
```typescript
// Improving trend (risk decreasing)
[
  { risk_score: 75, created_at: "2024-01-01" },
  { risk_score: 60, created_at: "2024-01-15" },
  { risk_score: 45, created_at: "2024-02-01" }
]
// Expected: Green line

// Declining trend (risk increasing)
[
  { risk_score: 30, created_at: "2024-01-01" },
  { risk_score: 50, created_at: "2024-01-15" },
  { risk_score: 70, created_at: "2024-02-01" }
]
// Expected: Red line
```

---

### Test 26.3: Handle Edge Cases ✅

**Test Case 1: Empty Prediction History**
```typescript
predictions = []
```
**Expected:** Display "No historical data" message

**Test Case 2: Single Prediction**
```typescript
predictions = [
  { risk_score: 50, created_at: "2024-01-01" }
]
```
**Expected:** Display "No historical data" message (need at least 2 points for trend)

**Test Case 3: Loading State**
**Expected:** Display spinner with RefreshCw icon

**Test Case 4: Error State**
**Expected:** Display error message

**Verification Steps:**
1. ✅ Empty array returns "No historical data"
2. ✅ Single prediction returns "No historical data"
3. ✅ Loading state shows spinner
4. ✅ Error state shows error message

---

### Test 26.4: Integrate in Student Detail Page ✅

**Verification Steps:**
1. ✅ RiskTrendChart imported in `frontend/app/student/[id]/page.tsx`
2. ✅ Component added below risk score display section
3. ✅ Component positioned after the 3-column metrics grid
4. ✅ studentId prop passed correctly

**Expected Behavior:**
- Chart appears on student detail page
- Chart loads after page renders
- Chart is positioned correctly in layout

---

### Test 26.5: Test Trend Chart (Manual Testing Required)

**Test Case 1: Multiple Predictions (Should Show Chart)**

**Steps:**
1. Start Docker containers: `docker-compose up`
2. Navigate to student detail page with multiple predictions
3. Verify chart displays with line connecting all points
4. Verify X-axis shows dates in chronological order
5. Verify Y-axis shows risk scores (0-100)

**Expected:**
- Chart renders with line connecting all data points
- Dates are formatted as "Mon DD" (e.g., "Jan 15")
- Risk scores are displayed correctly
- Tooltip shows full date and risk score on hover

---

**Test Case 2: Single Prediction (Should Show "No Historical Data")**

**Steps:**
1. Navigate to student detail page with only one prediction
2. Verify "No historical data" message displays

**Expected:**
- Message "No historical data" appears in card
- No chart is rendered

---

**Test Case 3: Improving Trend (Should Be Green)**

**Steps:**
1. Create student with multiple predictions where risk decreases over time
2. Navigate to student detail page
3. Verify line color is green (#10b981)
4. Verify trend label shows "Trend: Improving (risk decreasing)"

**Expected:**
- Line is green
- Trend indicator shows "Improving"

**Sample SQL to create test data:**
```sql
-- Insert student
INSERT INTO students (id, name, course_type, institute_tier, cgpa, year_of_grad)
VALUES ('test-uuid-1', 'Test Student', 'B.Tech', 1, 8.5, 2024);

-- Insert predictions with decreasing risk
INSERT INTO predictions (student_id, risk_score, risk_level, created_at)
VALUES 
  ('test-uuid-1', 75, 'high', '2024-01-01'),
  ('test-uuid-1', 60, 'medium', '2024-01-15'),
  ('test-uuid-1', 45, 'medium', '2024-02-01');
```

---

**Test Case 4: Declining Trend (Should Be Red)**

**Steps:**
1. Create student with multiple predictions where risk increases over time
2. Navigate to student detail page
3. Verify line color is red (#ef4444)
4. Verify trend label shows "Trend: Declining (risk increasing)"

**Expected:**
- Line is red
- Trend indicator shows "Declining"

**Sample SQL to create test data:**
```sql
-- Insert student
INSERT INTO students (id, name, course_type, institute_tier, cgpa, year_of_grad)
VALUES ('test-uuid-2', 'Test Student 2', 'B.Tech', 2, 7.0, 2024);

-- Insert predictions with increasing risk
INSERT INTO predictions (student_id, risk_score, risk_level, created_at)
VALUES 
  ('test-uuid-2', 30, 'low', '2024-01-01'),
  ('test-uuid-2', 50, 'medium', '2024-01-15'),
  ('test-uuid-2', 70, 'high', '2024-02-01');
```

---

## Implementation Details

### Component Features
1. **Data Fetching**
   - Uses fetch API to call GET /api/students/{id}/predictions
   - Handles loading, error, and success states
   - Automatically fetches on component mount

2. **Chart Configuration**
   - Y-axis: Risk Score (0-100 range with ticks at 0, 25, 50, 75, 100)
   - X-axis: Date (formatted as "Mon DD")
   - Line: Monotone curve with 2px stroke width
   - Dots: 4px radius, active dot 6px radius
   - Tooltip: Shows full date and risk score

3. **Trend Detection**
   - Compares first (oldest) and last (newest) risk scores
   - Improving: lastScore < firstScore (green line)
   - Declining: lastScore > firstScore (red line)
   - Stable: lastScore === firstScore (gray line)

4. **Edge Case Handling**
   - Empty array: "No historical data"
   - Single prediction: "No historical data"
   - Loading: Spinner animation
   - Error: Error message display

### API Endpoint Used
- **GET /api/students/{id}/predictions**
- Returns: Array of PredictionHistoryEntry
  ```typescript
  interface PredictionHistoryEntry {
    prediction_id: string;
    risk_score: number;
    risk_level: string;
    created_at: string;
  }
  ```

## Build Verification

### TypeScript Compilation ✅
```bash
cd frontend
npm run build
```
**Result:** Build successful, no TypeScript errors

### Route Analysis
- Student detail page: `/student/[id]` - 111 kB (221 kB First Load JS)
- Component adds minimal bundle size (Recharts already included)

## Next Steps for Manual Testing

1. **Start Docker Environment**
   ```bash
   docker-compose up
   ```

2. **Create Test Data**
   - Use the SQL queries above to create students with multiple predictions
   - Or use the API to create predictions over time

3. **Navigate to Student Detail Page**
   - Go to http://localhost:3000/student/{student-id}
   - Verify RiskTrendChart appears below the metrics grid

4. **Test All Scenarios**
   - Multiple predictions (chart should display)
   - Single prediction (should show "No historical data")
   - Improving trend (green line)
   - Declining trend (red line)

## Completion Checklist

- [x] 26.1 Create RiskTrendChart component
  - [x] Create `frontend/components/student/RiskTrendChart.tsx`
  - [x] Use Recharts LineChart
  - [x] Fetch prediction history from GET /api/students/{id}/predictions
- [x] 26.2 Implement chart visualization
  - [x] Plot risk_score on Y-axis
  - [x] Plot created_at timestamp on X-axis
  - [x] Add axis labels "Risk Score" and "Date"
  - [x] Use green line when trend improving (risk decreasing)
  - [x] Use red line when trend declining (risk increasing)
- [x] 26.3 Handle edge cases
  - [x] Display "No historical data" when only one prediction exists
  - [x] Handle empty prediction history
- [x] 26.4 Integrate in student detail page
  - [x] Add RiskTrendChart to student detail page
  - [x] Position below risk score display
- [ ] 26.5 Test trend chart (Requires manual testing with Docker)
  - [ ] Test with multiple predictions (should show chart)
  - [ ] Test with single prediction (should show "No historical data")
  - [ ] Test with improving trend (should be green)
  - [ ] Test with declining trend (should be red)

## Status: Implementation Complete ✅

All code implementation is complete. Manual testing with Docker environment is required to verify the visual behavior and trend detection logic.
