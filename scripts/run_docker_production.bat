@echo off
REM =========================================================================
REM  QMS HUB - One-Click Production Docker Compose Launcher
REM =========================================================================

echo ========================================================================
echo   QMS HUB - STARTING ON-PREMISE PRODUCTION STACK (DOCKER)
echo ========================================================================
echo.

cd /d "%~dp0\.."

echo [1/3] Building production multi-stage Docker container...
docker compose build

echo [2/3] Starting PostgreSQL 16 Alpine and QMS Web Gunicorn containers...
docker compose up -d

echo [3/3] Checking container service health...
docker compose ps

echo.
echo ========================================================================
echo   QMS Hub Production Stack is RUNNING!
echo   Web Portal: http://localhost:8000/
echo   API Docs:   http://localhost:8000/api/v1/docs/
echo   Health:     http://localhost:8000/health/
echo ========================================================================
pause
