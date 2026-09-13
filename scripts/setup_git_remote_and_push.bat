@echo off
REM =========================================================================
REM  QMS HUB - One-Click Git Remote Configuration & Push to GitHub
REM =========================================================================

echo ========================================================================
echo   QMS HUB - PUSH TO GITHUB REPOSITORY
echo ========================================================================
echo.
echo Please enter your GitHub repository URL:
echo (Example: https://github.com/your-username/qms_hub.git)
echo.

set /p REPO_URL="Repository URL: "

if "%REPO_URL%"=="" (
    echo [ERROR] No repository URL provided. Aborting.
    pause
    exit /b 1
)

echo.
echo [1/3] Setting Git remote origin...
git remote remove origin 2>nul
git remote add origin %REPO_URL%

echo [2/3] Setting primary branch to 'main'...
git branch -M main

echo [3/3] Pushing all commits and 19 apps to GitHub...
git push -u origin main

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ========================================================================
    echo   SUCCESS! QMS Hub is now live on GitHub!
    echo   Next step: Connect your GitHub repo to Railway for Cloud Deployment.
    echo ========================================================================
) else (
    echo.
    echo [WARNING] Push encountered an issue. Please verify your credentials or permissions.
)

pause
