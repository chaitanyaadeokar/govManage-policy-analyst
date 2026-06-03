#!/usr/bin/env bash
# ============================================================
#   govManage - Quick Launch (Linux / macOS)
# ============================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "============================================================"
echo "      govManage - Quick Launch"
echo "============================================================"
echo

# ── Preflight checks ──────────────────────────────────────────
echo "[0/3] Running preflight checks..."

if ! command -v python3 &>/dev/null && ! command -v python &>/dev/null; then
    echo "ERROR: Python is not found on your PATH."
    echo "Please install Python 3.13+ and ensure it is added to PATH."
    exit 1
fi
PYTHON=$(command -v python3 2>/dev/null || command -v python)

if ! command -v npm &>/dev/null; then
    echo "ERROR: Node.js / npm is not found on your PATH."
    echo "Please install Node.js 18+ from https://nodejs.org/"
    exit 1
fi

if [ ! -f ".env" ]; then
    echo "ERROR: .env file not found."
    echo "Please copy .env.example to .env and fill in your API keys:"
    echo "  cp .env.example .env"
    exit 1
fi

if [ ! -d "frontend/node_modules" ]; then
    echo "Installing frontend dependencies (first-time setup)..."
    (cd frontend && npm install)
fi

echo "Preflight checks passed!"
echo

# ── Helper: open a new terminal window ────────────────────────
mkdir -p logs

open_terminal() {
    local title="$1"; shift
    local cmd="$*"
    if command -v gnome-terminal &>/dev/null; then
        gnome-terminal --title="$title" -- bash -c "$cmd; exec bash" &
    elif command -v xterm &>/dev/null; then
        xterm -title "$title" -e bash -c "$cmd; exec bash" &
    elif [[ "${OSTYPE:-}" == "darwin"* ]]; then
        osascript -e "tell application \"Terminal\" to do script \"cd '$SCRIPT_DIR' && $cmd\""
    else
        echo "  [background] $title -> logs/${title}.log"
        bash -c "$cmd" > "logs/${title}.log" 2>&1 &
    fi
}

# ── 1. Backend API + all micro-agents (single process) ────────
echo "[1/3] Starting Backend (Flask + all Micro-Agents)..."
echo "       All 9 agents boot automatically inside the backend process."
open_terminal "govManage-Backend" "$PYTHON '$SCRIPT_DIR/serve.py'"
sleep 4

# ── 2. Frontend ────────────────────────────────────────────────
echo "[2/3] Starting Frontend (React/Vite)..."
open_terminal "govManage-Frontend" "cd '$SCRIPT_DIR/frontend' && npm run dev"

echo
echo "============================================================"
echo "  All Services Launched!   (2 terminal windows)"
echo "============================================================"
echo
echo "  Backend API + Agents:  http://localhost:5000"
echo "  Frontend:              http://localhost:5173"
echo
echo "  Run './stop.sh' to shut everything down."
echo "============================================================"
