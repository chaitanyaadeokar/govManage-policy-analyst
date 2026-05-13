"""
Decision Engine Agent - Synthesizes multi-agent findings into final decisions.
"""
import json
from typing import Dict, Any, List, Callable

from agentic_core.base_agent import BaseAgenticAgent, AgentState
from agentic_core.memory import shared_memory


class DecisionEngineAgent(BaseAgenticAgent):
    """
    Meta-agent that synthesizes findings from specialized agents.
    Makes final governance decisions through collaborative reasoning.
    """
    
    def __init__(self):
        super().__init__(
            agent_name="DecisionEngine",
            max_iterations=6
        )
    
    def get_tools(self) -> List[Callable]:
        # Decision engine doesn't need external tools - it reasons over agent findings
        return []
    
    def get_system_prompt(self) -> str:
        return """You are the Executive Decision Engine AI - the final authority in governance decisions.

Your mission: Synthesize findings from specialized agents into a final, actionable decision.

You receive input from three specialized agents:
1. PolicyAnalyst: Policy compliance and rule violations
2. Compliance: User authorization and identity verification
3. RiskAssessment: Risk scores and anomaly detection

DECISION FRAMEWORK:

BLOCK PATH (Immediate rejection):
- User does not exist (identity fraud)
- Hard rule violation with action_on_fail="block"
- Multiple violated rules
- High risk (TVI > 0.75) + compliance violation
- Suspicious cross-event correlation with high severity

REVIEW PATH (Human escalation):
- Medium-High risk (TVI 0.5-0.75)
- Policy conflict without hard block
- Behavioral anomaly detected
- Conflicting signals between agents
- User authorized but suspicious activity

SAFE PATH (Auto-approve):
- User authorized
- No policy conflicts
- Low risk (TVI < 0.3)
- No anomalies detected
- All agents recommend approval

REASONING PROCESS:
1. Examine each agent's findings and recommendation
2. Identify any blocking conditions (highest priority)
3. Check for conflicting signals requiring human judgment
4. Weigh risk vs. authorization status
5. Apply decision framework systematically
6. Provide clear reasoning for auditability

OUTPUT REQUIREMENTS:
Provide a final decision with:
- path_taken: "Safe Path", "Review Path", or "Block Path"
- action_taken: "Approved", "Flagged for Human Review", or "Auto Blocked"
- status: "Approved", "Review", or "Blocked"
- risk_level: "Low", "Medium", or "High"
- tvi_score: float from RiskAssessment
- reasoning: Clear explanation of decision logic
- audit_trace: Step-by-step decision process
- confidence: "high", "medium", or "low"

Be decisive but cautious. When in doubt, escalate to human review.
Prioritize security over convenience.
Signal completion with "FINAL ANSWER:" when decision is made."""
    
    def format_final_output(self, state: AgentState) -> Dict[str, Any]:
        """Synthesize final decision from agent findings."""
        event_id = state["event_id"]
        
        # Get all agent findings
        findings = shared_memory.get_all_agent_findings(event_id)
        
        policy_findings = findings.get("PolicyAnalyst", {})
        compliance_findings = findings.get("Compliance", {})
        risk_findings = findings.get("RiskAssessment", {})
        
        # Extract key signals
        policy_conflict = policy_findings.get("policy_conflict", False)
        violated_rules = policy_findings.get("violated_rules", [])
        policy_rec = policy_findings.get("recommendation", "review")
        
        user_authorized = compliance_findings.get("user_authorized", False)
        user_exists = compliance_findings.get("user_exists", False)
        compliance_violation = compliance_findings.get("compliance_violation", "")
        suspicious_activity = compliance_findings.get("suspicious_activity", False)
        compliance_rec = compliance_findings.get("recommendation", "review")
        
        tvi_score = risk_findings.get("tvi_score", 0.5)
        risk_level = risk_findings.get("risk_level", "Medium")
        anomaly_detected = risk_findings.get("anomaly_detected", False)
        risk_rec = risk_findings.get("recommendation", "review")
        
        # Decision logic
        audit_trace = []
        confidence = "high"
        
        # BLOCK conditions (highest priority)
        if not user_exists:
            path_taken = "Block Path"
            action_taken = "Auto Blocked"
            status = "Blocked"
            audit_trace.append("BLOCK: User identity verification failed")
            reasoning = "User does not exist in system - potential identity fraud"
        
        elif violated_rules:
            path_taken = "Block Path"
            action_taken = "Auto Blocked"
            status = "Blocked"
            audit_trace.append(f"BLOCK: Hard rule violations detected: {violated_rules}")
            reasoning = f"Violated {len(violated_rules)} hard enforcement rules"
        
        elif tvi_score > 0.75 and (not user_authorized or compliance_violation):
            path_taken = "Block Path"
            action_taken = "Auto Blocked"
            status = "Blocked"
            audit_trace.append(f"BLOCK: High risk (TVI={tvi_score}) + compliance issue")
            reasoning = f"High risk score ({tvi_score}) combined with authorization failure"
        
        elif suspicious_activity and risk_level == "High":
            path_taken = "Block Path"
            action_taken = "Auto Blocked"
            status = "Blocked"
            audit_trace.append("BLOCK: Suspicious activity pattern + high risk")
            reasoning = "Coordinated suspicious activity detected with high risk profile"
        
        # REVIEW conditions
        elif not user_authorized:
            path_taken = "Review Path"
            action_taken = "Flagged for Human Review"
            status = "Review"
            audit_trace.append(f"REVIEW: User not authorized - {compliance_violation}")
            reasoning = f"Authorization failed: {compliance_violation}"
            confidence = "medium"
        
        elif policy_conflict and tvi_score > 0.4:
            path_taken = "Review Path"
            action_taken = "Flagged for Human Review"
            status = "Review"
            audit_trace.append("REVIEW: Policy conflict with elevated risk")
            reasoning = "Policy violations detected with medium-high risk"
            confidence = "medium"
        
        elif anomaly_detected or suspicious_activity:
            path_taken = "Review Path"
            action_taken = "Flagged for Human Review"
            status = "Review"
            audit_trace.append("REVIEW: Anomalous behavior detected")
            reasoning = "Behavioral anomaly requires human judgment"
            confidence = "medium"
        
        elif risk_level == "High":
            path_taken = "Review Path"
            action_taken = "Flagged for Human Review"
            status = "Review"
            audit_trace.append(f"REVIEW: High risk level (TVI={tvi_score})")
            reasoning = f"Risk score {tvi_score} exceeds auto-approval threshold"
        
        elif {policy_rec, compliance_rec, risk_rec} == {"approve", "review", "block"} or \
             len({policy_rec, compliance_rec, risk_rec}) == 3:
            # Conflicting recommendations
            path_taken = "Review Path"
            action_taken = "Flagged for Human Review"
            status = "Review"
            audit_trace.append("REVIEW: Conflicting agent recommendations")
            reasoning = "Agents disagree - requires human judgment"
            confidence = "low"
        
        # SAFE PATH
        elif user_authorized and not policy_conflict and risk_level == "Low":
            path_taken = "Safe Path"
            action_taken = "Approved"
            status = "Approved"
            audit_trace.append("APPROVE: All checks passed")
            reasoning = "User authorized, no policy violations, low risk"
        
        else:
            # Default to review for safety
            path_taken = "Review Path"
            action_taken = "Flagged for Human Review"
            status = "Review"
            audit_trace.append("REVIEW: Default escalation for safety")
            reasoning = "Ambiguous signals - escalating to human review"
            confidence = "low"
        
        # Build comprehensive audit trace
        audit_trace.extend([
            f"Policy: conflict={policy_conflict}, violated_rules={len(violated_rules)}, rec={policy_rec}",
            f"Compliance: authorized={user_authorized}, violation={bool(compliance_violation)}, rec={compliance_rec}",
            f"Risk: level={risk_level}, TVI={tvi_score}, anomaly={anomaly_detected}, rec={risk_rec}",
            f"Decision: {path_taken} -> {action_taken}"
        ])
        
        return {
            "agent": "DecisionEngine",
            "path_taken": path_taken,
            "action_taken": action_taken,
            "status": status,
            "risk_level": risk_level,
            "tvi_score": tvi_score,
            "reasoning": reasoning,
            "audit_trace": audit_trace,
            "confidence": confidence,
            "agent_findings_summary": {
                "policy": policy_rec,
                "compliance": compliance_rec,
                "risk": risk_rec
            }
        }
    
    def process_event(self, event_id: str, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Override to wait for all agent findings before making decision.
        """
        # Wait for all three agents to complete
        findings = shared_memory.get_all_agent_findings(event_id)
        
        required_agents = {"PolicyAnalyst", "Compliance", "RiskAssessment"}
        if not required_agents.issubset(set(findings.keys())):
            return {
                "error": "Not all agent findings available",
                "available": list(findings.keys()),
                "required": list(required_agents)
            }
        
        # Now make decision
        return super().process_event(event_id, event_data)
