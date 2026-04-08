"""
Agentic Orchestrator - Coordinates multi-agent collaboration.
"""
import os
import json
import time
from typing import Dict, Any
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from dotenv import load_dotenv

from agentic_core.agents.policy_agent import PolicyAnalystAgent
from agentic_core.agents.compliance_agent import ComplianceAgent
from agentic_core.agents.risk_agent import RiskAssessmentAgent
from agentic_core.agents.decision_agent import DecisionEngineAgent
from agentic_core.memory import shared_memory
from database import db

load_dotenv()


class AgenticOrchestrator:
    """
    Orchestrates multi-agent collaboration for governance decisions.
    Runs specialized agents in parallel and synthesizes results.
    """
    
    def __init__(self):
        # Initialize all agents
        self.policy_agent = PolicyAnalystAgent()
        self.compliance_agent = ComplianceAgent()
        self.risk_agent = RiskAssessmentAgent()
        self.decision_agent = DecisionEngineAgent()
        
        print("[Orchestrator] All agentic agents initialized")
    
    def process_event(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a governance event through multi-agent system.
        
        Args:
            event: Event data with event_id, event_type, and payload
        
        Returns:
            Final governance decision
        """
        event_id = event.get("event_id")
        event_type = event.get("event_type")
        payload = event.get("payload", {})
        
        print(f"\n{'='*60}")
        print(f"[Orchestrator] Processing Event: {event_id}")
        print(f"[Orchestrator] Type: {event_type}")
        print(f"{'='*60}\n")
        
        start_time = time.time()
        
        # Prepare event data for agents
        event_data = {
            "event_id": event_id,
            "event_type": event_type,
            "payload": payload,
            "timestamp": datetime.now().isoformat()
        }
        
        # Phase 1: Run specialized agents in parallel
        print("[Orchestrator] Phase 1: Launching specialized agents in parallel...")
        
        agent_results = {}
        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = {
                executor.submit(self._run_agent_safely, self.policy_agent, event_id, event_data): "PolicyAnalyst",
                executor.submit(self._run_agent_safely, self.compliance_agent, event_id, event_data): "Compliance",
                executor.submit(self._run_agent_safely, self.risk_agent, event_id, event_data): "RiskAssessment"
            }
            
            for future in as_completed(futures):
                agent_name = futures[future]
                try:
                    result = future.result(timeout=60)  # 60 second timeout per agent
                    agent_results[agent_name] = result
                    print(f"[Orchestrator] ✓ {agent_name} completed")
                    print(f"  → Recommendation: {result.get('recommendation', 'unknown')}")
                    print(f"  → Tool calls: {result.get('tool_calls_made', 0)}")
                except Exception as e:
                    print(f"[Orchestrator] ✗ {agent_name} failed: {e}")
                    agent_results[agent_name] = {
                        "error": str(e),
                        "recommendation": "review"  # Safe default
                    }
        
        # Phase 2: Decision synthesis
        print(f"\n[Orchestrator] Phase 2: Synthesizing decision...")
        
        try:
            decision = self.decision_agent.process_event(event_id, event_data)
            print(f"[Orchestrator] ✓ Decision made: {decision.get('action_taken')}")
        except Exception as e:
            print(f"[Orchestrator] ✗ Decision synthesis failed: {e}")
            # Fallback decision
            decision = self._create_fallback_decision(event_id, agent_results)
        
        # Phase 3: Audit and persistence
        print(f"\n[Orchestrator] Phase 3: Audit and persistence...")
        
        final_result = self._build_final_result(event_id, event_type, payload, agent_results, decision)
        
        # Store in database
        try:
            db.log_action(final_result)
            db.add_audit_log({
                "event_id": event_id,
                "timestamp": datetime.now().isoformat(),
                "decision": decision,
                "agent_findings": agent_results
            })
            print("[Orchestrator] ✓ Persisted to database")
        except Exception as e:
            print(f"[Orchestrator] ✗ Database persistence failed: {e}")
        
        # Store in episodic memory for learning
        shared_memory.add_episodic_memory(
            event_id,
            decision,
            {"event_type": event_type, "payload": payload}
        )
        shared_memory.save_persistent_memory()
        
        # Cleanup working memory
        shared_memory.cleanup_event(event_id)
        
        elapsed = time.time() - start_time
        print(f"\n[Orchestrator] ✓ Event {event_id} processed in {elapsed:.2f}s")
        print(f"[Orchestrator] Final Decision: {decision.get('action_taken')}")
        print(f"{'='*60}\n")
        
        return final_result
    
    def _run_agent_safely(self, agent, event_id: str, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Run agent with error handling."""
        try:
            return agent.process_event(event_id, event_data)
        except Exception as e:
            print(f"[Orchestrator] Agent {agent.agent_name} error: {e}")
            return {
                "error": str(e),
                "agent": agent.agent_name,
                "recommendation": "review"
            }
    
    def _create_fallback_decision(self, event_id: str, agent_results: Dict[str, Any]) -> Dict[str, Any]:
        """Create safe fallback decision if decision agent fails."""
        # Count recommendations
        recommendations = [r.get("recommendation", "review") for r in agent_results.values()]
        
        # If any agent says block, block
        if "block" in recommendations:
            return {
                "path_taken": "Block Path",
                "action_taken": "Auto Blocked",
                "status": "Blocked",
                "reasoning": "Fallback decision: At least one agent recommended blocking",
                "confidence": "medium"
            }
        
        # If all say approve, approve
        if all(r == "approve" for r in recommendations):
            return {
                "path_taken": "Safe Path",
                "action_taken": "Approved",
                "status": "Approved",
                "reasoning": "Fallback decision: All agents recommended approval",
                "confidence": "medium"
            }
        
        # Default to review
        return {
            "path_taken": "Review Path",
            "action_taken": "Flagged for Human Review",
            "status": "Review",
            "reasoning": "Fallback decision: Mixed signals or errors detected",
            "confidence": "low"
        }
    
    def _build_final_result(
        self,
        event_id: str,
        event_type: str,
        payload: Dict[str, Any],
        agent_results: Dict[str, Any],
        decision: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Build comprehensive final result."""
        return {
            "event_id": event_id,
            "event_type": event_type,
            "payload": payload,
            "timestamp": datetime.now().isoformat(),
            
            # Decision
            "path_taken": decision.get("path_taken", "Review Path"),
            "action_taken": decision.get("action_taken", "Flagged for Human Review"),
            "status": decision.get("status", "Review"),
            
            # Risk metrics
            "risk_level": decision.get("risk_level", "Medium"),
            "tvi_score": decision.get("tvi_score", 0.5),
            
            # Reasoning
            "reasoning": decision.get("reasoning", "Decision synthesis completed"),
            "audit_trace": decision.get("audit_trace", []),
            "confidence": decision.get("confidence", "medium"),
            
            # Agent findings
            "agent_findings": agent_results,
            
            # Metadata
            "processing_metadata": {
                "agents_used": list(agent_results.keys()),
                "decision_engine": "AgenticOrchestrator",
                "version": "2.0-agentic"
            }
        }


# Global orchestrator instance
orchestrator = AgenticOrchestrator()
