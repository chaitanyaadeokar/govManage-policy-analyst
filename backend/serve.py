"""
serve.py — govManage backend entry point.

Project layout:
  <repo-root>/
  ├── .env              ← secrets live here (never committed)
  ├── backend/          ← YOU ARE HERE
  │   ├── serve.py      ← this file
  │   ├── app.py
  │   └── ...
  └── frontend/

Execution order:
  1. Load .env from repo root  (before any other import)
  2. Configure logging         (before any other import)
  3. Boot micro-agent threads
  4. Start the web server
"""

import os
from pathlib import Path

# ── 1. Load .env from repo root (../  relative to this file) ──────────────────
_BACKEND_DIR = Path(__file__).resolve().parent
_ROOT_DIR    = _BACKEND_DIR.parent
_ENV_PATH    = _ROOT_DIR / ".env"

from dotenv import load_dotenv
load_dotenv(dotenv_path=_ENV_PATH, override=False)   # override=False → don't clobber shell env

# ── 2. Logging must be configured before ANY other import ─────────────────────
from logger_config import setup_logging

_LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
setup_logging(log_level=_LOG_LEVEL, redirect_print=True)

# ── 3. Now safe to import everything else ─────────────────────────────────────
import sys
import logging
from app import app

logger = logging.getLogger("serve")

if __name__ == "__main__":
    port = int(os.getenv("PORT", "5000"))

    # ── 4. Boot micro-agent pipeline in background threads ────────────────────
    from agent_runner import start_all_agents
    start_all_agents()

    # ── 5. Start the web server ────────────────────────────────────────────────
    if sys.platform == "win32":
        logger.info("Windows detected — starting Waitress on port %s", port)
        try:
            from waitress import serve
            serve(app, host="0.0.0.0", port=port)
        except ImportError:
            logger.error("Waitress not installed. Run: pip install waitress")
            sys.exit(1)
    else:
        logger.info("Linux/Unix detected — starting Waitress on port %s", port)
        try:
            from waitress import serve
            serve(app, host="0.0.0.0", port=port)
        except ImportError:
            logger.warning("Waitress not found, falling back to Werkzeug dev server")
            app.run(host="0.0.0.0", port=port)
