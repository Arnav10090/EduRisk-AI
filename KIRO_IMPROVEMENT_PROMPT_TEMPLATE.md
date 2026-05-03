# Kiro Improvement Prompt Template

## Instructions
After getting the review from Claude Sonnet 4.6, fill in this template with the specific issues and improvements identified, then use it as a prompt for Kiro.

---

# EduRisk AI - Make Project Submission-Ready

## Context
I have an EduRisk AI project that is currently functional but needs improvements to be submission-ready for portfolio/production purposes. Based on a comprehensive code review, I need you to implement the following changes systematically.

## Project Overview
- **Tech Stack**: FastAPI (Python), Next.js 14 (TypeScript), PostgreSQL, Redis, Docker
- **Purpose**: AI-powered placement risk assessment for education loan lenders
- **Current Status**: Functional in Docker, needs refinement for professional quality

---

## Phase 1: Critical Fixes (Must Do)

### 1.1 Security Issues
**Priority**: CRITICAL

[FILL IN FROM REVIEW]
Example:
- [ ] Fix exposed API keys in code
- [ ] Add input validation for all API endpoints
- [ ] Implement proper CORS configuration
- [ ] Add rate limiting to prevent abuse
- [ ] Sanitize error messages to not expose sensitive data

**Files to modify**:
- [List specific files]

**Acceptance Criteria**:
- [Specific criteria for completion]

---

### 1.2 Critical Backend Issues
**Priority**: CRITICAL

[FILL IN FROM REVIEW]
Example:
- [ ] Fix database connection pooling
- [ ] Implement proper error handling in all routes
- [ ] Fix async/await issues in [specific files]
- [ ] Add proper logging throughout the application
- [ ] Fix database migration issues

**Files to modify**:
- [List specific files]

**Acceptance Criteria**:
- [Specific criteria for completion]

---

### 1.3 Critical Frontend Issues
**Priority**: CRITICAL

[FILL IN FROM REVIEW]
Example:
- [ ] Fix API error handling in dashboard
- [ ] Add proper loading states for all async operations
- [ ] Fix responsive design issues on mobile
- [ ] Implement proper form validation
- [ ] Fix accessibility issues (ARIA labels, keyboard navigation)

**Files to modify**:
- [List specific files]

**Acceptance Criteria**:
- [Specific criteria for completion]

---

### 1.4 Critical Docker/Infrastructure Issues
**Priority**: CRITICAL

[FILL IN FROM REVIEW]
Example:
- [ ] Optimize Dockerfiles for production
- [ ] Fix health check configurations
- [ ] Add proper volume management for data persistence
- [ ] Configure resource limits for containers
- [ ] Fix startup dependency issues

**Files to modify**:
- [List specific files]

**Acceptance Criteria**:
- [Specific criteria for completion]

---

## Phase 2: Important Improvements (Should Do)

### 2.1 Code Quality Improvements
**Priority**: HIGH

[FILL IN FROM REVIEW]
Example:
- [ ] Add type hints to all Python functions
- [ ] Refactor large functions into smaller, testable units
- [ ] Remove code duplication in [specific areas]
- [ ] Improve variable naming for clarity
- [ ] Add docstrings to all public functions

**Files to modify**:
- [List specific files]

**Acceptance Criteria**:
- [Specific criteria for completion]

---

### 2.2 Performance Optimizations
**Priority**: HIGH

[FILL IN FROM REVIEW]
Example:
- [ ] Add database indexes for frequently queried fields
- [ ] Implement caching for expensive operations
- [ ] Optimize database queries (N+1 issues)
- [ ] Add pagination to large data endpoints
- [ ] Optimize frontend bundle size

**Files to modify**:
- [List specific files]

**Acceptance Criteria**:
- [Specific criteria for completion]

---

### 2.3 Testing Improvements
**Priority**: HIGH

[FILL IN FROM REVIEW]
Example:
- [ ] Add unit tests for all service functions
- [ ] Add integration tests for all API endpoints
- [ ] Add property-based tests as per spec
- [ ] Achieve >80% code coverage
- [ ] Add frontend component tests

**Files to create/modify**:
- [List specific test files]

**Acceptance Criteria**:
- [Specific criteria for completion]

---

### 2.4 Documentation Improvements
**Priority**: HIGH

[FILL IN FROM REVIEW]
Example:
- [ ] Update README with complete setup instructions
- [ ] Add API documentation with examples
- [ ] Document all environment variables
- [ ] Add architecture diagrams
- [ ] Create deployment guide
- [ ] Add troubleshooting section

**Files to modify**:
- [List specific files]

**Acceptance Criteria**:
- [Specific criteria for completion]

---

### 2.5 Missing Features
**Priority**: MEDIUM-HIGH

[FILL IN FROM REVIEW]
Example:
- [ ] Implement authentication/authorization
- [ ] Add email/SMS notification system
- [ ] Complete ML model training pipeline
- [ ] Add data export functionality
- [ ] Implement audit trail viewing

**Files to create/modify**:
- [List specific files]

**Acceptance Criteria**:
- [Specific criteria for completion]

---

## Phase 3: Nice-to-Have Enhancements (Optional)

### 3.1 UI/UX Enhancements
**Priority**: MEDIUM

[FILL IN FROM REVIEW]
Example:
- [ ] Add dark mode support
- [ ] Improve dashboard visualizations
- [ ] Add data filtering and search
- [ ] Implement real-time updates
- [ ] Add keyboard shortcuts

**Files to modify**:
- [List specific files]

**Acceptance Criteria**:
- [Specific criteria for completion]

---

### 3.2 Advanced Features
**Priority**: LOW-MEDIUM

[FILL IN FROM REVIEW]
Example:
- [ ] Add batch prediction upload
- [ ] Implement advanced analytics
- [ ] Add report generation
- [ ] Implement data versioning
- [ ] Add A/B testing framework

**Files to create/modify**:
- [List specific files]

**Acceptance Criteria**:
- [Specific criteria for completion]

---

## Implementation Guidelines

### For Each Task:
1. **Read relevant files** before making changes
2. **Make incremental changes** - one task at a time
3. **Test after each change** - ensure nothing breaks
4. **Update documentation** as you go
5. **Commit frequently** with clear messages

### Code Standards:
- **Python**: Follow PEP 8, use type hints, add docstrings
- **TypeScript**: Follow ESLint rules, use proper types, add JSDoc comments
- **Testing**: Write tests before or alongside code changes
- **Documentation**: Update docs immediately after code changes

### Testing Requirements:
- All new functions must have unit tests
- All API endpoints must have integration tests
- All critical paths must have property-based tests
- Maintain >80% code coverage

### Security Requirements:
- Never commit secrets or API keys
- Always validate and sanitize user input
- Use parameterized queries for database operations
- Implement proper error handling without exposing internals
- Follow OWASP security best practices

---

## Execution Plan

### Step 1: Phase 1 - Critical Fixes
Start with security issues, then backend, then frontend, then infrastructure.
**Estimated Time**: [Fill in from review]

### Step 2: Phase 2 - Important Improvements
Focus on code quality, performance, testing, and documentation.
**Estimated Time**: [Fill in from review]

### Step 3: Phase 3 - Nice-to-Have Enhancements
Implement if time permits, prioritize based on impact.
**Estimated Time**: [Fill in from review]

---

## Success Criteria

The project will be considered submission-ready when:
- [ ] All Phase 1 critical fixes are complete
- [ ] All Phase 2 important improvements are complete
- [ ] Test coverage is >80%
- [ ] All documentation is complete and accurate
- [ ] Application runs without errors in Docker
- [ ] Security scan shows no critical vulnerabilities
- [ ] Code review shows professional quality
- [ ] README provides clear setup and usage instructions
- [ ] Project can be demonstrated to potential employers

---

## Questions for Kiro

1. Should we implement authentication/authorization now or defer it?
2. What's the priority order for missing features?
3. Are there any architectural changes needed?
4. Should we add monitoring/observability tools?
5. What deployment platform should we optimize for?

---

## Additional Notes

[Add any specific context, constraints, or preferences here]

Example:
- Must maintain Docker Compose setup
- Must use Groq API (not OpenAI)
- Prefer simple solutions over complex ones
- Focus on demonstrable features for portfolio
- Code should be interview-ready

---

## Let's Start!

Please begin with **Phase 1: Critical Fixes**, starting with **1.1 Security Issues**.

For each task:
1. Confirm you understand the requirement
2. List the files you'll modify
3. Make the changes
4. Test the changes
5. Update relevant documentation
6. Move to the next task

Let me know if you need any clarification before starting!
