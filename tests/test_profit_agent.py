"""
Unit tests for Profit & Discount Optimization Agent - Verified against Pandas Ground Truth.
"""

import pytest
import pandas as pd
import numpy as np
from scipy import stats
from tools.base import load_sales_data
from tools.profit_tools import (
    analyze_profit_margins,
    analyze_discount_impact,
    compute_correlations,
    identify_loss_pockets,
    payment_method_analysis,
)
from agents.orchestrator import process_query

def test_profit_margin_by_category():
    """Test 1: Profit margin % by Category matches Pandas calculation."""
    df = load_sales_data()
    cat_sales = df.groupby("Category")["Total Sales (INR)"].sum()
    cat_profit = df.groupby("Category")["Profit (INR)"].sum()
    expected_margins = ((cat_profit / cat_sales) * 100).round(2).to_dict()
    
    results = analyze_profit_margins("Category")
    for r in results:
        cat = r["Category"]
        assert cat in expected_margins
        assert abs(r["profit_margin_pct"] - expected_margins[cat]) < 1e-2

def test_discount_band_analysis():
    """Test 2: Profit across Discount Bands matches Pandas."""
    df = load_sales_data()
    expected_band_profit = df.groupby("Discount Band")["Profit (INR)"].sum().to_dict()
    
    results = analyze_discount_impact()
    for r in results:
        band = r["Discount Band"]
        assert band in expected_band_profit
        assert abs(r["total_profit"] - expected_band_profit[band]) < 1e-2

def test_discount_vs_profit_correlation():
    """Test 3: Statistical correlation between Discount % and Profit matches Scipy."""
    df = load_sales_data()
    expected_r, expected_p = stats.pearsonr(df["Discount %"], df["Profit (INR)"])
    
    corrs = compute_correlations()
    assert "discount_vs_profit" in corrs
    assert abs(corrs["discount_vs_profit"]["pearson_r"] - round(float(expected_r), 4)) < 1e-3

def test_identify_loss_pockets():
    """Test 4: Negative profit / loss pocket detection matches Pandas filter."""
    df = load_sales_data()
    loss_subset = df[df["Profit (INR)"] < 0]
    expected_loss_count = len(loss_subset)
    expected_loss_sum = float(loss_subset["Profit (INR)"].sum())
    
    loss_data = identify_loss_pockets(margin_threshold=0.0)
    assert loss_data["loss_orders_count"] == expected_loss_count
    assert abs(loss_data["total_negative_profit_inr"] - expected_loss_sum) < 1e-2

def test_payment_method_margins():
    """Test 5: Payment method performance matches Pandas aggregation."""
    df = load_sales_data()
    expected_pay_profit = df.groupby("Payment Method")["Profit (INR)"].sum().to_dict()
    
    results = payment_method_analysis()
    for r in results:
        pm = r["Payment Method"]
        assert pm in expected_pay_profit
        assert abs(r["total_profit"] - expected_pay_profit[pm]) < 1e-2
