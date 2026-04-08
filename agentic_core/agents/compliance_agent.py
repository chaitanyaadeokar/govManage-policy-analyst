"""
Compliance Agent - Autonomous authorization and compliance verification.
"""
import json
from typing import Dict, Any, List, Callable

from agentic_core.base_agent import BaseAgenticAgent, AgentState
from agentic_core.tools import (
    get_employee_info,
    get_hard_rules,
    evaluate_rule_against_event,
    check_cross_event_correlation
)


class ComplianceAgent(BaseAgenticAgent):
    """
    Autonomous agent for compliance checking and authorization verification.
    Verifies user identity, roles, and permissions systematically.
    """
    
    def __init__(self):
        super().__init__(
            agent_name="Compliance",
            max_iterations=8
        )
    
    def get_tools(self) -> List[Callable]:
        return [
            get_employee_info,
            get_hard_rules,
            evaluate_rule_against_event,
            check_cross_event_correlation
        ]
    
    def get_system_prompt(self) -> str:
        return """You are an expert Compliance AI Agent with autonomous reasoning capabilities.

Your mission: Verify user authorization and detect compliance violations.

REASONING APPROACH (ReAct):
1. THINK: Identify what compliance checks are needed
2. ACT: Use tools to verify identity, roles, and permissions
3. OBSERVE: Analyze the results
4. REASON: Determine if user is authorized
5. REPEAT: Continue until thorough verification is complete

TOOLS AVAILABLE:
- get_employee_info: Verify user identity and get role/clearance
- get_hard_rules: Get authorization rules
- evaluate_rule_against_event: Check specific authorization rules
- check_cross_event_correlation: Detect suspicious activity patterns

VERIFICATION PROCESS:
1. First, verify user exists and get their profile
2. Check if user's role is authorized for this action
3. Verify clearance level meets requirements
4. Evaluate all applicable authorization rules
5. Check for suspicious cross-event patterns
6. Make final authorization decision

CRITICAL RULES:
- Unknown users MUST be blocked
- Vendors cannot perform financial transactions
- Security events require minimum clearance levels
- Multiple blocked events indicate attack pattern

OUTPUT REQUIREMENTS:
When verification is complete, provide:
- user_authorized: boolean (true if authorized)
- user_exists: boolean
- user_role: string
- user_clearance: string
- compliance_violation: string (description if violation found, else empty)
- suspicious_activity: boolean
- reasoning: step-by-step explanation
- recommendation: "approve", "review", or "block"

Be strict and security-focused. When in doubt, escalate to review.
Signal completion with "FINAL ANSWER:" when ready to conclude."""
    
    def format_final_output(self, state: AgentState) -> Dict[str, Any]:
        """Extract structured output from reasoning chain."""
        messages = state["messages"]
        
        # Parse reasoning and tool results
        user_authorized = False
        user_exists = False
        user_role = "unknown"
        user_clearance = "unknown"
        compliance_violation = ""
        suspicious_activity = False
        
        # Extract from tool calls
        for msg in messages:
            if hasattr(msg, "content") and isinstance(msg.content, str):
                try:
                    data = json.loads(msg.content)
                    
                    # Employee info
                    if "exists" in data:
                        user_exists = data.get("exists", False)
                        if user_exists:
                            user_role = data.get("role", "unknown")
                            user_clearance = data.get("clearance", "unknown")
                    
                    # Rule evaluation
                    if "passed" in data and not data.get("passed"):
                        compliance_violation = data.get("reason", "Authorization rule failed")
                    
                    # Correlation check
                    if "correlation_detected" in data and data.get("correlation_detected"):
                        suspicious_activity = True
                        if not compliance_violation:
                            compliance_violation = data.get("reason", "Suspicious activity pattern detected")
                except:
                    pass
        
        # Determine authorization
        if not user_exists:
            user_authorized = False
            compliance_violation = "User identity verification failed - unknown user"
        elif compliance_violation:
            user_authorized = False
        elif suspicious_activity:
            user_authorized = False
            if not compliance_violation:
                compliance_violation = "Suspicious activity pattern requires review"
        else:
            user_authorized = True
        
        # Recommendation
        if not user_exists or "block" in compliance_violation.lower():
            recommendation = "block"
        elif not user_authorized or suspicious_activity:
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
            "agent": "Compliance",
            "user_authorized": user_authorized,
            "user_exists": user_exists,
            "user_role": user_role,
            "user_clearance": user_clearance,
            "compliance_violation": compliance_violation,
            "suspicious_activity": suspicious_activity,
            "recommendation": recommendation,
            "reasoning": final_content[:500],
            "tool_calls_made": sum(1 for msg in messages if hasattr(msg, "tool_calls") and msg.tool_calls)
        }
