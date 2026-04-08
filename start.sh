#!/bin/bash

# Agentic Governance System - Quick Start Script

echo "=========================================="
echo "Agentic Governance System"
echo "Professional-Grade AI Governance"
echo "=========================================="
echo ""

# Check Python version
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "✓ Python version: $python_version"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install -q --upgrade pip
pip install -q -r requirements.txt

# Check if .env exists
if [ ! -f ".env" ]; then
    echo ""
    echo "⚠️  No .env file found!"
    echo "Please create .env file with your configuration:"
    echo ""
    echo "GROQ_API_KEY=your_api_key_here"
    echo "GROQ_MODEL=openai/gpt-oss-120b"
    echo "MONGO_URI=mongodb://127.0.0.1:27017"
    echo "MONGO_DB_NAME=govmanage"
    echo ""
    exit 1
fi

# Check MongoDB
echo "Checking MongoDB connection..."
python3 -c "from database import db; db.count_actions(); print('✓ MongoDB connected')" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "⚠️  MongoDB connection failed!"
    echo "Please ensure MongoDB is running on localhost:27017"
    echo "Or update MONGO_URI in .env file"
    exit 1
fi

echo ""
echo "=========================================="
echo "System Ready!"
echo "=========================================="
echo ""
echo "Choose an option:"
echo "1. Run test suite"
echo "2. Start API server"
echo "3. Run single test event"
echo "4. Exit"
echo ""
read -p "Enter choice [1-4]: " choice

case $choice in
    1)
        echo ""
        echo "Running test suite..."
        python3 test_agentic_system.py
        ;;
    2)
        echo ""
        echo "Starting API server..."
        echo "API will be available at: http://localhost:8000"
        echo "Interactive docs at: http://localhost:8000/docs"
        echo ""
        python3 api.py
        ;;
    3)
        echo ""
        echo "Running single test event..."
        python3 -c "
from agents import process_governance_event
import json

event = {
    'event_id': 'quick-test',
    'event_type': 'financial_txn',
    'payload': {
        'user_id': 'E101',
        'amount': 1500,
        'vendor': 'Test Corp'
    }
}

print('Processing event...')
result = process_governance_event(event)
print('\n' + '='*60)
print('RESULT:')
print(json.dumps(result, indent=2))
print('='*60)
"
        ;;
    4)
        echo "Goodbye!"
        exit 0
        ;;
    *)
        echo "Invalid choice"
        exit 1
        ;;
esac
