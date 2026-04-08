@echo off
echo ==============================================
echo Launching Goverance Micro-Agents...
echo ==============================================

REM Start the main chain
start "AG-Orchestrator" cmd /k "uv run agents_micro\orchestrator\main.py"
start "AG-PolicyAnalyst" cmd /k "uv run agents_micro\policy_analyst\main.py"
start "AG-Compliance" cmd /k "uv run agents_micro\compliance\main.py"
start "AG-RiskAssessment" cmd /k "uv run agents_micro\risk_assessment\main.py"
start "AG-DecisionEngine" cmd /k "uv run agents_micro\decision_engine\main.py"
start "AG-Audit" cmd /k "uv run agents_micro\audit\main.py"
start "AG-Reporting" cmd /k "uv run agents_micro\reporting\main.py"
start "AG-Feedback" cmd /k "uv run agents_micro\feedback\main.py"
start "AG-Persistence" cmd /k "uv run agents_micro\persistence\main.py"

echo.
echo All micro-agents launched in background windows.
echo Keep those windows open for the system to process events!
echo.
pause
