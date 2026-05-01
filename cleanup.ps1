# EduRisk AI - Project Cleanup Script (PowerShell)
# This script removes unnecessary files and folders to reduce project size
# Run this script from the project root directory

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  EduRisk AI - Project Cleanup" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Ask for confirmation
Write-Host "This script will delete:" -ForegroundColor Yellow
Write-Host "  - Test coverage reports (htmlcov, .coverage, .pytest_cache)" -ForegroundColor Yellow
Write-Host "  - Redundant documentation files" -ForegroundColor Yellow
Write-Host "  - Task implementation summaries" -ForegroundColor Yellow
Write-Host "  - Test files (backend/test_*.py)" -ForegroundColor Yellow
Write-Host "  - Unused Docker files" -ForegroundColor Yellow
Write-Host "  - Build artifacts (.next, __pycache__)" -ForegroundColor Yellow
Write-Host "  - Empty placeholder files (.gitkeep)" -ForegroundColor Yellow
Write-Host ""
Write-Host "Estimated space to be freed: 300-500 MB" -ForegroundColor Green
Write-Host ""

$confirmation = Read-Host "Do you want to continue? (yes/no)"
if ($confirmation -ne "yes" -and $confirmation -ne "y") {
    Write-Host "Cleanup cancelled." -ForegroundColor Red
    exit
}

Write-Host ""
Write-Host "Starting cleanup..." -ForegroundColor Green
Write-Host ""

$deletedCount = 0
$errorCount = 0

# Function to safely delete files/folders
function Remove-SafeItem {
    param($Path, $Description)
    
    if (Test-Path $Path) {
        try {
            Remove-Item -Path $Path -Recurse -Force -ErrorAction Stop
            Write-Host "[OK] Deleted: $Description" -ForegroundColor Green
            return $true
        } catch {
            Write-Host "[ERROR] Failed to delete: $Description - $($_.Exception.Message)" -ForegroundColor Red
            return $false
        }
    } else {
        Write-Host "[SKIP] Not found: $Description" -ForegroundColor Gray
        return $null
    }
}

# 1. Delete test coverage reports
Write-Host "1. Removing test coverage reports..." -ForegroundColor Cyan
if (Remove-SafeItem "htmlcov" "HTML coverage reports") { $deletedCount++ }
if (Remove-SafeItem ".coverage" "Coverage data file") { $deletedCount++ }
if (Remove-SafeItem ".pytest_cache" "Pytest cache") { $deletedCount++ }

# 2. Delete redundant documentation
Write-Host ""
Write-Host "2. Removing redundant documentation..." -ForegroundColor Cyan
$docs = @(
    "DOCKER_FIXES_SUMMARY.md",
    "DOCKER_QUICKSTART.md",
    "RUN_LOCALLY.md",
    "STARTUP_INFO.md",
    "GITIGNORE_SUMMARY.md",
    "GITIGNORE_UPDATE_LOG.md",
    "GIT_SETUP.md",
    "GIT_TRACKING_GUIDE.md",
    "PROJECT_STATUS.md",
    "SETUP.md",
    ".github\GITIGNORE_QUICK_REFERENCE.md"
)
foreach ($doc in $docs) {
    if (Remove-SafeItem $doc "Documentation: $doc") { $deletedCount++ }
}

# 3. Delete task implementation summaries
Write-Host ""
Write-Host "3. Removing task implementation summaries..." -ForegroundColor Cyan
$taskFiles = @(
    "TASK_24_IMPLEMENTATION_SUMMARY.md",
    "TASK_26_INTEGRATION_SUMMARY.md",
    "backend\TASK_14_SUMMARY.md",
    "backend\TASK_16_IMPLEMENTATION_SUMMARY.md",
    "backend\TASK_17_IMPLEMENTATION_SUMMARY.md",
    "backend\TASK_18_IMPLEMENTATION_SUMMARY.md",
    "frontend\TASK_20_IMPLEMENTATION_SUMMARY.md",
    "frontend\TASK_21_IMPLEMENTATION_SUMMARY.md",
    "frontend\TASK_23_IMPLEMENTATION_SUMMARY.md"
)
foreach ($file in $taskFiles) {
    if (Remove-SafeItem $file "Task summary: $file") { $deletedCount++ }
}

# 4. Delete test files
Write-Host ""
Write-Host "4. Removing test files..." -ForegroundColor Cyan
$testFiles = @(
    "backend\demo_config.py",
    "backend\test_config.py",
    "backend\test_config_integration.py",
    "backend\test_endpoints.py",
    "backend\test_error_handling.py",
    "backend\test_rate_limit.py",
    "backend\services\test_risk_calculator.py",
    "test_integration.py"
)
foreach ($file in $testFiles) {
    if (Remove-SafeItem $file "Test file: $file") { $deletedCount++ }
}

# 5. Delete unused Docker files
Write-Host ""
Write-Host "5. Removing unused Docker files..." -ForegroundColor Cyan
$dockerFiles = @(
    "docker\Dockerfile.frontend.dev",
    "docker\validate-setup.sh",
    "docker-compose.dev.yml"
)
foreach ($file in $dockerFiles) {
    if (Remove-SafeItem $file "Docker file: $file") { $deletedCount++ }
}

# 6. Delete unused scripts
Write-Host ""
Write-Host "6. Removing unused setup scripts..." -ForegroundColor Cyan
$scripts = @(
    "quickstart.ps1",
    "quickstart.sh",
    "setup.sh"
)
foreach ($script in $scripts) {
    if (Remove-SafeItem $script "Script: $script") { $deletedCount++ }
}

# 7. Delete example configs
Write-Host ""
Write-Host "7. Removing unused example configs..." -ForegroundColor Cyan
if (Remove-SafeItem "backend\config.example.json" "Example config") { $deletedCount++ }

# 8. Delete build artifacts
Write-Host ""
Write-Host "8. Removing build artifacts (will be regenerated by Docker)..." -ForegroundColor Cyan
if (Remove-SafeItem "frontend\.next" "Next.js build output") { $deletedCount++ }
if (Remove-SafeItem "frontend\node_modules" "Node modules") { $deletedCount++ }
if (Remove-SafeItem "frontend\tsconfig.tsbuildinfo" "TypeScript build info") { $deletedCount++ }
if (Remove-SafeItem "backend\__pycache__" "Backend Python cache") { $deletedCount++ }
if (Remove-SafeItem "ml\__pycache__" "ML Python cache") { $deletedCount++ }

# 9. Delete empty placeholder files
Write-Host ""
Write-Host "9. Removing empty placeholder files..." -ForegroundColor Cyan
$gitkeeps = @(
    "backend\.gitkeep",
    "docker\.gitkeep",
    "ml\.gitkeep"
)
foreach ($file in $gitkeeps) {
    if (Remove-SafeItem $file "Placeholder: $file") { $deletedCount++ }
}

# 10. Optional: Delete spec files (commented out by default)
Write-Host ""
Write-Host "10. Spec files (SKIPPED - uncomment in script to delete)..." -ForegroundColor Yellow
# Uncomment the lines below if you want to delete spec files
# if (Remove-SafeItem ".kiro\specs" "Spec directory") { $deletedCount++ }
# if (Remove-SafeItem "Eduriskai kiro techspec.md" "Original spec document") { $deletedCount++ }

# Summary
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Cleanup Complete!" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Items deleted: $deletedCount" -ForegroundColor Green
if ($errorCount -gt 0) {
    Write-Host "Errors encountered: $errorCount" -ForegroundColor Red
}
Write-Host ""
Write-Host "Your project is now cleaner!" -ForegroundColor Green
Write-Host ""
Write-Host "Note: Build artifacts (.next, node_modules, __pycache__) will be" -ForegroundColor Yellow
Write-Host "regenerated automatically when you run 'docker-compose up --build'" -ForegroundColor Yellow
Write-Host ""
