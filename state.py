from typing import TypedDict, List, Dict, Any, Optional

class GovernanceState(TypedDict):
    """
    Represents the state of our governance processes traversing the graph.
    """
    # Original Event Payload
    event_id: str
    event_type: str  # e.g., 'financial_txn', 'security_alert', 'policy_upload'
    payload: Dict[str, Any]
    
    # Policy Analysis Results
    policy_found: bool
    policy_conflict: bool
    matched_policies: List[str]
    policy_analysis_score: float # 0 to 1
    
    # Compliance Results
    user_authorized: bool
    pending_approvals: bool
    compliance_violation: Optional[str]
    
    # Risk Engine Results
    tvi_score: float
    risk_level: str # 'Low', 'Medium', 'High'
    anomaly_detected: bool
    fraud_flag: bool
    
    # Final Decision & Actions
    path_taken: str # 'safe', 'conflict', 'human_review'
    action_taken: str
    audit_trace: List[str]
