"""
Flipkart Sales Intelligence System - Real-World Sales Analytics Specialist Agent
Handles revenue, unit volume, order velocity, AOV, category/subcategory/zone/location breakdowns, trends, and charts.
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
- Analyze revenue, unit volumes, Average Order Value (AOV), and customer ratings across dimensions (Category, SubCategory, Zone, Location, Delivery Type, Customer Gender, Age Group, Product Name).
- Identify top-performing and underperforming products and categories.
- Analyze monthly sales trajectories across the 6-year history (2015-2020).
- Produce clean, interactive Plotly charts when visual context is helpful.
STRICT CONSTRAINT: You must NEVER invent or hallucinate numeric values. All calculations are executed strictly via Pandas query tools.
"""

# Real catalog keywords for intelligent entity dispatch
CATALOG_KEYWORDS = [
    "creatine", "supplement", "vitamins", "blood pressure", "toner", "lotion", "foundation",
    "musk", "fragrance", "polo", "shirt", "jeans", "sneakers", "dress", "pants",
    "samsung", "phone", "tablet", "bluetooth", "theatre", "canon", "camera", "wardrobe", "bowl"
]

CATEGORIES = [
    "health and beauty", "health", "beauty", "fashion", "phones and tablet",
    "phone", "tablet", "mobile", "home and office", "home", "office", "electronics"
]
ZONES = ["zone 1", "zone 2", "zone 3", "zone 4"]
DELIVERY_TYPES = ["express", "standard delivery", "standard", "shipped from abroad", "abroad", "international"]
GENDERS = ["male", "female", "men", "women"]

def run_sales_agent(state: AgentState) -> AgentState:
    """Executes the Sales Analytics specialist node."""
    query = state["query"].lower()
    tool_traces = state.get("tool_traces", [])
    agent_results = state.get("agent_results", {})
    charts = state.get("charts", [])
    
    sales_data = {}
    
    # 1. Check for specific product / entity lookup
    matched_prod = next((p for p in CATALOG_KEYWORDS if p in query), None)
    matched_cat = next((c for c in CATEGORIES if c in query), None)
    matched_zone = next((z for z in ZONES if z in query), None)
    matched_dt = next((d for d in DELIVERY_TYPES if d in query), None)
    matched_g = next((g for g in GENDERS if g in query), None)
    
    if matched_prod or (matched_cat and (matched_zone or matched_dt or matched_g)):
        trace_lookup = execute_tool_with_trace(
            lookup_entity_analytics,
            product_name=matched_prod,
            category=matched_cat,
            zone=matched_zone,
            delivery_type=matched_dt,
            customer_gender="M" if matched_g in ["male", "men"] else ("F" if matched_g in ["female", "women"] else None)
        )
        trace_lookup["agent"] = "Sales Analytics Agent"
        tool_traces.append(trace_lookup)
        if trace_lookup["status"] == "success":
            sales_data["specific_entity_lookup"] = trace_lookup["result"]

    # 2. Check if KPIs requested
    if any(w in query for w in ["kpi", "overview", "total revenue", "total sales", "summary", "how much revenue", "how many orders", "aov", "performance", "volume"]):
        trace = execute_tool_with_trace(get_kpi_summary)
        trace["agent"] = "Sales Analytics Agent"
        tool_traces.append(trace)
        if trace["status"] == "success":
            sales_data["kpis"] = trace["result"]

    # 3. Dimension Breakdown
    dim_found = None
    if "subcategory" in query or "sub-category" in query:
        dim_found = "SubCategory"
    elif "category" in query or "categories" in query:
        dim_found = "Category"
    elif "zone" in query:
        dim_found = "Zone"
    elif "location" in query or "city" in query or "region" in query:
        dim_found = "Location"
    elif "delivery type" in query or "delivery method" in query or "express" in query:
        dim_found = "Delivery Type"
    elif "gender" in query or "demographic" in query:
        dim_found = "Customer Gender"
    elif "age" in query or "age group" in query:
        dim_found = "Age Group"
    elif "product" in query or "sku" in query or "item" in query:
        dim_found = "Product Name"
    elif "status" in query or "delivered" in query or "returned" in query:
        dim_found = "Status"
        
    if dim_found:
        trace = execute_tool_with_trace(query_sales_by_dimension, dimension=dim_found)
        trace["agent"] = "Sales Analytics Agent"
        tool_traces.append(trace)
        if trace["status"] == "success":
            sales_data[f"sales_by_{dim_found.lower().replace(' ', '_')}"] = trace["result"]

    # 4. Top/Bottom Products
    if any(w in query for w in ["top", "best", "bottom", "worst", "lowest", "highest", "ranking", "most sold"]):
        metric = "Total Sales (INR)"
        if "profit" in query: metric = "Profit (INR)"
        elif "unit" in query or "quantity" in query: metric = "units"
        elif "rating" in query: metric = "rating"
        elif "return" in query: metric = "return"
        
        is_asc = any(w in query for w in ["bottom", "worst", "lowest", "least"])
        trace_top = execute_tool_with_trace(get_top_bottom_products, n=5, metric=metric, ascending=is_asc)
        trace_top["agent"] = "Sales Analytics Agent"
        tool_traces.append(trace_top)
        if trace_top["status"] == "success":
            sales_data["top_bottom_products"] = trace_top["result"]

    # 5. Monthly Sales Trend
    if any(w in query for w in ["trend", "month", "monthly", "historical", "over time", "history", "growth"]):
        trace_trend = execute_tool_with_trace(get_monthly_sales_trend)
        trace_trend["agent"] = "Sales Analytics Agent"
        tool_traces.append(trace_trend)
        if trace_trend["status"] == "success":
            sales_data["monthly_trend"] = trace_trend["result"]

    # Visual Chart Generation
    if any(w in query for w in ["chart", "plot", "graph", "visual", "show me", "bar", "pie"]):
        c_type = "line" if "trend" in query or "month" in query else ("pie" if "share" in query or "ratio" in query else "bar")
        target_dim = dim_found or "Category"
        trace_chart = execute_tool_with_trace(generate_sales_chart, chart_type=c_type, dimension=target_dim)
        trace_chart["agent"] = "Sales Analytics Agent"
        tool_traces.append(trace_chart)
        if trace_chart["status"] == "success" and trace_chart["result"]:
            charts.append(trace_chart["result"])

    agent_results["sales_analytics"] = sales_data
    state["tool_traces"] = tool_traces
    state["agent_results"] = agent_results
    state["charts"] = charts
    return state
