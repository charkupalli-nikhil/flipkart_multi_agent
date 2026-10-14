"""
Flipkart Sales Intelligence System - Real-World Profit & Margin Optimization Tools
Provides margin analysis, reverse logistics & return diagnostics, statistical correlations,
and loss pocket detection across the 133,503-record dataset.
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

@register_tool(
    name="analyze_profit_margins",
    description="Calculate gross & realized profit, margin %, and return rates across Category, SubCategory, Zone, Location, Delivery Type, or Margin Band."
)
def analyze_profit_margins(dimension: str = "Category") -> List[Dict[str, Any]]:
    df = load_sales_data()
    valid_dims = {
        "category": "Category",
        "subcategory": "SubCategory",
        "sub-category": "SubCategory",
        "zone": "Zone",
        "region": "Region",
        "location": "Location",
        "delivery type": "Delivery Type",
        "delivery": "Delivery Type",
        "gender": "Customer Gender",
        "age group": "Age Group",
        "segment": "Customer Segment",
        "margin band": "Margin Band",
        "discount band": "Discount Band",
        "product": "Product Name",
        "payment": "Payment Method",
        "payment method": "Payment Method"
    }
    col = valid_dims.get(dimension.lower().strip(), "Category")
    if col not in df.columns:
        col = "Category"
        
    is_ret = df["Is Returned"] if "Is Returned" in df.columns else (df["Status"] == "Returned")
    df["_tmp_ret"] = is_ret.astype(int)

    grouped = df.groupby(col).agg(
        orders=("Order ID", "count"),
        total_sales=("Total Sales (INR)", "sum"),
        total_profit=("Profit (INR)", "sum"),
        return_orders=("_tmp_ret", "sum"),
        avg_price=("Sale Price (INR)", "mean"),
        avg_rating=("Customer Rating", "mean")
    ).reset_index()
    
    grouped["profit_margin_pct"] = np.round((grouped["total_profit"] / grouped["total_sales"]) * 100, 2)
    grouped["return_rate_pct"] = np.round((grouped["return_orders"] / grouped["orders"]) * 100, 2)
    grouped["avg_price"] = np.round(grouped["avg_price"], 2)
    grouped["avg_rating"] = np.round(grouped["avg_rating"], 2)
    
    # Sort by profit_margin_pct descending
    grouped = grouped.sort_values(by="profit_margin_pct", ascending=False)
    return grouped.to_dict(orient="records")

@register_tool(
    name="analyze_return_impact",
    description="Analyze return rates, return root causes, and reverse logistics financial losses across categories, subcategories, and delivery types."
)
def analyze_return_impact() -> Dict[str, Any]:
    df = load_sales_data()
    is_ret = df["Is Returned"] if "Is Returned" in df.columns else (df["Status"] == "Returned")
    returned_df = df[is_ret]
    
    total_orders = len(df)
    total_returns = len(returned_df)
    overall_return_rate = round((total_returns / total_orders) * 100, 2)
    
    # Financial impact of returns
    forfeited_revenue = float(returned_df["Total Sales (INR)"].sum())
    shipping_loss = float(returned_df["Shipping Fee (INR)"].sum()) if "Shipping Fee (INR)" in returned_df.columns else float(returned_df["Shipping Fee"].sum())
    forfeited_profit = float(returned_df["Profit (INR)"].sum())
    
    # Reasons breakdown
    reasons_agg = returned_df["Return Reason"].value_counts().reset_index()
    reasons_agg.columns = ["Return Reason", "Count"]
    reasons_agg["Share_Pct"] = np.round((reasons_agg["Count"] / total_returns) * 100, 2)
    
    # Category return rates
    cat_returns = df.groupby("Category").agg(
        total_orders=("Order ID", "count"),
        returns=("Is Returned" if "Is Returned" in df.columns else "Status", lambda x: (x == "Returned" if isinstance(x.iloc[0], str) else x).sum()),
        revenue=("Total Sales (INR)", "sum")
    ).reset_index()
    cat_returns["return_rate_pct"] = np.round((cat_returns["returns"] / cat_returns["total_orders"]) * 100, 2)
    cat_returns = cat_returns.sort_values(by="return_rate_pct", ascending=False)
    
    # Delivery Type return rates
    dtype_returns = df.groupby("Delivery Type").agg(
        orders=("Order ID", "count"),
        returns=("Is Returned" if "Is Returned" in df.columns else "Status", lambda x: (x == "Returned" if isinstance(x.iloc[0], str) else x).sum()),
        avg_delivery_days=("Delivery Days", "mean") if "Delivery Days" in df.columns else ("Order ID", "count")
    ).reset_index()
    dtype_returns["return_rate_pct"] = np.round((dtype_returns["returns"] / dtype_returns["orders"]) * 100, 2)
    if "Delivery Days" in df.columns:
        dtype_returns["avg_delivery_days"] = np.round(dtype_returns["avg_delivery_days"], 1)

    return {
        "total_orders_analyzed": total_orders,
        "returned_orders_count": total_returns,
        "overall_return_rate_pct": overall_return_rate,
        "forfeited_gross_revenue_inr": forfeited_revenue,
        "forfeited_gross_profit_inr": forfeited_profit,
        "reverse_logistics_shipping_loss_inr": shipping_loss,
        "total_financial_drag_inr": forfeited_profit + shipping_loss,
        "top_return_reasons": reasons_agg.to_dict(orient="records"),
        "returns_by_category": cat_returns.to_dict(orient="records"),
        "returns_by_delivery_type": dtype_returns.to_dict(orient="records"),
        "strategic_takeaway": (
            f"Reducing return rate from {overall_return_rate}% down to 18% would recover "
            f"over ₹{(forfeited_profit * 0.33):,.2f} in forfeited profit and eliminate packaging waste."
        )
    }

@register_tool(
    name="analyze_discount_impact",
    description="Analyze sales volume and profit margin % across Discount Bands."
)
def analyze_discount_impact() -> List[Dict[str, Any]]:
    df = load_sales_data()
    group_col = "Discount Band"
    
    is_ret = df["Is Returned"] if "Is Returned" in df.columns else (df["Status"] == "Returned")
    df["_tmp_ret"] = is_ret.astype(int)

    grouped = df.groupby(group_col).agg(
        orders=("Order ID", "count"),
        total_sales=("Total Sales (INR)", "sum"),
        total_profit=("Profit (INR)", "sum"),
        avg_rating=("Customer Rating", "mean"),
        return_orders=("_tmp_ret", "sum")
    ).reset_index()
    
    grouped["profit_margin_pct"] = np.round((grouped["total_profit"] / grouped["total_sales"]) * 100, 2)
    grouped["return_rate_pct"] = np.round((grouped["return_orders"] / grouped["orders"]) * 100, 2)
    grouped["avg_rating"] = np.round(grouped["avg_rating"], 2)
    
    return grouped.to_dict(orient="records")

@register_tool(
    name="compute_correlations",
    description="Calculate statistical correlations between Delivery Days, Sale Price, Quantity, Profit Margin, and Customer Rating."
)
def compute_correlations() -> Dict[str, Any]:
    df = load_sales_data()
    
    pairs = [
        ("Discount %", "Profit (INR)", "discount_vs_profit"),
        ("Sale Price (INR)", "Profit Margin %", "price_vs_margin"),
        ("Quantity Sold", "Profit Margin %", "quantity_vs_margin"),
        ("Customer Rating", "Profit Margin %", "rating_vs_margin"),
    ]
    if "Delivery Days" in df.columns:
        pairs.append(("Delivery Days", "Customer Rating", "delivery_days_vs_rating"))
    if "Discount %" in df.columns:
        pairs.append(("Discount %", "Profit Margin %", "discount_vs_margin"))
        
    results = {}
    for col1, col2, key in pairs:
        clean_subset = df[[col1, col2]].dropna()
        p_corr, p_val = stats.pearsonr(clean_subset[col1], clean_subset[col2])
        s_corr, s_val = stats.spearmanr(clean_subset[col1], clean_subset[col2])
        
        strength = "weak"
        if abs(p_corr) > 0.5:
            strength = "strong"
        elif abs(p_corr) > 0.2:
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

@register_tool(
    name="identify_loss_pockets",
    description="Detect products, categories, zones, or subcategories with low margins or high return rates."
)
def identify_loss_pockets(margin_threshold: float = 0.0) -> Dict[str, Any]:
    df = load_sales_data()
    
    loss_subset = df[df["Profit (INR)"] < margin_threshold] if margin_threshold <= 0 else df[df["Profit Margin %"] < margin_threshold]
    total_loss_orders = len(loss_subset)
    total_loss_inr = float(loss_subset["Profit (INR)"].sum())
    
    # Subcategories with margins below threshold
    subcat_agg = df.groupby("SubCategory").agg(
        orders=("Order ID", "count"),
        total_sales=("Total Sales (INR)", "sum"),
        total_profit=("Profit (INR)", "sum"),
        avg_rating=("Customer Rating", "mean")
    ).reset_index()
    subcat_agg["margin_pct"] = np.round((subcat_agg["total_profit"] / subcat_agg["total_sales"]) * 100, 2)
    threshold_for_subcats = margin_threshold if margin_threshold > 0 else 45.0
    low_margin_subcats = subcat_agg[subcat_agg["margin_pct"] < threshold_for_subcats].sort_values("margin_pct").to_dict(orient="records")
    
    # High return subcategories
    is_ret = df["Is Returned"] if "Is Returned" in df.columns else (df["Status"] == "Returned")
    df["_tmp_ret"] = is_ret.astype(int)
    
    ret_agg = df.groupby("SubCategory").agg(
        orders=("Order ID", "count"),
        returns=("_tmp_ret", "sum")
    ).reset_index()
    ret_agg["return_rate_pct"] = np.round((ret_agg["returns"] / ret_agg["orders"]) * 100, 2)
    high_return_subcats = ret_agg.sort_values("return_rate_pct", ascending=False).head(5).to_dict(orient="records")

    # High return zones
    zone_ret = df.groupby("Zone").agg(
        orders=("Order ID", "count"),
        returns=("_tmp_ret", "sum")
    ).reset_index()
    zone_ret["return_rate_pct"] = np.round((zone_ret["returns"] / zone_ret["orders"]) * 100, 2)
    high_return_zones = zone_ret.sort_values("return_rate_pct", ascending=False).to_dict(orient="records")

    return {
        "loss_orders_count": total_loss_orders,
        "total_negative_profit_inr": total_loss_inr,
        "margin_threshold_pct": margin_threshold,
        "subcategories_below_margin_threshold": low_margin_subcats,
        "top_high_return_subcategories": high_return_subcats,
        "zone_return_distribution": high_return_zones,
        "key_driver": "Product fit expectations and shipping delays across overseas and distant logistics zones."
    }

@register_tool(
    name="payment_method_analysis",
    description="Evaluate order volume, profit, margin %, and delivery SLA across Payment Methods."
)
def payment_method_analysis() -> List[Dict[str, Any]]:
    df = load_sales_data()
    group_col = "Payment Method"
    
    grouped = df.groupby(group_col).agg(
        orders=("Order ID", "count"),
        total_sales=("Total Sales (INR)", "sum"),
        total_profit=("Profit (INR)", "sum"),
        avg_rating=("Customer Rating", "mean"),
        avg_delivery=("Delivery Days", "mean") if "Delivery Days" in df.columns else ("Order ID", "count")
    ).reset_index()
    
    grouped["profit_margin_pct"] = np.round((grouped["total_profit"] / grouped["total_sales"]) * 100, 2)
    grouped["avg_order_value"] = np.round(grouped["total_sales"] / grouped["orders"], 2)
    if "Delivery Days" in df.columns:
        grouped["avg_delivery_days"] = np.round(grouped["avg_delivery"], 1)
        grouped = grouped.drop(columns=["avg_delivery"])
    grouped = grouped.sort_values(by="total_profit", ascending=False)
    
    return grouped.to_dict(orient="records")

@register_tool(
    name="generate_profit_chart",
    description="Generate Plotly chart for profit margins, returns by reason, or category margins."
)
def generate_profit_chart(chart_type: str = "margin_bar", dimension: str = "Category") -> Dict[str, Any]:
    df = load_sales_data()
    os.makedirs("outputs/charts", exist_ok=True)
    
    if chart_type == "returns_bar" or "return" in chart_type:
        is_ret = df["Is Returned"] if "Is Returned" in df.columns else (df["Status"] == "Returned")
        ret_df = df[is_ret]["Return Reason"].value_counts().reset_index()
        ret_df.columns = ["Return Reason", "Count"]
        fig = px.bar(
            ret_df,
            x="Count",
            y="Return Reason",
            orientation="h",
            title="Return Incidents by Root Cause Reason",
            template="plotly_dark",
            color="Count",
            color_continuous_scale="Reds"
        )
        fig.update_layout(
            font=dict(family="Plus Jakarta Sans, sans-serif"),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)"
        )
    elif chart_type == "margin_bar":
        dim_col = "Category" if dimension.lower() in ["category", "cat"] else ("Zone" if "zone" in dimension.lower() else "SubCategory")
        agg = df.groupby(dim_col).agg(
            Total_Sales=("Total Sales (INR)", "sum"),
            Total_Profit=("Profit (INR)", "sum")
        ).reset_index()
        agg["Profit Margin %"] = np.round((agg["Total_Profit"] / agg["Total_Sales"]) * 100, 2)
        agg = agg.sort_values("Profit Margin %", ascending=False).head(10)
        
        fig = px.bar(
            agg,
            x=dim_col,
            y="Profit Margin %",
            text=agg["Profit Margin %"].apply(lambda x: f"{x:.1f}%"),
            title=f"Profit Margin % by {dim_col}",
            color="Profit Margin %",
            color_continuous_scale="Viridis",
            template="plotly_dark"
        )
        fig.update_layout(
            font=dict(family="Plus Jakarta Sans, sans-serif"),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)"
        )
    else:
        # Scatter or Category vs Realized
        agg = df.groupby("Category").agg(
            Gross_Profit=("Profit (INR)", "sum"),
            Realized_Profit=("Realized Profit (INR)", "sum") if "Realized Profit (INR)" in df.columns else ("Profit (INR)", "sum")
        ).reset_index()
        fig = px.bar(
            agg,
            x="Category",
            y=["Gross_Profit", "Realized_Profit"],
            barmode="group",
            title="Gross vs Realized Profit (INR) by Category",
            template="plotly_dark",
            color_discrete_map={"Gross_Profit": "#6366F1", "Realized_Profit": "#10B981"}
        )
        fig.update_layout(
            font=dict(family="Plus Jakarta Sans, sans-serif"),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)"
        )
        
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
