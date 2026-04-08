"""
Agentic Core - Professional-grade autonomous AI agent framework.

This package provides the core infrastructure for building truly agentic AI systems
with autonomous reasoning, tool use, memory, and multi-agent collaboration.
"""

from agentic_core.base_agent import BaseAgenticAgent, AgentState
from agentic_core.memory import SharedMemory, shared_memory
from agentic_core.orchestrator import AgenticOrchestrator, orchestrator

__version__ = "2.0.0"
__all__ = [
    "BaseAgenticAgent",
    "AgentState",
    "SharedMemory",
    "shared_memory",
    "AgenticOrchestrator",
    "orchestrator",
]
