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
    Triggers the synchronous generation of a new policy document/pack. 
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
        from llm_utils import get_groq_llm, safe_invoke
        from langchain_core.messages import SystemMessage, HumanMessage
        from datetime import datetime, timezone

        # ── Agent 1: Fetch real framework controls from DB ─────────────────────
        compliance_data = []
        control_matrix_items = []
        compliance_text_parts = []

        # Try to resolve framework IDs from DB; if not found, treat as names
        for fw_id in selected_frameworks:
            fw = db.get_framework(fw_id)
            if fw:
                compliance_data.append(fw)
                controls = fw.get("controls", [])[:6]
                ctrl_titles = [f"{c['control_id']}: {c['title']}" for c in controls]
                compliance_text_parts.append(
                    f"Framework: {fw['name']} ({fw.get('region', 'Global')})\n"
                    f"Key Controls: {'; '.join(ctrl_titles)}"
                )
                for c in controls:
                    control_matrix_items.append({
                        "framework": fw["name"],
                        "framework_id": fw["framework_id"],
                        "control_id": c["control_id"],
                        "title": c["title"],
                        "coverage": "Addressed in Policy"
                    })

        # Fallback: if no DB matches, still provide the names to the LLM
        if not compliance_text_parts and selected_frameworks:
            compliance_text_parts = [f"Framework: {f}" for f in selected_frameworks]

        compliance_context = "\n\n".join(compliance_text_parts)

        # ── Agent 2: Fetch real risk items from DB ─────────────────────────────
        risk_items = []
        risk_mapping_items = []
        risk_text_parts = []

        # Try resolving risk IDs from DB
        if selected_risks:
            risk_items = db.get_risk_library_items_by_ids(selected_risks)

        for r in risk_items:
            risk_text_parts.append(
                f"[{r['risk_id']}] {r['title']} (Severity: {r['severity']})\n"
                f"Description: {r['description']}\n"
                f"Mitigation: {r['mitigation']}"
            )
            risk_mapping_items.append({
                "risk_id": r["risk_id"],
                "risk_type": r.get("risk_type", ""),
                "title": r["title"],
                "severity": r["severity"],
                "mitigation": r["mitigation"]
            })

        # Fallback: if no DB matches, use names
        if not risk_text_parts and selected_risks:
            risk_text_parts = [f"Risk: {r}" for r in selected_risks]

        risk_context = "\n\n".join(risk_text_parts)

        # ── Agent 3: LLM Policy Generation ────────────────────────────────────
        instructions_context = f"\nADDITIONAL INSTRUCTIONS:\n{additional_instructions}\n" if additional_instructions else ""
        prompt = f"""You are an expert governance policy writer and GRC specialist. Draft a comprehensive IT Governance / Compliance Policy.
Topic: {topic}
Sector: {sector}
{instructions_context}
COMPLIANCE FRAMEWORKS TO ADDRESS:
{compliance_context if compliance_context else "Use general best-practice frameworks."}

RISKS TO MITIGATE:
{risk_context if risk_context else "Apply standard risk mitigation practices."}

Return ONLY the raw Markdown text of the policy. Start with a title heading (# Title).
You MUST include EXACTLY the following sections, using clear markdown headings (##):
- Objective (why this policy exists and what it achieves)
- Scope (who and what systems/processes this applies to)
- Policy Statements (at least 5 specific, enforceable rules)
- Procedures (at least 3 procedures, each with actionable steps)
- Governance Structure (at least 3 roles and their key responsibilities)
- Enforcement (consequences for non-compliance)
- Review Cycle (how often this policy is reviewed)

CRITICAL REQUIREMENT: Do NOT include any placeholder metadata at the top or bottom of the document. Absolutely NO "Effective Date", "Version", "Approved By", "Board of Directors", or "Risk Committee" blocks. End the document immediately after the Review Cycle section.
"""
        llm = get_groq_llm()
        
        db.set_agent_status("reporting", f"Drafting Policy: {topic[:15]}...", "policy_gen")
        try:
            response = safe_invoke(llm, [
                SystemMessage(content="You output pure markdown documents. No introductory text. No metadata footers."),
                HumanMessage(content=prompt)
            ])
        finally:
            db.clear_agent_status("reporting")
            
        markdown_text = response.content.strip()
        if markdown_text.startswith("```markdown"):
            markdown_text = markdown_text[11:].strip()
        if markdown_text.startswith("```"):
            markdown_text = markdown_text[3:].strip()
        if markdown_text.endswith("```"):
            markdown_text = markdown_text[:-3].strip()

        # ── Append Compliance Control Matrix table ─────────────────────────────
        if control_matrix_items:
            markdown_text += "\n\n## Compliance Control Matrix\n\n"
            markdown_text += "| Framework | Control ID | Control Title | Coverage |\n"
            markdown_text += "|-----------|------------|---------------|----------|\n"
            for c in control_matrix_items:
                fw_name = c.get("framework", "")
                ctrl_id = c.get("control_id", "")
                ctrl_title = c.get("title", "")
                coverage = c.get("coverage", "Addressed in Policy")
                markdown_text += f"| {fw_name} | {ctrl_id} | {ctrl_title} | {coverage} |\n"

        # ── Append Risk Mitigation Mapping table ───────────────────────────────
        if risk_mapping_items:
            markdown_text += "\n\n## Risk Mitigation Mapping\n\n"
            markdown_text += "| Risk ID | Risk | Severity | Mitigation Strategy |\n"
            markdown_text += "|---------|------|----------|---------------------|\n"
            for r in risk_mapping_items:
                rid = r.get("risk_id", "")
                rtitle = r.get("title", "")
                rseverity = r.get("severity", "")
                rmitigation = r.get("mitigation", "")
                markdown_text += f"| {rid} | {rtitle} | {rseverity} | {rmitigation} |\n"

        # ── Build & store document ─────────────────────────────────────────────
        policy_id = f"pol_{uuid.uuid4().hex[:8]}"
        title = f"{topic} Policy"
        # Extract actual title from the first heading
        first_line = markdown_text.split('\n')[0].strip()
        if first_line.startswith('# '):
            title = first_line[2:].strip()
            
        doc = {
            "policy_id": policy_id,
            "title": title,
            "sector": sector,
            "content": markdown_text,
            "frameworks": [fw.get("name", fw_id) for fw, fw_id in zip(compliance_data, selected_frameworks)] if compliance_data else selected_frameworks,
            "risks": [r.get("title", "") for r in risk_items] if risk_items else selected_risks,
            "control_matrix": control_matrix_items,
            "risk_mapping": risk_mapping_items,
            "selected_compliance_ids": selected_frameworks,
            "selected_risk_ids": selected_risks,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "is_active": True,
        }
        db.db["policy_documents"].insert_one(doc)
        
        card_json = json.dumps({"id": policy_id, "title": title})
        return f"Policy generated successfully.\n<POLICY_CARD>{card_json}</POLICY_CARD>"
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        db.clear_agent_status("reporting")
        return json.dumps({"status": "error", "message": str(e)})

