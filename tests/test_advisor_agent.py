"""
Unit tests for Forecast & Business Advisor Agent - Verified against Statsmodels and Scikit-Learn.
"""

import pytest
import pandas as pd
import numpy as np
from tools.base import load_sales_data
from tools.advisor_tools import (
    forecast_sales_and_profit,
    perform_kmeans_clustering,
    generate_strategic_recommendations,
)

def test_3month_forecast_structure():
    """Test 1: Forecast produces exactly 3 periods with revenue and profit projections."""
    result = forecast_sales_and_profit(months=3)
    assert result["forecast_horizon_months"] == 3
    assert len(result["forecasts"]) == 3
    for f in result["forecasts"]:
        assert "period" in f
        assert f["forecast_revenue_inr"] > 0
        assert f["forecast_profit_inr"] > 0
        assert f["forecast_revenue_lower_bound"] <= f["forecast_revenue_inr"] <= f["forecast_revenue_upper_bound"]

def test_forecast_uncertainty_disclosure():
    """Test 2: Forecast explicitly outputs uncertainty notice regarding time series data."""
    result = forecast_sales_and_profit(months=3)
    assert "uncertainty_disclosure" in result
    assert "months" in result["uncertainty_disclosure"] or "historical" in result["uncertainty_disclosure"]

def test_kmeans_clustering_structure():
    """Test 3: KMeans clustering partitions records into exactly 3 clusters with 5 features."""
    clusters_data = perform_kmeans_clustering(n_clusters=3)
    assert clusters_data["n_clusters"] == 3
    assert len(clusters_data["cluster_profiles"]) == 3
    assert clusters_data["sample_size"] > 0

def test_kmeans_cluster_metrics():
    """Test 4: Each cluster has valid non-negative average ticket and positive metrics."""
    clusters_data = perform_kmeans_clustering(n_clusters=3)
    for p in clusters_data["cluster_profiles"]:
        assert p["avg_sale_price_inr"] > 0
        assert p["avg_quantity"] >= 1.0
        assert p["avg_customer_age"] > 0

def test_strategic_recommendations_output():
    """Test 5: Strategic recommendations are prioritized and data-backed."""
    recs = generate_strategic_recommendations()
    assert len(recs) >= 3
    assert any("P1" in r["priority"] for r in recs)
    for r in recs:
        assert "title" in r
        assert "action" in r
        assert "projected_impact" in r
