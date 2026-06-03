"""
serve.py — govManage backend entry point.

Starts logging FIRST (before any other import), then boots the micro-agent
pipeline, then starts the production web server.
"""

# ── 1. Logging must be configured before ANY other import ──────────────────────
import os
from logger_config import setup_logging

_LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
setup_logging(log_level=_LOG_LEVEL, redirect_print=True)

# ── 2. Now safe to import everything else ─────────────────────────────────────
import sys
import logging
from app import app

logger = logging.getLogger("serve")

if __name__ == "__main__":
    port = int(os.getenv("PORT", "5000"))

    # ── 3. Boot micro-agent pipeline in background threads ────────────────────
    from agent_runner import start_all_agents
    start_all_agents()

    # ── 4. Start the web server ────────────────────────────────────────────────
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
