<#
Start the Wanderly model backend in Windows PowerShell on port 9000.
Run from anywhere; this script finds the project root automatically.

Usage:
  .\backend_fine_tuning\start_backend_windows.ps1
  powershell -ExecutionPolicy Bypass -File .\backend_fine_tuning\start_backend_windows.ps1
#>

$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent $ScriptDir
$VenvDir = Join-Path $ScriptDir ".venv"
$PreferredPython = Join-Path $env:LOCALAPPDATA "Programs\Python\Python311\python.exe"

Write-Host "[Windows] Project root : $ProjectRoot"
Write-Host "[Windows] Backend dir  : $ScriptDir"

# Python environment
if (-not (Test-Path $VenvDir)) {
    Write-Host "[Windows] Creating Windows venv at $VenvDir ..."
    if (Test-Path $PreferredPython) {
        & $PreferredPython -m venv $VenvDir
    } else {
        python -m venv $VenvDir
    }

    Write-Host "[Windows] Installing dependencies..."
    & (Join-Path $VenvDir "Scripts\python.exe") -m pip install --upgrade pip --quiet
    & (Join-Path $VenvDir "Scripts\pip.exe") install -r (Join-Path $ScriptDir "requirements.txt") --quiet
}

$Python = Join-Path $VenvDir "Scripts\python.exe"
$Uvicorn = Join-Path $VenvDir "Scripts\uvicorn.exe"

if (-not (Test-Path $Python)) {
    throw "[Windows] Python executable not found in venv: $Python"
}

$PythonVersion = (& $Python -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}')").Trim()
Write-Host "[Windows] Python       : $PythonVersion"

if ($PythonVersion -match "^3\.13\.") {
    Write-Host "[Windows] WARNING: Python 3.13 may not be supported by some ML dependencies. Python 3.10 or 3.11 is safer."
}

# Make backend_fine_tuning importable.
# PROJECT_ROOT contains the backend_fine_tuning/ package directory.
if ($env:PYTHONPATH) {
    $env:PYTHONPATH = "$ProjectRoot;$env:PYTHONPATH"
} else {
    $env:PYTHONPATH = $ProjectRoot
}

# Best-effort editable install; works because pyproject.toml is present.
try {
    & (Join-Path $VenvDir "Scripts\pip.exe") install -e $ProjectRoot --quiet | Out-Null
} catch {
    Write-Host "[Windows] Editable install skipped: $($_.Exception.Message)"
}

# Environment variables
$EnvFile = Join-Path $ScriptDir ".env"
if (Test-Path $EnvFile) {
    Write-Host "[Windows] Loading env from $EnvFile"

    Get-Content $EnvFile | ForEach-Object {
        $Line = $_.Trim()
        if (-not $Line -or $Line.StartsWith("#") -or -not $Line.Contains("=")) {
            return
        }

        $Parts = $Line.Split("=", 2)
        $Key = $Parts[0].Trim()
        $Value = $Parts[1].Trim()

        if ($Value.Contains("#")) {
            $Value = $Value.Split("#", 2)[0].Trim()
        }

        if ($Key) {
            [Environment]::SetEnvironmentVariable($Key, $Value, "Process")
        }
    }
} else {
    Write-Host "[Windows] WARNING: $EnvFile not found. Copy .env.example -> .env and fill in your tokens."
}

# Defaults can be overridden by .env or caller environment.
if (-not $env:BACKEND_PRELOAD_MODEL) { $env:BACKEND_PRELOAD_MODEL = "fine_tuned" }
if (-not $env:MODEL_MAX_NEW_TOKENS) { $env:MODEL_MAX_NEW_TOKENS = "3000" }
if (-not $env:MODEL_MAX_INPUT_TOKENS) { $env:MODEL_MAX_INPUT_TOKENS = "2000" }
if (-not $env:MODEL_TEMPERATURE) { $env:MODEL_TEMPERATURE = "0.0" }

$HostName = if ($env:BACKEND_HOST) { $env:BACKEND_HOST } else { "127.0.0.1" }
$Port = if ($env:BACKEND_PORT) { $env:BACKEND_PORT } else { "9000" }

Write-Host ""
Write-Host "[Windows] PYTHONPATH              : $env:PYTHONPATH"
Write-Host "[Windows] BACKEND_PRELOAD_MODEL   : $env:BACKEND_PRELOAD_MODEL"
Write-Host "[Windows] MODEL_MAX_NEW_TOKENS    : $env:MODEL_MAX_NEW_TOKENS"
Write-Host "[Windows] Binding                 : ${HostName}:$Port"
Write-Host ""

# Run from PROJECT_ROOT so package imports resolve cleanly.
Set-Location $ProjectRoot
& $Uvicorn backend_fine_tuning.app.main:app `
    --host $HostName `
    --port $Port `
    --workers 1 `
    --log-level info
