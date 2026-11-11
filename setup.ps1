# ==============================================================================
# EZIO — Automated Local Setup Helper (Windows PowerShell)
# Automates Python venv creation, dependency installation, and frontend setup.
# ==============================================================================

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "  EZIO — Automated Local Setup Helper" -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

# 1. Check Python
Write-Host "`n[1/5] Checking Python installation..." -ForegroundColor Yellow
$pyLauncher = Get-Command py -ErrorAction SilentlyContinue
$pythonCmd = Get-Command python -ErrorAction SilentlyContinue

$basePython = "python"
if ($pyLauncher) {
    # Prefer supported Python 3.13 or 3.12 if py launcher is available
    $v313 = py -3.13 -c "import sys; print(sys.version_info.major)" 2>$null
    if ($v313 -eq "3") {
        $basePython = "py -3.13"
    } else {
        $v312 = py -3.12 -c "import sys; print(sys.version_info.major)" 2>$null
        if ($v312 -eq "3") {
            $basePython = "py -3.12"
        }
    }
}

if (-not $pythonCmd -and $basePython -eq "python") {
    Write-Host "ERROR: Python is not found in your PATH." -ForegroundColor Red
    Write-Host "Please install Python 3.11, 3.12, or 3.13 from https://www.python.org/downloads/" -ForegroundColor White
    Write-Host "Be sure to check 'Add Python to PATH' during installation." -ForegroundColor White
    exit 1
}

if ($basePython -like "py *") {
    $parts = $basePython.Split(" ")
    $pythonVersion = & $parts[0] $parts[1] --version 2>&1
} else {
    $pythonVersion = python --version 2>&1
}
Write-Host "Found: $pythonVersion ($basePython)" -ForegroundColor Green

# 2. Check Node.js & npm
Write-Host "`n[2/5] Checking Node.js and npm..." -ForegroundColor Yellow
$nodeCmd = Get-Command node -ErrorAction SilentlyContinue
$npmCmd = Get-Command npm -ErrorAction SilentlyContinue
if (-not $nodeCmd -or -not $npmCmd) {
    Write-Host "ERROR: Node.js or npm is not found in your PATH." -ForegroundColor Red
    Write-Host "Please install Node.js (v18+ or v20+ recommended) from https://nodejs.org/" -ForegroundColor White
    exit 1
}
$nodeVersion = node --version
$npmVersion = npm --version
Write-Host "Found: Node.js $nodeVersion (npm $npmVersion)" -ForegroundColor Green

# 3. Create Virtual Environment & Install Python Dependencies
Write-Host "`n[3/5] Setting up Python virtual environment..." -ForegroundColor Yellow
if (-not (Test-Path ".venv")) {
    Write-Host "Creating virtual environment in .venv..." -ForegroundColor Gray
    if ($basePython -like "py *") {
        $parts = $basePython.Split(" ")
        & $parts[0] $parts[1] -m venv .venv
    } else {
        python -m venv .venv
    }
    if ($LASTEXITCODE -ne 0) {
        Write-Host "ERROR: Failed to create virtual environment." -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host "Virtual environment .venv already exists." -ForegroundColor Gray
}

$venvPython = ".\.venv\Scripts\python.exe"
if (-not (Test-Path $venvPython)) {
    Write-Host "ERROR: Virtual environment python executable not found at $venvPython" -ForegroundColor Red
    exit 1
}

Write-Host "Installing Python dependencies from requirements.txt..." -ForegroundColor Gray
& $venvPython -m pip install --upgrade pip --quiet
& $venvPython -m pip install -r requirements.txt
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Failed to install Python dependencies." -ForegroundColor Red
    exit 1
}
Write-Host "Python dependencies installed successfully." -ForegroundColor Green

# 4. Configure Environment & Data
Write-Host "`n[4/5] Checking environment configuration and ChromaDB..." -ForegroundColor Yellow
if (-not (Test-Path ".env")) {
    if (Test-Path ".env.example") {
        Write-Host "Creating .env from .env.example..." -ForegroundColor Gray
        Copy-Item ".env.example" ".env"
    } else {
        Write-Host "Generating default .env template..." -ForegroundColor Gray
        "GROQ_API_KEY=your_groq_api_key_here`nENVIRONMENT=development`nALLOWED_ORIGINS=http://localhost:5173,http://localhost:3000" | Out-File -Encoding utf8 ".env"
    }
}
Write-Host "Environment configuration .env is ready." -ForegroundColor Green

# Check if ChromaDB exists, build if missing
$chromaDbPath = "data\chroma"
$needChromaBuild = $true
if (Test-Path $chromaDbPath) {
    $hasItems = (Get-ChildItem $chromaDbPath -ErrorAction SilentlyContinue | Measure-Object).Count -gt 0
    if ($hasItems) {
        $needChromaBuild = $false
        Write-Host "ChromaDB collections already indexed." -ForegroundColor Green
    }
}

if ($needChromaBuild) {
    Write-Host "Building local ChromaDB vector collections from precomputed embeddings..." -ForegroundColor Gray
    & $venvPython scripts\build_chroma_index.py
    if ($LASTEXITCODE -ne 0) {
        Write-Host "WARNING: ChromaDB build script encountered an issue. Backend will attempt to build on demand." -ForegroundColor Yellow
    } else {
        Write-Host "ChromaDB vector store indexed successfully." -ForegroundColor Green
    }
}

# 5. Install Frontend Dependencies
Write-Host "`n[5/5] Installing frontend dependencies..." -ForegroundColor Yellow
Push-Location frontend
if (Test-Path "package-lock.json") {
    npm ci
} else {
    npm install
}
$frontendExit = $LASTEXITCODE
Pop-Location

if ($frontendExit -ne 0) {
    Write-Host "ERROR: Failed to install frontend dependencies." -ForegroundColor Red
    exit 1
}
Write-Host "Frontend dependencies installed successfully." -ForegroundColor Green

Write-Host "`n==========================================================" -ForegroundColor Cyan
Write-Host "  Setup Complete! EZIO is ready to run." -ForegroundColor Green
Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "`nTo run EZIO, open two terminal tabs:" -ForegroundColor White
Write-Host "  Terminal 1 (Backend):" -ForegroundColor Yellow
Write-Host "    .\.venv\Scripts\activate" -ForegroundColor White
Write-Host "    uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload" -ForegroundColor White
Write-Host "`n  Terminal 2 (Frontend):" -ForegroundColor Yellow
Write-Host "    cd frontend" -ForegroundColor White
Write-Host "    npm run dev" -ForegroundColor White
Write-Host "`nThen open your browser at: http://localhost:5173" -ForegroundColor Cyan
Write-Host "==========================================================`n" -ForegroundColor Cyan
