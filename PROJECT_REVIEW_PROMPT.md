# EduRisk AI - Comprehensive Project Review Prompt for Claude Sonnet 4.6

## Context
I have an EduRisk AI project - an AI-powered placement risk assessment system for education loan lenders. The project uses:
- **Backend**: FastAPI (Python) with PostgreSQL, Redis, SQLAlchemy
- **Frontend**: Next.js 14 (TypeScript/React) with Tailwind CSS
- **ML**: Scikit-learn for placement prediction models
- **Infrastructure**: Docker Compose for containerization
- **LLM**: Groq API for AI-powered risk summaries

The application is currently functional and running in Docker, but I need a comprehensive review to make it **submission-ready** for production/portfolio purposes.

---

## Your Task

Please perform a **thorough code review** of the entire project and identify:

1. **Critical Issues** - Must be fixed before submission
2. **Best Practice Violations** - Should be fixed for professional quality
3. **Security Vulnerabilities** - Any security concerns
4. **Performance Issues** - Optimization opportunities
5. **Code Quality Issues** - Maintainability, readability, documentation
6. **Missing Features** - Essential functionality that's incomplete
7. **Configuration Issues** - Environment setup, deployment concerns
8. **Testing Gaps** - Missing or inadequate tests
9. **Documentation Gaps** - Missing or unclear documentation
10. **UI/UX Issues** - Frontend usability and design problems

---

## Review Checklist

### 🔐 Security Review
- [ ] Are API keys and secrets properly secured?
- [ ] Is there proper input validation and sanitization?
- [ ] Are SQL injection vulnerabilities prevented?
- [ ] Is CORS configured correctly?
- [ ] Are authentication/authorization mechanisms needed?
- [ ] Are rate limits properly configured?
- [ ] Is sensitive data properly encrypted?
- [ ] Are error messages exposing sensitive information?

### 🏗️ Backend Review (FastAPI/Python)
- [ ] Is the code following Python best practices (PEP 8)?
- [ ] Are all API endpoints properly documented?
- [ ] Is error handling comprehensive and consistent?
- [ ] Are database queries optimized?
- [ ] Is the database schema properly designed?
- [ ] Are migrations working correctly?
- [ ] Is logging properly implemented?
- [ ] Are environment variables properly managed?
- [ ] Is the code modular and maintainable?
- [ ] Are there proper type hints?
- [ ] Is async/await used correctly?
- [ ] Are dependencies up to date and secure?

### 🎨 Frontend Review (Next.js/React)
- [ ] Is the code following React/Next.js best practices?
- [ ] Are components properly structured and reusable?
- [ ] Is state management appropriate?
- [ ] Are API calls properly handled (loading, error states)?
- [ ] Is the UI responsive and mobile-friendly?
- [ ] Are accessibility standards met (WCAG)?
- [ ] Is the design consistent and professional?
- [ ] Are forms properly validated?
- [ ] Is error handling user-friendly?
- [ ] Are loading states properly displayed?
- [ ] Is the routing structure logical?
- [ ] Are environment variables properly used?

### 🤖 ML/AI Review
- [ ] Are ML models properly trained and validated?
- [ ] Is model versioning implemented?
- [ ] Are predictions properly validated?
- [ ] Is the LLM integration robust (error handling, fallbacks)?
- [ ] Are SHAP explanations correctly implemented?
- [ ] Is bias detection/mitigation implemented?
- [ ] Are model artifacts properly stored?

### 🐳 Docker/Infrastructure Review
- [ ] Are Dockerfiles optimized (multi-stage builds, layer caching)?
- [ ] Is docker-compose.yml production-ready?
- [ ] Are health checks properly configured?
- [ ] Are volumes properly configured for data persistence?
- [ ] Are container resources (CPU, memory) properly limited?
- [ ] Is the startup sequence correct (dependencies)?
- [ ] Are logs properly managed?

### 📊 Database Review
- [ ] Is the schema properly normalized?
- [ ] Are indexes properly created for performance?
- [ ] Are foreign keys and constraints properly defined?
- [ ] Is data migration strategy clear?
- [ ] Are backups considered?
- [ ] Is connection pooling configured?

### 🧪 Testing Review
- [ ] Are there unit tests for critical functions?
- [ ] Are there integration tests for API endpoints?
- [ ] Are there property-based tests as mentioned in specs?
- [ ] Is test coverage adequate (>80%)?
- [ ] Are edge cases tested?
- [ ] Are error scenarios tested?

### 📚 Documentation Review
- [ ] Is the README comprehensive and clear?
- [ ] Are setup instructions accurate and complete?
- [ ] Is API documentation complete?
- [ ] Are environment variables documented?
- [ ] Is the architecture documented?
- [ ] Are deployment instructions clear?
- [ ] Is troubleshooting documentation helpful?

### 🚀 Deployment Readiness
- [ ] Is there a clear deployment strategy?
- [ ] Are production environment variables documented?
- [ ] Is there a rollback strategy?
- [ ] Are monitoring/logging solutions in place?
- [ ] Is there a backup/restore strategy?
- [ ] Are performance benchmarks documented?

### 🎯 Feature Completeness
- [ ] Are all core features implemented?
- [ ] Are all API endpoints functional?
- [ ] Is the dashboard fully functional?
- [ ] Are student management features complete?
- [ ] Are prediction features working correctly?
- [ ] Are alerts/notifications implemented?
- [ ] Is the audit trail working?

---

## Output Format

Please provide your review in the following format:

### 1. Executive Summary
- Overall project status (1-10 rating)
- Top 3 critical issues that must be fixed
- Estimated effort to make submission-ready

### 2. Critical Issues (Must Fix)
For each issue:
- **Issue**: Clear description
- **Location**: File path and line numbers
- **Impact**: Why this is critical
- **Fix**: Specific solution
- **Priority**: High/Critical

### 3. Best Practice Violations (Should Fix)
For each issue:
- **Issue**: Clear description
- **Location**: File path
- **Impact**: Why this matters
- **Fix**: Recommended solution
- **Priority**: Medium

### 4. Security Concerns
List all security vulnerabilities with severity ratings

### 5. Performance Optimizations
List performance improvements with expected impact

### 6. Code Quality Issues
List maintainability and readability concerns

### 7. Missing Features
List incomplete or missing functionality

### 8. Documentation Gaps
List missing or unclear documentation

### 9. Testing Gaps
List missing tests and coverage issues

### 10. Recommended Action Plan
Prioritized list of tasks to make the project submission-ready, grouped by:
- **Phase 1**: Critical fixes (must do)
- **Phase 2**: Important improvements (should do)
- **Phase 3**: Nice-to-have enhancements (optional)

---

## Additional Context

### Current Known Issues
1. ML models are not trained yet (placeholder models)
2. Some test files exist but may not be comprehensive
3. Authentication/authorization is not implemented
4. Email/SMS notifications are not implemented
5. Production deployment configuration may need refinement

### Project Goals
- Make it portfolio-ready for job applications
- Ensure it can be demonstrated to potential employers
- Make it production-ready (or close to it)
- Showcase best practices and professional code quality

### Constraints
- Must work with Docker Compose (no Kubernetes required)
- Must use Groq API (not OpenAI/Anthropic)
- Must maintain current tech stack (FastAPI, Next.js, PostgreSQL)
- Should be deployable on standard cloud platforms (AWS, GCP, Azure)

---

## Files to Review

Please review all files in these directories:
- `/backend/` - FastAPI backend application
- `/frontend/` - Next.js frontend application
- `/docker/` - Docker configuration files
- `/ml/` - Machine learning code
- `docker-compose.yml` - Container orchestration
- `README.md` and all documentation files
- Configuration files (`.env.example`, `pyproject.toml`, `package.json`)

---

## Expected Deliverable

A comprehensive review report that I can use to create a detailed prompt for Kiro (AI coding assistant) to implement all necessary changes to make this project submission-ready.

The report should be actionable, specific, and prioritized so that I can systematically work through the improvements.

---

## Questions to Answer

1. Is the project architecture sound?
2. Are there any major design flaws?
3. Is the code production-ready?
4. What would impress a technical interviewer?
5. What would concern a technical interviewer?
6. Is the documentation sufficient for someone to understand and run the project?
7. Are there any "red flags" that would hurt my credibility?
8. What are the "quick wins" that would significantly improve the project?

---

Thank you for your thorough review! Please be as detailed and critical as necessary - I want this project to be truly impressive and professional.
