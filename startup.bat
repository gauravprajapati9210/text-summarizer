@echo off
REM TextSummarizer Startup Script for Windows
set "PROJECT_DIR=%~dp0"

echo.
echo ========================================
echo  TextSummarizer - Startup Script
echo ========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python is not installed or not in PATH
    echo Please install Python from https://www.python.org
    pause
    exit /b 1
)

echo Step 1: Checking and installing backend dependencies...
cd /d "%PROJECT_DIR%backend"
if exist venv (
    echo Virtual environment found, activating...
    call venv\Scripts\activate.bat
) else (
    echo Creating virtual environment...
    python -m venv venv
    call venv\Scripts\activate.bat
)

echo Installing dependencies...
pip install -q -r requirements.txt
if errorlevel 1 (
    echo Error installing dependencies
    pause
    exit /b 1
)

echo.
echo ✓ Backend dependencies installed successfully!
echo.
echo ========================================
echo.
echo Starting backend server...
echo Backend will run on: http://localhost:8000
echo API Docs: http://localhost:8000/docs
echo.
echo ========================================
echo.

REM Start backend in a new window
start "TextSummarizer Backend" cmd /k "cd /d ""%PROJECT_DIR%backend"" && python main.py"

REM Start a local HTTP server for the frontend.
start "TextSummarizer Frontend" cmd /k "cd /d ""%PROJECT_DIR%frontend"" && python -m http.server 8080"

timeout /t 3

echo.
echo ✓ Backend started!
echo.
echo ========================================
echo.
echo Frontend is ready at: http://localhost:8080
echo.
echo Options to view frontend:
echo 1. VS Code: Open index.html with Live Server extension (right-click -> Open with Live Server)
echo 2. Direct: Just open frontend\index.html in your browser
echo.
echo ========================================
echo.
echo Press any key to close this window...
pause
