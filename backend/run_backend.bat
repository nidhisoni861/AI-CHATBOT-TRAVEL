@echo off
title AI Travel Assistant Backend
echo ========================================
echo   AI Travel Assistant Backend
echo ========================================
echo.

REM Check if virtual environment exists
if not exist "venv\Scripts\python.exe" (
    echo [ERROR] Virtual environment not found!
    echo.
    echo Please run first-time setup:
    echo   python -m venv venv
    echo   .\venv\Scripts\activate
    echo   pip install -r requirements.txt
    echo.
    echo Press any key to exit...
    pause > nul
    exit /b 1
)

REM Check if requirements are installed
echo Checking requirements...
venv\Scripts\python.exe -c "import fastapi" 2>nul
if errorlevel 1 (
    echo [ERROR] Requirements not installed!
    echo.
    echo Please install requirements:
    echo   .\venv\Scripts\activate
    echo   pip install -r requirements.txt
    echo.
    echo Press any key to exit...
    pause > nul
    exit /b 1
)

echo Starting FastAPI backend...
echo Server will be available at: http://localhost:8000
echo API Documentation: http://localhost:8000/docs
echo.
echo Press Ctrl+C to stop the server
echo ========================================
echo.

REM Start the FastAPI backend
venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8000

REM Keep terminal open if there's an error
if errorlevel 1 (
    echo.
    echo [ERROR] Backend failed to start!
    echo Press any key to exit...
    pause > nul
    exit /b 1
)
