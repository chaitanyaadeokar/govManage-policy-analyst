@echo off
echo ============================================================
echo       govManage - Shutdown All Services
echo ============================================================
echo.

:: Kill the two terminal windows by title
echo [1/2] Closing terminal windows...
taskkill /FI "WINDOWTITLE eq govManage-Backend*"  /F >nul 2>&1
taskkill /FI "WINDOWTITLE eq govManage-Frontend*" /F >nul 2>&1

:: Force-free ports 5000 (Flask/agents) and 5173 (Vite)
echo [2/2] Releasing ports 5000 and 5173...
powershell -NoProfile -Command "try { $p = (Get-NetTCPConnection -LocalPort 5000 -ErrorAction Stop).OwningProcess | Select-Object -Unique; $p | ForEach-Object { Stop-Process -Id $_ -Force -ErrorAction SilentlyContinue } } catch {}"
powershell -NoProfile -Command "try { $p = (Get-NetTCPConnection -LocalPort 5173 -ErrorAction Stop).OwningProcess | Select-Object -Unique; $p | ForEach-Object { Stop-Process -Id $_ -Force -ErrorAction SilentlyContinue } } catch {}"

echo.
echo ============================================================
echo   All Services Stopped!
echo ============================================================
echo.
pause
