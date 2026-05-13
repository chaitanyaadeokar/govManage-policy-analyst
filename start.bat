@echo off
REM Agentic Governance System - Quick Start Script (Windows)

echo ==========================================
echo Agentic Governance System
echo Professional-Grade AI Governance
echo ==========================================
echo.

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python not found!
    echo Please install Python 3.9 or higher
    pause
    exit /b 1
)

echo Checking Python version...
python --version

REM Check if virtual environment exists
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Install dependencies
echo Installing dependencies...
pip install -q --upgrade pip
pip install -q -r requirements.txt

REM Check if .env exists
if not exist ".env" (
    echo.
    echo WARNING: No .env file found!
    echo Please create .env file with your configuration:
    echo.
    echo GROQ_API_KEY=your_api_key_here
    echo GROQ_MODEL=openai/gpt-oss-120b
    echo MONGO_URI=mongodb://127.0.0.1:27017
    echo MONGO_DB_NAME=govmanage
    echo.
    pause
    exit /b 1
)

REM Check MongoDB
echo Checking MongoDB connection...
python -c "from database import db; db.count_actions(); print('MongoDB connected')" 2>nul
if errorlevel 1 (
    echo WARNING: MongoDB connection failed!
    echo Please ensure MongoDB is running on localhost:27017
    echo Or update MONGO_URI in .env file
    pause
    exit /b 1
)

echo.
echo ==========================================
echo System Ready!
echo ==========================================
echo.
echo Choose an option:
echo 1. Run test suite
echo 2. Start API server
echo 3. Run single test event
echo 4. Exit
echo.
set /p choice="Enter choice [1-4]: "

if "%choice%"=="1" goto test_suite
if "%choice%"=="2" goto start_api
if "%choice%"=="3" goto single_test
if "%choice%"=="4" goto end
goto invalid

:test_suite
echo.
echo Running test suite...
python test_agentic_system.py
pause
goto end

:start_api
echo.
echo Starting API server...
echo API will be available at: http://localhost:8000
echo Interactive docs at: http://localhost:8000/docs
echo.
echo Press Ctrl+C to stop the server
python api.py
goto end

:single_test
echo.
echo Running single test event...
python -c "from agents import process_governance_event; import json; event = {'event_id': 'quick-test', 'event_type': 'financial_txn', 'payload': {'user_id': 'E101', 'amount': 1500, 'vendor': 'Test Corp'}}; print('Processing event...'); result = process_governance_event(event); print('\n' + '='*60); print('RESULT:'); print(json.dumps(result, indent=2)); print('='*60)"
pause
goto end

:invalid
echo Invalid choice
pause
goto end

:end
echo Goodbye!
