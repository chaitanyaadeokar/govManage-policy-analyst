"""
Enhanced tool suite for agentic reasoning.
Provides real data access, anomaly detection, and pattern analysis.
"""
import json
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from langchain_core.tools import tool

from database import db
from agentic_core.memory import shared_memory


@tool
def get_employee_info(user_id: str) -> str:
    """
    Fetch employee information including role, clearance level, and name.
    Use this to verify user identity and authorization level.
    
    Args:
        user_id: The unique identifier for the employee
    
    Returns:
        JSON string with employee details or error message
    """
    user = db.get_employee(user_id)
    if not user:
        return json.dumps({"error": f"User {user_id} not found", "exists": False})
    return json.dumps({"exists": True, **user})


@tool
def get_compliance_policies(sector: Optional[str] = None) -> str:
    """
    Retrieve active compliance policies, optionally filtered by sector.
    
    Args:
        sector: Optional sector filter (e.g., "Finance", "Technology", "Security")
    
    Returns:
        JSON string with list of applicable policies
    """
    policies = db.list_policies()
    if sector:
        policies = [p for p in policies if p.get("sector") == sector]
    return json.dumps({"policies": policies, "count": len(policies)})


@tool
def get_hard_rules(event_type: Optional[str] = None) -> str:
    """
    Retrieve strict enforcement rules from the rule engine.
    These rules define hard constraints that must be checked.
    
    Args:
        event_type: Optional filter for rules applicable to specific event types
    
    Returns:
        JSON string with list of rules and their enforcement actions
    """
    rules = db.list_rules()
    if event_type:
        rules = [r for r in rules if r.get("event_type") == event_type or not r.get("event_type")]
    return json.dumps({"rules": rules, "count": len(rules)})


@tool
def get_risk_parameters(event_type: str) -> str:
    """
    Get risk calculation parameters (threat, vulnerability, impact) for an event type.
    Use these to calculate TVI score: (Threat * Vulnerability * Impact) / 1000
    
    Args:
        event_type: The type of event (e.g., "financial_txn", "security_alert")
    
    Returns:
        JSON string with risk parameters
    """
    params = db.get_risk_params(event_type)
    return json.dumps(params)


@tool
def check_user_behavior_anomaly(user_id: str, event_type: str, amount: Optional[float] = None) -> str:
    """
    Analyze if this event represents anomalous behavior for the user.
    Compares against historical patterns and learned baselines.
    
    Args:
        user_id: The user performing the action
        event_type: Type of event
        amount: Optional transaction amount for financial events
    
    Returns:
        JSON string with anomaly analysis
    """
    # Get user's historical behavior from episodic memory
    similar_cases = shared_memory.query_similar_cases(event_type, limit=20)
    user_cases = [case for case in similar_cases 
                  if case.get("outcome", {}).get("payload", {}).get("user_id") == user_id]
    
    if len(user_cases) < 3:
        return json.dumps({
            "anomaly_detected": False,
            "confidence": "low",
            "reason": "Insufficient historical data for this user",
            "sample_size": len(user_cases)
        })
    
    # Analyze patterns
    avg_amount = None
    if amount and user_cases:
        amounts = [case.get("outcome", {}).get("payload", {}).get("amount", 0) 
                  for case in user_cases if case.get("outcome", {}).get("payload", {}).get("amount")]
        if amounts:
            avg_amount = sum(amounts) / len(amounts)
            std_dev = (sum((x - avg_amount) ** 2 for x in amounts) / len(amounts)) ** 0.5
            
            # Check if current amount is anomalous (>2 std devs)
            if amount > avg_amount + (2 * std_dev):
                return json.dumps({
                    "anomaly_detected": True,
                    "confidence": "high",
                    "reason": f"Amount ${amount} significantly exceeds user's typical ${avg_amount:.2f} (>2 std dev)",
                    "sample_size": len(amounts),
                    "baseline_avg": avg_amount,
                    "std_deviation": std_dev
                })
    
    return json.dumps({
        "anomaly_detected": False,
        "confidence": "medium",
        "reason": "Behavior within normal parameters",
        "sample_size": len(user_cases),
        "baseline_avg": avg_amount
    })


@tool
def query_similar_past_decisions(event_type: str, risk_level: Optional[str] = None) -> str:
    """
    Query similar past decisions from episodic memory to learn from precedent.
    
    Args:
        event_type: Type of event to find similar cases for
        risk_level: Optional risk level filter ("Low", "Medium", "High")
    
    Returns:
        JSON string with similar past cases and their outcomes
    """
    similar = shared_memory.query_similar_cases(event_type, limit=5)
    
    if risk_level:
        similar = [case for case in similar 
                  if case.get("decision", {}).get("risk_level") == risk_level]
    
    # Extract key insights
    if similar:
        actions = [case.get("decision", {}).get("action_taken") for case in similar]
        most_common_action = max(set(actions), key=actions.count) if actions else None
        
        return json.dumps({
            "similar_cases": similar,
            "count": len(similar),
            "most_common_action": most_common_action,
            "insights": f"Found {len(similar)} similar cases, most commonly resulted in: {most_common_action}"
        })
    
    return json.dumps({
        "similar_cases": [],
        "count": 0,
        "insights": "No similar historical cases found"
    })


@tool
def get_risk_baseline_for_event_type(event_type: str) -> str:
    """
    Get learned risk baseline statistics for an event type from historical data.
    
    Args:
        event_type: The event type to get baseline for
    
    Returns:
        JSON string with baseline statistics
    """
    baseline = shared_memory.get_risk_baseline(event_type)
    return json.dumps(baseline)


@tool
def check_cross_event_correlation(user_id: str, time_window_hours: int = 24) -> str:
    """
    Check for suspicious patterns across multiple events from the same user.
    Useful for detecting coordinated fraud or policy violations.
    
    Args:
        user_id: User to check
        time_window_hours: Time window to analyze (default 24 hours)
    
    Returns:
        JSON string with correlation analysis
    """
    # Get recent events for this user from episodic memory
    recent_episodes = []
    cutoff_time = datetime.now() - timedelta(hours=time_window_hours)
    
    for episode in reversed(shared_memory.episodic_memory):
        try:
            episode_time = datetime.fromisoformat(episode.get("timestamp", ""))
            if episode_time < cutoff_time:
                break
            
            if episode.get("outcome", {}).get("payload", {}).get("user_id") == user_id:
                recent_episodes.append(episode)
        except:
            continue
    
    if len(recent_episodes) < 2:
        return json.dumps({
            "correlation_detected": False,
            "event_count": len(recent_episodes),
            "reason": "Insufficient events in time window"
        })
    
    # Check for suspicious patterns
    event_types = [ep.get("outcome", {}).get("event_type") for ep in recent_episodes]
    blocked_count = sum(1 for ep in recent_episodes 
                       if ep.get("decision", {}).get("action_taken") == "Auto Blocked")
    
    if blocked_count >= 2:
        return json.dumps({
            "correlation_detected": True,
            "severity": "high",
            "event_count": len(recent_episodes),
            "blocked_count": blocked_count,
            "reason": f"User has {blocked_count} blocked events in {time_window_hours}h window - possible attack pattern",
            "event_types": event_types
        })
    
    if len(recent_episodes) > 10:
        return json.dumps({
            "correlation_detected": True,
            "severity": "medium",
            "event_count": len(recent_episodes),
            "reason": f"Unusually high activity: {len(recent_episodes)} events in {time_window_hours}h",
            "event_types": event_types
        })
    
    return json.dumps({
        "correlation_detected": False,
        "event_count": len(recent_episodes),
        "reason": "Normal activity pattern",
        "event_types": event_types
    })


@tool
def evaluate_rule_against_event(rule_code: str, event_payload: str) -> str:
    """
    Evaluate a specific rule against an event payload.
    Performs deterministic rule checking with clear pass/fail logic.
    
    Args:
        rule_code: The rule code to evaluate (e.g., "R001")
        event_payload: JSON string of the event payload
    
    Returns:
        JSON string with evaluation result
    """
    try:
        payload = json.loads(event_payload)
    except:
        return json.dumps({"error": "Invalid JSON payload"})
    
    rules = db.list_rules()
    rule = next((r for r in rules if r.get("rule_code") == rule_code), None)
    
    if not rule:
        return json.dumps({"error": f"Rule {rule_code} not found"})
    
    condition = rule.get("condition")
    result = {"rule_code": rule_code, "passed": True, "action": "allow"}
    
    # Evaluate based on condition type
    if condition == "amount_gt_role_required":
        amount = payload.get("amount", 0)
        threshold = rule.get("threshold", 0)
        user_id = payload.get("user_id")
        
        if amount > threshold:
            user = db.get_employee(user_id)
            required_role = rule.get("required_role")
            if not user or user.get("role") != required_role:
                result["passed"] = False
                result["action"] = rule.get("action_on_fail", "block")
                result["reason"] = f"Amount ${amount} exceeds ${threshold} but user lacks required role: {required_role}"
    
    elif condition == "role_block_for_event":
        user_id = payload.get("user_id")
        user = db.get_employee(user_id)
        blocked_roles = rule.get("blocked_roles", [])
        
        if user and user.get("role") in blocked_roles:
            result["passed"] = False
            result["action"] = rule.get("action_on_fail", "block")
            result["reason"] = f"Role {user.get('role')} is blocked for this event type"
    
    elif condition == "clearance_min_for_event":
        user_id = payload.get("user_id")
        user = db.get_employee(user_id)
        min_clearance = rule.get("min_clearance_level", 0)
        
        if user:
            user_clearance = int(user.get("clearance", "level_0").split("_")[1])
            if user_clearance < min_clearance:
                result["passed"] = False
                result["action"] = rule.get("action_on_fail", "review")
                result["reason"] = f"User clearance level_{user_clearance} below required level_{min_clearance}"
    
    elif condition == "known_user_required":
        user_id = payload.get("user_id")
        user = db.get_employee(user_id)
        if not user:
            result["passed"] = False
            result["action"] = rule.get("action_on_fail", "block")
            result["reason"] = "Unknown user - identity verification failed"
    
    return json.dumps(result)
