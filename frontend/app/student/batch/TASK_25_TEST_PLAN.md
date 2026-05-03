# Task 25: CSV Batch Upload UI - Test Plan

## Test Environment Setup

### Prerequisites
1. Backend server running at `http://localhost:8000`
2. Frontend server running at `http://localhost:3000`
3. Database initialized with test data
4. Sample CSV files prepared

### Test Data Files

#### 1. Valid CSV (sample-batch.csv)
Located at: `frontend/public/sample-batch.csv`
Contains: 10 valid student records

#### 2. Invalid CSV - Missing Columns
Create file: `test-missing-columns.csv`
```csv
name,course_type,institute_tier
Rahul Sharma,Engineering,1
Priya Patel,MBA,2
```
Expected: Validation error for missing columns (cgpa, year_of_grad, loan_amount, loan_emi)

#### 3. Invalid CSV - Wrong Data Types
Create file: `test-invalid-types.csv`
```csv
name,course_type,institute_tier,cgpa,year_of_grad,loan_amount,loan_emi
Rahul Sharma,Engineering,1,abc,2025,500000,15000
Priya Patel,MBA,2,7.8,xyz,800000,25000
```
Expected: Validation errors for invalid numeric values

#### 4. Large Batch CSV (500 students)
Create file: `test-large-batch.csv`
Generate 500 valid student records
Expected: Successful submission

#### 5. Oversized Batch CSV (501 students)
Create file: `test-oversized-batch.csv`
Generate 501 valid student records
Expected: Batch size validation error

## Test Cases

### Test Case 1: Valid CSV Upload via File Input

**Objective**: Verify successful CSV upload and parsing using file input button

**Steps**:
1. Navigate to `/student/batch`
2. Click "Select CSV File" button
3. Select `sample-batch.csv` from file picker
4. Observe preview table

**Expected Results**:
- ✅ File is accepted
- ✅ Preview table displays with 10 students
- ✅ All columns populated correctly (name, course, tier, CGPA, year, loan amount, EMI)
- ✅ "Submit Batch" button is enabled
- ✅ No validation errors displayed
- ✅ Message shows "10 students ready for processing"

**Status**: ⬜ Not Tested | ✅ Passed | ❌ Failed

---

### Test Case 2: Valid CSV Upload via Drag-and-Drop

**Objective**: Verify drag-and-drop functionality works correctly

**Steps**:
1. Navigate to `/student/batch`
2. Drag `sample-batch.csv` file over upload area
3. Observe visual feedback (border color change)
4. Drop file
5. Observe preview table

**Expected Results**:
- ✅ Upload area highlights during drag (border color changes)
- ✅ File is accepted on drop
- ✅ Preview table displays correctly
- ✅ Same results as Test Case 1

**Status**: ⬜ Not Tested | ✅ Passed | ❌ Failed

---

### Test Case 3: Invalid File Type

**Objective**: Verify rejection of non-CSV files

**Steps**:
1. Navigate to `/student/batch`
2. Try to upload a `.txt` or `.xlsx` file
3. Observe error message

**Expected Results**:
- ✅ File is rejected
- ✅ Error message: "Please select a CSV file"
- ✅ Preview table not displayed
- ✅ Submit button not available

**Status**: ⬜ Not Tested | ✅ Passed | ❌ Failed

---

### Test Case 4: Missing Required Columns

**Objective**: Verify validation of required CSV columns

**Steps**:
1. Navigate to `/student/batch`
2. Upload `test-missing-columns.csv`
3. Observe validation errors

**Expected Results**:
- ✅ Validation error displayed
- ✅ Error message lists missing columns: "Missing required columns: cgpa, year_of_grad, loan_amount, loan_emi"
- ✅ Preview table not displayed
- ✅ Submit button disabled

**Status**: ⬜ Not Tested | ✅ Passed | ❌ Failed

---

### Test Case 5: Invalid Data Types

**Objective**: Verify validation of numeric fields

**Steps**:
1. Navigate to `/student/batch`
2. Upload `test-invalid-types.csv`
3. Observe validation errors

**Expected Results**:
- ✅ Validation errors displayed for each invalid field
- ✅ Error messages include row numbers and field names
- ✅ Example: "Row 2: Invalid number: abc" for cgpa field
- ✅ Example: "Row 3: Invalid number: xyz" for year_of_grad field
- ✅ Submit button disabled

**Status**: ⬜ Not Tested | ✅ Passed | ❌ Failed

---

### Test Case 6: Batch Size Limit (500 students)

**Objective**: Verify maximum batch size is enforced

**Steps**:
1. Navigate to `/student/batch`
2. Upload `test-large-batch.csv` (exactly 500 students)
3. Observe preview
4. Click "Submit Batch"
5. Wait for processing

**Expected Results**:
- ✅ File is accepted
- ✅ Preview shows "500 students ready for processing"
- ✅ Submit button enabled
- ✅ Submission succeeds
- ✅ Results summary displays correctly

**Status**: ⬜ Not Tested | ✅ Passed | ❌ Failed

---

### Test Case 7: Batch Size Exceeded (501 students)

**Objective**: Verify rejection of oversized batches

**Steps**:
1. Navigate to `/student/batch`
2. Upload `test-oversized-batch.csv` (501 students)
3. Observe validation error

**Expected Results**:
- ✅ Validation error displayed
- ✅ Error message: "Batch size 501 exceeds maximum of 500 students"
- ✅ Submit button disabled

**Status**: ⬜ Not Tested | ✅ Passed | ❌ Failed

---

### Test Case 8: Successful Batch Submission

**Objective**: Verify complete batch submission workflow

**Steps**:
1. Navigate to `/student/batch`
2. Upload `sample-batch.csv`
3. Verify preview table
4. Click "Submit Batch"
5. Observe progress indicator
6. Wait for completion
7. Observe results summary

**Expected Results**:
- ✅ Progress indicator shows "Processing 10 students..."
- ✅ Submit button disabled during processing
- ✅ Results summary displays after completion
- ✅ Statistics cards show counts:
  - Low risk count (green)
  - Medium risk count (amber)
  - High risk count (red)
- ✅ Results table displays student data:
  - Student name
  - Risk level (color-coded badge)
  - Risk score
  - "View Details" link
- ✅ Total counts match: low + medium + high = 10
- ✅ "Upload Another Batch" button available
- ✅ "Go to Dashboard" button available

**Status**: ⬜ Not Tested | ✅ Passed | ❌ Failed

---

### Test Case 9: View Individual Student Details

**Objective**: Verify navigation to student detail page from results

**Steps**:
1. Complete Test Case 8 (successful batch submission)
2. Click "View Details" link for any student in results table
3. Observe navigation

**Expected Results**:
- ✅ Navigates to `/student/{student_id}` page
- ✅ Student detail page loads correctly
- ✅ Risk assessment data displayed
- ✅ Can navigate back to dashboard

**Status**: ⬜ Not Tested | ✅ Passed | ❌ Failed

---

### Test Case 10: Upload Another Batch

**Objective**: Verify reset functionality after successful submission

**Steps**:
1. Complete Test Case 8 (successful batch submission)
2. Click "Upload Another Batch" button
3. Observe form reset

**Expected Results**:
- ✅ Results summary cleared
- ✅ Upload area displayed again
- ✅ Ready to upload new file
- ✅ No previous data visible

**Status**: ⬜ Not Tested | ✅ Passed | ❌ Failed

---

### Test Case 11: Clear Preview

**Objective**: Verify ability to clear preview and select different file

**Steps**:
1. Navigate to `/student/batch`
2. Upload `sample-batch.csv`
3. Observe preview
4. Click "Clear" button
5. Observe form reset

**Expected Results**:
- ✅ Preview table cleared
- ✅ Upload area displayed again
- ✅ Can upload different file
- ✅ No validation errors remain

**Status**: ⬜ Not Tested | ✅ Passed | ❌ Failed

---

### Test Case 12: API Error Handling

**Objective**: Verify graceful handling of API errors

**Steps**:
1. Stop backend server
2. Navigate to `/student/batch`
3. Upload `sample-batch.csv`
4. Click "Submit Batch"
5. Observe error handling

**Expected Results**:
- ✅ Error message displayed
- ✅ Error message is user-friendly
- ✅ Submit button re-enabled after error
- ✅ Can retry submission
- ✅ Preview data preserved

**Status**: ⬜ Not Tested | ✅ Passed | ❌ Failed

---

### Test Case 13: Navigation Bar Link

**Objective**: Verify batch upload link in navigation bar

**Steps**:
1. Navigate to any page (e.g., `/dashboard`)
2. Locate "Batch Upload" link in navigation bar
3. Click link
4. Observe navigation

**Expected Results**:
- ✅ "Batch Upload" link visible in navigation bar
- ✅ Link highlighted when on `/student/batch` page
- ✅ Clicking link navigates to batch upload page
- ✅ Link works on both desktop and mobile views

**Status**: ⬜ Not Tested | ✅ Passed | ❌ Failed

---

### Test Case 14: Mobile Responsiveness

**Objective**: Verify batch upload works on mobile devices

**Steps**:
1. Open browser developer tools
2. Switch to mobile viewport (e.g., iPhone 12)
3. Navigate to `/student/batch`
4. Test upload functionality
5. Test preview table scrolling
6. Test results display

**Expected Results**:
- ✅ Upload area displays correctly on mobile
- ✅ Instructions card readable on mobile
- ✅ Preview table scrolls horizontally if needed
- ✅ Submit button accessible
- ✅ Results summary displays correctly
- ✅ Statistics cards stack vertically on mobile
- ✅ Results table scrolls horizontally if needed

**Status**: ⬜ Not Tested | ✅ Passed | ❌ Failed

---

### Test Case 15: Empty CSV File

**Objective**: Verify handling of empty CSV files

**Steps**:
1. Create empty CSV file: `test-empty.csv`
2. Navigate to `/student/batch`
3. Upload empty file
4. Observe error handling

**Expected Results**:
- ✅ Validation error displayed
- ✅ Error message: "CSV file is empty"
- ✅ Submit button disabled

**Status**: ⬜ Not Tested | ✅ Passed | ❌ Failed

---

## Performance Tests

### Performance Test 1: Large Batch Processing Time

**Objective**: Verify batch processing completes within acceptable time

**Steps**:
1. Upload CSV with 500 students
2. Click "Submit Batch"
3. Measure time from click to results display

**Expected Results**:
- ✅ Processing completes in under 60 seconds
- ✅ Progress indicator visible throughout
- ✅ No timeout errors
- ✅ All 500 students processed

**Status**: ⬜ Not Tested | ✅ Passed | ❌ Failed

---

### Performance Test 2: CSV Parsing Speed

**Objective**: Verify CSV parsing is fast for large files

**Steps**:
1. Upload CSV with 500 students
2. Measure time from file selection to preview display

**Expected Results**:
- ✅ Parsing completes in under 2 seconds
- ✅ Preview displays immediately after parsing
- ✅ No UI freezing during parsing

**Status**: ⬜ Not Tested | ✅ Passed | ❌ Failed

---

## Accessibility Tests

### Accessibility Test 1: Keyboard Navigation

**Objective**: Verify all functionality accessible via keyboard

**Steps**:
1. Navigate to `/student/batch` using keyboard only
2. Tab through all interactive elements
3. Use Enter/Space to activate buttons
4. Test file input with keyboard

**Expected Results**:
- ✅ All buttons focusable with Tab
- ✅ Focus indicators visible
- ✅ File input accessible via keyboard
- ✅ Submit button activatable with Enter/Space
- ✅ Navigation links accessible

**Status**: ⬜ Not Tested | ✅ Passed | ❌ Failed

---

### Accessibility Test 2: Screen Reader Compatibility

**Objective**: Verify screen reader can announce all content

**Steps**:
1. Enable screen reader (e.g., NVDA, JAWS)
2. Navigate to `/student/batch`
3. Listen to announcements
4. Test all interactions

**Expected Results**:
- ✅ Page title announced
- ✅ Instructions read correctly
- ✅ Upload area described
- ✅ Validation errors announced
- ✅ Table headers announced
- ✅ Results summary announced

**Status**: ⬜ Not Tested | ✅ Passed | ❌ Failed

---

## Test Summary

### Test Execution Checklist

- [ ] All functional tests completed
- [ ] All performance tests completed
- [ ] All accessibility tests completed
- [ ] All bugs documented
- [ ] All critical bugs fixed
- [ ] Regression testing completed

### Test Results Summary

| Category | Total Tests | Passed | Failed | Not Tested |
|----------|-------------|--------|--------|------------|
| Functional | 15 | 0 | 0 | 15 |
| Performance | 2 | 0 | 0 | 2 |
| Accessibility | 2 | 0 | 0 | 2 |
| **Total** | **19** | **0** | **0** | **19** |

### Known Issues

_Document any known issues or limitations here_

### Recommendations

1. Test with real-world CSV files from users
2. Add CSV template download button
3. Consider adding CSV format validation hints
4. Add progress bar for large batch processing
5. Consider adding batch history/logs

### Sign-off

- [ ] Developer: Implementation complete
- [ ] QA: All tests passed
- [ ] Product Owner: Acceptance criteria met
- [ ] Ready for deployment

---

## Notes

- All tests should be executed in both Chrome and Firefox browsers
- Mobile tests should cover iOS Safari and Android Chrome
- Performance tests should be run on production-like environment
- Accessibility tests should use latest WCAG 2.1 AA guidelines
