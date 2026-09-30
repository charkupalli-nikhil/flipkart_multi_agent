"""
Flipkart Sales Intelligence System - Agent State Schema
Defines the shared state schema for LangGraph multi-agent execution.
"""

from typing import Dict, Any, List, Optional, TypedDict

class ToolTrace(TypedDict):
    agent: str
    tool: str
    status: str
    parameters: Dict[str, Any]
    result: Any
    execution_time_sec: float
    error: Optional[str]

class AgentState(TypedDict):
    query: str
    chat_history: List[Dict[str, str]]
    routing_decision: List[str]
    current_agent_index: int
    agent_results: Dict[str, Any]
    tool_traces: List[Dict[str, Any]]
    charts: List[Dict[str, Any]]
    final_answer: str
    is_out_of_scope: bool
    refusal_reason: Optional[str]

def create_initial_state(query: str, chat_history: Optional[List[Dict[str, str]]] = None) -> AgentState:
    """Factory helper to construct clean initial AgentState."""
    return {
        "query": query,
        "chat_history": chat_history or [],
        "routing_decision": [],
        "current_agent_index": 0,
        "agent_results": {},
        "tool_traces": [],
        "charts": [],
        "final_answer": "",
        "is_out_of_scope": False,
        "refusal_reason": None,
    }
