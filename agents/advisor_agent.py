"""
Flipkart Sales Intelligence System - Forecast & Business Advisor Specialist Agent
Handles time-series forecasting, customer/order KMeans clustering, and prioritized business recommendations.
"""

from typing import Dict, Any, List
from agents.state import AgentState
from tools.base import execute_tool_with_trace
from tools.advisor_tools import (
    forecast_sales_and_profit,
    perform_kmeans_clustering,
    generate_strategic_recommendations,
)

ADVISOR_AGENT_SYSTEM_PROMPT = """
You are the Forecast & Business Advisor Specialist Agent for Flipkart Sales Intelligence System.
Your responsibility:
- Forecast monthly sales revenue and profit for the next 3 months using time-series models (Holt-Winters).
- Clearly communicate model uncertainty and confidence intervals given the ~12-month synthetic span (Feb 2024 - Feb 2025).
- Segment order behavioral archetypes using KMeans clustering on Price, Quantity, Discount %, Profit, and Customer Rating.
- Provide high-impact, data-backed strategic recommendations with clear priority rankings.
STRICT CONSTRAINT: Always mention time-based dataset limitations when discussing forecasts. Ground all recommendations in computed data.
"""

def run_advisor_agent(state: AgentState) -> AgentState:
    """Executes the Forecast & Business Advisor specialist node."""
    query = state["query"].lower()
    tool_traces = state.get("tool_traces", [])
    agent_results = state.get("agent_results", {})
    charts = state.get("charts", [])
    
    advisor_data = {}
    
    # 1. 3-Month Forecast
    if any(w in query for w in ["forecast", "future", "predict", "next 3 months", "projection", "upcoming", "q1", "q2", "next quarter"]):
        trace_fc = execute_tool_with_trace(forecast_sales_and_profit, months=3)
        trace_fc["agent"] = "Forecast & Business Advisor"
        tool_traces.append(trace_fc)
        if trace_fc["status"] == "success":
            advisor_data["forecast"] = trace_fc["result"]
            if "figure_json" in trace_fc["result"]:
                charts.append({
                    "chart_type": "line",
                    "title": "3-Month Forward Sales & Profit Forecast",
                    "file_path": trace_fc["result"].get("chart_path", ""),
                    "figure_json": trace_fc["result"]["figure_json"]
                })

    # 2. KMeans Customer/Order Clustering
    if any(w in query for w in ["cluster", "segment", "archetype", "kmeans", "persona", "behavior", "grouping"]):
        trace_km = execute_tool_with_trace(perform_kmeans_clustering, n_clusters=3)
        trace_km["agent"] = "Forecast & Business Advisor"
        tool_traces.append(trace_km)
        if trace_km["status"] == "success":
            advisor_data["clustering"] = trace_km["result"]

    # 3. Strategic Recommendations
    if any(w in query for w in ["recommend", "what should we do", "strategy", "action", "advice", "advisor", "improve", "optimize", "fix", "mitigate"]):
        trace_rec = execute_tool_with_trace(generate_strategic_recommendations)
        trace_rec["agent"] = "Forecast & Business Advisor"
        tool_traces.append(trace_rec)
        if trace_rec["status"] == "success":
            advisor_data["recommendations"] = trace_rec["result"]

    # Fallback if invoked generally or as part of a multi-agent chain
    if not advisor_data:
        trace_rec = execute_tool_with_trace(generate_strategic_recommendations)
        trace_rec["agent"] = "Forecast & Business Advisor"
        tool_traces.append(trace_rec)
        advisor_data["recommendations"] = trace_rec["result"]

    agent_results["business_advisor"] = advisor_data
    state["tool_traces"] = tool_traces
    state["agent_results"] = agent_results
    state["charts"] = charts
    return state
