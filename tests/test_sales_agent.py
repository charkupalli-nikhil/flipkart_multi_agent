"""
Unit tests for Sales Analytics Agent - Verified against Pandas Ground Truth.
"""

import pytest
import pandas as pd
import numpy as np
from tools.base import load_sales_data
from tools.sales_tools import (
    get_kpi_summary,
    query_sales_by_dimension,
    get_top_bottom_products,
    get_monthly_sales_trend,
)
from agents.orchestrator import process_query

def test_total_revenue_and_kpis():
    """Test 1: Total Revenue and core KPIs match Pandas direct sum."""
    df = load_sales_data()
    expected_sales = float(df["Total Sales (INR)"].sum())
    expected_profit = float(df["Profit (INR)"].sum())
    expected_orders = len(df)
    
    kpis = get_kpi_summary()
    assert kpis["total_orders"] == expected_orders == 1000
    assert abs(kpis["total_revenue_inr"] - expected_sales) < 1e-2
    assert abs(kpis["total_profit_inr"] - expected_profit) < 1e-2
    assert abs(kpis["average_order_value_inr"] - round(expected_sales / expected_orders, 2)) < 1e-2

def test_sales_by_category():
    """Test 2: Category sales breakdown matches Pandas groupby."""
    df = load_sales_data()
    expected_grouped = df.groupby("Category")["Total Sales (INR)"].sum().to_dict()
    
    records = query_sales_by_dimension("Category")
    for r in records:
        cat = r["Category"]
        assert cat in expected_grouped
        assert abs(r["total_sales"] - expected_grouped[cat]) < 1e-2

def test_top_5_products_by_revenue():
    """Test 3: Top 5 products by revenue match Pandas ranked aggregation."""
    df = load_sales_data()
    expected_top5 = df.groupby("Product Name")["Total Sales (INR)"].sum().sort_values(ascending=False).head(5)
    
    top5_results = get_top_bottom_products(n=5, metric="Total Sales (INR)", ascending=False)
    assert len(top5_results) == 5
    result_names = [r["Product Name"] for r in top5_results]
    expected_names = list(expected_top5.index)
    assert result_names == expected_names

def test_monthly_sales_trend():
    """Test 4: Monthly sales progression matches Pandas Year-Month aggregation."""
    df = load_sales_data()
    expected_monthly = df.groupby("Year-Month")["Total Sales (INR)"].sum().to_dict()
    
    trend = get_monthly_sales_trend()
    assert len(trend) == len(expected_monthly)
    for row in trend:
        ym = row["Year-Month"]
        assert ym in expected_monthly
        assert abs(row["total_sales"] - expected_monthly[ym]) < 1e-2

def test_sales_agent_query_processing():
    """Test 5: Sales Agent end-to-end query processing."""
    state = process_query("What is the total revenue and how many units were sold?")
    assert not state["is_out_of_scope"]
    assert "sales_analytics" in state["agent_results"]
    assert len(state["tool_traces"]) >= 1
    assert len(state["final_answer"]) > 50
    assert any(w in state["final_answer"] for w in ["Executive", "Briefing", "Summary", "Sales", "Revenue", "KPI", "Portfolio"])
