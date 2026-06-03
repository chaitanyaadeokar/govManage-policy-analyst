@echo off
:: ──────────────────────────────────────────────────────────────────────────────
:: govManage - Virtual Environment Setup Helper (Windows)
::
:: Run this ONCE after cloning to create a venv inside backend/ and install deps.
:: After that, activate the venv and run launch.bat.
:: ──────────────────────────────────────────────────────────────────────────────
cd /d "%~dp0backend"

if not exist ".venv\Scripts\python.exe" (
    echo Creating Python virtual environment in backend\.venv ...
    python -m venv .venv
)

echo Activating virtual environment...
call .venv\Scripts\activate.bat

echo Installing Python dependencies...
pip install -r requirements.txt

echo.
echo Setup complete! Your virtual environment is active.
echo Run launch.bat (from repo root) to start all services.
echo.