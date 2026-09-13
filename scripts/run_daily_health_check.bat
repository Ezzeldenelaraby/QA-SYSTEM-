@echo off
REM =========================================================================
REM  QMS HUB - Daily Compliance & Health Check Scheduled Automation Script
REM =========================================================================

echo [%date% %time%] Starting QMS Daily Compliance Check...
cd /d "%~dp0\.."
python manage.py run_quality_health_check --send-digest
echo [%date% %time%] QMS Daily Compliance Check finished with exit code %ERRORLEVEL%.
