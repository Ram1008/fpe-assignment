# Windows PowerShell Makefile Alias (make.ps1)
# Allows running .\make.ps1 <target> natively on Windows PowerShell without installing GNU make.

param (
    [string]$Target = "help"
)

$ErrorActionPreference = "Stop"
$ProjectRoot = $PSScriptRoot

# Detect python launcher (prefer 'py' on Windows if 'python' alias points to Windows Store)
$PythonCmd = if (Get-Command py -ErrorAction SilentlyContinue) { "py" } else { "python" }

switch ($Target) {
    "install" {
        Write-Host "Installing backend dependencies..." -ForegroundColor Cyan
        Set-Location "$ProjectRoot\backend"
        & $PythonCmd -m pip install -r requirements.txt
        Write-Host "Installing frontend dependencies..." -ForegroundColor Cyan
        Set-Location "$ProjectRoot\frontend"
        npm install
        Set-Location $ProjectRoot
    }
    "run" {
        Write-Host "Starting AI Decision-Tree Agent (Backend: 8000, Frontend: 3000)..." -ForegroundColor Green
        Set-Location $ProjectRoot
        & $PythonCmd run_dev.py
    }
    "backend" {
        Write-Host "Starting FastAPI Backend Server..." -ForegroundColor Cyan
        Set-Location "$ProjectRoot\backend"
        & $PythonCmd -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
    }
    "frontend" {
        Write-Host "Starting React Vite Frontend..." -ForegroundColor Cyan
        Set-Location "$ProjectRoot\frontend"
        npm run dev
    }
    "test" {
        Write-Host "Running backend pytest suite..." -ForegroundColor Cyan
        Set-Location "$ProjectRoot\backend"
        & $PythonCmd -m pytest -v
        Write-Host "Running frontend build verification..." -ForegroundColor Cyan
        Set-Location "$ProjectRoot\frontend"
        npm run build
        Set-Location $ProjectRoot
    }
    "clean" {
        Write-Host "Cleaning temporary artifacts..." -ForegroundColor Yellow
        & $PythonCmd -c "import shutil; [shutil.rmtree(p, ignore_errors=True) for p in ['backend/.pytest_cache', 'frontend/dist', 'frontend/node_modules/.cache']]"
        Set-Location $ProjectRoot
    }
    Default {
        Write-Host "AI Decision-Tree Agent PowerShell Commands (.\make.ps1 <target>):" -ForegroundColor Yellow
        Write-Host "  .\make.ps1 install  - Install backend & frontend dependencies"
        Write-Host "  .\make.ps1 run      - Run backend & frontend servers"
        Write-Host "  .\make.ps1 backend  - Run FastAPI backend (port 8000)"
        Write-Host "  .\make.ps1 frontend - Run React frontend (port 3000)"
        Write-Host "  .\make.ps1 test     - Run automated test suite"
        Write-Host "  .\make.ps1 clean    - Clean temporary files"
    }
}

