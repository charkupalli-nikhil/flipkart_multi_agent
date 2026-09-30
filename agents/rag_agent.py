"""
Flipkart Sales Intelligence System - Knowledge Base (RAG) Agent
Retrieves unstructured information from the knowledge base using semantic search.
"""

from typing import Dict, Any
from agents.state import AgentState
from tools.rag_tools import query_knowledge_base

def run_rag_agent(state: AgentState) -> AgentState:
    """
    Executes the RAG agent to retrieve relevant unstructured information.
    """
    query = state["query"]
    
    print(f"[RAG Agent] Retrieving knowledge for query: {query}")
    
    rag_results = query_knowledge_base(query)
    
    if "agent_results" not in state:
        state["agent_results"] = {}
        
    state["agent_results"]["rag"] = {
        "knowledge_base_retrieval": rag_results
    }
    
    return state
