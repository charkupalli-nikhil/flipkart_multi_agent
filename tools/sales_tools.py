"""
Flipkart Sales Intelligence System - Sales Analytics Tools
Provides tools for revenue, quantity, AOV, top/bottom products, and Plotly charts.
"""

import os
import json
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from typing import Dict, Any, List, Optional
from tools.base import load_sales_data, register_tool

@register_tool(name="get_kpi_summary", description="Calculate executive KPIs: Total Revenue, Total Profit, Profit Margin, Units Sold, Total Orders, Average Rating, and AOV.")
def get_kpi_summary() -> Dict[str, Any]:
    df = load_sales_data()
    total_sales = float(df["Total Sales (INR)"].sum())
    total_profit = float(df["Profit (INR)"].sum())
    total_units = int(df["Quantity Sold"].sum())
    total_orders = int(len(df))
    avg_rating = float(np.round(df["Customer Rating"].mean(), 2))
    aov = float(np.round(total_sales / total_orders, 2)) if total_orders > 0 else 0.0
    overall_margin = float(np.round((total_profit / total_sales) * 100, 2)) if total_sales > 0 else 0.0
    
    return {
        "total_revenue_inr": total_sales,
        "total_profit_inr": total_profit,
        "profit_margin_pct": overall_margin,
        "total_units_sold": total_units,
        "total_orders": total_orders,
        "average_customer_rating": avg_rating,
        "average_order_value_inr": aov,
        "formatted_revenue": f"₹{total_sales:,.2f}",
        "formatted_profit": f"₹{total_profit:,.2f}",
        "formatted_aov": f"₹{aov:,.2f}",
    }

@register_tool(name="query_sales_by_dimension", description="Aggregate sales metrics grouped by any dimension (Category, Region, Customer Segment, Payment Method, Product Name).")
def query_sales_by_dimension(dimension: str = "Category") -> List[Dict[str, Any]]:
    df = load_sales_data()
    valid_dims = {
        "category": "Category",
        "region": "Region",
        "segment": "Customer Segment",
        "customer segment": "Customer Segment",
        "payment": "Payment Method",
        "payment method": "Payment Method",
        "product": "Product Name",
        "product name": "Product Name",
        "month": "Month",
        "year-month": "Year-Month",
        "discount band": "Discount Band"
    }
    col = valid_dims.get(dimension.lower().strip(), dimension)
    if col not in df.columns:
        raise ValueError(f"Invalid dimension '{dimension}'. Available: {list(valid_dims.keys())}")
        
    grouped = df.groupby(col).agg(
        orders=("Order ID", "count"),
        total_sales=("Total Sales (INR)", "sum"),
        total_profit=("Profit (INR)", "sum"),
        units_sold=("Quantity Sold", "sum"),
        avg_price=("Price (INR)", "mean"),
        avg_rating=("Customer Rating", "mean"),
        avg_discount=("Discount %", "mean")
    ).reset_index()
    
    grouped["profit_margin_pct"] = np.round((grouped["total_profit"] / grouped["total_sales"]) * 100, 2)
    grouped["avg_order_value"] = np.round(grouped["total_sales"] / grouped["orders"], 2)
    grouped["avg_rating"] = np.round(grouped["avg_rating"], 2)
    grouped["avg_discount"] = np.round(grouped["avg_discount"], 1)
    
    # Sort by total_sales descending
    grouped = grouped.sort_values(by="total_sales", ascending=False)
    
    records = grouped.to_dict(orient="records")
    return records

@register_tool(name="get_top_bottom_products", description="Retrieve top or bottom N products ranked by Total Sales, Profit, Units Sold, or Rating.")
def get_top_bottom_products(n: int = 5, metric: str = "Total Sales (INR)", ascending: bool = False) -> List[Dict[str, Any]]:
    df = load_sales_data()
    
    metric_map = {
        "sales": "Total Sales (INR)",
        "total sales": "Total Sales (INR)",
        "revenue": "Total Sales (INR)",
        "profit": "Profit (INR)",
        "units": "Quantity Sold",
        "quantity": "Quantity Sold",
        "rating": "Customer Rating"
    }
    target_metric = metric_map.get(metric.lower().strip(), metric)
    if target_metric not in df.columns:
        target_metric = "Total Sales (INR)"
        
    grouped = df.groupby(["Product Name", "Category"]).agg(
        orders=("Order ID", "count"),
        total_sales=("Total Sales (INR)", "sum"),
        total_profit=("Profit (INR)", "sum"),
        units_sold=("Quantity Sold", "sum"),
        avg_rating=("Customer Rating", "mean"),
        avg_discount=("Discount %", "mean")
    ).reset_index()
    
    grouped["profit_margin_pct"] = np.round((grouped["total_profit"] / grouped["total_sales"]) * 100, 2)
    grouped["avg_rating"] = np.round(grouped["avg_rating"], 2)
    
    sort_col = "total_sales"
    if "profit" in target_metric.lower():
        sort_col = "total_profit"
    elif "quantity" in target_metric.lower() or "units" in target_metric.lower():
        sort_col = "units_sold"
    elif "rating" in target_metric.lower():
        sort_col = "avg_rating"
        
    sorted_df = grouped.sort_values(by=sort_col, ascending=ascending).head(n)
    return sorted_df.to_dict(orient="records")

@register_tool(name="get_monthly_sales_trend", description="Calculate chronological monthly sales, profit, order count, and growth velocity.")
def get_monthly_sales_trend() -> List[Dict[str, Any]]:
    df = load_sales_data()
    monthly = df.groupby("Year-Month").agg(
        orders=("Order ID", "count"),
        total_sales=("Total Sales (INR)", "sum"),
        total_profit=("Profit (INR)", "sum"),
        units_sold=("Quantity Sold", "sum"),
        avg_discount=("Discount %", "mean"),
        avg_rating=("Customer Rating", "mean")
    ).reset_index().sort_values("Year-Month")
    
    monthly["profit_margin_pct"] = np.round((monthly["total_profit"] / monthly["total_sales"]) * 100, 2)
    monthly["avg_order_value"] = np.round(monthly["total_sales"] / monthly["orders"], 2)
    monthly["avg_rating"] = np.round(monthly["avg_rating"], 2)
    
    # MoM sales growth %
    monthly["sales_growth_pct"] = np.round(monthly["total_sales"].pct_change() * 100, 2).fillna(0.0)
    
    return monthly.to_dict(orient="records")

@register_tool(name="generate_sales_chart", description="Generate an interactive Plotly chart (bar, line, pie, scatter) and save to outputs/charts/.")
def generate_sales_chart(chart_type: str = "bar", dimension: str = "Category", metric: str = "Total Sales (INR)", title: Optional[str] = None) -> Dict[str, Any]:
    df = load_sales_data()
    os.makedirs("outputs/charts", exist_ok=True)
    
    valid_dims = {
        "category": "Category",
        "region": "Region",
        "segment": "Customer Segment",
        "payment": "Payment Method",
        "product": "Product Name",
        "month": "Year-Month",
        "discount band": "Discount Band"
    }
    dim_col = valid_dims.get(dimension.lower().strip(), "Category")
    
    if chart_type == "bar":
        agg_df = df.groupby(dim_col)["Total Sales (INR)"].sum().reset_index().sort_values("Total Sales (INR)", ascending=False)
        fig = px.bar(
            agg_df,
            x=dim_col,
            y="Total Sales (INR)",
            title=title or f"Total Sales by {dim_col}",
            color=dim_col,
            template="plotly_dark",
            labels={"Total Sales (INR)": "Revenue (₹)", dim_col: dim_col},
            color_discrete_sequence=px.colors.qualitative.Prism
        )
        fig.update_layout(showlegend=False, font=dict(family="Inter, sans-serif"))
        
    elif chart_type == "line":
        agg_df = df.groupby("Year-Month").agg(
            Revenue=("Total Sales (INR)", "sum"),
            Profit=("Profit (INR)", "sum")
        ).reset_index().sort_values("Year-Month")
        fig = px.line(
            agg_df,
            x="Year-Month",
            y=["Revenue", "Profit"],
            title=title or "Monthly Revenue & Profit Trajectory",
            template="plotly_dark",
            markers=True,
            color_discrete_map={"Revenue": "#6366F1", "Profit": "#10B981"}
        )
        fig.update_layout(font=dict(family="Inter, sans-serif"), yaxis_title="Amount (₹)")
        
    elif chart_type == "pie" or chart_type == "donut":
        agg_df = df.groupby(dim_col)["Total Sales (INR)"].sum().reset_index()
        fig = px.pie(
            agg_df,
            names=dim_col,
            values="Total Sales (INR)",
            hole=0.45 if chart_type == "donut" else 0.0,
            title=title or f"Revenue Share by {dim_col}",
            template="plotly_dark",
            color_discrete_sequence=px.colors.qualitative.Pastel
        )
        fig.update_layout(font=dict(family="Inter, sans-serif"))
    else:
        # Scatter/Default
        fig = px.scatter(
            df,
            x="Discount %",
            y="Profit (INR)",
            color="Category",
            size="Quantity Sold",
            title=title or "Discount % vs Profit (INR)",
            template="plotly_dark"
        )
        fig.update_layout(font=dict(family="Inter, sans-serif"))
        
    filename = f"chart_{dim_col.lower().replace(' ', '_')}_{chart_type}.json"
    file_path = os.path.join("outputs/charts", filename)
    
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(fig.to_json())
        
    return {
        "chart_type": chart_type,
        "title": title or f"Sales Chart by {dim_col}",
        "file_path": file_path,
        "figure_json": fig.to_json()
    }
