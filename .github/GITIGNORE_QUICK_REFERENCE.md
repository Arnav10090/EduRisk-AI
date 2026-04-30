# .gitignore Quick Reference Card

## 🚀 Quick Commands

```bash
# Check if file is ignored
git check-ignore -v <file>

# See all ignored files
git status --ignored

# Remove file from Git (keep locally)
git rm --cached <file>

# Test .gitignore before committing
git add --dry-run .
```

## ✅ What IS Tracked

- ✅ Source code (`*.py`, `*.ts`, `*.tsx`)
- ✅ Configuration templates (`.env.example`)
- ✅ Dependencies (`requirements.txt`, `package.json`)
- ✅ Documentation (`*.md`)
- ✅ Database migrations (`alembic/versions/*.py`)
- ✅ ML metadata (`version.json`, `feature_names.json`)

## ❌ What is NOT Tracked

- ❌ Secrets (`.env`, `*.key`, `config.json`)
- ❌ ML models (`*.pkl`, `*.joblib`)
- ❌ Data files (`*.csv`, `*.parquet`)
- ❌ Generated files (`__pycache__/`, `node_modules/`)
- ❌ Databases (`*.db`, `*.sqlite`)
- ❌ Logs (`*.log`, `logs/`)
- ❌ IDE files (`.vscode/`, `.idea/`)

## 🔒 Security Checklist

- [ ] Never commit `.env` files
- [ ] Never commit API keys or passwords
- [ ] Never commit private keys (`*.key`, `*.pem`)
- [ ] Always use `.env.example` for templates
- [ ] Rotate secrets if accidentally committed

## 📦 Large Files

**Don't commit:**
- ML models (>100MB)
- Datasets (>10MB)
- Videos/images (>5MB)

**Instead use:**
- Model Registry (MLflow, W&B)
- Cloud Storage (S3, GCS)
- Git LFS (for smaller files)

## 🆘 Emergency: Committed Secret

```bash
# 1. IMMEDIATELY rotate the secret
# 2. Remove from Git
git rm --cached .env
git commit -m "Remove .env from tracking"

# 3. Add to .gitignore (if not already)
echo ".env" >> .gitignore
git add .gitignore
git commit -m "Add .env to gitignore"

# 4. Force push (if working alone)
git push --force
```

## 📋 Common Patterns

```bash
# Ignore all .env files
.env
.env.*

# Except .env.example
!.env.example

# Ignore all .pkl files
*.pkl

# Ignore directory
node_modules/

# Ignore files in directory
logs/*.log

# Keep empty directory
!logs/.gitkeep
```

## 🔍 Verification

```bash
# Before first commit
git status                    # Should not show .env, *.pkl, node_modules/
git check-ignore -v .env      # Should show it's ignored
git check-ignore -v *.pkl     # Should show it's ignored

# After adding files
git add .
git status                    # Review what will be committed
```

## 📚 Full Documentation

- **`.gitignore`** - The actual rules
- **`GIT_TRACKING_GUIDE.md`** - Detailed explanation
- **`GIT_SETUP.md`** - Setup instructions
- **`GITIGNORE_SUMMARY.md`** - Complete summary

---

**Need Help?** Check `GIT_TRACKING_GUIDE.md` for detailed information.
