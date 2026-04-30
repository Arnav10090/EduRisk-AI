# Git Repository Setup Guide

## Initial Setup

This project is ready to be initialized as a Git repository. Follow these steps:

### 1. Initialize Git Repository

```bash
# Initialize the repository
git init

# Check that .gitignore is working
git status
```

### 2. Configure Git (First Time Only)

```bash
# Set your name and email
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"

# Optional: Set default branch name to 'main'
git config --global init.defaultBranch main
```

### 3. Create Initial Commit

```bash
# Add all files (respecting .gitignore)
git add .

# Create initial commit
git commit -m "Initial commit: EduRisk AI - Placement Risk Intelligence

- FastAPI backend with async database operations
- Next.js frontend with TypeScript
- ML pipeline with XGBoost and SHAP
- Docker containerization
- Comprehensive error handling and logging
- Rate limiting and CORS middleware
- Database migrations with Alembic
- Structured logging with JSON format"

# Check commit
git log --oneline
```

### 4. Connect to Remote Repository (Optional)

```bash
# Add remote repository (GitHub/GitLab/Bitbucket)
git remote add origin https://github.com/yourusername/edurisk-ai.git

# Or using SSH
git remote add origin git@github.com:yourusername/edurisk-ai.git

# Verify remote
git remote -v

# Push to remote
git branch -M main
git push -u origin main
```

## What Will Be Committed

### ✅ Files That WILL Be Committed

**Configuration:**
- `.gitignore`, `.dockerignore`
- `requirements.txt`, `package.json`
- `docker-compose.yml`, `Dockerfile`
- `.env.example` files

**Source Code:**
- All Python files (`backend/**/*.py`, `ml/**/*.py`)
- All TypeScript/JavaScript files (`frontend/**/*.ts`, `frontend/**/*.tsx`)
- All CSS files

**Documentation:**
- All `.md` files (README, guides, specs)
- `.kiro/specs/` directory

**Database Migrations:**
- `backend/alembic/versions/*.py`

**ML Metadata:**
- `ml/models/version.json`
- `ml/models/feature_names.json`
- `ml/models/training_metrics.json`

### ❌ Files That Will NOT Be Committed

**Secrets:**
- `.env` files (actual environment variables)
- `backend/config.json` (actual configuration)
- `*.key`, `*.pem` (private keys)

**Generated Files:**
- `__pycache__/`, `*.pyc`
- `node_modules/`
- `.next/`, `build/`, `dist/`

**ML Models:**
- `ml/models/*.pkl` (trained models - too large)
- `ml/data/**/*.csv` (data files)

**Databases:**
- `*.db`, `*.sqlite`

**Logs:**
- `*.log`, `logs/`

**IDE Files:**
- `.vscode/`, `.idea/`
- `.DS_Store`, `Thumbs.db`

## Verify .gitignore is Working

```bash
# Check what files are ignored
git status --ignored

# Check if a specific file is ignored
git check-ignore -v backend/.env
git check-ignore -v ml/models/placement_model_3m.pkl

# Should show these files are ignored
```

## Branch Strategy (Recommended)

### Main Branches
- `main` - Production-ready code
- `develop` - Integration branch for features

### Feature Branches
```bash
# Create feature branch
git checkout -b feature/user-authentication

# Work on feature...
git add .
git commit -m "Add user authentication"

# Push feature branch
git push -u origin feature/user-authentication

# Merge to develop (after review)
git checkout develop
git merge feature/user-authentication
```

### Hotfix Branches
```bash
# Create hotfix from main
git checkout main
git checkout -b hotfix/fix-critical-bug

# Fix bug...
git add .
git commit -m "Fix critical bug in prediction service"

# Merge to main and develop
git checkout main
git merge hotfix/fix-critical-bug
git checkout develop
git merge hotfix/fix-critical-bug
```

## Commit Message Conventions

Use conventional commits for better changelog generation:

```bash
# Format: <type>(<scope>): <subject>

# Types:
feat:     # New feature
fix:      # Bug fix
docs:     # Documentation changes
style:    # Code style changes (formatting, etc.)
refactor: # Code refactoring
test:     # Adding or updating tests
chore:    # Maintenance tasks

# Examples:
git commit -m "feat(api): add batch scoring endpoint"
git commit -m "fix(ml): correct SHAP value calculation"
git commit -m "docs(readme): update installation instructions"
git commit -m "test(prediction): add unit tests for risk calculator"
git commit -m "refactor(logging): improve error handling middleware"
```

## Useful Git Commands

### Status and Diff
```bash
# Check status
git status

# See changes
git diff

# See staged changes
git diff --staged

# See changes in specific file
git diff backend/main.py
```

### Staging and Committing
```bash
# Stage specific files
git add backend/main.py backend/config.py

# Stage all changes
git add .

# Stage all Python files
git add "*.py"

# Unstage file
git restore --staged backend/main.py

# Discard changes
git restore backend/main.py
```

### History
```bash
# View commit history
git log

# Compact history
git log --oneline

# History with graph
git log --oneline --graph --all

# History for specific file
git log -- backend/main.py
```

### Branches
```bash
# List branches
git branch

# Create branch
git branch feature/new-feature

# Switch branch
git checkout feature/new-feature

# Create and switch
git checkout -b feature/new-feature

# Delete branch
git branch -d feature/new-feature

# Delete remote branch
git push origin --delete feature/new-feature
```

### Remote Operations
```bash
# Fetch changes
git fetch origin

# Pull changes
git pull origin main

# Push changes
git push origin main

# Push new branch
git push -u origin feature/new-feature
```

## Pre-commit Hooks (Optional)

Install pre-commit hooks to automatically check code before committing:

```bash
# Install pre-commit
pip install pre-commit

# Create .pre-commit-config.yaml
cat > .pre-commit-config.yaml << 'EOF'
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.5.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files
        args: ['--maxkb=10000']
      - id: check-json
      - id: check-merge-conflict
      - id: detect-private-key

  - repo: https://github.com/psf/black
    rev: 23.12.1
    hooks:
      - id: black
        language_version: python3.12

  - repo: https://github.com/pycqa/flake8
    rev: 7.0.0
    hooks:
      - id: flake8
        args: ['--max-line-length=100']

  - repo: https://github.com/pycqa/isort
    rev: 5.13.2
    hooks:
      - id: isort
        args: ['--profile', 'black']
EOF

# Install hooks
pre-commit install

# Run manually
pre-commit run --all-files
```

## Troubleshooting

### Accidentally Committed .env File

```bash
# Remove from Git but keep locally
git rm --cached backend/.env

# Commit the removal
git commit -m "Remove .env from tracking"

# Push changes
git push
```

### Large Files Error

```bash
# If you accidentally try to commit large model files
# Remove from staging
git reset HEAD ml/models/placement_model_3m.pkl

# Verify .gitignore includes it
cat .gitignore | grep "*.pkl"
```

### Merge Conflicts

```bash
# When pulling changes causes conflicts
git pull origin main

# Fix conflicts in files marked with <<<<<<< and >>>>>>>
# Then stage resolved files
git add conflicted-file.py

# Complete merge
git commit -m "Resolve merge conflicts"
```

## GitHub/GitLab Setup

### Create Repository on GitHub

1. Go to https://github.com/new
2. Name: `edurisk-ai`
3. Description: "AI-powered placement risk assessment for education loan lenders"
4. **Do NOT** initialize with README (we already have one)
5. Click "Create repository"

### Push to GitHub

```bash
# Add remote
git remote add origin https://github.com/yourusername/edurisk-ai.git

# Push
git branch -M main
git push -u origin main
```

### Set Up Branch Protection (Recommended)

On GitHub:
1. Go to Settings → Branches
2. Add rule for `main` branch
3. Enable:
   - Require pull request reviews
   - Require status checks to pass
   - Require branches to be up to date

## Summary Checklist

- [ ] Initialize Git repository (`git init`)
- [ ] Configure Git user name and email
- [ ] Verify `.gitignore` is working (`git status`)
- [ ] Create initial commit
- [ ] Create remote repository (GitHub/GitLab)
- [ ] Add remote origin
- [ ] Push to remote
- [ ] Set up branch protection (optional)
- [ ] Install pre-commit hooks (optional)
- [ ] Document workflow for team

---

**Next Steps:** After setting up Git, refer to `GIT_TRACKING_GUIDE.md` for details on what files are tracked and best practices.
