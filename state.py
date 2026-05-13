from typing import TypedDict, List, Dict, Any, Optional
from typing import TypedDict, Annotated, List, Dict, Any, Optional
from langgraph.graph.message import add_messages
from pydantic import BaseModel, Field

class GovernanceDecision(BaseModel):
    """The final strict decision structure required by the system."""
    risk_level: str = Field(description="Must be 'Low', 'Medium', or 'High'")
    tvi_score: float = Field(description="The numeric Threat x Vulnerability x Impact score (0-100)")
    path_taken: str = Field(description="Must be 'Safe Path', 'Review Path', or 'Block Path'")
    action_taken: str = Field(description="Must be 'Approved', 'Flagged for Human Review', or 'Auto Blocked'")
    status: str = Field(description="Must be 'Approved', 'Review', or 'Blocked'")
    audit_trace: List[str] = Field(description="A step-by-step trace of the reasoning logic and rules checked.")
    rules_used: List[Dict[str, Any]] = Field(description="List of rule or policy dictionaries that influenced the decision.")
    ai_explanation: str = Field(description="A concise 3-5 bullet point AI governance explanation of the decision.")

class GovernanceState(TypedDict):
    """Represents the state of the agentic workflow."""
    # Input
    event_id: str
    event_type: str
    payload: Dict[str, Any]
    
    # LangGraph State
    messages: Annotated[list, add_messages]
    
    # Output
    final_decision: Optional[GovernanceDecision]
