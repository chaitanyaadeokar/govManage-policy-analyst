#!/usr/bin/env bash
# ============================================================
#   govManage - Stop All Services (Linux / macOS)
# ============================================================
echo "Stopping govManage services..."

# Kill Python processes for govManage
pkill -f "serve.py"             2>/dev/null && echo "  Stopped Backend API"      || true
pkill -f "agents_micro"         2>/dev/null && echo "  Stopped Micro-Agents"     || true

# Kill Vite dev server
pkill -f "vite"                 2>/dev/null && echo "  Stopped Frontend (Vite)"  || true

# Force-free ports 5000 and 5173 if still bound
for PORT in 5000 5173; do
    PID=$(lsof -ti :"$PORT" 2>/dev/null) && kill -9 "$PID" 2>/dev/null && echo "  Released port $PORT" || true
done

echo
echo "All govManage services stopped."
