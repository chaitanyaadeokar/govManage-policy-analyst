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
        "messages": []
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
        "messages": []
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
        "messages": []
    }

    events = [
        ("Event 1 (Safe Txn)", event1),
        ("Event 2 (High Risk Txn)", event2),
        ("Event 3 (Malicious Attempt)", event3)
    ]

    for name, evt in events:
        log_cmd(f"Processing {name}")
        result = governance_app.invoke(evt)
        final_dec = result.get('final_decision')
        print("======== RESULTS ========")
        print(f"Path Taken: {final_dec.path_taken}")
        print(f"Final Action: {final_dec.action_taken}")
        print(f"Risk Score: {final_dec.tvi_score} ({final_dec.risk_level})")
        print("Reasoning Trace:")
        for log in final_dec.audit_trace:
            print(f"  - {log}")
        print(f"AI Explanation: {final_dec.ai_explanation}")
        print("=========================\n")
        log_cmd(f"Finished {name} - Action Taken: {final_dec.action_taken}")

if __name__ == "__main__":
    run_simulation()
