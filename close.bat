@echo off
echo ============================================================
echo       govManage - Shutdown All Services
echo ============================================================
echo.
echo Stopping all running services...
echo.

:: 1. Try to close windows gracefully by title (works in classic conhost)
echo [1/3] Closing terminal windows...
taskkill /FI "WINDOWTITLE eq Backend-API*" /F >nul 2>&1
taskkill /FI "WINDOWTITLE eq AG-*" /F >nul 2>&1
taskkill /FI "WINDOWTITLE eq Frontend-Vite*" /F >nul 2>&1

:: 2. Force kill the underlying Python/Node/UV processes based on command lines
:: This handles Windows Terminal where window titles don't register properly
echo [2/3] Terminating backend processes...
wmic process where "commandline like '%%app.py%%' and name='python.exe'" call terminate >nul 2>&1
wmic process where "commandline like '%%agents_micro%%' and name='python.exe'" call terminate >nul 2>&1
wmic process where "commandline like '%%app.py%%' and name='uv.exe'" call terminate >nul 2>&1
wmic process where "commandline like '%%agents_micro%%' and name='uv.exe'" call terminate >nul 2>&1

echo [3/3] Terminating frontend processes...
wmic process where "commandline like '%%vite%%' and name='node.exe'" call terminate >nul 2>&1

:: Also kill any orphaned cmd.exe windows that were specifically opened for these tasks
wmic process where "commandline like '%%app.py%%' and name='cmd.exe'" call terminate >nul 2>&1
wmic process where "commandline like '%%agents_micro%%' and name='cmd.exe'" call terminate >nul 2>&1
wmic process where "commandline like '%%npm run dev%%' and name='cmd.exe'" call terminate >nul 2>&1

echo.
echo ============================================================
echo   All Services Stopped!
echo ============================================================
echo.
echo   You can now safely close this window.
echo ============================================================
echo.
pause
