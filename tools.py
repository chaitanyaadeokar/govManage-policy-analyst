import json
from typing import Dict, Any, List
from langchain_core.tools import tool
from database import db

@tool
def get_employee_info(user_id: str) -> str:
    """
    Fetches the employee/user information based on user_id. 
    Use this to determine user role and clearance level before making a decision.
    """
    user = db.get_employee(user_id)
    if not user:
        return json.dumps({"error": f"User {user_id} not found."})
    return json.dumps(user)

@tool
def get_compliance_policies() -> str:
    """
    Retrieves the list of active compliance policies for the organization.
    These policies dictate overarching governance requirements.
    """
    policies = db.list_policies()
    return json.dumps(policies)

@tool
def get_hard_rules() -> str:
    """
    Retrieves strict rule-engine rules. These rules specify hard constraints.
    For example: role blocks, specific clearance minimums, or action thresholds.
    """
    rules = db.list_rules()
    return json.dumps(rules)

@tool
def get_risk_parameters(event_type: str) -> str:
    """
    Gets the risk multiplier parameters (threat, vulnerability, impact) for a given event_type.
    You can use these to calculate a base TVI score (Threat * Vulnerability * Impact).
    """
    params = db.get_risk_params(event_type)
    return json.dumps(params)
