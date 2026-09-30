"""
Flipkart Sales Intelligence System - Profit & Discount Optimization Specialist Agent
Handles profit margin analysis, discount elasticity, statistical correlations, payment methods, and loss pocket detection.
"""

from typing import Dict, Any, List
from agents.state import AgentState
from tools.base import execute_tool_with_trace
from tools.profit_tools import (
    analyze_profit_margins,
    analyze_discount_impact,
    compute_correlations,
    identify_loss_pockets,
    payment_method_analysis,
    generate_profit_chart,
)

PROFIT_AGENT_SYSTEM_PROMPT = """
You are the Profit & Discount Optimization Specialist Agent for Flipkart Sales Intelligence System.
Your responsibility:
- Analyze gross and net profit margins across categories, regions, customer segments, and products.
- Evaluate discount vs. profit and discount vs. customer rating relationships (statistical correlation + discount band grouping).
- Detect unprofitable or loss-making transactions and identify root causes.
- Compare payment gateway profitability.
STRICT CONSTRAINT: Provide statistically rigorous calculations computed directly using Pandas and Scipy/Statsmodels tools. Never guess numbers.
"""

def run_profit_agent(state: AgentState) -> AgentState:
    """Executes the Profit & Discount Optimization specialist node."""
    query = state["query"].lower()
    tool_traces = state.get("tool_traces", [])
    agent_results = state.get("agent_results", {})
    charts = state.get("charts", [])
    
    profit_data = {}
    
    # 1. Dimension Margins
    dim_found = "Category"
    if "region" in query or "least profitable" in query or "most profitable region" in query or "east" in query or "west" in query or "north" in query or "south" in query:
        dim_found = "Region"
    elif "segment" in query or "customer" in query or "wholesale" in query or "retail" in query:
        dim_found = "Customer Segment"
    elif "payment" in query or "upi" in query or "cod" in query or "gateway" in query:
        dim_found = "Payment Method"
    elif "product" in query:
        dim_found = "Product Name"

    trace_margins = execute_tool_with_trace(analyze_profit_margins, dimension=dim_found)
    trace_margins["agent"] = "Profit & Optimization Agent"
    tool_traces.append(trace_margins)
    if trace_margins["status"] == "success":
        profit_data["profit_margins"] = trace_margins["result"]

    # 2. Discount Bands & Impact
    if any(w in query for w in ["discount", "band", "margin", "elasticity", "pricing", "erosion"]):
        trace_disc = execute_tool_with_trace(analyze_discount_impact)
        trace_disc["agent"] = "Profit & Optimization Agent"
        tool_traces.append(trace_disc)
        if trace_disc["status"] == "success":
            profit_data["discount_impact"] = trace_disc["result"]

    # 3. Statistical Correlations
    if any(w in query for w in ["correlation", "relationship", "impact of discount", "vs rating", "vs profit", "stat", "pearson"]):
        trace_corr = execute_tool_with_trace(compute_correlations)
        trace_corr["agent"] = "Profit & Optimization Agent"
        tool_traces.append(trace_corr)
        if trace_corr["status"] == "success":
            profit_data["correlations"] = trace_corr["result"]

    # 4. Loss Pockets & Negative Margins
    if any(w in query for w in ["loss", "negative", "low margin", "least profitable", "unprofitable", "pocket", "risk", "leakage"]):
        trace_loss = execute_tool_with_trace(identify_loss_pockets, margin_threshold=0.0)
        trace_loss["agent"] = "Profit & Optimization Agent"
        tool_traces.append(trace_loss)
        if trace_loss["status"] == "success":
            profit_data["loss_pockets"] = trace_loss["result"]

    # 5. Payment Methods
    if any(w in query for w in ["payment", "gateway", "upi", "cod", "card", "wallet"]):
        trace_pay = execute_tool_with_trace(payment_method_analysis)
        trace_pay["agent"] = "Profit & Optimization Agent"
        tool_traces.append(trace_pay)
        if trace_pay["status"] == "success":
            profit_data["payment_method_analysis"] = trace_pay["result"]

    # Visual Chart
    if any(w in query for w in ["chart", "plot", "graph", "visual", "show me", "margin", "discount"]):
        chart_type = "discount_scatter" if "correlation" in query or "scatter" in query else "margin_bar"
        trace_chart = execute_tool_with_trace(generate_profit_chart, chart_type=chart_type, dimension=dim_found)
        trace_chart["agent"] = "Profit & Optimization Agent"
        tool_traces.append(trace_chart)
        if trace_chart["status"] == "success" and trace_chart["result"]:
            charts.append(trace_chart["result"])

    agent_results["profit_optimization"] = profit_data
    state["tool_traces"] = tool_traces
    state["agent_results"] = agent_results
    state["charts"] = charts
    return state
