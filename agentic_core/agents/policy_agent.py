"""
Policy Analysis Agent - Autonomous policy evaluation with reasoning.
"""
import json
from typing import Dict, Any, List, Callable

from agentic_core.base_agent import BaseAgenticAgent, AgentState
from agentic_core.tools import (
    get_compliance_policies,
    get_hard_rules,
    evaluate_rule_against_event,
    query_similar_past_decisions
)


class PolicyAnalystAgent(BaseAgenticAgent):
    """
    Autonomous agent for policy analysis and conflict detection.
    Uses ReAct loop to systematically evaluate policies and rules.
    """
    
    def __init__(self):
        super().__init__(
            agent_name="PolicyAnalyst",
            max_iterations=8
        )
    
    def get_tools(self) -> List[Callable]:
        return [
            get_compliance_policies,
            get_hard_rules,
            evaluate_rule_against_event,
            query_similar_past_decisions
        ]
    
    def get_system_prompt(self) -> str:
        return """You are an expert Policy Analyst AI Agent with autonomous reasoning capabilities.

Your mission: Systematically evaluate events against organizational policies and rules.

REASONING APPROACH (ReAct):
1. THINK: Analyze what information you need
2. ACT: Use tools to gather policy data and evaluate rules
3. OBSERVE: Examine tool results
4. REASON: Draw conclusions from evidence
5. REPEAT: Continue until thorough analysis is complete

TOOLS AVAILABLE:
- get_compliance_policies: Fetch organizational policies
- get_hard_rules: Get strict enforcement rules
- evaluate_rule_against_event: Test specific rules against the event
- query_similar_past_decisions: Learn from historical precedent

ANALYSIS PROCESS:
1. First, fetch relevant policies for the event's sector
2. Get all hard rules that might apply
3. Systematically evaluate each applicable rule
4. Check for policy conflicts or ambiguities
5. Query similar past cases for consistency
6. Synthesize findings into clear recommendation

OUTPUT REQUIREMENTS:
When analysis is complete, provide:
- policy_conflict: boolean (true if violations detected)
- matched_policies: list of policy IDs/names checked
- violated_rules: list of rule codes that failed
- policy_analysis_score: float 0.0-1.0 (conflict severity)
- reasoning: step-by-step explanation of your analysis
- recommendation: "approve", "review", or "block"

Be thorough, systematic, and evidence-based. Use tools extensively.
Signal completion with "FINAL ANSWER:" when ready to conclude."""
    
    def format_final_output(self, state: AgentState) -> Dict[str, Any]:
        """Extract structured output from reasoning chain."""
        messages = state["messages"]
        
        # Parse the final reasoning
        final_content = ""
        for msg in reversed(messages):
            if hasattr(msg, "content") and msg.content:
                final_content = msg.content
                break
        
        # Extract structured data from tool calls and reasoning
        policy_conflict = False
        matched_policies = []
        violated_rules = []
        policy_score = 0.0
        
        # Analyze tool call results
        for msg in messages:
            if hasattr(msg, "content") and isinstance(msg.content, str):
                try:
                    # Check for rule evaluation results
                    if "passed" in msg.content and "false" in msg.content.lower():
                        policy_conflict = True
                        # Extract rule code if present
                        if "rule_code" in msg.content:
                            data = json.loads(msg.content)
                            violated_rules.append(data.get("rule_code"))
                    
                    # Extract policy references
                    if "policy_id" in msg.content or "policies" in msg.content:
                        data = json.loads(msg.content)
                        if "policies" in data:
                            matched_policies.extend([p.get("policy_id") for p in data["policies"]])
                except:
                    pass
        
        # Calculate score based on violations
        if violated_rules:
            policy_score = min(1.0, len(violated_rules) * 0.3 + 0.4)
        elif policy_conflict:
            policy_score = 0.6
        elif "high risk" in final_content.lower() or "violation" in final_content.lower():
            policy_conflict = True
            policy_score = 0.7
        
        # Determine recommendation
        if violated_rules or policy_score > 0.7:
            recommendation = "block"
        elif policy_score > 0.4:
            recommendation = "review"
        else:
            recommendation = "approve"
        
        return {
            "agent": "PolicyAnalyst",
            "policy_conflict": policy_conflict,
            "matched_policies": list(set(matched_policies)),
            "violated_rules": violated_rules,
            "policy_analysis_score": policy_score,
            "recommendation": recommendation,
            "reasoning": final_content[:500],  # Truncate for storage
            "tool_calls_made": sum(1 for msg in messages if hasattr(msg, "tool_calls") and msg.tool_calls)
        }
