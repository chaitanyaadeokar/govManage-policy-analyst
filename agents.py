"""
LEGACY AGENTS MODULE - Kept for backward compatibility.
New agentic system is in agentic_core/

This module now serves as a bridge to the new agentic orchestrator.
"""
import os
from typing import Dict, Any
from dotenv import load_dotenv

from agentic_core.orchestrator import orchestrator

load_dotenv()

def process_governance_event(event: Dict[str, Any]) -> Dict[str, Any]:
    """
    Main entry point for governance event processing.
    Routes to new agentic orchestrator.
    
    Args:
        event: Event dict with event_id, event_type, and payload
    
    Returns:
        Final governance decision
    """
    return orchestrator.process_event(event)
