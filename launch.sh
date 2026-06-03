#!/usr/bin/env bash
# ============================================================
#   govManage - Quick Launch (Linux / macOS)
#   Backend serves both the API and the React production build.
#   Only ONE process needed.
# ============================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$SCRIPT_DIR/backend"
FRONTEND_DIR="$SCRIPT_DIR/frontend"

cd "$SCRIPT_DIR"

echo "============================================================"
echo "      govManage - Quick Launch"
echo "============================================================"
echo

# ── Preflight checks ──────────────────────────────────────────
echo "[0/4] Running preflight checks..."

if ! command -v python3 &>/dev/null && ! command -v python &>/dev/null; then
    echo "ERROR: Python is not found on your PATH."
    exit 1
fi
PYTHON=$(command -v python3 2>/dev/null || command -v python)

if ! command -v npm &>/dev/null; then
    echo "ERROR: Node.js / npm is not found on your PATH."
    echo "Please install Node.js 18+ from https://nodejs.org/"
    exit 1
fi

if [ ! -f ".env" ]; then
    echo "ERROR: .env file not found in project root."
    echo "Please run:  cp .env.example .env  and fill in your API keys."
    exit 1
fi

echo "Preflight checks passed!"
echo

# ── Backend venv setup (only if missing) ──────────────────────
echo "[1/4] Checking backend virtual environment..."
if [ ! -f "$BACKEND_DIR/.venv/bin/python" ]; then
    echo "  Creating Python virtual environment in backend/.venv..."
    $PYTHON -m venv "$BACKEND_DIR/.venv"
    echo "  Installing backend dependencies (this may take a minute)..."
    "$BACKEND_DIR/.venv/bin/python" -m pip install --upgrade pip
    "$BACKEND_DIR/.venv/bin/python" -m pip install -r "$BACKEND_DIR/requirements.txt"
    echo "  Backend environment ready."
else
    echo "  Backend environment already exists — skipping setup."
fi
VENV_PYTHON="$BACKEND_DIR/.venv/bin/python"
echo

# ── Build frontend (only if dist is missing or stale) ─────────
echo "[2/4] Checking frontend build..."
if [ ! -f "$FRONTEND_DIR/dist/index.html" ]; then
    if [ ! -d "$FRONTEND_DIR/node_modules" ]; then
        echo "  Installing frontend dependencies..."
        (cd "$FRONTEND_DIR" && npm install)
    fi
    echo "  Building Frontend (React/Vite)..."
    (cd "$FRONTEND_DIR" && npm run build)
    echo "  Frontend built → frontend/dist/"
else
    echo "  Frontend build already exists (frontend/dist/) — skipping rebuild."
    echo "  (Run 'cd frontend && npm run build' to rebuild after code changes)."
fi
echo

# ── Launch backend (serves API + React build) ─────────────────
echo "[3/4] Starting Backend (Flask + Micro-Agents)..."
mkdir -p "$BACKEND_DIR/logs"

open_terminal() {
    local title="$1"; shift
    local cmd="$*"
    if command -v gnome-terminal &>/dev/null; then
        gnome-terminal --title="$title" -- bash -c "$cmd; exec bash" &
    elif command -v xterm &>/dev/null; then
        xterm -title "$title" -e bash -c "$cmd; exec bash" &
    elif [[ "${OSTYPE:-}" == "darwin"* ]]; then
        osascript -e "tell application \"Terminal\" to do script \"$cmd\""
    else
        echo "  [background] $title -> backend/logs/${title}.log"
        bash -c "$cmd" > "$BACKEND_DIR/logs/${title}.log" 2>&1 &
    fi
}

open_terminal "govManage-Backend" "cd '$BACKEND_DIR' && '$VENV_PYTHON' serve.py"

echo
echo "[4/4] Done!"
echo
echo "============================================================"
echo "  govManage is running!"
echo "============================================================"
echo
echo "  App:        http://localhost:5000"
echo "  API health: http://localhost:5000/api/health"
echo
echo "  To rebuild the frontend after code changes:"
echo "    cd frontend && npm run build"
echo
echo "  To stop: ./stop.sh"
echo "============================================================"
