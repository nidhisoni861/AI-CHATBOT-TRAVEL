# =============================================================
# Start the Travel AI Chatbot - Next.js Frontend
# Run this script from the project root:
#   .\start_frontend.ps1
# =============================================================

Write-Host ""
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host "  Travel AI Chatbot - Frontend" -ForegroundColor Cyan
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host ""

$projectRoot = $PSScriptRoot

# Check node_modules exists
if (-not (Test-Path "$projectRoot\node_modules")) {
    Write-Host "node_modules not found. Running npm install first..." -ForegroundColor Yellow
    Set-Location $projectRoot
    npm install
}

Write-Host "Frontend: http://localhost:3000" -ForegroundColor Green
Write-Host ""
Write-Host "IMPORTANT: Make sure the backend is already running" -ForegroundColor Yellow
Write-Host "           (run start_backend.ps1 in a separate terminal first)" -ForegroundColor Yellow
Write-Host ""

Set-Location $projectRoot
npm run dev
