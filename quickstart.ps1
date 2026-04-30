# EduRisk AI - Quick Start Script (PowerShell)
# This script helps you get started with EduRisk AI quickly on Windows

$ErrorActionPreference = "Stop"

# Color functions
function Write-Success { param($Message) Write-Host "✓ $Message" -ForegroundColor Green }
function Write-Error-Custom { param($Message) Write-Host "✗ $Message" -ForegroundColor Red }
function Write-Warning-Custom { param($Message) Write-Host "⚠ $Message" -ForegroundColor Yellow }
function Write-Info { param($Message) Write-Host "ℹ $Message" -ForegroundColor Cyan }
function Write-Section { param($Message) Write-Host "`n$Message" -ForegroundColor Blue }

Write-Host "╔════════════════════════════════════════════════════════════╗" -ForegroundColor Blue
Write-Host "║         EduRisk AI - Quick Start Setup                    ║" -ForegroundColor Blue
Write-Host "║    Placement Risk Intelligence for Education Lenders      ║" -ForegroundColor Blue
Write-Host "╚════════════════════════════════════════════════════════════╝" -ForegroundColor Blue
Write-Host ""

# Check prerequisites
Write-Section "[1/6] Checking prerequisites..."

# Check Docker
try {
    $dockerVersion = docker --version
    Write-Success "Docker is installed ($dockerVersion)"
} catch {
    Write-Error-Custom "Docker is not installed"
    Write-Host "Please install Docker Desktop from https://docs.docker.com/desktop/install/windows/"
    exit 1
}

# Check Docker Compose
try {
    $composeVersion = docker-compose --version
    Write-Success "Docker Compose is installed ($composeVersion)"
} catch {
    Write-Error-Custom "Docker Compose is not installed"
    Write-Host "Please install Docker Compose from https://docs.docker.com/compose/install/"
    exit 1
}

# Check if Docker daemon is running
try {
    docker info | Out-Null
    Write-Success "Docker daemon is running"
} catch {
    Write-Error-Custom "Docker daemon is not running"
    Write-Host "Please start Docker Desktop and try again"
    exit 1
}

Write-Host ""

# Setup environment file
Write-Section "[2/6] Setting up environment configuration..."

if (Test-Path ".env") {
    Write-Warning-Custom ".env file already exists"
    $overwrite = Read-Host "Do you want to overwrite it? (y/N)"
    if ($overwrite -ne "y" -and $overwrite -ne "Y") {
        Write-Info "Using existing .env file"
    } else {
        Copy-Item ".env.example" ".env" -Force
        Write-Success "Created .env file from template"
    }
} else {
    Copy-Item ".env.example" ".env"
    Write-Success "Created .env file from template"
}

# Prompt for Anthropic API key
Write-Host ""
Write-Warning-Custom "Anthropic API Key Required"
Write-Host "EduRisk AI uses Claude AI for generating risk summaries."
Write-Host "You need an Anthropic API key to use this feature."
Write-Host ""
Write-Host "Get your API key from: https://console.anthropic.com/"
Write-Host ""
$apiKey = Read-Host "Enter your Anthropic API key (or press Enter to skip)"

if ($apiKey) {
    # Update .env file with API key
    $envContent = Get-Content ".env"
    $envContent = $envContent -replace "ANTHROPIC_API_KEY=.*", "ANTHROPIC_API_KEY=$apiKey"
    $envContent | Set-Content ".env"
    Write-Success "API key configured"
} else {
    Write-Warning-Custom "Skipped API key configuration"
    Write-Warning-Custom "  AI summaries will not be available"
    Write-Warning-Custom "  You can add it later in the .env file"
}

# Generate secret key
Write-Host ""
Write-Info "Generating secure SECRET_KEY..."
try {
    $secretKey = python -c "import secrets; print(secrets.token_urlsafe(32))"
    $envContent = Get-Content ".env"
    $envContent = $envContent -replace "SECRET_KEY=.*", "SECRET_KEY=$secretKey"
    $envContent | Set-Content ".env"
    Write-Success "Generated secure SECRET_KEY"
} catch {
    Write-Warning-Custom "Python not found, using default SECRET_KEY"
    Write-Warning-Custom "  Please change it in production!"
}

Write-Host ""

# Check ML models
Write-Section "[3/6] Checking ML models..."

$modelsExist = (Test-Path "ml/models/placement_model_3m.pkl") -and `
               (Test-Path "ml/models/placement_model_6m.pkl") -and `
               (Test-Path "ml/models/placement_model_12m.pkl") -and `
               (Test-Path "ml/models/salary_model.pkl")

if ($modelsExist) {
    Write-Success "ML models found"
} else {
    Write-Warning-Custom "ML models not found"
    Write-Info "Models will be trained on first startup"
    Write-Info "  This may take a few minutes..."
}

Write-Host ""

# Validate setup
Write-Section "[4/6] Validating setup..."

if (Test-Path "docker/validate-setup.sh") {
    Write-Info "Running validation script..."
    # Note: On Windows, we'll skip the bash script validation
    Write-Warning-Custom "Validation script requires bash, skipping on Windows"
    Write-Info "Manual validation recommended"
} else {
    Write-Warning-Custom "Validation script not found, skipping..."
}

Write-Host ""

# Start services
Write-Section "[5/6] Starting services..."
Write-Host "This may take a few minutes on first run..."
Write-Host ""

docker-compose up -d

Write-Host ""
Write-Info "Waiting for services to be ready..."

# Wait for backend to be ready
$maxAttempts = 30
$attempt = 0
$backendReady = $false

while ($attempt -lt $maxAttempts) {
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:8000/api/health" -UseBasicParsing -TimeoutSec 2
        if ($response.StatusCode -eq 200) {
            Write-Success "Backend is ready"
            $backendReady = $true
            break
        }
    } catch {
        # Ignore errors, keep trying
    }
    $attempt++
    Write-Warning-Custom "⏳ Waiting for backend... (attempt $attempt/$maxAttempts)"
    Start-Sleep -Seconds 2
}

if (-not $backendReady) {
    Write-Error-Custom "Backend failed to start"
    Write-Host "Check logs with: docker-compose logs backend"
    exit 1
}

# Wait for frontend to be ready
$attempt = 0
$frontendReady = $false

while ($attempt -lt $maxAttempts) {
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:3000" -UseBasicParsing -TimeoutSec 2
        if ($response.StatusCode -eq 200) {
            Write-Success "Frontend is ready"
            $frontendReady = $true
            break
        }
    } catch {
        # Ignore errors, keep trying
    }
    $attempt++
    Write-Warning-Custom "⏳ Waiting for frontend... (attempt $attempt/$maxAttempts)"
    Start-Sleep -Seconds 2
}

if (-not $frontendReady) {
    Write-Warning-Custom "Frontend may still be starting"
    Write-Host "Check logs with: docker-compose logs frontend"
}

Write-Host ""

# Verify deployment
Write-Section "[6/6] Verifying deployment..."

try {
    $healthResponse = Invoke-RestMethod -Uri "http://localhost:8000/api/health" -UseBasicParsing
    if ($healthResponse.status -eq "ok") {
        Write-Success "Health check passed"
        Write-Info "System status:"
        $healthResponse | ConvertTo-Json -Depth 10
    } else {
        Write-Warning-Custom "Health check returned unexpected response"
        $healthResponse | ConvertTo-Json -Depth 10
    }
} catch {
    Write-Warning-Custom "Could not verify health check"
    Write-Host $_.Exception.Message
}

Write-Host ""

# Success message
Write-Host "╔════════════════════════════════════════════════════════════╗" -ForegroundColor Green
Write-Host "║              🎉 Setup Complete! 🎉                         ║" -ForegroundColor Green
Write-Host "╚════════════════════════════════════════════════════════════╝" -ForegroundColor Green
Write-Host ""
Write-Host "Access the application:" -ForegroundColor Blue
Write-Host "  • Frontend:  " -NoNewline; Write-Host "http://localhost:3000" -ForegroundColor Green
Write-Host "  • Backend:   " -NoNewline; Write-Host "http://localhost:8000" -ForegroundColor Green
Write-Host "  • API Docs:  " -NoNewline; Write-Host "http://localhost:8000/docs" -ForegroundColor Green
Write-Host ""
Write-Host "Useful commands:" -ForegroundColor Blue
Write-Host "  • View logs:        " -NoNewline; Write-Host "docker-compose logs -f" -ForegroundColor Yellow
Write-Host "  • Stop services:    " -NoNewline; Write-Host "docker-compose down" -ForegroundColor Yellow
Write-Host "  • Restart services: " -NoNewline; Write-Host "docker-compose restart" -ForegroundColor Yellow
Write-Host "  • Run tests:        " -NoNewline; Write-Host "python test_integration.py" -ForegroundColor Yellow
Write-Host ""
Write-Host "Documentation:" -ForegroundColor Blue
Write-Host "  • README.md                - Getting started guide"
Write-Host "  • API_DOCUMENTATION.md     - Complete API reference"
Write-Host "  • DEPLOYMENT_GUIDE.md      - Production deployment"
Write-Host "  • ENVIRONMENT_VARIABLES.md - Configuration reference"
Write-Host ""
Write-Host "Happy predicting! 🚀" -ForegroundColor Green
Write-Host ""
