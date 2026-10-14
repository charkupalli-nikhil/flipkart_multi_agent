"""
Flipkart Sales Intelligence System - Profit & Margin Optimization Specialist Agent
Handles profit margin analysis, return rate diagnostics, statistical correlations, and loss pocket detection.
"""

from typing import Dict, Any, List
from agents.state import AgentState
from tools.base import execute_tool_with_trace
from tools.profit_tools import (
    analyze_profit_margins,
    analyze_return_impact,
    analyze_discount_impact,
    compute_correlations,
    identify_loss_pockets,
    payment_method_analysis,
    generate_profit_chart,
)

PROFIT_AGENT_SYSTEM_PROMPT = """
You are the Profit & Optimization Specialist Agent for Flipkart Sales Intelligence System.
Your responsibility:
- Analyze gross and realized profit margins across categories, subcategories, zones, delivery types, and locations.
- Evaluate return rate impact (27.0% return rate across catalog) and reverse logistics financial leakage.
- Provide statistical correlations between delivery duration, price, rating, and margins.
- Detect unprofitable pockets or low-margin subcategories and recommend pricing remedies.
STRICT CONSTRAINT: Provide statistically rigorous calculations computed directly using Pandas and Scipy tools. Never guess numbers.
"""

def run_profit_agent(state: AgentState) -> AgentState:
    """Executes the Profit & Margin Optimization specialist node."""
    query = state["query"].lower()
    tool_traces = state.get("tool_traces", [])
    agent_results = state.get("agent_results", {})
    charts = state.get("charts", [])
    
    profit_data = {}
    
    # 1. Dimension Margins
    dim_found = "Category"
    if "subcategory" in query or "sub-category" in query:
        dim_found = "SubCategory"
    elif "zone" in query or "least profitable zone" in query:
        dim_found = "Zone"
    elif "location" in query or "city" in query or "region" in query:
        dim_found = "Location"
    elif "delivery type" in query or "delivery" in query:
        dim_found = "Delivery Type"
    elif "band" in query or "margin band" in query:
        dim_found = "Margin Band"

    trace_margins = execute_tool_with_trace(analyze_profit_margins, dimension=dim_found)
    trace_margins["agent"] = "Profit & Optimization Agent"
    tool_traces.append(trace_margins)
    if trace_margins["status"] == "success":
        profit_data["profit_margins"] = trace_margins["result"]

    # 2. Return Rate & Reverse Logistics Diagnostics
    if any(w in query for w in ["return", "returns", "refund", "defect", "missing", "reason", "damage", "reverse logistics", "leakage"]):
        trace_ret = execute_tool_with_trace(analyze_return_impact)
        trace_ret["agent"] = "Profit & Optimization Agent"
        tool_traces.append(trace_ret)
        if trace_ret["status"] == "success":
            profit_data["return_diagnostics"] = trace_ret["result"]

    # 3. Statistical Correlations
    if any(w in query for w in ["correlation", "relationship", "stat", "pearson", "spearman", "vs rating", "vs margin", "vs delivery"]):
        trace_corr = execute_tool_with_trace(compute_correlations)
        trace_corr["agent"] = "Profit & Optimization Agent"
        tool_traces.append(trace_corr)
        if trace_corr["status"] == "success":
            profit_data["correlations"] = trace_corr["result"]

    # 4. Loss Pockets & Low Margin Thresholds
    if any(w in query for w in ["loss", "negative", "low margin", "least profitable", "unprofitable", "risk", "pocket", "drain"]):
        trace_loss = execute_tool_with_trace(identify_loss_pockets, margin_threshold=45.0)
        trace_loss["agent"] = "Profit & Optimization Agent"
        tool_traces.append(trace_loss)
        if trace_loss["status"] == "success":
            profit_data["loss_pockets"] = trace_loss["result"]

    # 5. Delivery Type / Fulfillment Profitability
    if any(w in query for w in ["delivery type", "express", "standard", "abroad", "payment", "channel"]):
        trace_pay = execute_tool_with_trace(payment_method_analysis)
        trace_pay["agent"] = "Profit & Optimization Agent"
        tool_traces.append(trace_pay)
        if trace_pay["status"] == "success":
            profit_data["fulfillment_profitability"] = trace_pay["result"]

    # Visual Chart
    if any(w in query for w in ["chart", "plot", "graph", "visual", "show me", "margin", "return"]):
        chart_type = "returns_bar" if "return" in query or "reason" in query else "margin_bar"
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
