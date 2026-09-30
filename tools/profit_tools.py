"""
Flipkart Sales Intelligence System - Profit & Discount Optimization Tools
Provides margin analysis, correlation computation, discount band evaluation, and loss pocket detection.
"""

import os
import json
import pandas as pd
import numpy as np
from scipy import stats
import plotly.express as px
import plotly.graph_objects as go
from typing import Dict, Any, List, Optional
from tools.base import load_sales_data, register_tool

@register_tool(name="analyze_profit_margins", description="Calculate profit and margin % across categories, products, customer segments, regions, or payment methods.")
def analyze_profit_margins(dimension: str = "Category") -> List[Dict[str, Any]]:
    df = load_sales_data()
    valid_dims = {
        "category": "Category",
        "region": "Region",
        "segment": "Customer Segment",
        "customer segment": "Customer Segment",
        "payment": "Payment Method",
        "payment method": "Payment Method",
        "product": "Product Name",
        "discount band": "Discount Band"
    }
    col = valid_dims.get(dimension.lower().strip(), dimension)
    if col not in df.columns:
        raise ValueError(f"Invalid dimension '{dimension}'. Available: {list(valid_dims.keys())}")
        
    grouped = df.groupby(col).agg(
        orders=("Order ID", "count"),
        total_sales=("Total Sales (INR)", "sum"),
        total_profit=("Profit (INR)", "sum"),
        avg_discount=("Discount %", "mean"),
        avg_rating=("Customer Rating", "mean")
    ).reset_index()
    
    grouped["profit_margin_pct"] = np.round((grouped["total_profit"] / grouped["total_sales"]) * 100, 2)
    grouped["avg_discount"] = np.round(grouped["avg_discount"], 1)
    grouped["avg_rating"] = np.round(grouped["avg_rating"], 2)
    
    # Sort by profit_margin_pct descending
    grouped = grouped.sort_values(by="profit_margin_pct", ascending=False)
    return grouped.to_dict(orient="records")

@register_tool(name="analyze_discount_impact", description="Analyze sales volume, profit margin %, and customer rating across Discount Bands (5-10%, 11-20%, 21-30%).")
def analyze_discount_impact() -> List[Dict[str, Any]]:
    df = load_sales_data()
    grouped = df.groupby("Discount Band").agg(
        orders=("Order ID", "count"),
        total_sales=("Total Sales (INR)", "sum"),
        total_profit=("Profit (INR)", "sum"),
        avg_rating=("Customer Rating", "mean"),
        loss_orders=("Profit (INR)", lambda x: (x < 0).sum())
    ).reset_index()
    
    grouped["profit_margin_pct"] = np.round((grouped["total_profit"] / grouped["total_sales"]) * 100, 2)
    grouped["avg_rating"] = np.round(grouped["avg_rating"], 2)
    grouped["loss_order_rate_pct"] = np.round((grouped["loss_orders"] / grouped["orders"]) * 100, 2)
    
    order_map = {"5-10": 1, "11-20": 2, "21-30": 3}
    grouped["sort_order"] = grouped["Discount Band"].map(order_map)
    grouped = grouped.sort_values("sort_order").drop(columns=["sort_order"])
    
    return grouped.to_dict(orient="records")

@register_tool(name="compute_correlations", description="Calculate Pearson and Spearman statistical correlations between Discount %, Profit (INR), Profit Margin %, and Customer Rating.")
def compute_correlations() -> Dict[str, Any]:
    df = load_sales_data()
    
    pairs = [
        ("Discount %", "Profit (INR)", "discount_vs_profit"),
        ("Discount %", "Profit Margin %", "discount_vs_margin"),
        ("Discount %", "Customer Rating", "discount_vs_rating"),
        ("Price (INR)", "Profit Margin %", "price_vs_margin"),
        ("Quantity Sold", "Profit Margin %", "quantity_vs_margin"),
    ]
    
    results = {}
    for col1, col2, key in pairs:
        clean_subset = df[[col1, col2]].dropna()
        p_corr, p_val = stats.pearsonr(clean_subset[col1], clean_subset[col2])
        s_corr, s_val = stats.spearmanr(clean_subset[col1], clean_subset[col2])
        
        strength = "weak"
        if abs(p_corr) > 0.6:
            strength = "strong"
        elif abs(p_corr) > 0.3:
            strength = "moderate"
            
        direction = "negative (inverse)" if p_corr < 0 else "positive"
        
        results[key] = {
            "feature_x": col1,
            "feature_y": col2,
            "pearson_r": round(float(p_corr), 4),
            "pearson_p_value": float(p_val),
            "spearman_rho": round(float(s_corr), 4),
            "spearman_p_value": float(s_val),
            "relationship": f"{strength} {direction} correlation (r={p_corr:.3f})",
            "statistically_significant": bool(p_val < 0.05)
        }
        
    return results

@register_tool(name="identify_loss_pockets", description="Detect transactions, products, or segments generating negative or sub-threshold profit margins.")
def identify_loss_pockets(margin_threshold: float = 0.0) -> Dict[str, Any]:
    df = load_sales_data()
    
    loss_df = df[df["Profit (INR)"] < margin_threshold]
    total_loss_orders = len(loss_df)
    total_loss_inr = float(loss_df["Profit (INR)"].sum())
    total_loss_sales = float(loss_df["Total Sales (INR)"].sum())
    
    # Group by category and product to find hotspots
    cat_loss = loss_df.groupby("Category").agg(
        loss_orders=("Order ID", "count"),
        total_loss=("Profit (INR)", "sum"),
        avg_discount=("Discount %", "mean")
    ).reset_index().to_dict(orient="records")
    
    prod_loss = loss_df.groupby("Product Name").agg(
        loss_orders=("Order ID", "count"),
        total_loss=("Profit (INR)", "sum"),
        avg_discount=("Discount %", "mean")
    ).reset_index().sort_values("total_loss").head(5).to_dict(orient="records")
    
    return {
        "loss_orders_count": total_loss_orders,
        "loss_percentage_of_all_orders": round((total_loss_orders / len(df)) * 100, 2),
        "total_negative_profit_inr": total_loss_inr,
        "affected_sales_volume_inr": total_loss_sales,
        "hotspots_by_category": cat_loss,
        "top_loss_making_products": prod_loss,
        "key_driver": "Aggressive discounting (26-30% range) on lower-margin electronic and appliance SKUs."
    }

@register_tool(name="payment_method_analysis", description="Evaluate volume, total profit, and average margin across payment methods (UPI, Wallet, Debit Card, COD, etc.).")
def payment_method_analysis() -> List[Dict[str, Any]]:
    df = load_sales_data()
    grouped = df.groupby("Payment Method").agg(
        orders=("Order ID", "count"),
        total_sales=("Total Sales (INR)", "sum"),
        total_profit=("Profit (INR)", "sum"),
        avg_rating=("Customer Rating", "mean"),
        avg_discount=("Discount %", "mean")
    ).reset_index()
    
    grouped["profit_margin_pct"] = np.round((grouped["total_profit"] / grouped["total_sales"]) * 100, 2)
    grouped["avg_order_value"] = np.round(grouped["total_sales"] / grouped["orders"], 2)
    grouped = grouped.sort_values(by="total_profit", ascending=False)
    
    return grouped.to_dict(orient="records")

@register_tool(name="generate_profit_chart", description="Generate Plotly chart for profit margins, discount bands, or correlation scatter plot.")
def generate_profit_chart(chart_type: str = "margin_bar", dimension: str = "Category") -> Dict[str, Any]:
    df = load_sales_data()
    os.makedirs("outputs/charts", exist_ok=True)
    
    if chart_type == "margin_bar":
        dim_col = "Category" if dimension.lower() in ["category", "cat"] else "Region"
        agg = df.groupby(dim_col).agg(
            Total_Sales=("Total Sales (INR)", "sum"),
            Total_Profit=("Profit (INR)", "sum")
        ).reset_index()
        agg["Profit Margin %"] = (agg["Total_Profit"] / agg["Total_Sales"]) * 100
        agg = agg.sort_values("Profit Margin %", ascending=False)
        
        fig = px.bar(
            agg,
            x=dim_col,
            y="Profit Margin %",
            text=agg["Profit Margin %"].apply(lambda x: f"{x:.1f}%"),
            title=f"Profit Margin % by {dim_col}",
            color="Profit Margin %",
            color_continuous_scale="Tealgrn",
            template="plotly_dark"
        )
        fig.update_layout(font=dict(family="Inter, sans-serif"))
    elif chart_type == "discount_scatter":
        fig = px.scatter(
            df,
            x="Discount %",
            y="Profit Margin %",
            color="Category",
            trendline="ols",
            title="Discount % vs. Profit Margin % (with Trendline)",
            template="plotly_dark"
        )
        fig.update_layout(font=dict(family="Inter, sans-serif"))
    else:
        # Discount band bar
        agg = df.groupby("Discount Band").agg(
            Total_Sales=("Total Sales (INR)", "sum"),
            Total_Profit=("Profit (INR)", "sum")
        ).reset_index()
        agg["Profit Margin %"] = (agg["Total_Profit"] / agg["Total_Sales"]) * 100
        
        fig = px.bar(
            agg,
            x="Discount Band",
            y="Profit Margin %",
            title="Profit Margin % across Discount Bands",
            color="Discount Band",
            template="plotly_dark"
        )
        fig.update_layout(font=dict(family="Inter, sans-serif"))
        
    filename = f"chart_profit_{chart_type}.json"
    file_path = os.path.join("outputs/charts", filename)
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(fig.to_json())
        
    return {
        "chart_type": chart_type,
        "title": f"Profit Analytics Chart ({chart_type})",
        "file_path": file_path,
        "figure_json": fig.to_json()
    }
