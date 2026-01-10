@echo off
REM Soulfra Launcher for Windows
REM Double-click this file to start Soulfra

color 0A
title Soulfra Ghost Writer Platform

echo ================================================================
echo                  SOULFRA GHOST WRITER
echo           AI-Powered Blog Platform Starting...
echo ================================================================
echo.

REM Get the directory where this batch file is located
cd /d "%~dp0"

echo Working directory: %CD%
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed!
    echo.
    echo Please install Python from: https://www.python.org/downloads/
    echo Make sure to check "Add Python to PATH" during installation
    pause
    exit /b 1
)

echo [OK] Python found:
python --version
echo.

REM Check if database exists
if not exist "soulfra.db" (
    echo [WARNING] Database not found. Initializing...
    python -c "from database import init_db; init_db()" 2>nul || echo Note: Run install.py for full setup
    echo.
)

REM Check if .env exists
if not exist ".env" (
    echo [WARNING] .env file not found. Creating default...
    (
        echo BASE_URL=http://localhost:5001
        echo SECRET_KEY=dev-secret-key-change-in-production
        echo PLATFORM_VERSION=1.0.0
    ) > .env
    echo.
)

REM Kill any existing instance on port 5001
netstat -ano | findstr :5001 | findstr LISTENING >nul 2>&1
if not errorlevel 1 (
    echo [WARNING] Port 5001 is in use. Stopping previous instance...
    for /f "tokens=5" %%a in ('netstat -ano ^| findstr :5001 ^| findstr LISTENING') do taskkill /F /PID %%a >nul 2>&1
    timeout /t 1 >nul
    echo.
)

echo [STARTING] Soulfra server...
echo URL: http://localhost:5001
echo.
echo Press Ctrl+C to stop the server
echo.

REM Start the server
python app.py

REM If server exits, pause so user can see error message
if errorlevel 1 (
    echo.
    echo [ERROR] Server stopped with errors
    echo.
    pause
)
