from langgraph.graph import StateGraph, END
from state import GovernanceState
from agents import (
    preprocess_event_node,
    policy_analyst_node,
    compliance_node,
    risk_assessment_node,
    decision_engine_node,
    action_engine_node,
    audit_node,
    reporting_node
)

def build_governance_graph():
    # Initialize StateGraph
    workflow = StateGraph(GovernanceState)

    # Add Nodes
    workflow.add_node("Preprocessor", preprocess_event_node)
    
    # Actually, in LangGraph parallel execution can be done by specifying parallel nodes but simpler is sequential for demo or just define them.
    # We will just map them sequentially for simplicity without losing the logic context.
    # The architecture states Orchestrator -> Parallel(Policy, Compliance, Risk). We can add edges.
    
    workflow.add_node("PolicyAnalyst", policy_analyst_node)
    workflow.add_node("Compliance", compliance_node)
    workflow.add_node("RiskAssessment", risk_assessment_node)
    
    workflow.add_node("DecisionEngine", decision_engine_node)
    workflow.add_node("ActionEngine", action_engine_node)
    workflow.add_node("Audit", audit_node)
    workflow.add_node("Reporting", reporting_node)
    
    # Define edges. We will execute them sequentially for the data dependencies
    # since LangGraph handles parallel branch merging differently if doing multi-node paths without a common merger.
    # Real world: Preproc -> Policy -> Compliance -> Risk -> Decision -> Action -> Audit -> Reporting
    workflow.add_edge("Preprocessor", "PolicyAnalyst")
    workflow.add_edge("PolicyAnalyst", "Compliance")
    workflow.add_edge("Compliance", "RiskAssessment")
    workflow.add_edge("RiskAssessment", "DecisionEngine")
    
    workflow.add_edge("DecisionEngine", "ActionEngine")
    workflow.add_edge("ActionEngine", "Audit")
    workflow.add_edge("Audit", "Reporting")
    workflow.add_edge("Reporting", END)
    
    workflow.set_entry_point("Preprocessor")
    
    # Compile
    app = workflow.compile()
    
    return app

# Singleton for importing
governance_app = build_governance_graph()
