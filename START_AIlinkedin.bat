@echo off
setlocal
cd /d "%~dp0"

echo ========================================
echo AIlinkedin - local startup
echo ========================================

where docker >nul 2>&1
if errorlevel 1 (
  echo [ERROR] Docker was not found in PATH.
  echo Start Docker Desktop and run this file again.
  pause
  exit /b 1
)

docker info >nul 2>&1
if errorlevel 1 (
  echo [ERROR] Docker Desktop is not running.
  echo Start Docker Desktop and run this file again.
  pause
  exit /b 1
)

if not exist ".env" (
  echo Creating .env from .env.example...
  copy /Y ".env.example" ".env" >nul
  if errorlevel 1 (
    echo [ERROR] Could not create .env.
    pause
    exit /b 1
  )
  echo.
  echo IMPORTANT:
  echo Open .env and fill OPENAI_API_KEY and APIFY_API_TOKEN.
  echo For email notifications also fill BREVO_API_KEY and
  echo NOTIFICATION_SENDER_EMAIL.
  echo.
  pause
)

echo Starting AIlinkedin...
docker compose up --build

endlocal
