@echo off
echo ============================================================
echo       govManage - Quick Launch
echo ============================================================
echo.

:: Change to script directory (relative anchor — works from any clone path)
cd /d "%~dp0"

:: ── Preflight checks ──────────────────────────────────────────
echo [0/3] Running preflight checks...

python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not found on your PATH.
    echo Please install Python 3.13+ and ensure it is added to PATH.
    pause & exit /b 1
)

npm --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Node.js / npm is not found on your PATH.
    echo Please install Node.js 18+ from https://nodejs.org/
    pause & exit /b 1
)

if not exist ".env" (
    echo ERROR: .env file not found.
    echo Please copy .env.example to .env and fill in your API keys.
    echo   copy .env.example .env
    pause & exit /b 1
)

if not exist "frontend\node_modules" (
    echo Installing frontend dependencies (first-time setup)...
    cd frontend & npm install & cd ..
)

echo Preflight checks passed!
echo.

:: ── 1. Backend API + all micro-agents (single process) ────────
echo [1/3] Starting Backend API (+ Micro-Agent Pipeline)...
echo        All 9 agents boot automatically inside the backend process.
start "Backend" cmd /c "title govManage-Backend & python serve.py"
timeout /t 4 /nobreak >nul

:: ── 2. Frontend (React/Vite dev server) ───────────────────────
echo [2/3] Starting Frontend (React/Vite)...
start "Frontend" cmd /c "title govManage-Frontend & cd /d "%~dp0frontend" && npm run dev"

:: ── Done ──────────────────────────────────────────────────────
echo.
echo ============================================================
echo   All Services Launched!   (2 terminal windows)
echo ============================================================
echo.
echo   Backend API + Agents:  http://localhost:5000
echo   Frontend:              http://localhost:5173
echo.
echo   Run close.bat to shut everything down cleanly.
echo ============================================================
echo.
pause
