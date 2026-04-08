"""
Professional REST API for Agentic Governance System.
Provides endpoints for event submission, status checking, and analytics.
"""
import os
import uuid
from datetime import datetime
from typing import Dict, Any, Optional

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from dotenv import load_dotenv

from agents import process_governance_event
from database import db

load_dotenv()

app = FastAPI(
    title="Agentic Governance API",
    description="Professional-grade AI governance system with autonomous multi-agent reasoning",
    version="2.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request/Response Models
class GovernanceEventRequest(BaseModel):
    """Request model for governance event submission."""
    event_type: str = Field(..., description="Type of event (e.g., financial_txn, security_alert)")
    payload: Dict[str, Any] = Field(..., description="Event payload with user_id and event-specific data")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "event_type": "financial_txn",
                "payload": {
                    "user_id": "E101",
                    "amount": 1500,
                    "vendor": "Acme Corp",
                    "description": "Software license purchase"
                }
            }
        }
    }


class GovernanceEventResponse(BaseModel):
    """Response model for governance event submission."""
    event_id: str
    status: str
    message: str
    processing_mode: str = "async"


class DecisionResponse(BaseModel):
    """Response model for decision retrieval."""
    event_id: str
    event_type: str
    status: str
    action_taken: str
    path_taken: str
    risk_level: str
    tvi_score: float
    reasoning: str
    timestamp: str
    confidence: Optional[str] = None


class AnalyticsResponse(BaseModel):
    """Response model for system analytics."""
    total_events: int
    approved: int
    blocked: int
    under_review: int
    average_tvi: float
    high_risk_percentage: float


# API Endpoints

@app.get("/")
async def root():
    """API health check and information."""
    return {
        "service": "Agentic Governance API",
        "version": "2.0.0",
        "status": "operational",
        "features": [
            "Multi-agent autonomous reasoning",
            "ReAct-based decision making",
            "Anomaly detection",
            "Episodic learning",
            "Real-time risk assessment"
        ]
    }


@app.post("/api/v2/events", response_model=GovernanceEventResponse)
async def submit_event(
    request: GovernanceEventRequest,
    background_tasks: BackgroundTasks
):
    """
    Submit a governance event for processing.
    
    The event will be processed by autonomous AI agents that:
    - Analyze policy compliance
    - Verify user authorization
    - Assess risk and detect anomalies
    - Make final governance decision
    
    Processing is asynchronous. Use GET /api/v2/events/{event_id} to check status.
    """
    # Generate event ID
    event_id = str(uuid.uuid4())
    
    # Prepare event
    event = {
        "event_id": event_id,
        "event_type": request.event_type,
        "payload": request.payload,
        "submitted_at": datetime.now().isoformat()
    }
    
    # Process in background
    background_tasks.add_task(process_governance_event, event)
    
    return GovernanceEventResponse(
        event_id=event_id,
        status="processing",
        message="Event submitted successfully. Autonomous agents are analyzing.",
        processing_mode="async"
    )


@app.post("/api/v2/events/sync", response_model=DecisionResponse)
async def submit_event_sync(request: GovernanceEventRequest):
    """
    Submit a governance event and wait for synchronous processing.
    
    Use this endpoint when you need immediate decision results.
    Note: May take 10-30 seconds depending on complexity.
    """
    # Generate event ID
    event_id = str(uuid.uuid4())
    
    # Prepare event
    event = {
        "event_id": event_id,
        "event_type": request.event_type,
        "payload": request.payload,
        "submitted_at": datetime.now().isoformat()
    }
    
    # Process synchronously
    try:
        result = process_governance_event(event)
        
        return DecisionResponse(
            event_id=result["event_id"],
            event_type=result["event_type"],
            status=result["status"],
            action_taken=result["action_taken"],
            path_taken=result["path_taken"],
            risk_level=result["risk_level"],
            tvi_score=result["tvi_score"],
            reasoning=result["reasoning"],
            timestamp=result["timestamp"],
            confidence=result.get("confidence")
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")


@app.get("/api/v2/events/{event_id}", response_model=DecisionResponse)
async def get_event_decision(event_id: str):
    """
    Retrieve the decision for a processed event.
    
    Returns 404 if event not found or still processing.
    """
    # Query from database
    actions = db.list_actions()
    event_result = next((a for a in actions if a.get("event_id") == event_id), None)
    
    if not event_result:
        raise HTTPException(
            status_code=404,
            detail=f"Event {event_id} not found. It may still be processing."
        )
    
    return DecisionResponse(
        event_id=event_result["event_id"],
        event_type=event_result["event_type"],
        status=event_result["status"],
        action_taken=event_result["action_taken"],
        path_taken=event_result["path_taken"],
        risk_level=event_result["risk_level"],
        tvi_score=event_result["tvi_score"],
        reasoning=event_result["reasoning"],
        timestamp=event_result["timestamp"],
        confidence=event_result.get("confidence")
    )


@app.get("/api/v2/analytics", response_model=AnalyticsResponse)
async def get_analytics():
    """
    Get system-wide analytics and metrics.
    
    Provides insights into decision patterns, risk levels, and system performance.
    """
    total = db.count_actions()
    approved = db.count_actions_by_status("Approved")
    blocked = db.count_actions_by_status("Blocked")
    review = db.count_actions_by_status("Review")
    avg_tvi = db.average_tvi()
    
    # Calculate high risk percentage
    actions = db.list_actions()
    high_risk_count = sum(1 for a in actions if a.get("risk_level") == "High")
    high_risk_pct = (high_risk_count / total * 100) if total > 0 else 0
    
    return AnalyticsResponse(
        total_events=total,
        approved=approved,
        blocked=blocked,
        under_review=review,
        average_tvi=round(avg_tvi, 3),
        high_risk_percentage=round(high_risk_pct, 2)
    )


@app.get("/api/v2/events")
async def list_recent_events(limit: int = 20):
    """
    List recent governance events and their decisions.
    
    Args:
        limit: Maximum number of events to return (default 20, max 100)
    """
    limit = min(limit, 100)
    actions = db.list_actions()[:limit]
    
    return {
        "count": len(actions),
        "events": [
            {
                "event_id": a["event_id"],
                "event_type": a["event_type"],
                "status": a["status"],
                "action_taken": a["action_taken"],
                "risk_level": a["risk_level"],
                "timestamp": a["timestamp"]
            }
            for a in actions
        ]
    }


@app.get("/api/v2/health")
async def health_check():
    """Detailed health check for monitoring."""
    try:
        # Check database connectivity
        db_status = "healthy" if db.count_actions() >= 0 else "unhealthy"
    except:
        db_status = "unhealthy"
    
    return {
        "status": "healthy" if db_status == "healthy" else "degraded",
        "components": {
            "api": "healthy",
            "database": db_status,
            "agents": "healthy"
        },
        "timestamp": datetime.now().isoformat()
    }


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("API_PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
