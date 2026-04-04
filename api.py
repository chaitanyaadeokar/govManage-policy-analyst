from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any, List
import uuid

# Import our LangGraph mock dependencies
from orchestrator import governance_app
from database import db, policies

app = FastAPI(title="GovManage AI API")

# Allow CORS for local dev
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # For dev purposes
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class EventPayload(BaseModel):
    user_id: str
    amount: float = 0.0
    description: str = ""

class EventTrigger(BaseModel):
    event_type: str
    payload: EventPayload

@app.get("/")
def read_root():
    return {"status": "GovManage API is active"}

@app.get("/api/kpis")
def get_kpis():
    # Summarize stats from mock database
    active_policies = 5 # hardcoded in init_chroma
    total_actions = len(db.governance_actions)
    approved = sum(1 for a in db.governance_actions if a.get("status") == "Approved")
    compliance_pct = (approved / total_actions * 100) if total_actions > 0 else 100
    
    # Calculate a mock Risk Index based on recent audit logs
    high_risks = sum(1 for log in db.audit_logs if log.get("risk_score", 0) > 70)
    risk_index = min(100, 20 + (high_risks * 10))
    
    return {
        "active_policies": active_policies,
        "compliance_pct": round(compliance_pct, 1),
        "citizen_satisfaction": 84,  # Mock
        "risk_index": risk_index
    }

@app.get("/api/masters")
def get_masters():
    # Return mock policy masters
    return [
        {"id": "P001", "name": "Financial transactions > 1000 require manager approval.", "sector": "Finance", "risk": "Medium"},
        {"id": "P002", "name": "External vendors cannot access sensitive IT.", "sector": "Technology", "risk": "High"},
        {"id": "P003", "name": "Security alerts with critical classification must auto-freeze.", "sector": "Governance", "risk": "High"},
        {"id": "P004", "name": "Employees can only expense up to 500 without receipt.", "sector": "Finance", "risk": "Low"},
        {"id": "P005", "name": "IT alerts requires level_2 clearance to suppress.", "sector": "Technology", "risk": "Medium"}
    ]

@app.get("/api/transactions")
def get_transactions():
    return db.governance_actions

@app.get("/api/reports")
def get_reports():
    return db.reports

@app.post("/api/trigger")
def trigger_event(event: EventTrigger):
    evt_id = str(uuid.uuid4())
    
    initial_state = {
        "event_id": evt_id,
        "event_type": event.event_type,
        "payload": event.payload.dict(),
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
    
    # Run the langgraph simulation
    result = governance_app.invoke(initial_state)
    
    return {
        "event_id": evt_id,
        "path_taken": result["path_taken"],
        "action_taken": result["action_taken"],
        "tvi_score": result["tvi_score"],
        "risk_level": result["risk_level"],
        "audit_trace": result["audit_trace"]
    }
