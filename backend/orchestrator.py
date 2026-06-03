from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode

from state import GovernanceState
from agents import reasoner_node, formatter_node, route_reasoner, tools

def build_agentic_governance_graph():
    workflow = StateGraph(GovernanceState)
    
    # Add Nodes
    workflow.add_node("reasoner", reasoner_node)
    workflow.add_node("tools", ToolNode(tools))
    workflow.add_node("formatter", formatter_node)
    
    # Edges
    workflow.add_edge(START, "reasoner")
    
    # Conditional edge from reasoner
    workflow.add_conditional_edges(
        "reasoner",
        route_reasoner,
        {
            "tools": "tools",
            "formatter": "formatter"
        }
    )
    
    # Tool node always goes back to reasoner
    workflow.add_edge("tools", "reasoner")
    
    # Formatter ends the graph
    workflow.add_edge("formatter", END)
    
    app = workflow.compile()
    return app

# Singleton for importing
governance_app = build_agentic_governance_graph()
