# Git Tracking Guide for EduRisk AI

This document explains what files are tracked in version control and what files are ignored.

## Files That ARE Tracked ✅

### Configuration Files
- `.env.example` - Template for environment variables
- `backend/.env.example` - Backend environment template
- `frontend/.env.example` - Frontend environment template
- `backend/config.example.json` - Configuration template
- `requirements.txt` - Python dependencies
- `package.json` - Node.js dependencies
- `docker-compose.yml` - Docker orchestration
- `Dockerfile` - Docker build instructions
- `.gitignore` - Git ignore rules
- `.dockerignore` - Docker ignore rules

### Source Code
- All `.py` files (Python source code)
- All `.ts`, `.tsx`, `.js`, `.jsx` files (TypeScript/JavaScript)
- All `.css`, `.scss` files (Stylesheets)
- All `.html` files (HTML templates)

### Database Migrations
- `backend/alembic/versions/*.py` - Database migration scripts
- `backend/alembic/env.py` - Alembic configuration

### ML Pipeline
- `ml/pipeline/*.py` - ML training and inference code
- `ml/data/generate_synthetic.py` - Data generation scripts
- `ml/models/version.json` - Model version tracking
- `ml/models/feature_names.json` - Feature definitions
- `ml/models/training_metrics.json` - Training metrics
- `ml/models/salary_metrics.json` - Salary model metrics

### Documentation
- `README.md` - Project documentation
- `*.md` files - Documentation files
- `.kiro/specs/` - Specification documents

### Tests
- `test_*.py` - Python test files
- `*_test.py` - Python test files
- `*.test.ts`, `*.test.tsx` - TypeScript test files

### Placeholder Files
- `.gitkeep` files - Keep empty directories in Git

## Files That Are IGNORED ❌

### Secrets & Environment Variables
- `.env` - Actual environment variables (contains secrets!)
- `backend/.env` - Backend environment variables
- `frontend/.env` - Frontend environment variables
- `*.key`, `*.pem` - Private keys and certificates
- `secrets/` - Secrets directory
- `backend/config.json` - Actual configuration (may contain secrets)

### Generated Files
- `__pycache__/` - Python bytecode cache
- `*.pyc`, `*.pyo` - Compiled Python files
- `.next/` - Next.js build output
- `node_modules/` - Node.js dependencies
- `dist/`, `build/` - Build outputs
- `*.egg-info/` - Python package metadata

### ML Models & Data
- `ml/models/*.pkl` - Trained model files (too large for Git)
- `ml/models/*.joblib` - Serialized models
- `ml/data/synthetic/*.csv` - Generated data files
- `ml/data/raw/*.csv` - Raw data files
- `ml/data/processed/*.csv` - Processed data files

**Why?** Model files are large (>100MB) and should be stored in:
- Model registry (MLflow, Weights & Biases)
- Cloud storage (S3, GCS, Azure Blob)
- Git LFS (for smaller models)

### Database Files
- `*.db`, `*.sqlite`, `*.sqlite3` - SQLite databases
- `*.dump` - Database dumps
- `dump.rdb` - Redis snapshots

### Logs & Coverage
- `*.log` - Log files
- `logs/` - Log directory
- `.coverage` - Coverage data
- `htmlcov/` - Coverage HTML reports

### IDE & OS Files
- `.vscode/` - VSCode settings (except shared configs)
- `.idea/` - JetBrains IDE settings
- `.DS_Store` - macOS metadata
- `Thumbs.db` - Windows thumbnails

### Temporary Files
- `*.tmp`, `*.temp` - Temporary files
- `*.bak`, `*.backup` - Backup files
- `*.swp`, `*.swo` - Vim swap files
- `tmp/`, `temp/` - Temporary directories

## Special Cases

### Model Files
**Tracked:**
- `ml/models/version.json` - Model version metadata
- `ml/models/feature_names.json` - Feature definitions
- `ml/models/training_metrics.json` - Performance metrics

**Ignored:**
- `ml/models/*.pkl` - Actual model binaries

**Reason:** Metadata is small and useful for tracking, but model binaries are too large.

### Environment Files
**Tracked:**
- `.env.example` - Template with placeholder values

**Ignored:**
- `.env` - Actual file with real secrets

**Reason:** Never commit secrets to version control!

### Configuration Files
**Tracked:**
- `backend/config.example.json` - Template configuration

**Ignored:**
- `backend/config.json` - Actual configuration (may contain secrets)

**Reason:** Actual configs may contain API keys or database credentials.

## Best Practices

### ✅ DO
1. **Always use `.env.example`** - Update it when adding new environment variables
2. **Commit small files** - Source code, configs, documentation
3. **Use Git LFS for large files** - If you must track large files
4. **Keep .gitkeep files** - To preserve empty directory structure
5. **Document secrets** - In `.env.example` with placeholder values

### ❌ DON'T
1. **Never commit `.env` files** - They contain secrets!
2. **Never commit API keys** - Use environment variables
3. **Never commit large model files** - Use model registry or cloud storage
4. **Never commit `node_modules/`** - Use `package.json` instead
5. **Never commit database files** - Use migrations instead
6. **Never commit logs** - They grow indefinitely

## Checking What's Ignored

To see what files are being ignored:

```bash
# List all ignored files
git status --ignored

# Check if a specific file is ignored
git check-ignore -v path/to/file

# See what would be committed
git status
```

## Accidentally Committed Secrets?

If you accidentally committed secrets:

1. **Immediately rotate the secrets** (change passwords, regenerate API keys)
2. **Remove from Git history:**
   ```bash
   # Remove file from Git but keep locally
   git rm --cached .env
   
   # Commit the removal
   git commit -m "Remove .env from tracking"
   
   # For complete history removal (use with caution!)
   git filter-branch --force --index-filter \
     "git rm --cached --ignore-unmatch .env" \
     --prune-empty --tag-name-filter cat -- --all
   ```
3. **Force push** (if working alone):
   ```bash
   git push origin --force --all
   ```

## Model Storage Recommendations

For ML models, use one of these approaches:

### 1. Model Registry (Recommended)
- **MLflow**: Track experiments and models
- **Weights & Biases**: Experiment tracking
- **Neptune.ai**: ML metadata store

### 2. Cloud Storage
- **AWS S3**: `s3://edurisk-models/`
- **Google Cloud Storage**: `gs://edurisk-models/`
- **Azure Blob Storage**: `https://edurisk.blob.core.windows.net/models/`

### 3. Git LFS (for smaller models)
```bash
# Install Git LFS
git lfs install

# Track model files
git lfs track "ml/models/*.pkl"

# Commit .gitattributes
git add .gitattributes
git commit -m "Track models with Git LFS"
```

## Summary

| Category | Tracked | Ignored | Storage |
|----------|---------|---------|---------|
| Source Code | ✅ | ❌ | Git |
| Secrets | ❌ | ✅ | Environment Variables |
| ML Models | ❌ | ✅ | Model Registry / Cloud |
| Model Metadata | ✅ | ❌ | Git |
| Dependencies | ✅ (package.json) | ✅ (node_modules/) | Package Manager |
| Database | ❌ | ✅ | Database Server |
| Migrations | ✅ | ❌ | Git |
| Logs | ❌ | ✅ | Log Aggregation |
| Documentation | ✅ | ❌ | Git |

---

**Remember:** When in doubt, check `.gitignore` or use `git check-ignore -v <file>` to see if a file is ignored.
