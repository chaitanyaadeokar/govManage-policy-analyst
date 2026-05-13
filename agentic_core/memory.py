"""
Shared memory system for multi-agent collaboration.
Enables agents to share context, learn from past decisions, and coordinate actions.
"""
import json
import os
from datetime import datetime
from typing import Dict, Any, List, Optional
from collections import defaultdict
import threading


class SharedMemory:
    """Thread-safe shared memory for agent coordination."""
    
    def __init__(self, persistence_path: str = "agents_micro/shared_memory.json"):
        self.persistence_path = persistence_path
        self.lock = threading.RLock()
        
        # Working memory (current event context)
        self.working_memory: Dict[str, Dict[str, Any]] = {}
        
        # Episodic memory (past decisions and outcomes)
        self.episodic_memory: List[Dict[str, Any]] = []
        
        # Semantic memory (learned patterns and rules)
        self.semantic_memory: Dict[str, Any] = {
            "risk_patterns": defaultdict(list),
            "fraud_indicators": [],
            "policy_conflicts": [],
            "user_behavior_baselines": {}
        }
        
        # Agent communication channel
        self.agent_messages: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        
        self._load_persistent_memory()
    
    def _load_persistent_memory(self):
        """Load persistent memory from disk."""
        if os.path.exists(self.persistence_path):
            try:
                with open(self.persistence_path, 'r') as f:
                    data = json.load(f)
                    self.episodic_memory = data.get("episodic_memory", [])
                    self.semantic_memory.update(data.get("semantic_memory", {}))
            except Exception as e:
                print(f"[Memory] Failed to load persistent memory: {e}")
    
    def save_persistent_memory(self):
        """Save memory to disk."""
        with self.lock:
            try:
                os.makedirs(os.path.dirname(self.persistence_path), exist_ok=True)
                with open(self.persistence_path, 'w') as f:
                    json.dump({
                        "episodic_memory": self.episodic_memory[-1000:],  # Keep last 1000
                        "semantic_memory": dict(self.semantic_memory)
                    }, f, indent=2)
            except Exception as e:
                print(f"[Memory] Failed to save persistent memory: {e}")
    
    def set_working_context(self, event_id: str, context: Dict[str, Any]):
        """Set working memory for an event."""
        with self.lock:
            self.working_memory[event_id] = context
    
    def get_working_context(self, event_id: str) -> Optional[Dict[str, Any]]:
        """Get working memory for an event."""
        with self.lock:
            return self.working_memory.get(event_id)
    
    def update_working_context(self, event_id: str, updates: Dict[str, Any]):
        """Update working memory for an event."""
        with self.lock:
            if event_id in self.working_memory:
                self.working_memory[event_id].update(updates)
            else:
                self.working_memory[event_id] = updates
    
    def add_agent_finding(self, event_id: str, agent_name: str, findings: Dict[str, Any]):
        """Add agent findings to working memory."""
        with self.lock:
            if event_id not in self.working_memory:
                self.working_memory[event_id] = {"agent_findings": {}}
            if "agent_findings" not in self.working_memory[event_id]:
                self.working_memory[event_id]["agent_findings"] = {}
            
            self.working_memory[event_id]["agent_findings"][agent_name] = {
                **findings,
                "timestamp": datetime.now().isoformat()
            }
    
    def get_all_agent_findings(self, event_id: str) -> Dict[str, Any]:
        """Get all agent findings for an event."""
        with self.lock:
            context = self.working_memory.get(event_id, {})
            return context.get("agent_findings", {})
    
    def send_agent_message(self, event_id: str, from_agent: str, to_agent: str, message: Dict[str, Any]):
        """Send message between agents."""
        with self.lock:
            key = f"{event_id}:{to_agent}"
            self.agent_messages[key].append({
                "from": from_agent,
                "message": message,
                "timestamp": datetime.now().isoformat()
            })
    
    def get_agent_messages(self, event_id: str, agent_name: str) -> List[Dict[str, Any]]:
        """Get messages for an agent."""
        with self.lock:
            key = f"{event_id}:{agent_name}"
            return self.agent_messages.get(key, [])
    
    def add_episodic_memory(self, event_id: str, decision: Dict[str, Any], outcome: Dict[str, Any]):
        """Store a decision episode for learning."""
        with self.lock:
            episode = {
                "event_id": event_id,
                "timestamp": datetime.now().isoformat(),
                "decision": decision,
                "outcome": outcome
            }
            self.episodic_memory.append(episode)
            
            # Trigger learning from this episode
            self._learn_from_episode(episode)
    
    def _learn_from_episode(self, episode: Dict[str, Any]):
        """Extract patterns from episode and update semantic memory."""
        decision = episode.get("decision", {})
        outcome = episode.get("outcome", {})
        
        # Learn risk patterns
        risk_level = decision.get("risk_level")
        event_type = outcome.get("event_type")
        if risk_level and event_type:
            pattern = {
                "event_type": event_type,
                "risk_level": risk_level,
                "tvi_score": decision.get("tvi_score", 0),
                "action": decision.get("action_taken")
            }
            self.semantic_memory["risk_patterns"][event_type].append(pattern)
    
    def query_similar_cases(self, event_type: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Query similar past cases from episodic memory."""
        with self.lock:
            similar = []
            for episode in reversed(self.episodic_memory):
                if episode.get("outcome", {}).get("event_type") == event_type:
                    similar.append(episode)
                    if len(similar) >= limit:
                        break
            return similar
    
    def get_risk_baseline(self, event_type: str) -> Dict[str, Any]:
        """Get learned risk baseline for event type."""
        with self.lock:
            patterns = self.semantic_memory["risk_patterns"].get(event_type, [])
            if not patterns:
                return {"avg_tvi": 0.5, "common_action": "review", "sample_size": 0}
            
            avg_tvi = sum(p.get("tvi_score", 0) for p in patterns) / len(patterns)
            actions = [p.get("action") for p in patterns if p.get("action")]
            common_action = max(set(actions), key=actions.count) if actions else "review"
            
            return {
                "avg_tvi": avg_tvi,
                "common_action": common_action,
                "sample_size": len(patterns)
            }
    
    def cleanup_event(self, event_id: str):
        """Clean up working memory for completed event."""
        with self.lock:
            self.working_memory.pop(event_id, None)
            # Clean up agent messages
            keys_to_remove = [k for k in self.agent_messages.keys() if k.startswith(f"{event_id}:")]
            for key in keys_to_remove:
                del self.agent_messages[key]


# Global shared memory instance
shared_memory = SharedMemory()
