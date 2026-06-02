@echo off
echo ============================================================
echo       govManage - Quick Launch
echo ============================================================
echo.
echo Starting all services...
echo.

:: Change to script directory
cd /d "%~dp0"

:: Launch Backend API (Flask app.py)
echo [1/3] Starting Backend API (Flask)...
start "Backend-API" cmd /c "title Backend-API & uv run python serve.py"
timeout /t 2 /nobreak >nul

:: Launch All Micro-Agents
echo [2/3] Starting Micro-Agents...
start "AG-Orchestrator" cmd /c "title AG-Orchestrator & uv run python agents_micro\orchestrator\main.py"
start "AG-PolicyAnalyst" cmd /c "title AG-PolicyAnalyst & uv run python agents_micro\policy_analyst\main.py"
start "AG-Compliance" cmd /c "title AG-Compliance & uv run python agents_micro\compliance\main.py"
start "AG-RiskAssessment" cmd /c "title AG-RiskAssessment & uv run python agents_micro\risk_assessment\main.py"
start "AG-DecisionEngine" cmd /c "title AG-DecisionEngine & uv run python agents_micro\decision_engine\main.py"
start "AG-Audit" cmd /c "title AG-Audit & uv run python agents_micro\audit\main.py"
start "AG-Reporting" cmd /c "title AG-Reporting & uv run python agents_micro\reporting\main.py"
start "AG-Feedback" cmd /c "title AG-Feedback & uv run python agents_micro\feedback\main.py"
start "AG-Persistence" cmd /c "title AG-Persistence & uv run python agents_micro\persistence\main.py"
timeout /t 3 /nobreak >nul

:: Launch Frontend (React/Vite)
echo [3/3] Starting Frontend (React/Vite)...
start "Frontend-Vite" cmd /c "title Frontend-Vite & cd /d "%~dp0frontend" && npx serve -s dist -p 5173"

echo.
echo ============================================================
echo   All Services Launched!
echo ============================================================
echo.
echo   Backend API:  http://localhost:5000
echo   Frontend:     http://localhost:5173
echo.
echo   Keep all terminal windows open for the system to work!
echo   Close individual windows to stop services.
echo ============================================================
echo.
pause
