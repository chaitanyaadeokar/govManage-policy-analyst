"""
Base agentic framework with ReAct reasoning loop.
All specialized agents inherit from this to gain autonomous reasoning capabilities.
"""
import json
from typing import Dict, Any, List, Optional, Callable
from abc import ABC, abstractmethod
from datetime import datetime

from langchain_core.messages import SystemMessage, HumanMessage, AIMessage, ToolMessage
from langchain_groq import ChatGroq
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode
from typing_extensions import TypedDict

from agentic_core.memory import shared_memory


class AgentState(TypedDict):
    """State for ReAct reasoning loop."""
    event_id: str
    messages: List
    iteration: int
    max_iterations: int
    final_output: Optional[Dict[str, Any]]
    agent_name: str


class BaseAgenticAgent(ABC):
    """
    Base class for all agentic agents.
    Implements ReAct (Reasoning + Acting) loop with tool use.
    """
    
    def __init__(
        self,
        agent_name: str,
        model_name: str = "openai/gpt-oss-120b",  # Use a model that supports tools better
        temperature: float = 0.1,
        max_iterations: int = 10
    ):
        self.agent_name = agent_name
        self.max_iterations = max_iterations
        
        # Initialize LLM
        self.llm = ChatGroq(model_name=model_name, temperature=temperature)
        
        # Get agent-specific tools
        self.tools = self.get_tools()
        
        # Bind tools to LLM (only if tools exist)
        if self.tools:
            try:
                self.llm_with_tools = self.llm.bind_tools(self.tools)
            except Exception as e:
                print(f"[{agent_name}] Warning: Could not bind tools: {e}")
                print(f"[{agent_name}] Running without tool binding")
                self.llm_with_tools = self.llm
        else:
            self.llm_with_tools = self.llm
        
        # Build ReAct graph
        self.app = self._build_react_graph()
    
    @abstractmethod
    def get_tools(self) -> List[Callable]:
        """Return list of tools this agent can use."""
        pass
    
    @abstractmethod
    def get_system_prompt(self) -> str:
        """Return the system prompt defining agent's role and reasoning approach."""
        pass
    
    @abstractmethod
    def format_final_output(self, state: AgentState) -> Dict[str, Any]:
        """Format the final output after reasoning loop completes."""
        pass
    
    def _build_react_graph(self) -> StateGraph:
        """Build the ReAct reasoning graph."""
        workflow = StateGraph(AgentState)
        
        # Add nodes
        workflow.add_node("reason", self._reason_node)
        if self.tools:
            workflow.add_node("act", ToolNode(self.tools))
        workflow.add_node("finalize", self._finalize_node)
        
        # Add edges
        workflow.add_edge(START, "reason")
        workflow.add_conditional_edges(
            "reason",
            self._route_after_reasoning,
            {
                "act": "act" if self.tools else END,
                "finalize": "finalize",
                "continue": "reason"
            }
        )
        if self.tools:
            workflow.add_edge("act", "reason")
        workflow.add_edge("finalize", END)
        
        return workflow.compile()
    
    def _reason_node(self, state: AgentState) -> Dict[str, Any]:
        """
        Core reasoning node - implements the 'Think' step of ReAct.
        Agent analyzes current context and decides next action.
        """
        messages = state["messages"]
        event_id = state["event_id"]
        iteration = state.get("iteration", 0)
        
        # Check for messages from other agents
        agent_messages = shared_memory.get_agent_messages(event_id, self.agent_name)
        if agent_messages:
            collab_context = "\n".join([
                f"[Message from {msg['from']}]: {json.dumps(msg['message'])}"
                for msg in agent_messages
            ])
            messages.append(HumanMessage(content=f"Collaboration context:\n{collab_context}"))
        
        # Get relevant episodic memory
        context = shared_memory.get_working_context(event_id)
        if context and iteration == 0:
            event_type = context.get("event_type")
            similar_cases = shared_memory.query_similar_cases(event_type, limit=3)
            if similar_cases:
                memory_context = f"\nRelevant past cases:\n{json.dumps(similar_cases, indent=2)}"
                messages.append(HumanMessage(content=memory_context))
        
        # Invoke LLM with tools
        response = self.llm_with_tools.invoke(messages)
        
        return {
            "messages": [response],
            "iteration": iteration + 1
        }
    
    def _route_after_reasoning(self, state: AgentState) -> str:
        """Route based on agent's decision."""
        messages = state["messages"]
        last_message = messages[-1]
        iteration = state.get("iteration", 0)
        max_iterations = state.get("max_iterations", self.max_iterations)
        
        # Check if max iterations reached
        if iteration >= max_iterations:
            return "finalize"
        
        # Check if agent wants to use tools
        if hasattr(last_message, "tool_calls") and last_message.tool_calls:
            return "act"
        
        # Check if agent signals completion
        if hasattr(last_message, "content"):
            content = last_message.content.lower()
            if any(phrase in content for phrase in ["final answer", "conclusion:", "my analysis is complete"]):
                return "finalize"
        
        # Continue reasoning if needed
        if iteration < 3:  # Allow at least 3 reasoning steps
            return "continue"
        
        return "finalize"
    
    def _finalize_node(self, state: AgentState) -> Dict[str, Any]:
        """Finalize and format output."""
        final_output = self.format_final_output(state)
        
        # Store findings in shared memory
        event_id = state["event_id"]
        shared_memory.add_agent_finding(event_id, self.agent_name, final_output)
        
        return {"final_output": final_output}
    
    def process_event(self, event_id: str, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main entry point for processing an event.
        Runs the full ReAct reasoning loop.
        """
        # Initialize working memory
        shared_memory.set_working_context(event_id, event_data)
        
        # Create initial message
        system_prompt = self.get_system_prompt()
        event_description = self._format_event_description(event_data)
        
        initial_state = {
            "event_id": event_id,
            "messages": [
                SystemMessage(content=system_prompt),
                HumanMessage(content=event_description)
            ],
            "iteration": 0,
            "max_iterations": self.max_iterations,
            "final_output": None,
            "agent_name": self.agent_name
        }
        
        # Run ReAct loop
        result = self.app.invoke(initial_state)
        
        return result.get("final_output", {})
    
    def _format_event_description(self, event_data: Dict[str, Any]) -> str:
        """Format event data for agent consumption."""
        return f"""
Event Analysis Request:
Event ID: {event_data.get('event_id', 'unknown')}
Event Type: {event_data.get('event_type', 'unknown')}
Payload: {json.dumps(event_data.get('payload', {}), indent=2)}

Analyze this event using your specialized capabilities. Use available tools to gather information.
Think step-by-step and provide thorough reasoning for your conclusions.
"""
    
    def collaborate_with(self, event_id: str, target_agent: str, message: Dict[str, Any]):
        """Send a message to another agent."""
        shared_memory.send_agent_message(event_id, self.agent_name, target_agent, message)
    
    def reflect_on_outcome(self, event_id: str, decision: Dict[str, Any], outcome: Dict[str, Any]):
        """Reflect on decision outcome for learning."""
        shared_memory.add_episodic_memory(event_id, decision, outcome)
