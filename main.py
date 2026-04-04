import json
from uuid import uuid4
from datetime import datetime
from orchestrator import governance_app

def log_cmd(action_str: str):
    """Utility to log CLI actions locally to cmds.txt"""
    with open("cmds.txt", "a") as f:
        f.write(f"[{datetime.now().isoformat()}] {action_str}\n")
    print(f"[CMD] {action_str}")

def run_simulation():
    log_cmd("Starting Governance Management AI Framework Simulation")
    
    # Event 1: Safe Financial Transaction (Director level)
    event1 = {
        "event_id": str(uuid4()),
        "event_type": "financial_txn",
        "payload": {
            "user_id": "E303", 
            "amount": 500,
            "description": "Software License Renewal"
        },
        "policy_found": False,
        "policy_conflict": False,
        "matched_policies": [],
        "policy_analysis_score": 0.0,
        "user_authorized": False,
        "pending_approvals": False,
        "compliance_violation": None,
        "tvi_score": 0.0,
        "risk_level": "Low",
        "anomaly_detected": False,
        "fraud_flag": False,
        "path_taken": "",
        "action_taken": "",
        "audit_trace": []
    }

    # Event 2: High Risk Conflict Transaction (Employee trying to expense 50000)
    event2 = {
        "event_id": str(uuid4()),
        "event_type": "financial_txn",
        "payload": {
            "user_id": "E101", 
            "amount": 50000,
            "description": "Unapproved Server Hardware"
        },
        "policy_found": False,
        "policy_conflict": False,
        "matched_policies": [],
        "policy_analysis_score": 0.0,
        "user_authorized": False,
        "pending_approvals": False,
        "compliance_violation": None,
        "tvi_score": 0.0,
        "risk_level": "Low",
        "anomaly_detected": False,
        "fraud_flag": False,
        "path_taken": "",
        "action_taken": "",
        "audit_trace": []
    }
    
    # Event 3: Unknown user (Vendor trying an internal transfer)
    event3 = {
        "event_id": str(uuid4()),
        "event_type": "financial_txn",
        "payload": {
            "user_id": "UNKNOWN_USER", 
            "amount": 100,
            "description": "Sneaky Transfer"
        },
        "policy_found": False,
        "policy_conflict": False,
        "matched_policies": [],
        "policy_analysis_score": 0.0,
        "user_authorized": False,
        "pending_approvals": False,
        "compliance_violation": None,
        "tvi_score": 0.0,
        "risk_level": "Low",
        "anomaly_detected": False,
        "fraud_flag": False,
        "path_taken": "",
        "action_taken": "",
        "audit_trace": []
    }

    events = [
        ("Event 1 (Safe Txn)", event1),
        ("Event 2 (High Risk Txn)", event2),
        ("Event 3 (Malicious Attempt)", event3)
    ]

    for name, evt in events:
        log_cmd(f"Processing {name}")
        result = governance_app.invoke(evt)
        print("======== RESULTS ========")
        print(f"Path Taken: {result['path_taken']}")
        print(f"Final Action: {result['action_taken']}")
        print(f"Risk Score: {result['tvi_score']} ({result['risk_level']})")
        print("Reasoning Trace:")
        for log in result['audit_trace']:
            print(f"  - {log}")
        print("=========================\n")
        log_cmd(f"Finished {name} - Action Taken: {result['action_taken']}")

if __name__ == "__main__":
    run_simulation()
