@echo off
echo ============================================================
echo       govManage - Quick Launch
echo Backend serves both the API and the React production build.
echo ============================================================
echo.

cd /d "%~dp0"

:: ── Preflight checks ──────────────────────────────────────────
echo [0/4] Running preflight checks...

python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not found on your PATH.
    pause & exit /b 1
)

npm --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Node.js / npm is not found on your PATH.
    echo Please install Node.js 18+ from https://nodejs.org/
    pause & exit /b 1
)

if not exist ".env" (
    echo ERROR: .env not found. Run:  copy .env.example .env
    pause & exit /b 1
)
echo Preflight checks passed!
echo.

:: ── Backend venv setup ────────────────────────────────────────
echo [1/4] Checking backend virtual environment...
if not exist "backend\.venv\Scripts\python.exe" (
    echo   Creating Python virtual environment in backend\.venv...
    python -m venv backend\.venv
    echo   Installing backend dependencies (this may take a minute)...
    backend\.venv\Scripts\python.exe -m pip install --upgrade pip
    backend\.venv\Scripts\python.exe -m pip install -r backend\requirements.txt
    echo   Backend environment ready.
) else (
    echo   Backend environment already exists - skipping.
)
echo.

:: ── Build frontend if dist is missing ─────────────────────────
echo [2/4] Checking frontend build...
if not exist "frontend\dist\index.html" (
    echo   Building frontend (React/Vite)...
    if not exist "frontend\node_modules" (
        echo   Installing frontend dependencies...
        cd frontend & npm install & cd ..
    )
    cd frontend & npm run build & cd ..
    echo   Frontend built - frontend\dist\
) else (
    echo   Build already exists (frontend\dist\) - skipping.
    echo   (Run "cd frontend ^&^& npm run build" to rebuild after code changes).
)
echo.

:: ── Launch backend only ────────────────────────────────────────
echo [3/4] Starting Backend (Flask + Micro-Agents)...
start "govManage-Backend" cmd /c "title govManage-Backend & cd /d "%~dp0backend" && .venv\Scripts\python.exe serve.py"

echo.
echo [4/4] Done!
echo.
echo ============================================================
echo   govManage is running!
echo ============================================================
echo.
echo   App:        http://localhost:5000
echo   API health: http://localhost:5000/api/health
echo.
echo   To rebuild frontend after code changes:
echo     cd frontend ^&^& npm run build
echo.
echo   Run close.bat to shut down.
echo ============================================================
echo.
pause
