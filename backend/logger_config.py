"""
logger_config.py
────────────────
Centralized logging configuration for the govManage backend.

Call `setup_logging()` ONCE, as early as possible (first line of serve.py),
before any other imports. Every module that subsequently calls
`logging.getLogger(name)` will automatically inherit the handlers and format
configured here.

Log file: logs/govmanage.log  (rotating, max 10 MB × 5 backups)
Console:  same format, colorised severity prefix
"""

import logging
import os
import sys
from logging.handlers import RotatingFileHandler

# ── Constants ──────────────────────────────────────────────────────────────────
LOG_DIR      = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")
LOG_FILE     = os.path.join(LOG_DIR, "govmanage.log")
MAX_BYTES    = 10 * 1024 * 1024   # 10 MB per file
BACKUP_COUNT = 5                   # keep last 5 rotated files

LOG_FORMAT   = "%(asctime)s [%(levelname)-8s] %(name)s: %(message)s"
DATE_FORMAT  = "%Y-%m-%dT%H:%M:%S"

# ── ANSI colour codes for the console handler ──────────────────────────────────
_COLOURS = {
    "DEBUG":    "\033[36m",   # Cyan
    "INFO":     "\033[32m",   # Green
    "WARNING":  "\033[33m",   # Yellow
    "ERROR":    "\033[31m",   # Red
    "CRITICAL": "\033[35m",   # Magenta
}
_RESET = "\033[0m"


class _ColouredFormatter(logging.Formatter):
    """Formatter that adds ANSI colour to the level name in console output."""

    def format(self, record: logging.LogRecord) -> str:
        colour = _COLOURS.get(record.levelname, "")
        record.levelname = f"{colour}{record.levelname}{_RESET}"
        return super().format(record)


class _StreamToLogger(object):
    """
    Redirect raw stdout `print()` calls (from agents that use print instead of
    logging) into the logging system so everything ends up in the log file.
    """

    def __init__(self, logger: logging.Logger, level: int = logging.INFO):
        self._logger = logger
        self._level  = level
        self._buf    = ""

    def write(self, buf: str):
        for line in buf.rstrip().splitlines():
            stripped = line.strip()
            if stripped:
                self._logger.log(self._level, stripped)

    def flush(self):
        pass

    def isatty(self):
        return False


def setup_logging(log_level: str = "INFO", redirect_print: bool = True) -> logging.Logger:
    """
    Configure the root logger with:
      - RotatingFileHandler  → logs/govmanage.log
      - StreamHandler        → console (colourised)

    All third-party loggers (flask, werkzeug, watchdog, pymongo, etc.) inherit
    these handlers automatically.

    Args:
        log_level:       Minimum severity to record (default "INFO").
        redirect_print:  If True, redirects sys.stdout to the logger so that
                         agent print() calls are also captured in the log file.

    Returns:
        The configured root logger.
    """
    os.makedirs(LOG_DIR, exist_ok=True)

    numeric_level = getattr(logging, log_level.upper(), logging.INFO)

    # ── Root logger ────────────────────────────────────────────────────────────
    root = logging.getLogger()
    root.setLevel(numeric_level)

    # Avoid adding duplicate handlers if called more than once
    if root.handlers:
        return root

    plain_fmt   = logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT)
    colour_fmt  = _ColouredFormatter(LOG_FORMAT, datefmt=DATE_FORMAT)

    # ── File handler (rotating) ────────────────────────────────────────────────
    file_handler = RotatingFileHandler(
        LOG_FILE,
        maxBytes=MAX_BYTES,
        backupCount=BACKUP_COUNT,
        encoding="utf-8",
    )
    file_handler.setFormatter(plain_fmt)
    file_handler.setLevel(numeric_level)

    # ── Console handler ────────────────────────────────────────────────────────
    console_handler = logging.StreamHandler(sys.stderr)
    console_handler.setFormatter(colour_fmt)
    console_handler.setLevel(numeric_level)

    root.addHandler(file_handler)
    root.addHandler(console_handler)

    # ── Quiet noisy third-party libraries ─────────────────────────────────────
    # These are extremely chatty at DEBUG; keep them at WARNING unless needed.
    for noisy in ("urllib3", "httpcore", "httpx", "pymongo", "langchain", "openai", "chromadb"):
        logging.getLogger(noisy).setLevel(logging.WARNING)

    # ── Redirect print() → logger (captures agent output) ─────────────────────
    if redirect_print:
        _print_logger = logging.getLogger("stdout")
        sys.stdout = _StreamToLogger(_print_logger, logging.INFO)

    root.info(
        "Logging initialised │ file=%s │ level=%s │ max_size=%sMB × %s backups",
        LOG_FILE, log_level.upper(), MAX_BYTES // (1024 * 1024), BACKUP_COUNT,
    )
    return root
