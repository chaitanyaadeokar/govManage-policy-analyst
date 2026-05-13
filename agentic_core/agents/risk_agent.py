"""
Risk Assessment Agent - Autonomous risk analysis with anomaly detection.
"""
import json
from typing import Dict, Any, List, Callable

from agentic_core.base_agent import BaseAgenticAgent, AgentState
from agentic_core.tools import (
    get_risk_parameters,
    check_user_behavior_anomaly,
    get_risk_baseline_for_event_type,
    query_similar_past_decisions,
    check_cross_event_correlation
)


class RiskAssessmentAgent(BaseAgenticAgent):
    """
    Autonomous agent for risk assessment and anomaly detection.
    Calculates TVI scores and identifies suspicious patterns.
    """
    
    def __init__(self):
        super().__init__(
            agent_name="RiskAssessment",
            max_iterations=10
        )
    
    def get_tools(self) -> List[Callable]:
        return [
            get_risk_parameters,
            check_user_behavior_anomaly,
            get_risk_baseline_for_event_type,
            query_similar_past_decisions,
            check_cross_event_correlation
        ]
    
    def get_system_prompt(self) -> str:
        return """You are an expert Risk Assessment AI Agent with autonomous reasoning capabilities.

Your mission: Calculate comprehensive risk scores and detect anomalies.

REASONING APPROACH (ReAct):
1. THINK: Identify risk factors to analyze
2. ACT: Use tools to gather risk data and check for anomalies
3. OBSERVE: Examine the results
4. REASON: Calculate risk scores and identify patterns
5. REPEAT: Continue until thorough risk assessment is complete

TOOLS AVAILABLE:
- get_risk_parameters: Get base TVI parameters for event type
- check_user_behavior_anomaly: Detect unusual user behavior
- get_risk_baseline_for_event_type: Get historical risk baselines
- query_similar_past_decisions: Learn from similar cases
- check_cross_event_correlation: Detect coordinated attack patterns

RISK ASSESSMENT PROCESS:
1. Get base risk parameters (Threat, Vulnerability, Impact)
2. Calculate base TVI score: (T * V * I) / 1000 (normalized 0-1)
3. Check for behavioral anomalies
4. Compare against historical baselines
5. Check for cross-event correlation patterns
6. Apply risk multipliers for anomalies
7. Classify final risk level

TVI SCORE CALCULATION:
- Base TVI = (Threat * Vulnerability * Impact) / 1000
- Apply multipliers:
  * Behavioral anomaly detected: +0.2
  * Cross-event correlation: +0.3
  * Significantly above baseline: +0.15
- Final TVI capped at 1.0

RISK LEVELS:
- Low: TVI <= 0.3
- Medium: 0.3 < TVI <= 0.7
- High: TVI > 0.7

OUTPUT REQUIREMENTS:
When assessment is complete, provide:
- tvi_score: float 0.0-1.0
- risk_level: "Low", "Medium", or "High"
- base_tvi: float (before multipliers)
- risk_multipliers: dict of applied multipliers
- anomaly_detected: boolean
- anomaly_details: string
- reasoning: step-by-step calculation explanation
- recommendation: "approve", "review", or "block"

Be analytical and data-driven. Show your calculations clearly.
Signal completion with "FINAL ANSWER:" when ready to conclude."""
    
    def format_final_output(self, state: AgentState) -> Dict[str, Any]:
        """Extract structured output from reasoning chain."""
        messages = state["messages"]
        event_id = state["event_id"]
        
        # Initialize values
        base_tvi = 0.5
        tvi_score = 0.5
        risk_multipliers = {}
        anomaly_detected = False
        anomaly_details = ""
        
        # Extract from tool calls
        threat = vulnerability = impact = 0.5
        
        for msg in messages:
            if hasattr(msg, "content") and isinstance(msg.content, str):
                try:
                    data = json.loads(msg.content)
                    
                    # Risk parameters
                    if "threat" in data and "vulnerability" in data and "impact" in data:
                        threat = data.get("threat", 0.5)
                        vulnerability = data.get("vulnerability", 0.5)
                        impact = data.get("impact", 0.5)
                        base_tvi = (threat * vulnerability * impact) / 1000
                    
                    # Anomaly detection
                    if "anomaly_detected" in data and data.get("anomaly_detected"):
                        anomaly_detected = True
                        anomaly_details = data.get("reason", "Anomalous behavior detected")
                        risk_multipliers["behavioral_anomaly"] = 0.2
                    
                    # Correlation
                    if "correlation_detected" in data and data.get("correlation_detected"):
                        severity = data.get("severity", "medium")
                        multiplier = 0.3 if severity == "high" else 0.15
                        risk_multipliers["cross_event_correlation"] = multiplier
                        if not anomaly_details:
                            anomaly_details = data.get("reason", "Suspicious event correlation")
                    
                    # Baseline comparison
                    if "avg_tvi" in data:
                        baseline_avg = data.get("avg_tvi", 0.5)
                        if base_tvi > baseline_avg * 1.5:
                            risk_multipliers["above_baseline"] = 0.15
                except:
                    pass
        
        # Calculate final TVI
        tvi_score = base_tvi + sum(risk_multipliers.values())
        tvi_score = min(1.0, tvi_score)  # Cap at 1.0
        
        # Determine risk level
        if tvi_score <= 0.3:
            risk_level = "Low"
        elif tvi_score <= 0.7:
            risk_level = "Medium"
        else:
            risk_level = "High"
        
        # Recommendation
        if risk_level == "High" or tvi_score > 0.75:
            recommendation = "block"
        elif risk_level == "Medium" or anomaly_detected:
            recommendation = "review"
        else:
            recommendation = "approve"
        
        # Get final reasoning
        final_content = ""
        for msg in reversed(messages):
            if hasattr(msg, "content") and msg.content:
                final_content = msg.content
                break
        
        return {
            "agent": "RiskAssessment",
            "tvi_score": round(tvi_score, 3),
            "risk_level": risk_level,
            "base_tvi": round(base_tvi, 3),
            "risk_multipliers": risk_multipliers,
            "anomaly_detected": anomaly_detected,
            "anomaly_details": anomaly_details,
            "threat": threat,
            "vulnerability": vulnerability,
            "impact": impact,
            "recommendation": recommendation,
            "reasoning": final_content[:500],
            "tool_calls_made": sum(1 for msg in messages if hasattr(msg, "tool_calls") and msg.tool_calls)
        }
