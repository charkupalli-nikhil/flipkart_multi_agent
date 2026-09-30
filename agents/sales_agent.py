"""
Flipkart Sales Intelligence System - Sales Analytics Specialist Agent
Handles revenue, unit volume, AOV, category/product/regional/segment breakdowns, trends, and charts.
"""

import re
from typing import Dict, Any, List
from agents.state import AgentState
from tools.base import execute_tool_with_trace
from tools.sales_tools import (
    get_kpi_summary,
    query_sales_by_dimension,
    get_top_bottom_products,
    get_monthly_sales_trend,
    generate_sales_chart,
)
from tools.query_tools import lookup_entity_analytics

SALES_AGENT_SYSTEM_PROMPT = """
You are the Sales Analytics Specialist Agent for Flipkart Sales Intelligence System.
Your responsibility:
- Analyze revenue, unit volumes, Average Order Value (AOV), and customer ratings across dimensions (Category, Region, Customer Segment, Payment Method, Product).
- Identify top-performing and underperforming products and categories.
- Analyze monthly sales trajectories and velocity.
- Produce clean, interactive Plotly charts when visual context is helpful.
STRICT CONSTRAINT: You must NEVER invent or hallucinate numeric values. All calculations are executed strictly via Pandas query tools.
"""

# Catalog keywords for intelligent entity dispatch
CATALOG_PRODUCTS = [
    "smartphone", "earbuds", "smartwatch", "tv", "laptop",
    "python", "data science", "ai revolution", "fiction", "habit mastery",
    "air fryer", "cookware", "vacuum", "coffee maker", "bedsheet",
    "face serum", "serum", "lipstick", "sunscreen", "shampoo", "anti-aging",
    "casual shirt", "shirt", "jeans", "denim", "running shoes", "shoes", "kurta", "hoodie"
]

CATEGORIES = ["electronics", "books", "home & kitchen", "home", "kitchen", "beauty", "clothing"]
REGIONS = ["north", "south", "east", "west"]
SEGMENTS = ["retail", "online", "wholesale"]
PAYMENTS = ["upi", "wallet", "debit", "credit", "cod", "net banking"]

def run_sales_agent(state: AgentState) -> AgentState:
    """Executes the Sales Analytics specialist node."""
    query = state["query"].lower()
    tool_traces = state.get("tool_traces", [])
    agent_results = state.get("agent_results", {})
    charts = state.get("charts", [])
    
    sales_data = {}
    
    # 1. Check for specific product / entity lookup
    matched_prod = next((p for p in CATALOG_PRODUCTS if p in query), None)
    matched_cat = next((c for c in CATEGORIES if c in query), None)
    matched_reg = next((r for r in REGIONS if r in query), None)
    matched_seg = next((s for s in SEGMENTS if s in query), None)
    matched_pay = next((p for p in PAYMENTS if p in query), None)
    
    if matched_prod or (matched_cat and (matched_reg or matched_seg or matched_pay)):
        trace_lookup = execute_tool_with_trace(
            lookup_entity_analytics,
            product_name=matched_prod,
            category=matched_cat,
            region=matched_reg,
            segment=matched_seg,
            payment_method=matched_pay
        )
        trace_lookup["agent"] = "Sales Analytics Agent"
        tool_traces.append(trace_lookup)
        if trace_lookup["status"] == "success":
            sales_data["specific_entity_lookup"] = trace_lookup["result"]

    # 2. Check if KPIs requested
    if any(w in query for w in ["kpi", "overview", "total revenue", "total sales", "summary", "how much revenue", "how many orders", "aov", "performance"]):
        trace = execute_tool_with_trace(get_kpi_summary)
        trace["agent"] = "Sales Analytics Agent"
        tool_traces.append(trace)
        if trace["status"] == "success":
            sales_data["kpis"] = trace["result"]

    # 3. Dimension Breakdown
    dim_found = None
    if "category" in query or "categories" in query:
        dim_found = "Category"
    elif "region" in query or "regional" in query:
        dim_found = "Region"
    elif "segment" in query or "wholesale" in query or "retail" in query:
        dim_found = "Customer Segment"
    elif "payment" in query:
        dim_found = "Payment Method"
    elif "product" in query or "item" in query:
        dim_found = "Product Name"
        
    if dim_found:
        trace = execute_tool_with_trace(query_sales_by_dimension, dimension=dim_found)
        trace["agent"] = "Sales Analytics Agent"
        tool_traces.append(trace)
        if trace["status"] == "success":
            sales_data[f"sales_by_{dim_found.lower().replace(' ', '_')}"] = trace["result"]
            sales_data["sales_by_category"] = trace["result"]

    # 4. Top / Bottom Products
    if any(w in query for w in ["top", "best", "highest", "bottom", "worst", "lowest", "rank", "most sold"]):
        is_bottom = any(w in query for w in ["bottom", "worst", "lowest"])
        n_match = re.search(r"\b(\d+)\b", query)
        n = int(n_match.group(1)) if n_match and int(n_match.group(1)) <= 25 else 5
        
        trace = execute_tool_with_trace(get_top_bottom_products, n=n, metric="Total Sales (INR)", ascending=is_bottom)
        trace["agent"] = "Sales Analytics Agent"
        tool_traces.append(trace)
        if trace["status"] == "success":
            sales_data["top_products"] = trace["result"]

    # 5. Monthly Trend
    if any(w in query for w in ["month", "trend", "monthly", "time", "growth", "trajectory", "history"]):
        trace = execute_tool_with_trace(get_monthly_sales_trend)
        trace["agent"] = "Sales Analytics Agent"
        tool_traces.append(trace)
        if trace["status"] == "success":
            sales_data["monthly_trend"] = trace["result"]

    # Fallback if empty
    if not sales_data:
        t1 = execute_tool_with_trace(get_kpi_summary)
        t1["agent"] = "Sales Analytics Agent"
        tool_traces.append(t1)
        sales_data["kpis"] = t1["result"]
        
        t2 = execute_tool_with_trace(query_sales_by_dimension, dimension="Category")
        t2["agent"] = "Sales Analytics Agent"
        tool_traces.append(t2)
        sales_data["sales_by_category"] = t2["result"]

    # Chart Generation
    if any(w in query for w in ["chart", "plot", "graph", "visual", "show me", "trend", "breakdown", "top"]):
        chart_dim = dim_found or "Category"
        chart_type = "line" if "trend" in query or "month" in query else "bar"
        trace_chart = execute_tool_with_trace(generate_sales_chart, chart_type=chart_type, dimension=chart_dim)
        trace_chart["agent"] = "Sales Analytics Agent"
        tool_traces.append(trace_chart)
        if trace_chart["status"] == "success" and trace_chart["result"]:
            charts.append(trace_chart["result"])

    agent_results["sales_analytics"] = sales_data
    state["tool_traces"] = tool_traces
    state["agent_results"] = agent_results
    state["charts"] = charts
    return state
