# =============================================================
# Start the Travel AI Chatbot - Python Backend
# Run this script from the project root:
#   .\start_backend.ps1
# =============================================================

Write-Host ""
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host "  Travel AI Chatbot - Backend" -ForegroundColor Cyan
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host ""

# Path to venv Python
$venvPython = "$PSScriptRoot\backend\venv\Scripts\python.exe"
$venvUvicorn = "$PSScriptRoot\backend\venv\Scripts\uvicorn.exe"

# Check venv exists
if (-not (Test-Path $venvPython)) {
    Write-Host "ERROR: Virtual environment not found at backend\venv" -ForegroundColor Red
    Write-Host "Please contact your setup assistant." -ForegroundColor Red
    exit 1
}

Write-Host "Python  : $venvPython" -ForegroundColor Green
Write-Host "Backend : http://localhost:8000" -ForegroundColor Green
Write-Host "API docs: http://localhost:8000/docs" -ForegroundColor Green
Write-Host ""
Write-Host "Starting backend... (model loading takes 2-4 minutes)" -ForegroundColor Yellow
Write-Host "Wait for 'Backend is ready!' message before using the chatbot." -ForegroundColor Yellow
Write-Host ""

# Start uvicorn from the backend directory so relative paths resolve correctly
Set-Location "$PSScriptRoot\backend"
& $venvUvicorn main:app --reload --port 8000
