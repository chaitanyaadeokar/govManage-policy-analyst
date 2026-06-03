@echo off
:: ──────────────────────────────────────────────────────────────
:: govManage - Virtual Environment Setup Helper (Windows)
::
:: Run this ONCE after cloning to create a venv and install deps.
:: After that, just run launch.bat — it uses the venv Python.
:: ──────────────────────────────────────────────────────────────
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    echo Creating Python virtual environment...
    python -m venv .venv
)

echo Activating virtual environment...
call .venv\Scripts\activate.bat

echo Installing Python dependencies...
pip install -r requirements.txt

echo.
echo Setup complete! Your virtual environment is now active.
echo Run launch.bat to start all services.
echo.