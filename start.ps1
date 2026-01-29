# RONIN - Universal Startup Script
# This script ensures Prerequisites are installed, sets up environments, and runs both servers.

Write-Host "--- RONIN: Starting Setup & Launch ---" -ForegroundColor Cyan

function Check-AndInstall($Name, $Command, $ID) {
    Write-Host "Checking for $Name..." -NoNewline
    $path = Get-Command $Command -ErrorAction SilentlyContinue
    if ($path) {
        Write-Host " FOUND" -ForegroundColor Green
    } else {
        Write-Host " NOT FOUND. Installing via winget..." -ForegroundColor Yellow
        winget install --id $ID --silent --accept-package-agreements --accept-source-agreements
        if ($LASTEXITCODE -ne 0) {
            Write-Error "Failed to install $Name. Please install it manually."
            exit 1
        }
    }
}

# 1. Check/Install Prerequisites
Check-AndInstall "Python" "python" "Python.Python.3.12"
Check-AndInstall "Node.js" "node" "OpenJS.NodeJS.LTS"

# 2. Setup Backend
Write-Host "`n[1/3] Setting up Backend..." -ForegroundColor Cyan
cd backend
if (-not (Test-Path "venv")) {
    Write-Host "Creating virtual environment..." -ForegroundColor Gray
    python -m venv venv
}
Write-Host "Installing/Updating dependencies..." -ForegroundColor Gray
.\venv\Scripts\python -m pip install --upgrade pip --quiet
.\venv\Scripts\pip install -r requirements.txt --quiet
cd ..

# 3. Setup Frontend
Write-Host "`n[2/3] Setting up Frontend..." -ForegroundColor Cyan
cd frontend
if (-not (Test-Path "node_modules")) {
    Write-Host "Installing dependencies (this may take a minute)..." -ForegroundColor Gray
    npm install --silent
}
cd ..

# 4. Launch Application
Write-Host "`n[3/3] Launching RONIN!" -ForegroundColor Green
Write-Host "------------------------------------------------"
Write-Host "Backend: http://localhost:8000" -ForegroundColor Gray
Write-Host "Frontend: http://localhost:3000" -ForegroundColor Gray
Write-Host "------------------------------------------------"

# Start Backend in a new window
# We use -NoExit so the window stays open if it crashes
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd backend; .\venv\Scripts\python -m uvicorn app.main:app --reload --port 8000"

# Start Frontend in the current window
cd frontend
npm run dev
