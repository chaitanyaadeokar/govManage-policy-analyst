@echo off
call ".venv\scripts\activate"
python main.py > output.txt 2>&1
