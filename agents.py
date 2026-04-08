import os
from typing import Dict, Any, List
from dotenv import load_dotenv

from langchain_core.messages import SystemMessage, HumanMessage
from langchain_groq import ChatGroq

from state import GovernanceState, GovernanceDecision
from tools import get_employee_info, get_compliance_policies, get_hard_rules, get_risk_parameters

load_dotenv()

# Setup LLM
model_name = os.getenv("GROQ_MODEL", "llama3-70b-8192") # default if env not configured
# Note: user wants openai/gpt-oss-120b but passing that exactly via groq since it's the requested behavior
model_name = "openai/gpt-oss-120b"

llm = ChatGroq(model_name=model_name, temperature=0.0)

# Bind tools
tools = [get_employee_info, get_compliance_policies, get_hard_rules, get_risk_parameters]
llm_with_tools = llm.bind_tools(tools)
llm_with_structured_output = llm.with_structured_output(GovernanceDecision)

def reasoner_node(state: GovernanceState) -> Dict:
    """The main LLM reasoner that evaluates the task and decides which tool to call next or formats final output."""
    messages = state.get("messages", [])
    
    if len(messages) == 0:
        event_str = f"Evaluating Event ID: {state['event_id']}, Type: {state['event_type']}\nPayload: {state['payload']}"
        sys_msg = SystemMessage(content=(
            "You are a Senior Governance AI Agent. "
            "\nDatabase Schema Context:\n"
            "- User Info: { user_id, role, clearance, name }\n"
            "- Policy: { policy_id, name, sector, risk }\n"
            "- Rule: { rule_code, description, condition, threshold, severity, action_on_fail }\n"
            "- Risk Parameters: { event_type, threat, vulnerability, impact, weight }\n\n"
            "1. Fetch the user info using get_employee_info. "
            "2. Fetch hard rules using get_hard_rules and policies using get_compliance_policies. "
            "3. Calculate TVI based on get_risk_parameters. "
            "4. Follow the rules carefully! If the rule requires block, you block. If it requires review, review. "
            "ALWAYS CALL TOOLS BEFORE MAKING A DECISION. Provide multiple independent tool calls if possible."
        ))
        messages = [sys_msg, HumanMessage(content=event_str)]
    
    # Invoke the LLM with current message history
    response = llm_with_tools.invoke(messages)
    
    return {"messages": [response]}


def formatter_node(state: GovernanceState) -> Dict:
    """Invoked when the LLM decides it has finished tool-calling and wants to output the final result."""
    messages = state["messages"]
    sys_msg = SystemMessage(content=(
        "You have completed your investigation via tool calls. "
        "Now, summarize all your findings into the strict final structured GovernanceDecision format."
    ))
    
    # Force the strict Pydantic parsing
    final_decision = llm_with_structured_output.invoke(messages + [sys_msg])
    
    return {"final_decision": final_decision}

def route_reasoner(state: GovernanceState):
    """Routing logic."""
    messages = state["messages"]
    last_message = messages[-1]
    
    if hasattr(last_message, "tool_calls") and len(last_message.tool_calls) > 0:
        return "tools"
    
    return "formatter"
