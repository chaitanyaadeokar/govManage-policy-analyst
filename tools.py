import json
import os
import uuid
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

@tool
def list_all_frameworks() -> str:
    """
    Retrieves the list of all compliance frameworks available in the system.
    Use this when the user asks to see all frameworks or wants to know what frameworks are supported.
    """
    frameworks = db.list_frameworks()
    # Return essential data to save tokens
    summary = [{"id": f["framework_id"], "name": f["name"], "category": f.get("category", "")} for f in frameworks]
    return json.dumps(summary)

@tool
def get_framework_details(framework_id: str) -> str:
    """
    Retrieves the specific controls and details for a given compliance framework.
    Pass the framework ID (e.g., 'gdpr_2024') to see its specific controls.
    """
    controls = db.get_controls_for_framework(framework_id)
    return json.dumps(controls[:15]) # Limit to 15 to avoid massive token usage

@tool
def list_risk_library() -> str:
    """
    Retrieves the entire library of risk factors and risk matrices.
    Use this when the user wants to see what risks the system tracks.
    """
    matrices = db.list_risk_matrices()
    summary = [{"id": m.get("matrix_id", m.get("risk_id")), "name": m.get("name", m.get("title")), "description": m.get("description", "")} for m in matrices]
    return json.dumps(summary)

@tool
def suggest_frameworks(topic: str, sector: str = "General", country: str = "Global") -> str:
    """
    Analyzes a policy topic to suggest relevant compliance frameworks.
    Use this during the investigation phase before generating a policy.
    Returns a list of suggested framework IDs and their names.
    """
    import requests
    try:
        port = os.getenv("PORT", "5000")
        res = requests.post(
            f"http://127.0.0.1:{port}/api/compliance/frameworks/discover",
            json={"topic": topic, "sector": sector, "country": country},
            timeout=15
        )
        if res.ok:
            data = res.json()
            # Extract basic info
            frameworks = data.get("frameworks", [])
            suggestions = [{"id": f.get("framework_id"), "name": f.get("name")} for f in frameworks]
            return json.dumps({"suggested_frameworks": suggestions, "rationale": data.get("search_rationale")})
        return json.dumps({"error": f"Failed to discover frameworks: {res.status_code}"})
    except Exception as e:
        return json.dumps({"error": str(e)})

@tool
def suggest_risks(topic: str, sector: str = "General") -> str:
    """
    Analyzes a policy topic to suggest relevant risk factors.
    Use this during the investigation phase before generating a policy.
    Returns a list of suggested risk IDs.
    """
    import requests
    try:
        port = os.getenv("PORT", "5000")
        res = requests.post(
            f"http://127.0.0.1:{port}/api/policies/suggest-context",
            json={"topic": topic, "sector": sector},
            timeout=15
        )
        if res.ok:
            data = res.json()
            return json.dumps({"suggested_risks": data.get("suggested_risks", [])})
        return json.dumps({"error": f"Failed to suggest risks: {res.status_code}"})
    except Exception as e:
        return json.dumps({"error": str(e)})

@tool
def trigger_policy_generation(
    topic: str, 
    sector: str = "General", 
    additional_instructions: str = "",
    selected_frameworks: List[str] = None,
    selected_risks: List[str] = None
) -> str:
    """
    Triggers the autonomous background generation of a new policy document/pack. 
    Use this ONLY when the user explicitly asks you to generate a new policy AND you have already gathered enough context and confirmed the specific frameworks and risks to include.
    Args:
        topic: The subject of the policy (e.g., 'Cloud Security', 'Acceptable Use').
        sector: The industry sector (e.g., 'Finance', 'General'). Default is 'General'.
        additional_instructions: Any specific requirements or framework alignments requested.
        selected_frameworks: A list of framework IDs confirmed by the user.
        selected_risks: A list of risk IDs confirmed by the user.
    """
    if selected_frameworks is None:
        selected_frameworks = []
    if selected_risks is None:
        selected_risks = []
        
    try:
        # We manually craft the event payload and drop it into 1_inbox for the agents to pick up
        event_id = f"evt_{uuid.uuid4().hex[:8]}"
        payload = {
            "event_id": event_id,
            "event_type": "policy_upload",
            "timestamp": "now",
            "payload": {
                "topic": topic,
                "sector": sector,
                "additional_instructions": additional_instructions,
                "source": "ai_policy_chat_tool",
                "mode": "hybrid",
                "risk_level": "High",
                "selected_compliances": selected_frameworks,
                "selected_risks": selected_risks
            }
        }
        
        base_dir = os.path.dirname(os.path.abspath(__file__))
        inbox_dir = os.path.join(base_dir, "agents_micro", "shared_queues", "1_inbox")
        os.makedirs(inbox_dir, exist_ok=True)
        file_path = os.path.join(inbox_dir, f"{event_id}.json")
        
        with open(file_path, "w") as f:
            json.dump(payload, f, indent=4)
            
        return json.dumps({
            "status": "success", 
            "message": f"Successfully queued policy generation for '{topic}' in the '{sector}' sector. The background micro-agents (Policy Repo, Compliance, Risk) have started synthesizing the pack using {len(selected_frameworks)} frameworks and {len(selected_risks)} risks."
        })
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)})
