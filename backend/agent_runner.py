"""
agent_runner.py
───────────────
Starts all micro-agent watchdog observers as daemon threads inside the same
Python process as the Flask backend.  Import and call `start_all_agents()`
once at server startup — no extra terminals, no subprocesses.

Each agent module uses `if __name__ == "__main__"` guards around its observer
loop, so importing them is safe.  We reconstruct the observer here by reusing
each module's Handler class and INBOX_DIR constant.
"""

import os
import sys
import time
import threading
import logging

from watchdog.observers import Observer

logger = logging.getLogger("agent_runner")

# ── Resolve paths ──────────────────────────────────────────────────────────────
ROOT_DIR   = os.path.dirname(os.path.abspath(__file__))
AGENTS_DIR = os.path.join(ROOT_DIR, "agents_micro")

# Put root on sys.path so agent modules can `from database import db` etc.
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

# ── Agent registry ─────────────────────────────────────────────────────────────
# Each entry: (display_name, module_path, HandlerClass, inbox_dir)
# We import the Handler class directly rather than running __main__.
AGENT_REGISTRY = [
    (
        "Orchestrator",
        os.path.join(AGENTS_DIR, "orchestrator", "main.py"),
        "InboxHandler",
        os.path.join(AGENTS_DIR, "shared_queues", "1_inbox"),
    ),
    (
        "PolicyAnalyst",
        os.path.join(AGENTS_DIR, "policy_analyst", "main.py"),
        "PolicyHandler",
        os.path.join(AGENTS_DIR, "shared_queues", "2_policy"),
    ),
    (
        "Compliance",
        os.path.join(AGENTS_DIR, "compliance", "main.py"),
        "ComplianceHandler",
        os.path.join(AGENTS_DIR, "shared_queues", "2_compliance"),
    ),
    (
        "RiskAssessment",
        os.path.join(AGENTS_DIR, "risk_assessment", "main.py"),
        "RiskHandler",
        os.path.join(AGENTS_DIR, "shared_queues", "2_risk"),
    ),
    (
        "DecisionEngine",
        os.path.join(AGENTS_DIR, "decision_engine", "main.py"),
        "DecisionHandler",
        os.path.join(AGENTS_DIR, "shared_queues", "3_decision"),
    ),
    (
        "Audit",
        os.path.join(AGENTS_DIR, "audit", "main.py"),
        "AuditHandler",
        os.path.join(AGENTS_DIR, "shared_queues", "4_audit"),
    ),
    (
        "Reporting",
        os.path.join(AGENTS_DIR, "reporting", "main.py"),
        "ReportingHandler",
        os.path.join(AGENTS_DIR, "shared_queues", "5_report"),
    ),
    (
        "Feedback",
        os.path.join(AGENTS_DIR, "feedback", "main.py"),
        "FeedbackHandler",
        os.path.join(AGENTS_DIR, "shared_queues", "6_feedback"),
    ),
    (
        "Persistence",
        os.path.join(AGENTS_DIR, "persistence", "main.py"),
        "PersistenceHandler",
        os.path.join(AGENTS_DIR, "shared_queues", "6_feedback"),
    ),
]


def _load_handler(module_path: str, handler_class_name: str):
    """Dynamically import a module from an absolute file path and return the handler class."""
    import importlib.util
    spec = importlib.util.spec_from_file_location("_agent_mod", module_path)
    mod  = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return getattr(mod, handler_class_name)


def _run_agent_observer(name: str, handler_class, inbox_dir: str):
    """Target function for each agent daemon thread."""
    os.makedirs(inbox_dir, exist_ok=True)
    handler  = handler_class()
    observer = Observer()
    observer.schedule(handler, path=inbox_dir, recursive=False)
    observer.start()
    logger.info(f"[AgentRunner] ✔  {name} watching {inbox_dir}")
    try:
        while True:
            time.sleep(1)
    except Exception:
        pass
    finally:
        observer.stop()
        observer.join()


_started = False   # guard against double-init (e.g. Flask debug reloader)

def start_all_agents():
    """
    Boot every micro-agent observer as a daemon thread.
    Call this once before starting the web server.
    Daemon threads die automatically when the main process exits.
    """
    global _started
    if _started:
        return
    _started = True

    logger.info("[AgentRunner] Booting micro-agent pipeline...")

    for name, module_path, handler_cls_name, inbox_dir in AGENT_REGISTRY:
        try:
            handler_cls = _load_handler(module_path, handler_cls_name)
            t = threading.Thread(
                target=_run_agent_observer,
                args=(name, handler_cls, inbox_dir),
                name=f"agent-{name}",
                daemon=True,           # dies when main process exits
            )
            t.start()
        except Exception as exc:
            logger.error(f"[AgentRunner] ✘  Failed to start {name}: {exc}")

    logger.info("[AgentRunner] All agents launched in background threads.")
