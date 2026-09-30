"""
Flipkart Sales Intelligence System - LangGraph Multi-Agent Orchestrator
Coordinates intent classification, routing, agent execution chains, and synthesis.
"""

import os
from typing import Dict, Any, List
from agents.state import AgentState, create_initial_state
from agents.sales_agent import run_sales_agent
from agents.profit_agent import run_profit_agent
from agents.advisor_agent import run_advisor_agent
from agents.rag_agent import run_rag_agent
from tools.llm_provider import get_llm_provider

# Check for out-of-scope triggers
OUT_OF_SCOPE_KEYWORDS = [
    "review text", "reviews text", "customer review sentiment", "user feedback text",
    "customer name", "customer email", "customer id", "user id", "phone number",
    "customer address", "product description", "image url", "delivery boy", "courier tracking"
]

def check_out_of_scope(query: str) -> bool:
    q_lower = query.lower()
    return any(k in q_lower for k in OUT_OF_SCOPE_KEYWORDS)

def route_query(query: str) -> List[str]:
    """Classifies user query intent and determines the agent execution plan."""
    q = query.lower()
    
    is_forecast_or_strategy = any(w in q for w in ["forecast", "future", "predict", "next 3 months", "next quarter", "projection", "cluster", "kmeans", "recommend", "what should we do", "strategy", "advice"])
    is_profit_q = any(w in q for w in ["profit", "margin", "discount", "loss", "unprofitable", "least profitable", "correlation", "payment method", "elasticity"])
    is_sales_q = any(w in q for w in ["revenue", "sales", "kpi", "overview", "top product", "bottom product", "units sold", "aov", "category sales", "monthly trend"])
    is_rag_q = any(w in q for w in ["policy", "return", "guideline", "manual", "rule", "delivery time"])

    # Multi-Agent Combinations:
    if is_rag_q:
        data_agent = None
        if is_forecast_or_strategy: data_agent = "advisor"
        elif is_profit_q: data_agent = "profit"
        elif is_sales_q: data_agent = "sales"
        
        if data_agent:
            return [data_agent, "rag"]
        return ["rag"]
    # "Which region is least profitable and what should we do about it?" -> profit + advisor
    if is_profit_q and any(w in q for w in ["what should we do", "strategy", "recommend", "advice", "how to improve", "how to fix"]):
        return ["profit", "advisor"]
        
    if is_sales_q and any(w in q for w in ["what should we do", "strategy", "recommend", "how to scale"]):
        return ["sales", "advisor"]

    if is_forecast_or_strategy:
        return ["advisor"]

    if is_profit_q and is_sales_q and not any(w in q for w in ["top", "bottom", "kpi", "units"]):
        return ["profit"]
        
    if is_profit_q:
        return ["profit"]
        
    if is_sales_q:
        return ["sales"]
        
    # Default to Sales Agent if general
    return ["sales"]

def refusal_node(state: AgentState) -> AgentState:
    """Handles out-of-scope requests with dataset boundary explanation."""
    state["is_out_of_scope"] = True
    state["refusal_reason"] = (
        "### ⚠️ Query Outside Dataset Scope\n\n"
        "I cannot fulfill this request because the **Flipkart Sales Intelligence Dataset** contains no customer review text, "
        "no product descriptions, and no individual customer IDs.\n\n"
        "**Available verified features include:**\n"
        "- `Order ID`, `Product Name` (25 items), `Category` (5 categories)\n"
        "- `Price (INR)`, `Quantity Sold`, `Total Sales (INR)`, `Profit (INR)`, `Discount %`\n"
        "- `Payment Method`, `Customer Rating` (1.0-5.0), `Customer Segment`, `Region`, `Order Date`\n\n"
        "Please ask questions regarding sales revenue, profit margins, discount elasticity, forward forecasting, or strategic optimization."
    )
    state["final_answer"] = state["refusal_reason"]
    return state

def response_synthesizer_node(state: AgentState) -> AgentState:
    """Merges specialist agent outputs into a unified response."""
    llm = get_llm_provider()
    
    # Flatten collected agent results into a single context dict
    combined_context = {}
    for agent_key, data in state.get("agent_results", {}).items():
        combined_context.update(data)
        
    system_prompt = (
        "You are the Orchestrator for the Flipkart Sales Intelligence Multi-Agent System. "
        "Consolidate the findings from the specialist agents into an executive briefing. "
        "Highlight key revenue figures, margin dynamics, root causes, and actionable recommendations. "
        "Always mention the data time horizon (~12 months: Feb 2024 - Feb 2025) when discussing time-based findings."
    )
    
    final_answer = llm.generate_response(
        system_prompt=system_prompt,
        user_prompt=state["query"],
        tool_context=combined_context
    )
    
    state["final_answer"] = final_answer
    return state

# LangGraph Workflow Construction
def build_orchestrator_graph():
    """Builds and compiles the LangGraph StateGraph workflow."""
    try:
        from langgraph.graph import StateGraph, END
        
        builder = StateGraph(AgentState)
        
        # Add Nodes
        builder.add_node("refusal", refusal_node)
        builder.add_node("sales_agent", run_sales_agent)
        builder.add_node("profit_agent", run_profit_agent)
        builder.add_node("advisor_agent", run_advisor_agent)
        builder.add_node("rag_agent", run_rag_agent)
        builder.add_node("synthesizer", response_synthesizer_node)
        
        # Define conditional entry point
        def orchestrator_router(state: AgentState):
            if check_out_of_scope(state["query"]):
                return "refusal"
            routes = route_query(state["query"])
            state["routing_decision"] = routes
            if routes[0] == "sales":
                return "sales_agent"
            elif routes[0] == "profit":
                return "profit_agent"
            elif routes[0] == "advisor":
                return "advisor_agent"
            elif routes[0] == "rag":
                return "rag_agent"
            return "sales_agent"
            
        builder.set_conditional_entry_point(
            orchestrator_router,
            {
                "refusal": "refusal",
                "sales_agent": "sales_agent",
                "profit_agent": "profit_agent",
                "advisor_agent": "advisor_agent",
                "rag_agent": "rag_agent",
            }
        )
        
        # Define transitions
        def sales_next(state: AgentState):
            routes = state.get("routing_decision", [])
            if len(routes) > 1:
                if routes[1] == "profit": return "profit_agent"
                if routes[1] == "advisor": return "advisor_agent"
                if routes[1] == "rag": return "rag_agent"
            return "synthesizer"

        def profit_next(state: AgentState):
            routes = state.get("routing_decision", [])
            if len(routes) > 1:
                if routes[1] == "advisor": return "advisor_agent"
                if routes[1] == "rag": return "rag_agent"
            return "synthesizer"
            
        def advisor_next(state: AgentState):
            routes = state.get("routing_decision", [])
            if len(routes) > 1 and routes[1] == "rag":
                return "rag_agent"
            return "synthesizer"
            
        builder.add_conditional_edges("sales_agent", sales_next, {"profit_agent": "profit_agent", "advisor_agent": "advisor_agent", "rag_agent": "rag_agent", "synthesizer": "synthesizer"})
        builder.add_conditional_edges("profit_agent", profit_next, {"advisor_agent": "advisor_agent", "rag_agent": "rag_agent", "synthesizer": "synthesizer"})
        builder.add_conditional_edges("advisor_agent", advisor_next, {"rag_agent": "rag_agent", "synthesizer": "synthesizer"})
        builder.add_edge("rag_agent", "synthesizer")
        builder.add_edge("synthesizer", END)
        builder.add_edge("refusal", END)
        
        return builder.compile()
    except Exception as e:
        print(f"[LangGraph] Fallback to direct state execution: {e}")
        return None

_COMPILED_GRAPH = None

def get_orchestrator():
    global _COMPILED_GRAPH
    if _COMPILED_GRAPH is None:
        _COMPILED_GRAPH = build_orchestrator_graph()
    return _COMPILED_GRAPH

def process_query(query: str, chat_history: List[Dict[str, str]] = None) -> AgentState:
    """Main entry point to execute a query through the multi-agent system."""
    initial_state = create_initial_state(query, chat_history)
    
    # 1. Scope check
    if check_out_of_scope(query):
        return refusal_node(initial_state)
        
    routes = route_query(query)
    initial_state["routing_decision"] = routes
    
    graph = get_orchestrator()
    if graph:
        try:
            return graph.invoke(initial_state)
        except Exception as e:
            print(f"[Orchestrator] Graph execution error: {e}. Running sequential fallback.")
            
    # Sequential Fallback Execution
    state = initial_state
    for agent_name in routes:
        if agent_name == "sales":
            state = run_sales_agent(state)
        elif agent_name == "profit":
            state = run_profit_agent(state)
        elif agent_name == "advisor":
            state = run_advisor_agent(state)
        elif agent_name == "rag":
            state = run_rag_agent(state)
            
    state = response_synthesizer_node(state)
    return state
